from src.parser import parse


class YASMCompileError(Exception):
    pass


class YASMCompiler:
    def __init__(self):
        self.functions = []  # compiled wat functions
        self.exports = []  # exported function names
        self.data = []  # string data section
        self.str_count = 0  # string label counter
        self.str_offset = 0  # tracks actual memory byte offset
        self.locals = {}  # local variable → index

    def new_string(self, value):
        offset = self.str_offset
        encoded = value.encode("utf-8")
        self.data.append((offset, value, len(encoded)))
        self.str_offset += len(encoded) + 1  # +1 for null terminator
        return offset

    def compile_expr(self, expr):
        instrs = []

        if isinstance(expr, int):
            instrs.append(f"i32.const {expr}")
            return instrs

        if isinstance(expr, float):
            instrs.append(f"f64.const {expr}")
            return instrs

        if isinstance(expr, str):
            expr = expr.strip()

            if expr.lstrip("-").isdigit():
                instrs.append(f"i32.const {expr}")
                return instrs

            if expr == "love":
                instrs.append("i32.const 1")
                return instrs

            if expr == "ache":
                instrs.append("i32.const 0")
                return instrs

            # variable lookup
            if expr in self.locals:
                instrs.append(f"local.get ${expr}")
                return instrs

            # inline binary
            for op in ["plus", "minus", "times", "over"]:
                if f" {op} " in expr:
                    parts = expr.split(f" {op} ", 1)
                    instrs += self.compile_expr(parts[0].strip())
                    instrs += self.compile_expr(parts[1].strip())
                    op_map = {
                        "plus": "i32.add",
                        "minus": "i32.sub",
                        "times": "i32.mul",
                        "over": "i32.div_s",
                    }
                    instrs.append(op_map[op])
                    return instrs

        return instrs

    def compile_node(self, node, body):
        """Append WAT instructions to body list."""

        if node.type in ("root", "entry"):
            for child in node.children:
                self.compile_node(child, body)

        elif node.type == "assign":
            name, val = node.value
            if name not in self.locals:
                self.locals[name] = len(self.locals)
                body.append(f"(local ${name} i32)")
            body += self.compile_expr(val)
            body.append(f"local.set ${name}")

        elif node.type == "print":
            for token in node.value:
                token = token.strip()
                if token.startswith('"') and token.endswith('"'):
                    # string print via imported js console.log
                    idx = self.new_string(token[1:-1])
                    body.append(f"i32.const {idx}")
                    body.append("call $print_str")
                elif token in self.locals:
                    body.append(f"local.get ${token}")
                    body.append("call $print_int")

        elif node.type == "return":
            body += self.compile_expr(node.value)
            body.append("return")

        elif node.type == "if":
            left, op, right = node.value[0], node.value[1], node.value[2]
            body += self.compile_expr(left)
            body += self.compile_expr(right)
            cmp_map = {
                "==": "i32.eq",
                "!=": "i32.ne",
                ">": "i32.gt_s",
                "<": "i32.lt_s",
                ">=": "i32.ge_s",
                "<=": "i32.le_s",
            }
            body.append(cmp_map.get(op, "i32.eq"))

            # separate if/else
            if_body, else_body = [], []
            in_else = False
            for child in node.children:
                if child.type == "else":
                    in_else = True
                    continue
                (else_body if in_else else if_body).append(child)

            body.append("(if")
            body.append("  (then")
            for child in if_body:
                self.compile_node(child, body)
            body.append("  )")
            if else_body:
                body.append("  (else")
                for child in else_body:
                    self.compile_node(child, body)
                body.append("  )")
            body.append(")")

        elif node.type == "loop":
            count = node.value[-1]
            body += self.compile_expr(count)
            body.append("(local $__loop_i i32)")
            body.append("local.set $__loop_i")
            body.append("(block $break")
            body.append("  (loop $continue")
            body.append("    local.get $__loop_i")
            body.append("    i32.const 0")
            body.append("    i32.le_s")
            body.append("    br_if $break")
            for child in node.children:
                self.compile_node(child, body)
            body.append("    local.get $__loop_i")
            body.append("    i32.const 1")
            body.append("    i32.sub")
            body.append("    local.set $__loop_i")
            body.append("    br $continue")
            body.append("  )")
            body.append(")")

        elif node.type == "function":
            name, params = node.value
            func_body = []
            old_locals = self.locals.copy()
            self.locals = {}

            for param in params:
                self.locals[param] = len(self.locals)

            for child in node.children:
                self.compile_node(child, func_body)

            params_wat = " ".join(f"(param ${p} i32)" for p in params)
            self.functions.append((name, params_wat, func_body))
            self.exports.append(name)
            self.locals = old_locals

        else:
            pass

    def compile(self, code):
        tree = parse(code)

        # compile @ship functions first
        main_body = []
        for node in tree.children:
            if node.type == "function":
                self.compile_node(node, [])
            else:
                self.compile_node(node, main_body)

        # assemble .wat
        lines = ["(module"]

        # imports — js console bridge
        lines += [
            '  (import "env" "print_int" (func $print_int (param i32)))',
            '  (import "env" "print_str" (func $print_str (param i32)))',
            '  (import "env" "print_float" (func $print_float (param f64)))',
        ]

        lines.append("  (memory 1)")
        lines.append('  (export "memory" (memory 0))')

        # string data section
        offset = 0
        for offset, value, length in self.data:
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            lines.append(f'  (data (i32.const {offset}) "{escaped}\\00")')

        # compiled @ship functions
        for name, params_wat, func_body in self.functions:
            lines.append(f"  (func ${name} {params_wat} (result i32)")
            for line in func_body:
                lines.append(f"    {line}")
            lines.append("  )")
            lines.append(f'  (export "{name}" (func ${name}))')

        # main entry (_start)
        lines.append("  (func $_start")
        local_decls = [l for l in main_body if l.startswith("(local")]
        instrs = [l for l in main_body if not l.startswith("(local")]
        for d in local_decls:
            lines.append(f"    {d}")
        for instr in instrs:
            lines.append(f"    {instr}")
        lines.append("  )")
        lines.append('  (export "_start" (func $_start))')

        lines.append(")")
        return "\n".join(lines)


def compile_to_yasm(code):
    return YASMCompiler().compile(code)
