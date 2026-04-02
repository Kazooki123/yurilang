import json
import os


MEMORY_FILE = "yuri.db"


def _load():
    if not os.path.exists(MEMORY_FILE):
        return {}
    with open(MEMORY_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def _save(data):
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=2)


def memory_set(key, value):
    data = _load()
    data[key] = value
    _save(data)


def memory_get(key):
    data = _load()
    if key not in data:
        raise Exception(f"@recall failed — '{key}' was never remembered.")
    return data[key]


def memory_forget(key):
    data = _load()
    if key in data:
        del data[key]
        _save(data)


def memory_exists(key):
    data = _load()
    return key in data


def memory_all():
    return _load()
