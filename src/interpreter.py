import ctypes
import os
import asyncio
from src.parser import parse
from src.modules import load_module
from vm.memory import memory_set, memory_get, memory_forget
# error handling
from src.error import (
    err_undefined_variable, err_undefined_function,
    err_type_mismatch, err_index_out_of_range,
    err_invalid_index, err_awakened_reassign,
    err_divide_by_zero, err_infinite_loop,
    err_module_not_found, err_stack_overflow,
    err_reject, err_devoted_moved, err_missing_key
)
from src.asynchronous import (
    YuriDream, make_async_ship, run_dream,
    gather_dreams, sleep_dream, get_event_loop
)
from src.types import (
    register_crush, register_func_hints,
    check_hint, type_name, crush_summary,
    YURI_TYPES
)
from src.etc.itmye_check import run_itmye # ITMYE 

variables = {}
functions = {}
c_functions = {}
personas = {}
spectrums = {}
owned = {}
shared_ptrs = {}

glances = {} # (immutable borrows)
reaches = {} # (mutable borrows, max 1 per source)
glances_of = {} # set of glance aliases
reach_of   = {} # reach alias or None

awakened = set()


YURI_OPS = {
    "plus":   lambda a, b: a + b,
    "with":   lambda a, b: a + b,
    "minus":  lambda a, b: a - b,
    "times":  lambda a, b: a * b,
    "over":   lambda a, b: a / b,
    "band":   lambda a, b: int(a) & int(b),
    "bor":    lambda a, b: int(a) | int(b),
    "bxor":   lambda a, b: int(a) ^ int(b),
    "bshift": lambda a, b: int(a) << int(b) if int(b) >= 0 else int(a) >> abs(int(b)),
    "and":    lambda a, b: a and b,
    "or":     lambda a, b: a or b,
    "not":    lambda a: not a,
}

def coerce(v):
    if isinstance(v, (int, float, bool)):
        return v
    if isinstance(v, str):
        if v.lstrip('-').isdigit():
            return int(v)
        try:
            return float(v)
        except ValueError:
            pass
    return v


class YuriRuntimeError(Exception):
    pass


class ReturnSignal:
    def __init__(self, value):
        self.value = value


class BreakSignal:
    pass


class ContinueSignal:
    pass


class YuriLambda:
    def __init__(self, params, body_expr, closure):
        self.params     = params
        self.body_expr  = body_expr
        self.closure    = closure.copy()  # captures current scope

    def __repr__(self):
        params = " ".join(self.params)
        return f"@bloom {params}: {self.body_expr}"


def translate_expr(expr):
    for word, sym in YURI_OPS.items():
        if callable(sym):
            continue

    return expr


def set_indexed(obj_name, index_expr, value):
    import re
    indices = re.findall(r'\[\[([^\]]+)\]\]', index_expr)
    indices = [evaluate(i.strip()) for i in indices]

    obj = variables[obj_name]
    for idx in indices[:-1]:
        obj = obj[idx]
   
    obj[indices[-1]] = value


def parse_array_literal(expr):
    expr = expr.strip()

    if expr.startswith("#[[") and expr.endswith("]]"):
        inner = expr[3:-2]
    elif expr.startswith("[[") and expr.endswith("]]"):
        inner = expr[2:-2]
    else:
        return None

    items = []
    depth = 0
    current = ""

    for char in inner:
        if char == "[":
            depth += 1
            current += char
        elif char == "]":
            depth -= 1
            current += char
        elif char == "," and depth == 0:
            item = current.strip()
            if item:
                items.append(_parse_item(item))
            current = ""
        else:
            current += char

    if current.strip():
        items.append(_parse_item(current.strip()))

    return items


def _parse_item(item):
    if item.startswith("[[") or item.startswith("#[["):
        return parse_array_literal(item)
    if item.startswith('"') and item.endswith('"'):
        return item[1:-1]
    if item.startswith("'") and item.endswith("'"):
        return item[1:-1]
    if item.lstrip('-').isdigit():
        return int(item)
    try:
        return float(item)
    except ValueError:
        return item
    

def _py_to_ctype(value):
    
    # detect types
    if isinstance(value, float):
        return ctypes.c_double(value)
    
    if isinstance(value, int):
        return ctypes.c_long(value)
    
    if isinstance(value, str):
        return ctypes.c_char_p(value.encode())
    
    return value

def _ctype_to_py(value):
    if isinstance(value, ctypes.c_long):
        return value.value
    
    if isinstance(value, ctypes.c_double):
        return value.value
    
    if isinstance(value, ctypes.c_char_p):
        return value.value.decode() if value.value else None
    
    return value

def _call_c(name, raw_args):
    # to not copy paste this block in run node and evaluate

    evaluated = [evaluate(a) for a in raw_args]
    c_args = [_py_to_ctype(a) for a in evaluated]
    return _ctype_to_py(c_functions[name](*c_args))


