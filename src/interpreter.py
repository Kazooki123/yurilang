import re
from src.parser import parse
from src.modules import load_module
from vm.memory import memory_set, memory_get, memory_forget

variables = {}
functions = {}
personas = {}
awakened = set()

YURI_OPS = {
    "plus": lambda a, b: a + b,
    "with": lambda a, b: a + b,
    "minus": lambda a, b: a - b,
    "times": lambda a, b: a * b,
    "over": lambda a, b: a / b,
}

class YuriRuntimeError(Exception):
    pass


class ReturnSignal:
    def __init__(self, value):
        self.value = value


def translate_expr(expr):
    for word, sym in YURI_OPS.items():
        if callable(sym):
            continue

    return expr


def parse_array_literal(expr):
    expr = expr.strip()

    if expr.startswith("#[[") and expr.endswith("]]"):
        inner = expr[3:-2]
    elif expr.startswith("[[") and expr.endswith("]]"):
        inner = expr[2:-2]
    else:
        return None

    items = []
    for item in inner.split(","):
        item = item.strip()
        if not item:
            continue

        if item.startswith('"') and item.endswith('"'):
            items.append(item[1:-1])
        
        elif item.startswith("'") and item.endswith("'"):
            items.append(item[1:-1])
        
        elif item.lstrip('-').isdigit():
            items.append(int(item))
        # float
        else:
            try:
                items.append(float(item))
            except ValueError:
                items.append(item)

    return items


def evaluate(expr):
    global variables

    if isinstance(expr, (int, float, bool)):
        return expr

    if isinstance(expr, list):
        if len(expr) == 0:
            return None

        if len(expr) == 1:
            return evaluate(expr[0])

        if len(expr) == 3:
            left = evaluate(expr[0])
            op   = expr[1]
            right = evaluate(expr[2])

            if op in YURI_OPS:
                return YURI_OPS[op](left, right)

        return [evaluate(e) for e in expr]

    if not isinstance(expr, str):
        return expr

    expr = expr.strip()

    if expr.startswith('"') and expr.endswith('"'):
        return expr[1:-1]

    if expr.lstrip('-').isdigit():
        return int(expr)

    try:
        return float(expr)
    except ValueError:
        pass

    if (expr.startswith("[[") or expr.startswith("#[[")):
        return parse_array_literal(expr)

    if "." in expr and not expr.startswith('"'):
        parts = expr.split(".", 1)
        obj = variables.get(parts[0])
        if isinstance(obj, dict):
            return obj.get(parts[1])

    if expr.startswith("@"):
        parts = expr.split()
        func_name = parts[0][1:]
        raw_args  = parts[1:]

        # Debugging
        # print(f"DEBUG CALL: func={func_name}, raw_args={raw_args}")

        if func_name not in functions:
            raise YuriRuntimeError(f"Undefined function: @{func_name}")

        params, body = functions[func_name]
        old_vars = variables.copy()

        for i, param in enumerate(params):
            if i < len(raw_args):
                variables[param] = evaluate(raw_args[i])

        result = None
        for child in body:
            ret = run_node(child)
            if isinstance(ret, ReturnSignal):
                result = ret.value
                break

        variables.clear()
        variables.update(old_vars)
        return result

    if expr in variables:
        return variables[expr]

    return expr


def run_map(array, step):
    if not isinstance(array, list):
        raise YuriRuntimeError("@affect requires an array on the left side of @>")

    step = step.strip()

    parts = step.split()
    if len(parts) < 2:
        raise YuriRuntimeError("@affect requires a function name")

    func_name = parts[1]

    if func_name not in functions:
        raise YuriRuntimeError(f"Undefined function: {func_name}")

    results = []
    for item in array:
        params, body = functions[func_name]
        old_vars = variables.copy()

        if params:
            variables[params[0]] = item

        result = None
        for child in body:
            ret = run_node(child)
            if isinstance(ret, ReturnSignal):
                result = ret.value
                break

        variables.clear()
        variables.update(old_vars)
        results.append(result)

    return results


