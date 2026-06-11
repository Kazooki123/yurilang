YURI_TYPES = {
    "heart": str,  # "feelings expressed in words"
    "int": int,  # numbers, universal language
    "float": float,  # decimal feelings
    "bloom": bool,  # love/ache/uncertain
    "list": list,  # a collection of feelings
    "uncertain": type(None),  # she doesn't know yet
}

# Hints
crush_hints = {}
func_hints = {}


def register_crush(name, type_hint):
    """Registers a type hint for a variable."""
    crush_hints[name] = type_hint


def register_func_hints(func_name, param_hints, return_hint=None):
    """Register type hints for a @ship function."""
    func_hints[func_name] = {"params": param_hints, "returns": return_hint}


def get_hint(name):
    return crush_hints.get(name)


def get_func_hint(func_name):
    return func_hints.get(func_name)


def type_name(value):
    if value is None:
        return "uncertain"
    if isinstance(value, bool):
        return "bloom"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "heart"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "persona"
    return type(value).__name__


def check_hint(name, value, context="variable"):
    """
    Check if a value matches its declared @crush hint.
    Since hints only — never raises, just returns a
    (matches, expected, actual) tuple for optional display.
    """
    hint = crush_hints.get(name)
    if hint is None:
        return True, None, None

    actual = type_name(value)

    if hint not in YURI_TYPES:
        if isinstance(value, str):
            return True, hint, actual
        return False, hint, actual

    expected_type = YURI_TYPES[hint]
    if isinstance(value, bool) and hint == "bloom":
        return True, hint, actual
    if isinstance(value, bool) and hint != "bloom":
        return False, hint, actual
    matches = isinstance(value, expected_type)
    return matches, hint, actual


def format_hint(name):
    hint = crush_hints.get(name)
    if hint:
        return f"{name}:{hint}"
    return name


def crush_summary():
    """
    Print a summary of all declared @crush hints.
    Used by --crush flag or the ITMYE auditor.
    """
    if not crush_hints and not func_hints:
        return "  No @crush hints declared yet.\n  She hasn't named her feelings."

    lines = []
    lines.append("  @crush type hints declared:")
    lines.append("")

    if crush_hints:
        lines.append("  Variables:")
        for name, hint in crush_hints.items():
            lines.append(f"    {name} → {hint}")

        if func_hints:
            lines.append("")
            lines.append("  Functions:")
            for func, hints in func_hints.items():
                params = ", ".join(f"{p}:{t}" for p, t in hints["params"].items())
                ret = f" → {hints['returns']}" if hints["returns"] else ""
                lines.append(f"    @ship {func}({params}){ret}")

        return "\n".join(lines)
