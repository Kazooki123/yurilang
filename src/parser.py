# Parser for keywords, operators, and more
# They'll be added slowly later on

import re
from src.lexer import tokenize, get_indent_lvl

class Node:
    def __init__(self, type_, value=None):
        self.type = type_
        self.value = value
        self.children = []

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

    elif keyword == "@yuri":
        return Node("import", tokens[1])

    elif keyword == "@wlw":
        return Node("entry")

    elif keyword == "@ship":
        name = tokens[1]
        params = tokens[2:]
        return Node("function", (name, params))

    elif keyword == "@sappho":
        return Node("match", tokens[1])

    elif keyword == "@poet":
        return Node("case", tokens[1])

    elif keyword == "@reject":
        return Node("reject", tokens[1:])

    elif keyword == "@persona":
        name = tokens[1]
        return Node("persona", name)

    elif keyword == "@new":
        type_name = tokens[1]
        fields = {}
        rest = " ".join(tokens[2:])
        for match in re.finditer(r'(\w+)\s*=\s*(".*?"|\d+|\w+)', rest):
            fields[match.group(1)] = match.group(2)

        return Node("new", (type_name, fields))
   
    elif keyword == "@promise":
        return Node("return", tokens[1:])

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

    stack = [(-1, root)]  # (indent_level, node)

    for line in lines:
        if not line.strip():
            continue

        indent = get_indent_lvl(line)
        node = parse_line(line.strip())

        if not node:
            continue

        # Fix indentation hierarchy
        while stack and indent <= stack[-1][0]:
            stack.pop()

        stack[-1][1].children.append(node)
        stack.append((indent, node))

    return root

