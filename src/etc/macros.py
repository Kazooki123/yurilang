"""
Macros - Yurilang

Macro systems of Yurilang, using the `@novel` keyword.
"""

from src.core.interpreter import run_node, variables


def run_macro(node):
    if node.type == "novel":
        name = node.value[0]
        body = node.value[1]
        params = node.value[2]

        if name in variables:
            raise Exception(f"Macro {name} already exists.")

        variables[name] = lambda *args: run_node(body)

        return

    raise Exception(f"Unknown macro: {node.type}")