def _apply_affect(arr, func_ref):
    results = []
    for item in arr:
        if func_ref in functions:
            params, body = functions[func_ref][:2]
            old_vars = variables.copy()
            if params:
                variables[params[0]] = item
                result = None
                for child in body:
                    ret = run_node(child)
                    if isinstance(ret, ReturnSignal):
                        result = ret.value
                        break
                variables.clear()
                variables.update(old_vars)
                results.append(result)

            elif func_ref in variables and isinstance(variables[func_ref], YuriLambda):
                lam = variables[func_ref]
                old_vars = variables.copy()
                variables.clear()
                variables.update(lam.closure)
                if lam.params:
                        variables[lam.params[0]] = item
                result = evaluate(lam.body_expr)
                variables.clear()
                variables.update(old_vars)
                results.append(result)

            else:
                raise YuriRuntimeError(
                    f"\n💔 @affect — '{func_ref}' is not a @ship or @bloom\n"
                    f" |> hint: Define it first:\n"
                    f"           @ship {func_ref} x:\n"
                    f"               @promise x\n"
                )
        return results


def _apply_choose(arr, func_ref):
    results = []
    for item in arr:
        if func_ref in functions:
            params, body = functions[func_ref][:2]
            old_vars = variables.copy()
            if params:
                variables[params[0]] = item
                result = None
                for child in body:
                    ret = run_node(child)
                    if isinstance(ret, ReturnSignal):
                        result = ret.value
                        break
                    variables.clear()
                    variables.update(old_vars)
                if result:
                    results.append(item)

                elif func_ref in variables and isinstance(variables[func_ref], YuriLambda):
                    lam = variables[func_ref]
                    old_vars = variables.copy()
                    variables.clear()
                    variables.update(lam.closure)
                    if lam.params:
                        variables[lam.params[0]] = item
                    result = evaluate(lam.body_expr)
                    variables.clear()
                    variables.update(old_vars)
                    if result:
                        results.append(item)

                else:
                    raise YuriRuntimeError(
                        f"\n💔 @choose — '{func_ref}' is not a @ship or @bloom\n"
                    )
        return results


