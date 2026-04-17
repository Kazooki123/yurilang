import json


def save_yuric(instructions, path):
    with open(path, "w") as f:
        json.dump(instructions, f, indent=2)
    print(f"Bytecode written to {path}")


def load_yuric(path):
    with open(path, "r") as f:
        return [tuple(i) for i in json.load(f)]
