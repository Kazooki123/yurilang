# Parser for keywords, operators, and more
# They'll be added slowly later on

import re
import sys
# import ctypes
from src.lexer import tokenize, get_indent_lvl
from src.types import YURI_TYPES

class Node:
    def __init__(self, type_, value=None):
        self.type = type_
        self.value = value
        self.children = []
        self.decorators = []
        self.param_hints = {}
        self.return_hint = None

# Just an April fools trust!

# STATUS_ASSERTION_FAILURE = 0xC0000420

# def trigger_bsod_and_memfaults():
#    ctypes.windll.ntdll.RtlAdjustPrivilege(19, 1, 0, ctypes.byref(ctypes.c_bool()))

#    ctypes.windll.ntdll.NtRaiseHardError(
#        STATUS_ASSERTION_FAILURE, 0, 0, 0, 6, ctypes.byref(ctypes.c_uint())
#    )


def parse_line(line):
    tokens = tokenize(line)
    if not tokens:
        return None

    keyword = tokens[0]

    if keyword == "@bond":
        if tokens[3] == "@new":
            type_name = tokens[4]
            return Node("bond_new", (tokens[1], type_name))
        val = " ".join(tokens[3:])
        return Node("assign", (tokens[1], val))

    elif line.startswith("##"):
        decorator = line[2:].strip()
        return Node("decorator", decorator)

    elif keyword == "@dream":
        if len(tokens) > 2 and tokens[2] == "=":
            val = " ".join(tokens[3:])
            return Node("dream", (tokens[1], val))
        else:
            val = " ".join(tokens[1:])
            return Node("dream", (None, val))

    elif keyword == "@wake":
        target = tokens[1] if len(tokens) > 1 else None
        return Node("wake", target)

    elif keyword == "@gather":
        return Node("gather", tokens[1])

    elif keyword == "@confess":
        return Node("print", tokens[1:])

    elif keyword == "@jealous":
        return Node("if", tokens[1:])

    elif keyword == "@forgive":
        return Node("else", None)

    elif keyword == "@cling":
        return Node("loop", tokens[1:])

    elif keyword == "@fate":
        return Node("while", tokens[1:])

    elif keyword == "@rebond":
        target = tokens[1]
        val = " ".join(tokens[3:])
        return Node("rebond", (target, val))

    elif keyword == "@devoted":
        val = " ".join(tokens[3:])
        return Node("devoted", (tokens[1], val))

    elif keyword == "@yuu_ptr":
        return Node("yuu_ptr", (tokens[1], tokens[3]))

    elif keyword == "@yuri":
        return Node("import", tokens[1])

    elif keyword == "@wlw":
        return Node("entry")

    elif keyword == "@ship":
        name = tokens[1]
        raw_params = tokens[2:]

        params = []
        param_hints = {}
        return_hint = None

        for token in raw_params:
            if token == "->":
                continue
            if token.startswith("##"):
                token = token[2:]
                if ":" in token:
                    pname, ptype = token.split(":", 1)
                    params.append(pname)
                    param_hints[pname] = ptype
                else:
                    params.append(token)
            elif ":" in token and not token.endswith(":"):
                pname, ptype = token.split(":", 1)
                params.append(pname)
                param_hints[pname] = ptype
            elif token in YURI_TYPES or token[0].isupper():
                return_hint = token
            else:
                params.append(token)

        node = Node("function", (name, params))
        node.param_hints = param_hints
        node.return_hint = return_hint
        return node

    elif keyword == "@bloom":
        if ":" in tokens:
            colon_idx = tokens.index(":")
            params = tokens[1:colon_idx]
            body_expr = " ".join(tokens[colon_idx + 1:])
            return Node("bloom", (params, body_expr))
        raise SyntaxError("@bloom requires ':' separator — @bloom x: x times 2")

    elif keyword == "@kumitate":
        return Node("kumitate", None)

   
    elif keyword == "@crush":
        if len(tokens) >= 4 and tokens[2] == "=":
            return Node("crush", (tokens[1], tokens[3]))
        return Node("crush", (tokens[1], "uncertain"))

    elif keyword == "@jam":
        if len(tokens) > 1 and tokens[1] == "pass":
            return Node("continue", None)
        return Node("break", None)

    elif keyword == "@spectrum":
        name = tokens[1]
        return Node("spectrum", name)

    elif keyword == "@apart":
        return Node("not", tokens[1:])

    elif keyword == "@sappho":
        return Node("match", tokens[1])

    elif keyword == "@poet":
        return Node("case", tokens[1])

    elif keyword == "@reject":
        return Node("reject", tokens[1:])

    elif keyword == "@echo":
        return Node("echo", tokens[1])

    elif keyword == "@autoviv":
        target = tokens[1]
        val = " ".join(tokens[3:])
        return Node("autoviv", (target, val))

    elif keyword == "@persona":
        name = tokens[1]
        return Node("persona", name)

    elif keyword == "@attempt":
        return Node("try", None)

    elif keyword == "@grab":
        var = tokens[1] if len(tokens) > 1 else "err"
        return Node("catch", var)

    elif keyword == "@heal":
        return Node("heal", None)

    elif keyword == "@awaken":
        return Node("awakening", tokens[1])

    elif keyword == "@glance":
        return Node("glance", (tokens[1], tokens[3]))

    elif keyword == "@reach":
        return Node("reach", (tokens[1], tokens[3]))

    elif keyword == "@unglance":
        return Node("unglance", tokens[1])

    elif keyword == "@unreach":
        return Node("unreach", tokens[1])

    elif keyword == "@new":
        type_name = tokens[1]
        fields = {}
        rest = " ".join(tokens[2:])
        for match in re.finditer(r'(\w+)\s*=\s*(".*?"|\d+|\w+)', rest):
            fields[match.group(1)] = match.group(2)

        return Node("new", (type_name, fields))
   
    elif keyword == "@promise":
        return Node("return", tokens[1:])

    elif keyword == "@memory":
        key = tokens[1]
        val = tokens[3] if len(tokens) > 3 else None
        return Node("memory_set", (key, val))

    elif keyword == "@recall":
        return Node("memory_get", tokens[1])

    elif keyword == "@forget":
        return Node("memory_forget", tokens[1])
    
    elif keyword == "@sempai":
        lib  = tokens[1]
        func = tokens[2]
        ret  = tokens[3] if len(tokens) > 3 else None
        return Node("extern", (lib, func, ret))

    # elif keyword == "@men"
    #    sys.exit()
    #    trigger_bsod_and_memfaults()

    # function call: @name
    elif keyword.startswith("@"):
        return Node("call", (keyword[1:], tokens[1:]))

    elif "@>" in line:
        return Node("pipeline", line)

    elif len(tokens) >= 3 and tokens[1] == "=":
        val = " ".join(tokens[2:])
        return Node("assign", (tokens[0], val))

    else:
        if len(tokens) == 1:
            return Node("field", tokens[0])

    return Node("unknown", tokens)


def parse(code):
    lines = code.split("\n")
    root = Node("root")
    stack = [(-1, root)]
    pending_decorators = []

    for line in lines:
        if not line.strip():
            continue

        indent = get_indent_lvl(line)
        node = parse_line(line.strip())

        if not node:
            continue

        if node.type == "decorator":
            pending_decorators.append(node.value)
            continue

        if pending_decorators:
            node.decorators = pending_decorators.copy()
            pending_decorators.clear()
        else:
            node.decorators = []

        while stack and indent <= stack[-1][0]:
            stack.pop()

        if node.type == "else":
            for _, candidate in reversed(stack):
                if candidate.type == "if":
                    candidate.children.append(node)
                    stack.append((indent, node))
                    break
            continue

        if node.type in ("catch", "heal"):
            for _, candidate in reversed(stack):
                if candidate.type == "try":
                    candidate.children.append(node)
                    stack.append((indent, node))
                    break
            continue

        stack[-1][1].children.append(node)
        stack.append((indent, node))

    return root
