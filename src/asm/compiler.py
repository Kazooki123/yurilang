# Main Assembly Transpiler
# .yuri -> .asm/.s
# x86-64 Architect (because it's based)

# TODO: Expansion of the code and keywords implemented.

from src.core.parser import parse


class YuriCompileError(Exception):
    pass


class Compiler:
    def __init__(self):
        self.data_section = []  # .data labels
        self.bss_section = []  # .bss labels (uninitialized vars)
        self.text_section = []  # .text instructions
        self.string_count = 0  # unique label counter for strings
        self.var_offsets = {}  # variable name → stack offset
        self.stack_offset = 0  # current rsp offset

    def new_string_label(self, value):
        """Store a string in .data and return its label."""
        label = f"str_{self.string_count}"
        self.string_count += 1
        # escape newlines, NASM needs explicit 10 for newline
        self.data_section.append(f'    {label} db "{value}", 10, 0')
        return label, len(value) + 1  # +1 for newline

    def emit(self, line):
        self.text_section.append(f"    {line}")

    def emit_label(self, label):
        self.text_section.append(f"{label}:")

    def allocate_var(self, name):
        """Allocate 8 bytes on the stack for a variable."""
        self.stack_offset += 8
        self.var_offsets[name] = self.stack_offset
        return self.stack_offset

    def var_addr(self, name):
        if name not in self.var_offsets:
            raise YuriCompileError(f"Undefined variable: {name}")
        offset = self.var_offsets[name]
        return f"[rbp - {offset}]"

    def compile_expr(self, expr):
        """Compile an expression, result ends up in rax."""
        if isinstance(expr, int):
            self.emit(f"mov rax, {expr}")
            return

        if isinstance(expr, str):
            expr = expr.strip()

            # integer literal
            if expr.lstrip("-").isdigit():
                self.emit(f"mov rax, {expr}")
                return

            if expr in self.var_offsets:
                self.emit(f"mov rax, {self.var_addr(expr)}")
                return

            if expr.startswith("@"):
                parts = expr.split()
                func = parts[0][1:]
                args = parts[1:]
                self.compile_builtin_call(func, args)
                return

            raise YuriCompileError(f"Cannot compile expression: {expr}")

    def compile_builtin_call(self, func, args):
        """Compiles built-in math calls like add, sub, mul, div."""
        if len(args) != 2:
            raise YuriCompileError(f"@{func} requires exactly 2 arguments")

        # evaluate left into rax, push it
        self.compile_expr(args[0])
        self.emit("push rax")

        # evaluate right into rax
        self.compile_expr(args[1])
        self.emit("mov rbx, rax")

        # pop left into rax
        self.emit("pop rax")

        if func == "add":
            self.emit("add rax, rbx")
        elif func == "sub":
            self.emit("sub rax, rbx")
        elif func == "mul":
            self.emit("imul rax, rbx")
        elif func == "div":
            self.emit("cqo")
            self.emit("idiv rbx")
        else:
            raise YuriCompileError(f"Unknown built-in: @{func}")

    def compile_node(self, node):
        # ENTRY
        if node.type in ("root", "entry"):
            for child in node.children:
                self.compile_node(child)

        # ASSIGN
        elif node.type == "assign":
            name, val = node.value
            self.compile_expr(val)  # result in rax

            if name not in self.var_offsets:
                self.allocate_var(name)

            self.emit(f"mov {self.var_addr(name)}, rax")

        # PRINT
        elif node.type == "print":
            for token in node.value:
                token = token.strip()

                # string literal
                if token.startswith('"') and token.endswith('"'):
                    value = token[1:-1]
                    label, length = self.new_string_label(value)
                    self.emit("mov rax, 1")  # sys_write
                    self.emit("mov rdi, 1")  # stdout
                    self.emit(f"mov rsi, {label}")  # string address
                    self.emit(f"mov rdx, {length}")  # length
                    self.emit("syscall")

                # variable — convert int to string via helper
                elif token in self.var_offsets:
                    self.emit(f"mov rdi, {self.var_addr(token)}")
                    self.emit("call print_int")  # helper we emit at end

                else:
                    raise YuriCompileError(f"@confess can't print: {token}")

        # LOOP
        elif node.type == "loop":
            count = node.value[-1]
            loop_label = f"loop_{len(self.text_section)}"
            end_label = f"end_{loop_label}"

            # store counter in rcx
            self.compile_expr(count)
            self.emit("mov rcx, rax")

            self.emit_label(loop_label)
            self.emit("cmp rcx, 0")
            self.emit(f"je {end_label}")
            self.emit("push rcx")  # preserve counter

            for child in node.children:
                self.compile_node(child)

            self.emit("pop rcx")  # restore counter
            self.emit("dec rcx")
            self.emit(f"jmp {loop_label}")
            self.emit_label(end_label)

        # IF
        elif node.type == "if":
            left, op, right = node.value[0], node.value[1], node.value[2]
            end_label = f"end_if_{len(self.text_section)}"
            else_label = f"else_{len(self.text_section)}"

            self.compile_expr(left)
            self.emit("push rax")
            self.compile_expr(right)
            self.emit("mov rbx, rax")
            self.emit("pop rax")
            self.emit("cmp rax, rbx")

            # separate if/else children
            if_body, else_body = [], []
            in_else = False
            for child in node.children:
                if child.type == "else":
                    in_else = True
                    continue
                (else_body if in_else else if_body).append(child)

            jump = {
                "==": "jne",
                "!=": "je",
                ">": "jle",
                "<": "jge",
                ">=": "jl",
                "<=": "jg",
            }
            self.emit(f"{jump[op]} {else_label if else_body else end_label}")

            for child in if_body:
                self.compile_node(child)

            if else_body:
                self.emit(f"jmp {end_label}")
                self.emit_label(else_label)
                for child in else_body:
                    self.compile_node(child)

            self.emit_label(end_label)

        else:
            pass

    def emit_print_int_helper(self):
        """Emit a print_int subroutine that prints rdi as decimal."""
        self.text_section.append("")
        self.text_section.append("print_int:")
        self.text_section.append("    mov rax, rdi")
        self.text_section.append("    mov rcx, 0")  # digit count
        self.text_section.append("    mov rbx, 10")  # base 10
        self.text_section.append("    lea rsi, [rsp - 24]")  # buffer on stack
        self.text_section.append("    mov byte [rsi + 20], 10")  # newline
        self.text_section.append("    mov rdi, 20")  # position
        self.text_section.append(".conv_loop:")
        self.text_section.append("    cqo")
        self.text_section.append("    idiv rbx")
        self.text_section.append("    add rdx, 48")  # to ASCII
        self.text_section.append("    dec rdi")
        self.text_section.append("    mov [rsi + rdi], dl")
        self.text_section.append("    inc rcx")
        self.text_section.append("    test rax, rax")
        self.text_section.append("    jnz .conv_loop")
        self.text_section.append("    ; sys_write")
        self.text_section.append("    lea rsi, [rsi + rdi]")
        self.text_section.append("    inc rcx")  # +1 for newline
        self.text_section.append("    mov rax, 1")
        self.text_section.append("    mov rdi, 1")
        self.text_section.append("    mov rdx, rcx")
        self.text_section.append("    syscall")
        self.text_section.append("    ret")

    def compile(self, code):
        tree = parse(code)

        # emit file header
        lines = [
            "global _start",
            "",
            "section .data",
        ]

        self.emit_label("_start")
        self.emit("push rbp")
        self.emit("mov rbp, rsp")
        self.emit("sub rsp, 256")

        for node in tree.children:
            self.compile_node(node)

        # Clean exit
        self.emit("mov rax, 60")  # sys_exit
        self.emit("xor rdi, rdi")  # exit code 0
        self.emit("syscall")

        # Assemble the final output
        lines += self.data_section
        lines += ["", "section .text", ""]
        lines += self.text_section
        self.emit_print_int_helper()
        lines += self.text_section[-(len(self.text_section)) :]

        return "\n".join(lines)


def compile_yuri(code):
    return Compiler().compile(code)
