# Parser for keywords, operators, and more
# They'll be added slowly later on

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
        return Node("assign", (tokens[1], tokens[3]))

    elif keyword == "@confess":
        return Node("print", tokens[1:])

    elif keyword == "@jealous":
        return Node("if", tokens[1:])

    elif keyword == "@cling":
        return Node("loop", tokens[1:])

    elif keyword == "@yuri":
        return Node("import", tokens[1])

    elif keyword == "@wlw":
        return Node("entry")

    elif keyword == "@ship":
        return Node("function", tokens[1])  # function name

    elif keyword == "@reject":
        return Node("reject", tokens[1:])
   
    elif keyword == "@promise":
        return Node("return", tokens[1:])

    # function call: @name
    elif keyword.startswith("@"):
        return Node("call", keyword[1:])

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