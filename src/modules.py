import os
from src.parser import parse


loaded_modules = set()
STORE_PATH = "../store"


def extract_functions(node, functions):
    if node.type == "function":
        functions[node.value] = node.children

    for child in node.children:
        extract_functions(child, functions)


def load_module(name, functions):
    filename = os.path.join(STORE_PATH, f"{name}.yuri")

    if name in loaded_modules:
        return

    if not os.path.exists(filename):
        raise Exception(f"Module '{name}' not found in store/")

    with open(filename, "r") as f:
        code = f.read()

    tree = parse(code)

    extract_functions(tree, functions)

    loaded_modules.add(name)
