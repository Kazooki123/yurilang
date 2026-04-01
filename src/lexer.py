# YuriLangs main lexer
import re

T_REGEX = r'(#\[\[[^\]]*\]\])|(\[\[[^\]]*\]\])|(@\w+)|("(?:[^"]*)")|(\d+)|([=:+\-*/><!]+)|(\w+)'

def get_indent_lvl(line):
    return len(line) - len(line.lstrip(" "))

def tokenize(line):
    tokens = []
    for match in re.finditer(T_REGEX, line):
        tokens.append(match.group())
    return tokens
