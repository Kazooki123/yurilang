# YuriLangs main lexer
import re


T_REGEX = r'(#\[\[[^\]]*\]\])|(\[\[[^\]]*\]\])|(@\w+)|("(?:[^"]*)")|(\d+)|([=:+\-*/><!]+)|(\w+\.\w+)|(\w+)'


def get_indent_lvl(line):
    return len(line) - len(line.lstrip(" "))

def tokenize(line):
    comment_match = re.search(r'\?\s*\(.*\)', line)
    if comment_match:
        line = line[:comment_match.start()]

    if not line.strip():
        return []

    tokens = []
    for match in re.finditer(T_REGEX, line):
        tokens.append(match.group())
    return tokens