def run_reduce(array, step):
    if not isinstance(array, list):
        raise YuriRuntimeError("@melt requires an array on the left side of @>")

    if len(array) == 0:
        raise YuriRuntimeError("@melt cannot melt an empty array — nothing to feel.")

    parts = step.split()
    if len(parts) < 2:
        raise YuriRuntimeError("@melt requires a function name")

    func_name = parts[1]

    if func_name not in functions:
        raise YuriRuntimeError(f"Undefined function: @{func_name}")

    accumulator = array[0]

    for item in array[1:]:
        params, body = functions[func_name]
        old_vars = variables.copy()

        if len(params) >= 2:
            variables[params[0]] = accumulator
            variables[params[1]] = item
        elif len(params) == 1:
            variables[params[0]] = item

        result = None
        for child in body:
            ret = run_node(child)
            if isinstance(ret, ReturnSignal):
                result = ret.value
                break

        variables.clear()
        variables.update(old_vars)
        accumulator = result if result is not None else accumulator

    return accumulator


def run_filter(array, step):
    if not isinstance(array, list):
        raise YuriRuntimeError("@choose requires an array on the left side of @>")

    parts = step.split()
    if len(parts) < 2:
        raise YuriRuntimeError("@choose requires a function name")

    func_name = parts[1]

    if func_name not in functions:
        raise YuriRuntimeError(f"Undefined function: {func_name}")

    results = []
    for item in array:
        params, body = functions[func_name]
        old_vars = variables.copy()

        if params:
            variables[params[0]] = item

        result = None
        for child in body:
            ret = run_node(child)
            if isinstance(ret, ReturnSignal):
                result = ret.value
                break

        variables.clear()
        variables.update(old_vars)

        if result:
            results.append(item)

    return results


def interpolate(template, variables):
    import re
    def replacer(match):
        key = match.group(1)
        if key in variables:
            return str(variables[key])
        return f"{{{key}}}"
    return re.sub(r'\{(\w+)\}', replacer, template)


