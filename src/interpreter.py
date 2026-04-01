import re
from src.parser import parse
from src.modules import load_module

variables = {}
functions = {}

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
        expr = expr.replace(word, sym)
    return expr


def evaluate(expr):
    if isinstance(expr, list):
        expr = " ".join(expr)

    expr = str(expr).strip()

    if re.fullmatch(r"\d+", expr):
        return int(expr)

    if expr.startswith('"') and expr.endswith('"'):
        return expr.strip('"')

    if expr.startswith("[[") and expr.endswith("]]"):
        inner = expr[2:-2].strip()
        if not inner:
            return []
        items = [x.strip() for x in inner.split(",")]
        return [evaluate(item) for item in items]

    if expr.startswith("#[[") and expr.endswith("]]"):
        inner = expr[3:-2].strip()
        if not inner:
            return []
        items = [x.strip() for x in inner.split(",")]
        return [str(evaluate(item)) for item in items]

    match = re.match(r"(\w+)\[(\d+)\]", expr)
    if match:
        name = match.group(1)
        index = int(match.group(2))
        if name in variables:
            return variables[name][index]

    if expr.startswith("@"):
        parts = expr.split()
        func_name = parts[0][1:]
        args = parts[1:]

        if func_name in functions:
            params, body = functions[func_name]
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
            return None

    if expr in variables:
        return variables[expr]

    tokens = expr.split()

    if len(tokens) == 3:
        left = evaluate(tokens[0])
        op = tokens[1]
        right = evaluate(tokens[2])

        if op in ("plus", "+"):
            return left + right
        elif op in ("minus", "-"):
            return left - right
        elif op in ("times", "*"):
            return left * right
        elif op in ("over", "/"):
            return left / right

    try:
        expr = translate_expr(expr)
        return eval(expr, {"__builtins__": {}})
    except:
        return expr


def run_node(node):
    global variables, functions

    # ENTRY
    if node.type == "entry":
        for child in node.children:
            run_node(child)

    # ASSIGN
    elif node.type == "assign":
        name, val = node.value
        variables[name] = evaluate(val)

    # PRINT
    elif node.type == "print":
        output = [str(evaluate(v)) for v in node.value]
        print(" ".join(output))

    # REJECT
    elif node.type == "reject":
        raise YuriRuntimeError(evaluate(node.value))

    # IF
    elif node.type == "if":
        left = evaluate(node.value[0])
        op = node.value[1]
        right = evaluate(node.value[2])

        condition = False
        if op == "==":
            condition = left == right

        if condition:
            for child in node.children:
                result = run_node(child)
                if isinstance(result, ReturnSignal):
                    return result

    # LOOP
    elif node.type == "loop":
        count = int(evaluate(node.value[0]))
        for _ in range(count):
            for child in node.children:
                result = run_node(child)
                if isinstance(result, ReturnSignal):
                    return result

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

        return current

    else:
        print("Unknown node:", node.type)


def run(code):
    tree = parse(code)

    for node in tree.children:
        run_node(node)

