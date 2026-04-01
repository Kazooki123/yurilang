import os
from src.parser import parse


loaded_modules = set()
STORE_PATH = "store"


def normalize(name):
    return name.replace("_", "").lower()


def extract_functions(node, functions):
    if node.type == "function":
        name, params = node.value
functions[name] = (params, node.children)

    for child in node.children:
        extract_functions(child, functions)


def load_module(name, functions):
    normalized = normalize(name)
    filename = os.path.join(STORE_PATH, f"{normalized}.yuri")

    if normalized in loaded_modules:
        return

    if name in loaded_modules:
        return

    if not os.path.exists(filename):
        raise Exception(f"Module '{name}' not found in store/")

    with open(filename, "r") as f:
        code = f.read()

    tree = parse(code)

    extract_functions(tree, functions)

    loaded_modules.add(normalized)
