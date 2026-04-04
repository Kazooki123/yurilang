import re
from src.parser import parse
from src.modules import load_module
from vm.memory import memory_set, memory_get, memory_forget

variables = {}
functions = {}
personas = {}
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


def evaluate(expr):
    global variables

    if isinstance(expr, (int, float, bool)):
        return expr

    if isinstance(expr, list):
        if len(expr) == 3:
            left = evaluate(expr[0])
            op = expr[1]
            right = evaluate(expr[2])

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

            if op in YURI_OPS:
                if op in ("plus", "with"):
                    l, r = coerce(left), coerce(right)
                    if isinstance(l, (int, float)) and isinstance(r, (int, float)):
                        return YURI_OPS[op](l, r)

                    return str(left) + str(right)
                else:
                    return YURI_OPS[op](coerce(left), coerce(right))

    if not isinstance(expr, str):
        return expr

    expr = expr.strip()

    if expr.startswith('"') and expr.endswith('"'):
        return expr[1:-1]

    if expr.lstrip('-').isdigit():
        return int(expr)

    try:
        return float(expr)
    except ValueError:
        pass

    for op in YURI_OPS:
        if f" {op} " in expr:
            parts = expr.split(f" {op} ", 1)
            left = evaluate(parts[0].strip())
            right = evaluate(parts[1].strip())
            left = coerce(left)
            right = coerce(right)
            if op in ("plus", "with"):
                if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                    return YURI_OPS[op](left, right)
                return str(left) + str(right)
            return YURI_OPS[op](left, right)

    if "[[" in expr and not expr.startswith("[[") and not expr.startswith("#[["):
        import re
        obj_name = expr.split("[[")[0].strip()
        rest = expr[len(obj_name):]
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

    if (expr.startswith("[[") or expr.startswith("#[[")):
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
        parts = expr.split()
        func_name = parts[0][1:]
        raw_args  = parts[1:]

        # Debugging
        # print(f"DEBUG CALL: func={func_name}, raw_args={raw_args}")

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

        elif func_name == "input":
            prompt = evaluate(raw_args[0]) if raw_args else ""
            return input(prompt)

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
        raise YuriRuntimeError("@affect requires an array on the left side of @>")

    step = step.strip()

    parts = step.split()
    if len(parts) < 2:
        raise YuriRuntimeError("@affect requires a function name")

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

    if func_name not in functions:
        raise YuriRuntimeError(f"Undefined function: @{func_name}")

    accumulator = array[0]

    for item in array[1:]:
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

    # ENTRY
    if node.type == "entry":
        for child in node.children:
            run_node(child)

    # ASSIGN
    elif node.type == "assign":
        name, val = node.value
        if name in awakened:
            raise YuriRuntimeError(f"'{name}' has already awakened. It is permanent.")
        variables[name] = evaluate(val)
        # print(f"DEBUG assign: {name} = {variables[name]}")

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

        if "[[" in target:
            obj_name = target.split("[[")[0].strip()
            if obj_name not in variables:
                raise YuriRuntimeError(f"Undefined variable: {obj_name}")
            if obj_name in awakened:
                raise YuriRuntimeError(f"'{obj_name}' has already awakened. She knows who she is.")
            set_indexed(obj_name, target, value)
        else:
            if target in awakened:
                raise YuriRuntimeError(f"'{target}' has already awakened. She knows who she is.")
            variables[target] = value

    # PRINT
    elif node.type == "print":
        output = [str(evaluate(v)) for v in node.value]
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

    # FUNCTION DEFINE
    elif node.type == "function":
        name, params = node.value
        functions[name] = (params, node.children)

    # FUNCTION CALL
    elif node.type == "call":
        name, args = node.value

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

    # RETURN
    elif node.type == "return":
        return ReturnSignal(evaluate(node.value))

    # IMPORT
    elif node.type == "import":
        load_module(node.value, functions)

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
        if name not in variables:
            raise YuriRuntimeError(f"'{name}' cannot awaken!")
        awakened.add(name)

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
