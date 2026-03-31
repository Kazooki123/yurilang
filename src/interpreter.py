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

    expr = str(expr)

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


    expr = translate_expr(expr)


    for var in variables:
        expr = re.sub(rf"\b{var}\b", str(variables[var]), expr)

    try:
        return eval(expr, {"__builtins__": {}})
    except:
        return expr.strip('"')


def run_node(node):
    global variables, functions

    # ENTRY
    if node.type == "entry":
        for child in node.children:
            run_node(child)

    # VARIABLE
    elif node.type == "assign":
        name, val = node.value
        variables[name] = evaluate(val)

    # PRINT
    elif node.type == "print":
        output = []
        for v in node.value:
            output.append(str(evaluate(v)))
        print(" ".join(output))

    # REJECT / THROW ERR
    elif node.type == "reject":
        message = evaluate(node.value)
        raise YuriRuntimeError(message)

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
        func_name, args = node.value

        if func_name not in functions:
            print(f"Undefined function: {func_name}")
            return

        params, body = functions[func_name]

        # backup variables (scope)
        old_vars = variables.copy()

        # assign arguments
        for i, param in enumerate(params):
            if i < len(args):
                variables[param] = evaluate(args[i])

        # execute function
        for child in body:
            result = run_node(child)
            if isinstance(result, ReturnSignal):
                variables.clear()
                variables.update(old_vars)
                return result.value

        # restore variables
        variables.clear()
        variables.update(old_vars)

    # RETURN
    elif node.type == "return":
        value = evaluate(node.value)
        return ReturnSignal(value)

    # IMPORT SYSTEM
    elif node.type == "import":
        load_module(node.value, functions)

    else:
        print("Unknown node:", node.type)


def run(code):
    tree = parse(code)

    for node in tree.children:
        run_node(node)

