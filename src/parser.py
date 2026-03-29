# Parser for keywords, operators, and more
# They'll be added slowly later on

from src.lexer import tokenize

def parse_line(line):
    tokens = tokenize(line)
    if not tokens:
        return None

    keyword = tokens[0]

    if keyword == "@bond":
        return ("assign", tokens[1], tokens[3])

    elif keyword == "@confess":
        return ("print", tokens[1:])

    elif keyword == "@jealous":
        return ("if", tokens[1:])

    elif keyword == "@cling":
        return ("loop", tokens[1:])

    elif keyword == "@yuri":
        return ("import", tokens[1])

    elif keyword == "@wlw":
        return ("entry",)

    return ("unknown", tokens)
