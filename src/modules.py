import os
from src.parser import parse

loaded_modules = set()

def load_module(name, functions):
    filename = f"{name}.yuri"

    if name in loaded_modules:
        return  # already loaded

    if not os.path.exists(filename):
        raise Exception(f"Module '{name}' not found ({filename})")

    with open(filename, "r") as f:
        code = f.read()

    tree = parse(code)

    # Extract functions
    for node in tree.children:
        if node.type == "function":
            functions[node.value] = node.children

    loaded_modules.add(name)
