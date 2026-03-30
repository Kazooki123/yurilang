from src.parser import parse

variables = {}
functions = {}

def evaluate(value):
    if isinstance(value, tuple):
        value = value[1]

    if isinstance(value, list):
        value = value[0]

    if str(value).isdigit():
        return int(value)

    return variables.get(value, str(value).strip('"'))


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
                run_node(child)

    # LOOP
    elif node.type == "loop":
        count = int(evaluate(node.value[0]))
        for _ in range(count):
            for child in node.children:
                run_node(child)

    # FUNCTION DEFINE
    elif node.type == "function":
        func_name = node.value
        functions[func_name] = node.children

    # FUNCTION CALL
    elif node.type == "call":
        func_name = node.value
        if func_name in functions:
            for child in functions[func_name]:
                run_node(child)
        else:
            print(f"Undefined function: {func_name}")

    # IMPORT (stub)
    elif node.type == "import":
        print(f"Importing {node.value} (not implemented)")

    else:
        print("Unknown node:", node.type)


def run(code):
    tree = parse(code)

    for node in tree.children:
        run_node(node)
