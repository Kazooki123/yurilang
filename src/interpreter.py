import re
from src.parser import parse
from src.modules import load_module, loaded_modules

variables = {}
functions = {}

YURI_OPS = {
    "plus": "+",
    "with": "+",
    "minus": "-",
    "times": "*",
    "over": "/"
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

    if expr.isdigit():
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


def run(code):
    tree = parse(code)

    for node in tree.children:
        run_node(node)