def evaluate(expr):
    global variables

    if isinstance(expr, (int, float, bool)) or expr is None:
        return expr

    if isinstance(expr, list):
        if len(expr) == 0:
            return None
        if len(expr) == 1:
            return evaluate(expr[0])
        if len(expr) == 3:
            left  = coerce(evaluate(expr[0]))
            op    = expr[1]
            right = coerce(evaluate(expr[2]))
            if op in YURI_OPS:
                if op in ("plus", "with"):
                    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                        return YURI_OPS[op](left, right)
                    return str(left) + str(right)
                return YURI_OPS[op](left, right)
                
        return [evaluate(e) for e in expr]

    if not isinstance(expr, str):
        return expr

    expr = expr.strip()

    if expr.startswith('"') and expr.endswith('"'):
        return expr[1:-1]

    if expr == "love":      return True
    if expr == "ache":      return False
    if expr == "uncertain": return None

    if expr.lstrip('-').isdigit():
        return int(expr)

    try:
        return float(expr)
    except ValueError:
        pass

    for op in sorted(YURI_OPS.keys(), key=len, reverse=True):
        if f" {op} " in expr:
            parts = expr.split(f" {op} ", 1)
            left  = coerce(evaluate(parts[0].strip()))
            right = coerce(evaluate(parts[1].strip()))
            if op in ("plus", "with"):
                if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                    return YURI_OPS[op](left, right)
                return str(left) + str(right)
            return YURI_OPS[op](left, right)

    if "[[" in expr and not expr.startswith("[[") and not expr.startswith("#[["):
        import re
        obj_name   = expr.split("[[")[0].strip()
        rest       = expr[len(obj_name):]
        raw_indices = re.findall(r'\[\[([^\]]+)\]\]', rest)

        obj = evaluate(obj_name)
        for raw_idx in raw_indices:
            idx = evaluate(raw_idx.strip())
            if isinstance(obj, dict):
                if idx not in obj:
                    raise YuriRuntimeError(
                        f"Key '{idx}' doesn't exist yet — use @autoviv to create it."
                    )
                obj = obj[idx]
            elif isinstance(obj, list):
                idx = coerce(idx)
                if not isinstance(idx, int):
                    raise YuriRuntimeError(f"List index must be integer, got: {idx}")
                if idx < 0 or idx >= len(obj):
                    raise YuriRuntimeError(
                        f"Index {idx} out of range for array of length {len(obj)}"
                    )
                obj = obj[idx]
            else:
                raise YuriRuntimeError(f"Cannot index into: {type(obj).__name__}")
        return obj

    if expr.startswith("[[") or expr.startswith("#[["):
        return parse_array_literal(expr)

    if "." in expr and not expr.startswith('"'):
        parts = expr.split(".", 1)
        obj = variables.get(parts[0])
        if isinstance(obj, dict):
            key = parts[1]
            if key in obj:
                return obj[key]
            raise YuriRuntimeError(f"'{parts[1]}' is not a variant of '{parts[0]}'")

    if expr.startswith("@"):
        parts     = expr.split()
        func_name = parts[0][1:]
        raw_args  = parts[1:]

        if func_name in variables and isinstance(variables[func_name], YuriLambda):
            lam = variables[func_name]
            old_vars = variables.copy()

            # restore closure scope
            variables.clear()
            variables.update(lam.closure)

            # bind arguments
            for i, param in enumerate(lam.params):
                if i < len(raw_args):
                    variables[param] = evaluate(raw_args[i])

            result = evaluate(lam.body_expr)

            variables.clear()
            variables.update(old_vars)
            return result

        # built-in functions
        if func_name == "join":
            arr = evaluate(raw_args[0]) if raw_args else []
            sep = evaluate(raw_args[1]) if len(raw_args) > 1 else ""
            if not isinstance(arr, list):
                raise YuriRuntimeError("@join requires an array")
            return sep.join(str(i) for i in arr)

        elif func_name == "length":
            val = evaluate(raw_args[0]) if raw_args else None
            if isinstance(val, (list, str)):
                return len(val)
            raise YuriRuntimeError("@length requires an array or string")

        elif func_name == "band":
            return int(evaluate(raw_args[0])) & int(evaluate(raw_args[1]))
        elif func_name == "bor":
            return int(evaluate(raw_args[0])) | int(evaluate(raw_args[1]))
        elif func_name == "bxor":
            return int(evaluate(raw_args[0])) ^ int(evaluate(raw_args[1]))
        elif func_name == "bshift":
            a = int(evaluate(raw_args[0]))
            b = int(evaluate(raw_args[1]))
            return a << b if b >= 0 else a >> abs(b)

        elif func_name == "affect":
            arr = evaluate(raw_args[0]) if raw_args else []
            func_ref = raw_args[1] if len(raw_args) > 1 else None

            if not isinstance(arr, list):
                raise YuriRuntimeError("@affect requires an array as first argument")
            if func_ref is None:
                raise YuriRuntimeError("@affect requires a function as second argument")

            return _apply_affect(arr, func_ref)

        elif func_name == "choose":
            arr = evaluate(raw_args[0]) if raw_args else []
            func_ref = raw_args[1] if len(raw_args) > 1 else None

            if not isinstance(arr, list):
                raise YuriRuntimeError("@choose requires an array as first argument")

            return _apply_choose(arr, func_ref)

        elif func_name == "slice":
            arr = evaluate(raw_args[0]) if raw_args else []
            start = int(evaluate(raw_args[1])) if len(raw_args) > 1 else 0
            end = int(evaluate(raw_args[2])) if len(raw_args) > 2 else None

            if isinstance(arr, list):
                return arr[start:end]
            if isinstance(arr, str):
                return arr[start:end]
            raise YuriRuntimeError("@slice requires an array or string")

        elif func_name == "read":
            path = evaluate(raw_args[0]) if raw_args else ""
            try:
                with open(path, 'r') as f:
                    return f.read()
            except FileNotFoundError:
                raise YuriRuntimeError(
                    f"\n💔 @read — file not found: '{path}'\n"
                    f" | She reached for a story that doesn't exist.\n"
                    f" |> Hint: Check the file path.\n"
                )
            except PermissionError:
                raise YuriRuntimeError(
                    f"\n💔 @read — permission denied: '{path}'\n"
                    f"  She wasn't allowed to read that story.\n"
                )

        elif func_name == "write":
            path = evaluate(raw_args[0]) if raw_args else ""
            content = evaluate(raw_args[1]) if len(raw_args) > 1 else ""
            try:
                with open(path, 'w') as f:
                    f.write(str(content))
                return love  # returns True on success
            except PermissionError:
                raise YuriRuntimeError(
                    f"\n💔 @write — permission denied: '{path}'\n"
                    f"  She wasn't allowed to write there.\n"
                )

        elif func_name == "input":
            prompt = evaluate(raw_args[0]) if raw_args else ""
            return input(prompt)

        elif func_name == "sleep":
            seconds = float(evaluate(raw_args[0])) if raw_args else 1.0
            dream = YuriDream(sleep_dream(seconds), name="sleep")
            return dream

        if func_name in c_functions:
            return _call_c(func_name, raw_args)

        if func_name not in functions:
            raise YuriRuntimeError(f"Undefined function: @{func_name}")

        params, body = functions[func_name]
        old_vars = variables.copy()

        for i, param in enumerate(params):
            if i < len(raw_args):
                variables[param] = evaluate(raw_args[i])

        result = None
        for child in body:
            ret = run_node(child)
            if isinstance(ret, ReturnSignal):
                result = ret.value
                break

        variables.clear()
        variables.update(old_vars)
        return result

    if expr in variables:
        if expr in shared_ptrs:
            source = shared_ptrs[expr]
            if source in variables:
                variables[expr] = variables[source]
            elif source in owned:
                variables[expr] = owned[source]
        return variables[expr]

    return expr


