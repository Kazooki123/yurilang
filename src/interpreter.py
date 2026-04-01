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
        if callable(sym):
            continue

    return expr


def evaluate(expr, variables):
    if isinstance(expr, (int, float, bool)):
        return expr

    if isinstance(expr, str):
        expr = expr.strip()

        if expr.startswith('"') and expr.endswith('"'):
            return expr[1:-1]

        if expr.isdigit():
            return int(expr)

        # Variable lookup (IMPORTANT FIX)
        if expr in variables:
            return variables[expr]

        return expr

    if isinstance(expr, list):
        if len(expr) == 1:
            return evaluate(expr[0], variables)

        if len(expr) == 3:
            left = evaluate(expr[0], variables)
            op = expr[1]
            right = evaluate(expr[2], variables)

            # Math operations
            if op == "plus":
                return left + right
            if op == "minus":
                return left - right
            if op == "times":
                return left * right
            if op == "over":
                return left / right

        return [evaluate(e, variables) for e in expr]

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

