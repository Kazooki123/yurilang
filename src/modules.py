import os
from src.parser import parse

loaded_modules = set()

def extract_functions(node, functions):
    if node.type == "function":
        functions[node.value] = node.children

    for child in node.children:
        extract_functions(child, functions)


def load_module(name, functions):
    import os
    from src.parser import parse

    filename = f"{name}.yuri"

    if not os.path.exists(filename):
        raise Exception(f"Module '{name}' not found")

    with open(filename, "r") as f:
        code = f.read()

    tree = parse(code)

    extract_functions(tree, functions)

