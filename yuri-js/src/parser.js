import { tokenize, getIndentLevel } from './lexer.js';

export class Node {
  constructor(type, value = null) {
    this.type = type;
    this.value = value;
    this.children = [];
  }
}

function parseLine(line) {
  const tokens = tokenize(line);
  if (!tokens.length) return null;

  const keyword = tokens[0];

  if (keyword === '@bond') {
    if (tokens[3] === '@new') {
      const typeName = tokens[4];
      return new Node('bond_new', [tokens[1], typeName]);
    }
    const val = tokens.slice(3).join(' ');
    return new Node('assign', [tokens[1], val]);
  }

  if (keyword === '@confess') return new Node('print', tokens.slice(1));
  if (keyword === '@jealous') return new Node('if', tokens.slice(1));
  if (keyword === '@forgive') return new Node('else');
  if (keyword === '@cling') return new Node('loop', tokens.slice(1));
  if (keyword === '@fate') return new Node('while', tokens.slice(1));
  if (keyword === '@yuri') return new Node('import', tokens[1]);
  if (keyword === '@wlw') return new Node('entry');

  if (keyword === '@ship') {
    const name = tokens[1];
    const params = tokens.slice(2);
    return new Node('function', [name, params]);
  }

  if (keyword === '@sappho') return new Node('match', tokens[1]);
  if (keyword === '@poet') return new Node('case', tokens[1]);
  if (keyword === '@reject') return new Node('reject', tokens.slice(1));
  if (keyword === '@persona') return new Node('persona', tokens[1]);

  if (keyword === '@new') {
    const typeName = tokens[1];
    const fields = {};
    const rest = tokens.slice(2).join(' ');

    for (const match of rest.matchAll(/(\w+)\s*=\s*(".*?"|\d+|\w+)/g)) {
      fields[match[1]] = match[2];
    }

    return new Node('new', [typeName, fields]);
  }

  if (keyword === '@promise') return new Node('return', tokens.slice(1));

  if (keyword.startsWith('@')) {
    return new Node('call', [keyword.slice(1), tokens.slice(1)]);
  }

  if (line.includes('@>')) return new Node('pipeline', line);

  if (tokens.length >= 3 && tokens[1] === '=') {
    const val = tokens.slice(2).join(' ');
    return new Node('assign', [tokens[0], val]);
  }

  if (tokens.length === 1) return new Node('field', tokens[0]);

  return new Node('unknown', tokens);
}

export function parse(code) {
  const lines = code.split('\n');
  const root = new Node('root');
  const stack = [[-1, root]];

  for (const line of lines) {
    if (!line.trim()) continue;

    const indent = getIndentLevel(line);
    const node = parseLine(line.trim());

    if (!node) continue;

    while (stack.length > 1 && indent <= stack.at(-1)[0]) {
      stack.pop();
    }

    const parent = stack.at(-1)[1];
    if (node.type === 'else' && parent.children.at(-1)?.type === 'if') {
      parent.children.at(-1).children.push(node);
    } else {
      parent.children.push(node);
      stack.push([indent, node]);
    }
  }

  return root;
}