def run_node(node):
    global variables, functions

    # ENTRY
    if node.type == "entry":
        for child in node.children:
            run_node(child)

    # ASSIGN
    elif node.type == "assign":
        name, val = node.value
        if name in awakened:
            raise YuriRuntimeError(f"'{name}' has already awakened. It is permanent.")
        variables[name] = evaluate(val)
        # print(f"DEBUG assign: {name} = {variables[name]}")

    # BOND @NEW
    elif node.type == "bond_new":
        var_name, type_name = node.value

        if type_name not in personas:
            raise YuriRuntimeError(f"Unknown persona: {type_name}")

        template = personas[type_name]
        instance = {}

        for child in node.children:
            if child.type == "assign":
                field_name, field_val = child.value
                instance[field_name] = evaluate(field_val)

        for field in template:
            if field not in instance:
                instance[field] = None

        variables[var_name] = instance

    # PRINT
    elif node.type == "print":
        output = [str(evaluate(v)) for v in node.value]
        print(" ".join(output))

    # REJECT
    elif node.type == "reject":
        raise YuriRuntimeError(evaluate(node.value))

    # ECHO
    elif node.type == "echo":
        template = evaluate(node.value)
        result = interpolate(template, variables)
        print(result)

    # IF
    elif node.type == "if":
        left = evaluate(node.value[0])
        op = node.value[1]
        right = evaluate(node.value[2])

        condition = False
        if op == "==":
            condition = left == right
        elif op == "!=":
            condition = left != right
        elif op == ">":
            condition = left > right
        elif op == "<":
            condition = left < right
        elif op == ">=":
            condition = left >= right
        elif op == "<=":
            condition = left <= right

        if_body = []
        else_body = []
        in_else = False

        for child in node.children:
            if child.type == "else":
                in_else = True
                continue
            if in_else:
                else_body.append(child)
            else:
                if_body.append(child)

        if condition:
            for child in if_body:
                result = run_node(child)
                if isinstance(result, ReturnSignal):
                    return result
        else:
            for child in else_body:
                result = run_node(child)
                if isinstance(result, ReturnSignal):
                    return result

    # ELSE
    elif node.type == "else":
        pass

    # LOOP
    elif node.type == "loop":
        count = int(evaluate(node.value[-1]))
        label = evaluate(node.value[0]) if len(node.value) > 1 else None

        for _ in range(count):
            if label:
                print(label)
            for child in node.children:
                result = run_node(child)
                if isinstance(result, ReturnSignal):
                    return result

    # NOT / APART
    elif node.type == "not":
        left = evaluate(node.value[0])
        op = node.value[1]
        right = evaluate(node.value[2])

        condition = False
        if op == "==":  condition = left == right
        elif op == "!=": condition = left != right
        elif op == ">":  condition = left > right
        elif op == "<":  condition = left < right
        elif op == ">=": condition = left >= right
        elif op == "<=": condition = left <= right

        if not condition:
            for child in node.children:
                result = run_node(child)
                if isinstance(result, ReturnSignal):
                    return result

    # WHILE LOOP
    elif node.type == "while":
        def check_condition():
            left = evaluate(node.value[0])
            op = node.value[1]
            right = evaluate(node.value[2])

            if op == "==": return left == right
            if op == "!=": return left != right
            if op == ">":  return left > right
            if op == "<":  return left < right
            if op == ">=": return left >= right
            if op == "<=": return left <= right
            return False

        # To prevent infinite loops bs
        max_iterations = 10000
        count = 0

        while check_condition():
            if count >= max_iterations:
                raise YuriRuntimeError("@fate loop exceeded 10000 iterations — infinite loop!?")
            for child in node.children:
                result = run_node(child)
                if isinstance(result, ReturnSignal):
                    return result

            count += 1

    # PATTERN MATCHING 
    elif node.type == "match":
        subject = evaluate(node.value)

        for case in node.children:
            if case.type != "case":
                continue

            if case.value == "_":
                for child in case.children:
                    result = run_node(child)
                    if isinstance(result, ReturnSignal):
                        return result
                break

            case_val = evaluate(case.value)

            if subject == case_val:
                for child in case.children:
                    result = run_node(child)
                    if isinstance(result, ReturnSignal):
                        return result
                break

    # MEMORY / RECALL / FORGET
    elif node.type == "memory_set":
        key, val = node.value
        memory_set(evaluate(key), evaluate(val))

    elif node.type == "memory_get":
        key = evaluate(node.value)
        result = memory_get(key)
    
        clean_key = key.strip('"')
        variables[clean_key] = result
        return result

    elif node.type == "memory_forget":
        key = evaluate(node.value)
        memory_forget(key)

    # FUNCTION DEFINE
    elif node.type == "function":
        name, params = node.value
        functions[name] = (params, node.children)

    # FUNCTION CALL
    elif node.type == "call":
        name, args = node.value

        if name not in functions:
            print(f"Undefined function: {name}")
            return

        params, body = functions[name]
        old_vars = variables.copy()

        for i, param in enumerate(params):
            if i < len(args):
                variables[param] = evaluate(args[i])

        for child in body:
            result = run_node(child)
            if isinstance(result, ReturnSignal):
                variables.clear()
                variables.update(old_vars)
                return result.value

        variables.clear()
        variables.update(old_vars)

    # RETURN
    elif node.type == "return":
        return ReturnSignal(evaluate(node.value))

    # IMPORT
    elif node.type == "import":
        load_module(node.value, functions)

    # PIPELINES
    elif node.type == "pipeline":
        parts = node.value.split("@>")
        current = evaluate(parts[0].strip())

        for step in parts[1:]:
            step = step.strip()

            if step.startswith("@affect"):
                current = run_map(current, step)
            elif step.startswith("@choose"):
                current = run_filter(current, step)
            elif step.startswith("@melt"):
                current = run_reduce(current, step)

        return current

    # AWAKE / PERMANENT VAR
    elif node.type == "awakening":
        name = node.value
        if name not in variables:
            raise YuriRuntimeError(f"'{name}' cannot awaken!")
        awakened.add(name)

    # STRUCTS
    elif node.type == "persona":
        name = node.value
        fields = [child.value for child in node.children if child.type == "field"]
        personas[name] = fields

    elif node.type == "new":
        type_name, raw_fields = node.value

        if type_name not in personas:
            raise YuriRuntimeError(f"Unknown persona: {type_name}")

        template = personas[type_name]
        instance = {}

        for field in template:
            if field in raw_fields:
                instance[field] = evaluate(raw_fields[field])
            else:
                instance[field] = None

        return instance

    else:
        print("Unknown node:", node.type)


def run(code):
    tree = parse(code)

    for node in tree.children:
        run_node(node)