def autoviv_set(obj_name, index_expr, value):
    import re
    raw_indices = re.findall(r'\[\[([^\]]+)\]\]', index_expr)
    indices = [evaluate(i.strip()) for i in raw_indices]

    if obj_name not in variables or variables[obj_name] == []:
        variables[obj_name] = {}

    obj = variables[obj_name]

    for i, idx in enumerate(indices[:-1]):
        if isinstance(obj, dict):
            if idx not in obj:
                next_idx = indices[i + 1]
                obj[idx] = {} if isinstance(next_idx, str) else []
            obj = obj[idx]
        elif isinstance(obj, list):
            while len(obj) <= idx:
                obj.append(None)
            if obj[idx] is None:
                next_idx = indices[i + 1]
                obj[idx] = {} if isinstance(next_idx, str) else []
            obj = obj[idx]

    final = indices[-1]
    if isinstance(obj, dict):
        obj[final] = value
    elif isinstance(obj, list):
        while len(obj) <= final:
            obj.append(None)
        obj[final] = value


def run_map(array, step):
    if not isinstance(array, list):
        raise YuriRuntimeError("@affect requires an array")

    parts = step.split(None, 1)  # split on first whitespace
    if len(parts) < 2:
        raise YuriRuntimeError("@affect requires a function name or @bloom")

    rest = parts[1].strip()

    if rest.startswith("@bloom"):
        bloom_tokens = rest.split()
        colon_idx = bloom_tokens.index(":")
        params = bloom_tokens[1:colon_idx]
        body_expr = " ".join(bloom_tokens[colon_idx + 1:])
        lam = YuriLambda(params, body_expr, variables.copy())
    elif rest in variables and isinstance(variables[rest], YuriLambda):
        lam = variables[rest]
    elif rest in functions:
        params, body = functions[rest]
        lam = None  # handle below
    else:
        raise YuriRuntimeError(f"@affect: '{rest}' is not a function or @bloom")

    results = []
    for item in array:
        if lam is not None:
            old_vars = variables.copy()
            variables.clear()
            variables.update(lam.closure)
            if lam.params:
                variables[lam.params[0]] = item
            result = evaluate(lam.body_expr)
            variables.clear()
            variables.update(old_vars)
        else:
            params, body = functions[rest]
            old_vars = variables.copy()
            if params:
                variables[params[0]] = item
            result = None
            for child in body:
                ret = run_node(child)
                if isinstance(ret, ReturnSignal):
                    result = ret.value
                    break
            variables.clear()
            variables.update(old_vars)
        results.append(result)

    return results


def run_reduce(array, step):
    if not isinstance(array, list):
        raise YuriRuntimeError("@melt requires an array on the left side of @>")

    if len(array) == 0:
        raise YuriRuntimeError("@melt cannot melt an empty array — nothing to feel.")

    parts = step.split()
    if len(parts) < 2:
        raise YuriRuntimeError("@melt requires a function name")

    func_name = parts[1]

    if func_name not in functions and func_name not in c_functions:
        raise YuriRuntimeError(f"Undefined function: @{func_name}")

    rest = parts[1].strip()

    if rest.startswith("@bloom"):
        bloom_tokens = rest.split()
        colon_idx = bloom_tokens.index(":")
        params = bloom_tokens[1:colon_idx]
        body_expr = " ".join(bloom_tokens[colon_idx + 1:])
        lam = YuriLambda(params, body_expr, variables.copy())
    elif rest in variables and isinstance(variables[rest], YuriLambda):
        lam = variables[rest]
    elif rest in functions:
        params, body = functions[rest]
        lam = None  # handle below
    else:
        raise YuriRuntimeError(f"@melt: '{rest}' is not a function or @bloom")


    accumulator = array[0]

    for item in array[1:]:
        if lam is not None:
            old_vars = variables.copy()
            variables.clear()
            variables.update(lam.closure)
            if lam.params:
                variables[lam.params[0]] = item
            result = evaluate(lam.body_expr)
            variables.clear()
            variables.update(old_vars)
        else:
            params, body = functions[func_name]
            old_vars = variables.copy()

            if len(params) >= 2:
                variables[params[0]] = accumulator
                variables[params[1]] = item
            elif len(params) == 1:
                variables[params[0]] = item

            result = None
            for child in body:
                ret = run_node(child)
                if isinstance(ret, ReturnSignal):
                    result = ret.value
                    break

            variables.clear()
            variables.update(old_vars)
            accumulator = result if result is not None else accumulator

    return accumulator


def run_filter(array, step):
    if not isinstance(array, list):
        raise YuriRuntimeError("@choose requires an array on the left side of @>")

    parts = step.split()
    if len(parts) < 2:
        raise YuriRuntimeError("@choose requires a function name")

    func_name = parts[1]

    if func_name not in functions:
        raise YuriRuntimeError(f"Undefined function: {func_name}")

    results = []
    for item in array:
        params, body = functions[func_name]
        old_vars = variables.copy()

        if params:
            variables[params[0]] = item

        result = None
        for child in body:
            ret = run_node(child)
            if isinstance(ret, ReturnSignal):
                result = ret.value
                break

        variables.clear()
        variables.update(old_vars)

        if result:
            results.append(item)

    return results


