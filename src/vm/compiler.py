"""
Bytecode Compiler - Yurilang

Outputs `.yuric` files that you can execute by using the `--vm` flag.
"""

from src.core.parser import parse


class BytecodeCompiler:
    def __init__(self):
        self.instructions = []
        self.label_count = 0

    def new_label(self, name="label"):
        self.label_count += 1
        return f"{name}_{self.label_count}"

    def emit(self, *instr):
        self.instructions.append(instr)

    def compile_expr(self, expr):
        if isinstance(expr, int):
            self.emit("PUSH", expr)
            return

        if isinstance(expr, str):
            expr = expr.strip()

            if expr.lstrip("-").isdigit():
                self.emit("PUSH", int(expr))
                return

            if expr.startswith('"') and expr.endswith('"'):
                self.emit("PUSH", expr[1:-1])
                return

            if expr.startswith("@"):
                parts = expr.split()
                func = parts[0][1:]
                args = parts[1:]
                for arg in args:
                    self.compile_expr(arg)
                op_map = {"add": "ADD", "sub": "SUB", "mul": "MUL", "div": "DIV"}
                if func in op_map:
                    self.emit(op_map[func])
                else:
                    self.emit("CALL", func)
                return

            self.emit("LOAD", expr)

        if isinstance(expr, list):
            if len(expr) == 3:
                self.compile_expr(expr[0])
                self.compile_expr(expr[2])
                op_map = {"plus": "ADD", "minus": "SUB", "times": "MUL", "over": "DIV"}
                if expr[1] in op_map:
                    self.emit(op_map[expr[1]])
            return

    def compile_node(self, node):
        if node.type in ("root", "entry"):
            for child in node.children:
                self.compile_node(child)

        elif node.type == "assign":
            name, val = node.value
            self.compile_expr(val)
            self.emit("STORE", name)

        elif node.type == "print":
            for token in node.value:
                token = token.strip()
                if token.startswith('"') and token.endswith('"'):
                    self.emit("PRINT_STR", token[1:-1])
                else:
                    self.emit("LOAD", token)
                    self.emit("PRINT")

        elif node.type == "if":
            left, op, right = node.value[0], node.value[1], node.value[2]
            else_label = self.new_label("else")
            end_label = self.new_label("end_if")

            if_body, else_body = [], []
            in_else = False
            for child in node.children:
                if child.type == "else":
                    in_else = True
                    continue
                (else_body if in_else else if_body).append(child)

            self.compile_expr(left)
            self.compile_expr(right)
            self.emit("COMPARE", op)
            self.emit("JUMP_IF_FALSE", else_label if else_body else end_label)

            for child in if_body:
                self.compile_node(child)

            if else_body:
                self.emit("JUMP", end_label)
                self.emit("LABEL", else_label)
                for child in else_body:
                    self.compile_node(child)

            self.emit("LABEL", end_label)

        elif node.type == "loop":
            count = node.value[-1]
            loop_label = self.new_label("loop")
            end_label = self.new_label("end_loop")
            counter = f"__loop_{self.label_count}"

            self.compile_expr(count)
            self.emit("STORE", counter)

            self.emit("LABEL", loop_label)
            self.emit("LOAD", counter)
            self.emit("PUSH", 0)
            self.emit("COMPARE", ">")
            self.emit("JUMP_IF_FALSE", end_label)

            for child in node.children:
                self.compile_node(child)

            self.emit("LOAD", counter)
            self.emit("PUSH", 1)
            self.emit("SUB")
            self.emit("STORE", counter)
            self.emit("JUMP", loop_label)
            self.emit("LABEL", end_label)

        elif node.type == "while":
            loop_label = self.new_label("while")
            end_label = self.new_label("end_while")
            left, op, right = node.value[0], node.value[1], node.value[2]

            self.emit("LABEL", loop_label)
            self.compile_expr(left)
            self.compile_expr(right)
            self.emit("COMPARE", op)
            self.emit("JUMP_IF_FALSE", end_label)

            for child in node.children:
                self.compile_node(child)

            self.emit("JUMP", loop_label)
            self.emit("LABEL", end_label)

        elif node.type == "function":
            name, params = node.value
            end_label = self.new_label(f"end_{name}")

            self.emit("JUMP", end_label)
            self.emit("LABEL", name)

            for i, param in enumerate(params):
                self.emit("STORE", param)

            for child in node.children:
                self.compile_node(child)

            self.emit("RETURN")
            self.emit("LABEL", end_label)

        elif node.type == "return":
            self.compile_expr(node.value)
            self.emit("RETURN")

        else:
            pass

    def compile(self, code):
        tree = parse(code)
        for node in tree.children:
            self.compile_node(node)
        self.emit("HALT")
        return self.instructions


def compile_to_bytecode(code):
    return BytecodeCompiler().compile(code)
