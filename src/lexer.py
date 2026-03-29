# YuriLangs main lexer
import re

T_REGEX = r'(@\w+)|("(?:[^"]*)")|(\d+)|([=:+\-*/><!]+)|(\w+)'

def tokenize(line):
    tokens = []
    for match in re.finditer(T_REGEX, line):
        tokens.append(match.group())
    return tokens