def interpolate(template, variables):
    import re
    def replacer(match):
        key = match.group(1)
        if key in variables:
            return str(variables[key])
        return f"{{{key}}}"
    return re.sub(r'\{(\w+)\}', replacer, template)


def run_node(node):
    global variables, functions

    def yuri_repr(val):
        if val is True:  return "love"
        if val is False: return "ache"
        if val is None:  return "uncertain"
        return str(val)

    # ENTRY
    if node.type == "entry":
        for child in node.children:
            run_node(child)

    # ASSIGN
    elif node.type == "assign":
        name, val = node.value

        if name in glances:
            source = glances[name]
            raise YuriRuntimeError(
            f"\n💔 YuriLang Error — glance_mutate\n\n"
            f" | '{name}' is a @glance — she can look but not touch.\n"
            f" | The original is '{source}'.\n\n"
            f" | Hint: Use @reach to mutate:\n"
            f"           @unglance {name}\n"
            f"           @reach {name} = {source}\n"
            f"           @rebond {name} = <value>\n"
            )

        if name in shared_ptrs:
            raise YuriRuntimeError(
            f"\n💔 YuriLang Error — immutable_shared\n\n"
            f" | She holds the feeling but cannot change it.\n\n"
            f" | '{name}' is a @yuu_ptr — immutable shared view.\n"
            f" | Only the original @devoted '{shared_ptrs[name]}' can be modified.\n\n"
            f" |> Hint: Use @rebond on the original @devoted variable instead.\n"
            )

        if name in awakened:
            raise YuriRuntimeError(str(err_awakened_reassign(name)))

        variables[name] = evaluate(val)

    # BOND @NEW
    elif node.type == "bond_new":
        var_name, type_name = node.value

        if type_name not in personas:
            raise YuriRuntimeError(f"Unknown persona: {type_name}")

        template = personas[type_name]
        instance = {}

        for child in node.children:
            if child.type == "assign":
                field_name, field_val = child.value
                instance[field_name] = evaluate(field_val)

        for field in template:
            if field not in instance:
                instance[field] = None

        variables[var_name] = instance

    # REBOND
    elif node.type == "rebond":
        target, val = node.value
        value = evaluate(val)

        if "[[" not in target:
            if target in glances:
                source = glances[target]
                raise YuriRuntimeError(
                f"\n💔 '{target}' is a @glance — read only.\n"
                f" |> Hint: @reach {target} = {source} for mutation.\n"
                )

            if target in reaches:
                source = reaches[target]
                variables[target] = value

                if source in variables:
                    variables[source] = value
                elif source in owned:
                    owned[source] = value
                return

            if target in shared_ptrs:
                raise YuriRuntimeError(
                f"'{target}' is a @yuu_ptr — immutable."
                )

            if target in awakened:
                raise YuriRuntimeError(str(err_awakened_reassign(target)))

            variables[target] = value
        else:
            obj_name = target.split("[[")[0].strip()
            if obj_name in glances:
                raise YuriRuntimeError(
                f"'{obj_name}' is a @glance — read only."
                )
            if obj_name in awakened:
                raise YuriRuntimeError(str(err_awakened_reassign(obj_name)))
            set_indexed(obj_name, target, value)

    # OWNERSHIP
    elif node.type == "devoted":
        name, val = node.value
        value = evaluate(val)

        if val.strip() in owned:
            source = val.strip()
            owned[name] = value

            del variables[source]
            del owned[source]
        else:
            owned[name] = value

        variables[name] = value

    # PRINT
    elif node.type == "print":
        output = [yuri_repr(evaluate(v)) for v in node.value]
        print(" ".join(output))

    # REJECT
    elif node.type == "reject":
        raise YuriRuntimeError(evaluate(node.value))

    elif node.type == "break":
        return BreakSignal()

    elif node.type == "continue":
        return ContinueSignal()

    # ECHO
    elif node.type == "echo":
        template = evaluate(node.value)
        result = interpolate(template, variables)
        print(result)

    # TRY / CATCH / FINALLY
    elif node.type == "try":
        try_body  = []
        catch_body = []
        heal_body  = []
        catch_var  = "err"

        for child in node.children:
            if child.type == "catch":
                catch_var = child.value
                catch_body = child.children
            elif child.type == "heal":
                heal_body = child.children
            else:
                try_body.append(child)

        error_caught = None
        try:
            for child in try_body:
                result = run_node(child)
                if isinstance(result, ReturnSignal):
                    for h in heal_body:
                        run_node(h)
                    return result

        except YuriRuntimeError as e:
            error_caught = str(e)

        except Exception as e:
            error_caught = str(e)

        if error_caught is not None:
            variables[catch_var] = error_caught
            for child in catch_body:
                result = run_node(child)
                if isinstance(result, ReturnSignal):
                    for h in heal_body:
                        run_node(h)
                    return result

        for child in heal_body:
            result = run_node(child)
            if isinstance(result, ReturnSignal):
                return result

    # IF
    elif node.type == "if":
        left = evaluate(node.value[0])
        op = node.value[1]
        right = evaluate(node.value[2])

        condition = False
        if op == "==":
            condition = left == right
        elif op == "!=":
            condition = left != right
        elif op == ">":
            condition = left > right
        elif op == "<":
            condition = left < right
        elif op == ">=":
            condition = left >= right
        elif op == "<=":
            condition = left <= right

        if_body = []
        else_body = []
        in_else = False

        for child in node.children:
            if child.type == "else":
                in_else = True
                continue
            if in_else:
                else_body.append(child)
            else:
                if_body.append(child)

        if condition:
            for child in if_body:
                result = run_node(child)
                if isinstance(result, ReturnSignal):
                    return result
        else:
            for child in else_body:
                result = run_node(child)
                if isinstance(result, ReturnSignal):
                    return result

    # ELSE
    elif node.type == "else":
        pass

    # LOOP
    elif node.type == "loop":
        count = int(evaluate(node.value[-1]))
        label = evaluate(node.value[0]) if len(node.value) > 1 else None

        for _ in range(count):
            if label:
                print(label)
            should_break = False
            for child in node.children:
                result = run_node(child)
                if isinstance(result, ReturnSignal):
                    return result
                if isinstance(result, BreakSignal):
                    should_break = True
                    break
                if isinstance(result, ContinueSignal):
                    break
            if should_break:
                break

    # AUTOVIVIFICATION (PERL :3)
    elif node.type == "autoviv":
        target, val = node.value
        value = evaluate(val)

        if "[[" in target:
            obj_name = target.split("[[")[0].strip()
            if obj_name in awakened:
                raise YuriRuntimeError(
                    f"'{obj_name}' has already awakened. She knows who she is."
                )
            autoviv_set(obj_name, target, value)
        else:
            if target in awakened:
                raise YuriRuntimeError(
                    f"'{target}' has already awakened. She knows who she is."
                )
            variables[target] = value

    # NOT / APART
    elif node.type == "not":
        left = evaluate(node.value[0])
        op = node.value[1]
        right = evaluate(node.value[2])

        condition = False
        if op == "==":  condition = left == right
        elif op == "!=": condition = left != right
        elif op == ">":  condition = left > right
        elif op == "<":  condition = left < right
        elif op == ">=": condition = left >= right
        elif op == "<=": condition = left <= right

        if not condition:
            for child in node.children:
                result = run_node(child)
                if isinstance(result, ReturnSignal):
                    return result

    # WHILE LOOP
    elif node.type == "while":
        def check_condition():
            left = evaluate(node.value[0])
            op = node.value[1]
            right = evaluate(node.value[2])
            if op == "==":  return left == right
            if op == "!=":  return left != right
            if op == ">":   return left > right
            if op == "<":   return left < right
            if op == ">=":  return left >= right
            if op == "<=":  return left <= right
            return False

        max_iterations = 10000
        count = 0

        def check_condition():
            left = evaluate(node.value[0])
            op = node.value[1]
            right = evaluate(node.value[2])
            print(f"DEBUG FATE: left={repr(left)} op={op} right={repr(right)}")

            def coerce(v):
                if isinstance(v, (int, float)):
                    return v
                if isinstance(v, str):
                    if v.lstrip('-').isdigit():
                        return int(v)
                    try:
                        return float(v)
                    except ValueError:
                        pass
                return v

            left = coerce(left)
            right = coerce(right)

            if op == "==":  return left == right
            if op == "!=":  return left != right
            if op == ">":   return left > right
            if op == "<":   return left < right
            if op == ">=":  return left >= right
            if op == "<=":  return left <= right
            return False

        while check_condition():
            if count >= max_iterations:
                raise YuriRuntimeError("@fate loop exceeded 10000 iterations — infinite loop?")
            should_break = False
            for child in node.children:
                result = run_node(child)
                if isinstance(result, ReturnSignal):
                    return result
                if isinstance(result, BreakSignal):
                    should_break = True
                    break
                if isinstance(result, ContinueSignal):
                    break
            if should_break:
                break
            count += 1

    # PATTERN MATCHING 
    elif node.type == "match":
        subject = evaluate(node.value)

        for case in node.children:
            if case.type != "case":
                continue

            if case.value == "_":
                for child in case.children:
                    result = run_node(child)
                    if isinstance(result, ReturnSignal):
                        return result
                break

            case_val = evaluate(case.value)

            if subject == case_val:
                for child in case.children:
                    result = run_node(child)
                    if isinstance(result, ReturnSignal):
                        return result
                break

    # MEMORY / RECALL / FORGET
    elif node.type == "memory_set":
        key, val = node.value
        memory_set(evaluate(key), evaluate(val))

    elif node.type == "memory_get":
        key = evaluate(node.value)
        result = memory_get(key)
    
        clean_key = key.strip('"')
        variables[clean_key] = result
        return result

    elif node.type == "memory_forget":
        key = evaluate(node.value)
        memory_forget(key)

    elif node.type == "yuu_ptr":
        alias, source = node.value
        source_val = evaluate(source)

        if source not in variables and source not in owned:
            raise YuriRuntimeError(
            str(err_undefined_variable(source))
        )

        shared_ptrs[alias] = source

        variables[alias] = source_val

    # MAPPING
    elif node.type == "affect_standalone":
        arr_name, func_ref = node.value
        arr = evaluate(arr_name)
        return _apply_affect(arr, func_ref)

    # FILTER 
    elif node.type == "choose_standalone":
        arr_name, func_ref = node.value
        arr = evaluate(arr_name)
        return _apply_choose(arr, func_ref)

    # SLICE 
    elif node.type == "slice":
        arr_expr, start_expr, end_expr = node.value
        arr = evaluate(arr_expr)
        start = int(evaluate(start_expr))
        end = int(evaluate(end_expr))
        if isinstance(arr, (list, str)):
            return arr[start:end]
        raise YuriRuntimeError("@slice requires an array or string")

    # READ/WRITE IO
    elif node.type == "read":
        path = evaluate(node.value)
        try:
            with open(path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            raise YuriRuntimeError(
                f"\n💔 @read — '{path}' not found.\n"
                f"  She reached for a story that doesn't exist. 🪷\n"
            )

    elif node.type == "write":
        path, val = node.value
        path    = evaluate(path)
        content = evaluate(val)
        with open(path, 'w') as f:
            f.write(str(content))

    # FUNCTION DEFINE
    elif node.type == "function":
        name, params = node.value
        functions[name] = (params, node.children)

        if node.param_hints or node.return_hint:
            register_func_hints(name, node.param_hints, node.return_hint)

        if "async" in node.decorators:
            async_fn = make_async_ship(
                params, node.children, functions, variables
            )
            functions[name] = (params, node.children, "async")
            functions[f"__async_{name}"] = async_fn
        else:
            functions[name] = (params, node.children)

    # FUNCTION CALL
    elif node.type == "call":
        name, args = node.value

        if name in c_functions:
            return _call_c(name, args)

        if name not in functions:
            print(f"Undefined function: {name}")
            return

        params, body = functions[name]
        old_vars = variables.copy()

        for i, param in enumerate(params):
            if i < len(args):
                variables[param] = evaluate(args[i])

        for child in body:
            result = run_node(child)
            if isinstance(result, ReturnSignal):
                variables.clear()
                variables.update(old_vars)
                return result.value

        variables.clear()
        variables.update(old_vars)

    # TYPE ANNOTATIOND
    elif node.type == "crush":
        name, hint = node.value
        register_crush(name, hint)

    # ASYNCHRONOUS
    elif node.type == "dream":
        var_name, expr = node.value
        expr = expr.strip()

        if expr.startswith("@"):
            parts = expr.split()
            func_name = parts[0][1:]
            raw_args  = parts[1:]

            if func_name in functions:
                entry = functions[func_name]
                if len(entry) == 3 and entry[2] == "async":
                    async_fn = functions[f"__async_{func_name}"]
                    evaled_args = [evaluate(a) for a in raw_args]
                    coro = async_fn(*evaled_args)
                    dream = YuriDream(coro, name=func_name)

                    if var_name:
                        variables[var_name] = dream
                        return dream
                    else:
                        raise YuriRuntimeError(
                        f"\n💔 @dream — '{func_name}' is not ##async\n"
                        f" | She tried to dream about a function that doesn't dream.\n"
                        f" |> Hint: Add ##async above @ship {func_name}:\n"
                        )

        if expr.startswith("@sleep"):
            parts = expr.split()
            seconds = float(evaluate(parts[1])) if len(parts) > 1 else 1.0
            dream = YuriDream(sleep_dream(seconds), name="sleep")
            if var_name:
                variables[var_name] = dream
            return dream

    # AWAIT
    elif node.type == "wake":
        target = node.value

        if target is None:
            return

        val = variables.get(target)

        if val is None:
            raise YuriRuntimeError(
            f"\n💔 @wake — '{target}' has no dream to wake from\n"
            f" |> Hint: Use @dream first: @dream {target} = @my_async_func\n"
            )

        if isinstance(val, YuriDream):
            result = run_dream(val)
            variables[target] = result
            val.done = True
            val.result = result
            return result

        return val

    # GATHER
    elif node.type == "gather":
        arr_name = node.value
        dreams = evaluate(arr_name)

        loop = get_event_loop()
        results = loop.run_until_complete(gather_dreams(dreams))
        variables[arr_name] = results
        return results

    # LAMBDA
    elif node.type == "bloom":
        params, body_expr = node.value
        return YuriLambda(params, body_expr, variables.copy())

    # RETURN
    elif node.type == "return":
        return ReturnSignal(evaluate(node.value))

    # IMPORT
    elif node.type == "import":
        load_module(node.value, functions)

    # EXTERN
    elif node.type == "extern":
        path, name, ret = node.value

        lib = ctypes.CDLL(path)
        func = getattr(lib, name)

        # assume args match return type
        if ret == "double":
            func.restype = ctypes.c_double
            func.argtypes = [ctypes.c_double]   

        elif ret == "float":
            func.restype = ctypes.c_float
            func.argtypes = [ctypes.c_float]

        elif ret == "string":
            func.restype = ctypes.c_char_p
            
        elif ret == "int":
            func.restype = ctypes.c_long
            func.argtypes = [ctypes.c_long]

        c_functions[name] = func
        
    # PIPELINES
    elif node.type == "pipeline":
        parts = node.value.split("@>")
        current = evaluate(parts[0].strip())

        for step in parts[1:]:
            step = step.strip()

            if step.startswith("@affect"):
                current = run_map(current, step)
            elif step.startswith("@choose"):
                current = run_filter(current, step)
            elif step.startswith("@melt"):
                current = run_reduce(current, step)

        return current

    # AWAKE / PERMANENT VAR
    elif node.type == "awakening":
        name = node.value

        if name in shared_ptrs:
            source = shared_ptrs[name]
            raise YuriRuntimeError(
            f"\n💔 YuriLang Error — awakening_blocked\n\n"
            f" | She holds the feeling, but it isn't hers to awaken.\n\n"
            f" | '{name}' is a @yuu_ptr pointing to @devoted '{source}'.\n"
            f" | Only the original can awaken.\n\n"
            f" |> Hint: @awakening {source}\n"
            )

        if name not in variables and name not in owned:
            raise YuriRuntimeError(
            f"'{name}' cannot awaken — she hasn't found herself yet."
            )

        awakened.add(name)

    # BORROWINGS
    elif node.type == "glance":
        alias, source = node.value

        if source not in variables and source not in owned:
            raise YuriRuntimeError(
            str(err_undefined_variable(source))
            )

        if reach_of.get(source):
            reacher = reach_of[source]
            raise YuriRuntimeError(
            f"\n💔 YuriLang Error — borrow_conflict\n\n"
            f" | She tried to glance at '{source}' but\n"
            f" | '{reacher}' is already reaching into it.\n\n"
            f" | You cannot @glance while a @reach is active.\n"
            f" |> Hint: @unreach {reacher} first, then @glance.\n"
            )

        # register glance borrow
        glances[alias] = source
        glances_of.setdefault(source, set()).add(alias)
        variables[alias] = variables.get(source) or owned.get(source)

    elif node.type == "reach":
        alias, source = node.value

        if source not in variables and source not in owned:
            raise YuriRuntimeError(
            str(err_undefined_variable(source))
            )

        # cannot reach while someone (or a var) is glancing
        active_glances = glances_of.get(source, set())
        if active_glances:
            glancers = ", ".join(active_glances)
            raise YuriRuntimeError(
            f"\n💔 YuriLang Error — borrow_conflict\n\n"
            f" | She tried to reach into '{source}' but\n"
            f" | [{glancers}] are already glancing at it.\n\n"
            f" | You cannot @reach while @glance is active.\n"
            f" | Hint: @unglance first, then @reach.\n"
            )

        # cannot reach while already reached
        if reach_of.get(source):
            existing = reach_of[source]
            raise YuriRuntimeError(
            f"\n💔 YuriLang Error — borrow_conflict\n\n"
            f" | She tried to reach into '{source}' but\n"
            f" | '{existing}' is already reaching into it.\n\n"
            f" | Only one @reach at a time.\n"
            f" |> Hint: @unreach {existing} first.\n"
            )

        # register reach borrow
        reaches[alias] = source
        reach_of[source] = alias
        variables[alias] = variables.get(source) or owned.get(source)

    elif node.type == "unglance":
        alias = node.value
        if alias in glances:
            source = glances[alias]
            glances_of.get(source, set()).discard(alias)
            del glances[alias]
            if alias in variables:
                del variables[alias]

    elif node.type == "unreach":
        alias = node.value
        if alias in reaches:
            source = reaches[alias]

        if alias in variables:
            if source in variables:
                variables[source] = variables[alias]
            elif source in owned:
                owned[source] = variables[alias]
            del variables[alias]
        reach_of[source] = None
        del reaches[alias]

    # STRUCTS
    elif node.type == "persona":
        name = node.value
        fields = [child.value for child in node.children if child.type == "field"]
        personas[name] = fields

    elif node.type == "new":
        type_name, raw_fields = node.value

        if type_name not in personas:
            raise YuriRuntimeError(f"Unknown persona: {type_name}")

        template = personas[type_name]
        instance = {}

        for field in template:
            if field in raw_fields:
                instance[field] = evaluate(raw_fields[field])
            else:
                instance[field] = None

        return instance

    # ENUMS
    elif node.type == "spectrum":
        name = node.value
        variants = {}
        for child in node.children:
            if child.type == "field":
                variant_name = child.value
                variants[variant_name] = f"{name}.{variant_name}"
        spectrums[name] = variants
        variables[name] = variants

    else:
        print("Unknown node:", node.type)


def run(code):
    tree = parse(code)

    for node in tree.children:
        run_node(node)
