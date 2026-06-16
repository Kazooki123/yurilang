"""
Module - Yurilang

Modular system of Yurilang using the `@yuri` keyword, can do namespacing for example:
   `@yuri math as m`
   
TODO: Support importing the entire stdlib or store.
"""

import os
from src.parser import parse

loaded_modules = set()

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STORE_PATH = os.path.join(BASE_DIR, "store")


def normalize(name):
    return name.replace("_", "").lower()


def get_module_functions(name):
    normalized = normalize(name)
    filename = os.path.join(STORE_PATH, f"{normalized}.yuri")

    if not os.path.exists(filename):
        raise Exception(f"Module '{name} not found!'")

    with open(filename, "r") as f:
        code = f.read()

    tree = parse(code)
    funcs = {}
    extract_functions(tree, funcs)
    return funcs


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

    if not os.path.exists(filename):
        raise Exception(f"Module '{name}' not found at {filename}")

    with open(filename, "r") as f:
        code = f.read()

    tree = parse(code)
    extract_functions(tree, functions)

    loaded_modules.add(normalized)
