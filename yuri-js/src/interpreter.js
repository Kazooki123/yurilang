import { parse } from './parser.js';
import { loadModule } from './modules.js';

const YURI_OPS = {
  plus: (a, b) => a + b,
  with: (a, b) => a + b,
  minus: (a, b) => a - b,
  times: (a, b) => a * b,
  over: (a, b) => a / b
};

class YuriRuntimeError extends Error {
  constructor(message) {
    super(message);
    this.name = 'YuriRuntimeError';
  }
}

const RETURN = Symbol('ReturnSignal');

class ReturnSignal {
  constructor(value) {
    this.type = RETURN;
    this.value = value;
  }
}

function isReturn(v) {
  return v instanceof ReturnSignal;
}

class Interpreter {
  variables = new Map();
  functions = new Map();
  personas = new Map();

  #restoreVars(snapshot) {
    this.variables.clear();
    for (const [k, v] of snapshot) this.variables.set(k, v);
  }

  evaluate(expr) {
    if (typeof expr === 'number' || typeof expr === 'boolean') return expr;

    if (Array.isArray(expr)) {
      if (expr.length === 0) return null;
      if (expr.length === 1) return this.evaluate(expr[0]);

      if (expr.length === 3) {
        const left = this.evaluate(expr[0]);
        const op = expr[1];
        const right = this.evaluate(expr[2]);

        if (op in YURI_OPS) return YURI_OPS[op](left, right);
      }

      return expr.map(e => this.evaluate(e));
    }

    if (typeof expr !== 'string') return expr;

    expr = expr.trim();

    if (expr.startsWith('"') && expr.endsWith('"')) return expr.slice(1, -1);
    if (/^-?\d+$/.test(expr)) return parseInt(expr, 10);

    const asFloat = parseFloat(expr);
    if (!Number.isNaN(asFloat) && String(asFloat) === expr) return asFloat;

    if (expr.startsWith('[[') || expr.startsWith('#[[')) {
      return this.#parseArrayLiteral(expr);
    }

    if (expr.includes('.') && !expr.startsWith('"')) {
      const [objName, field] = expr.split('.', 2);
      const obj = this.variables.get(objName);
      if (obj && typeof obj === 'object' && !Array.isArray(obj)) {
        return obj[field] ?? null;
      }
    }

    if (expr.startsWith('@')) {
      const parts = expr.split(/\s+/);
      const funcName = parts[0].slice(1);
      const rawArgs = parts.slice(1);

      if (!this.functions.has(funcName)) {
        throw new YuriRuntimeError(`Undefined function: @${funcName}`);
      }

      const [params, body] = this.functions.get(funcName);
      const oldVars = new Map(this.variables);

      for (let i = 0; i < params.length; i++) {
        if (i < rawArgs.length) {
          this.variables.set(params[i], this.evaluate(rawArgs[i]));
        }
      }

      let result = null;
      for (const child of body) {
        const ret = this.runNode(child);
        if (isReturn(ret)) {
          result = ret.value;
          break;
        }
      }

      this.#restoreVars(oldVars);
      return result;
    }

    if (this.variables.has(expr)) return this.variables.get(expr);

    return expr;
  }

  #parseArrayLiteral(expr) {
    expr = expr.trim();

    let inner;
    if (expr.startsWith('#[[') && expr.endsWith(']]')) {
      inner = expr.slice(3, -2);
    } else if (expr.startsWith('[[') && expr.endsWith(']]')) {
      inner = expr.slice(2, -2);
    } else return null;

    return inner
      .split(',')
      .map(s => s.trim())
      .filter(Boolean)
      .map(item => {
        if ((item.startsWith('"') && item.endsWith('"')) || (item.startsWith("'") && item.endsWith("'"))) {
          return item.slice(1, -1);
        }

        if (/^-?\d+$/.test(item)) return parseInt(item, 10);

        const f = parseFloat(item);
        return Number.isNaN(f) ? item : f;
      });
  }

  #checkCondition(tokens) {
    const left = this.evaluate(tokens[0]);
    const op = tokens[1];
    const right = this.evaluate(tokens[2]);

    switch (op) {
      case '==':
        return left === right;
      case '!=':
        return left !== right;
      case '>':
        return left > right;
      case '<':
        return left < right;
      case '>=':
        return left >= right;
      case '<=':
        return left <= right;
      default:
        return false;
    }
  }

  #runBody(children) {
    for (const child of children) {
      const result = this.runNode(child);
      if (isReturn(result)) return result;
    }
  }

  #runMap(array, step) {
    if (!Array.isArray(array)) {
      throw new YuriRuntimeError('@affect requires an array on the left side of @>');
    }

    const parts = step.trim().split(/\s+/);
    if (parts.length < 2) {
      throw new YuriRuntimeError('@affect requires a function name');
    }

    const funcName = parts[1];
    if (!this.functions.has(funcName)) {
      throw new YuriRuntimeError(`Undefined function: ${funcName}`);
    }

    return array.map(item => {
      const [params, body] = this.functions.get(funcName);
      const oldVars = new Map(this.variables);

      if (params.length) this.variables.set(params[0], item);

      let result = null;
      for (const child of body) {
        const ret = this.runNode(child);
        if (isReturn(ret)) {
          result = ret.value;
          break;
        }
      }

      this.#restoreVars(oldVars);
      return result;
    });
  }

  #runFilter(array, step) {
    if (!Array.isArray(array)) {
      throw new YuriRuntimeError('@choose requires an array on the left side of @>');
    }

    const parts = step.trim().split(/\s+/);
    if (parts.length < 2) {
      throw new YuriRuntimeError('@choose requires a function name');
    }

    const funcName = parts[1];
    if (!this.functions.has(funcName)) {
      throw new YuriRuntimeError(`Undefined function: ${funcName}`);
    }

    return array.filter(item => {
      const [params, body] = this.functions.get(funcName);
      const oldVars = new Map(this.variables);

      if (params.length) this.variables.set(params[0], item);

      let result = null;
      for (const child of body) {
        const ret = this.runNode(child);
        if (isReturn(ret)) {
          result = ret.value;
          break;
        }
      }

      this.#restoreVars(oldVars);
      return result;
    });
  }

  runNode(node) {
    switch (node.type) {
      case 'entry':
        return this.#runBody(node.children);

      case 'assign': {
        const [name, val] = node.value;
        const evaluated = this.evaluate(val);
        this.variables.set(name, evaluated);
        break;
      }

      case 'bond_new': {
        const [varName, typeName] = node.value;

        if (!this.personas.has(typeName)) {
          throw new YuriRuntimeError(`Unknown persona: ${typeName}`);
        }

        const template = this.personas.get(typeName);
        const instance = {};

        for (const child of node.children) {
          if (child.type === 'assign') {
            const [fieldName, fieldVal] = child.value;
            instance[fieldName] = this.evaluate(fieldVal);
          }
        }

        for (const field of template) {
          instance[field] ??= null;
        }

        this.variables.set(varName, instance);
        break;
      }

      case 'print': {
        const output = node.value.map(v => String(this.evaluate(v)));
        console.log(output.join(' '));
        break;
      }

      case 'reject':
        throw new YuriRuntimeError(this.evaluate(node.value));

      case 'if': {
        const condition = this.#checkCondition(node.value);

        const ifBody = [];
        const elseBody = [];
        let inElse = false;

        for (const child of node.children) {
          if (child.type === 'else') {
            inElse = true;
            continue;
          }
          (inElse ? elseBody : ifBody).push(child);
        }

        const body = condition ? ifBody : elseBody;
        for (const child of body) {
          const result = this.runNode(child);
          if (isReturn(result)) return result;
        }
        break;
      }

      case 'loop': {
        const count = Number(this.evaluate(node.value.at(-1)));
        const label = node.value.length > 1 ? this.evaluate(node.value[0]) : null;

        for (let i = 0; i < count; i++) {
          if (label) console.log(label);
          for (const child of node.children) {
            const result = this.runNode(child);
            if (isReturn(result)) return result;
          }
        }
        break;
      }

      case 'while': {
        const MAX_ITERATIONS = 10_000;
        let count = 0;

        while (this.#checkCondition(node.value)) {
          if (count >= MAX_ITERATIONS) {
            throw new YuriRuntimeError('@fate loop exceeded 10000 iterations — infinite loop!?');
          }
          for (const child of node.children) {
            const result = this.runNode(child);
            if (isReturn(result)) return result;
          }
          count++;
        }
        break;
      }

      case 'match': {
        const subject = this.evaluate(node.value);

        for (const caseNode of node.children) {
          if (caseNode.type !== 'case') continue;

          if (caseNode.value === '_') {
            for (const child of caseNode.children) {
              const result = this.runNode(child);
              if (isReturn(result)) return result;
            }
            break;
          }

          if (subject === this.evaluate(caseNode.value)) {
            for (const child of caseNode.children) {
              const result = this.runNode(child);
              if (isReturn(result)) return result;
            }
            break;
          }
        }
        break;
      }

      case 'function': {
        const [name, params] = node.value;
        this.functions.set(name, [params, node.children]);
        break;
      }

      case 'call': {
        const [name, args] = node.value;

        if (!this.functions.has(name)) {
          console.log(`Undefined function: ${name}`);
          return;
        }

        const [params, body] = this.functions.get(name);
        const oldVars = new Map(this.variables);

        for (let i = 0; i < params.length; i++) {
          if (i < args.length) {
            this.variables.set(params[i], this.evaluate(args[i]));
          }
        }

        for (const child of body) {
          const result = this.runNode(child);
          if (isReturn(result)) {
            this.#restoreVars(oldVars);
            return result.value;
          }
        }

        this.#restoreVars(oldVars);
        break;
      }

      case 'return':
        return new ReturnSignal(this.evaluate(node.value));

      case 'import':
        loadModule(node.value, this.functions);
        break;

      case 'pipeline': {
        const parts = node.value.split('@>');
        let current = this.evaluate(parts[0].trim());

        for (const step of parts.slice(1)) {
          const trimmed = step.trim();
          if (trimmed.startsWith('@affect')) {
            current = this.#runMap(current, trimmed);
          } else if (trimmed.startsWith('@choose')) {
            current = this.#runFilter(current, trimmed);
          }
        }

        return current;
      }

      case 'persona': {
        const name = node.value;
        const fields = node.children.filter(c => c.type === 'field').map(c => c.value);
        this.personas.set(name, fields);
        break;
      }

      case 'new': {
        const [typeName, rawFields] = node.value;

        if (!this.personas.has(typeName)) {
          throw new YuriRuntimeError(`Unknown persona: ${typeName}`);
        }

        const template = this.personas.get(typeName);
        const instance = {};

        for (const field of template) {
          instance[field] = field in rawFields ? this.evaluate(rawFields[field]) : null;
        }

        return instance;
      }

      default:
        console.log('Unknown node:', node.type);
    }
  }
}

export function run(code) {
  const tree = parse(code);
  const interp = new Interpreter();

  for (const node of tree.children) {
    interp.runNode(node);
  }
}
