class Node:
    def __init__(self, type_, value=None):
        self.type = type_
        self.value = value
        self.children = []
        self.decorators = []
        self.param_hints = {}
        self.return_hint = None
