# GLC — Girls Love to Compile 👩🏼‍❤️‍💋‍👩🏽
# YuriLang native compiler
# Produces Linux ELF x86-64 binaries directly


import struct
import os
from src.parser import parse


# Load the address
LOAD_ADDR = 0x400000  # standard Linux ELF load address
TEXT_OFF = 0x78  # ELF header && program header = 120 bytes


# x86-64 instruction emitter (ARM64 soon)
class Emitter:
    """
    Emits raw x86-64 machine code bytes.
    """

    def __init__(self):
        self.code = bytearray()
        self.labels = {}  # label -> offset
        self.patches = []  # (offset, label) to patch later
        self.data = bytearray()
        self.data_labels = {}  # label -> offset in data section
        self.rodata = bytearray()

    def pos(self):
        return len(self.code)

    def emit(self, *bytes_):
        for b in bytes_:
            if isinstance(b, int):
                self.code.append(b & 0xFF)
            elif isinstance(b, (bytes, bytearray)):
                self.code.extend(b)

    def emit_data(self, label, data):
        self.data_labels[label] = len(self.data)
        self.data.extend(data)
        return len(self.data) - len(data)

    # LABEL
    def label(self, name):
        self.labels[name] = self.pos()

    def patch_jumps(self):
        """Resolve all forward jump references."""
        for offset, label in self.patches:
            if label is None:
                continue
            if label.startswith("__rip_"):
                continue
            if label not in self.labels:
                raise GlcError(f"Undefined label: {label}")
            target = self.labels[label]
            rel32 = target - (offset + 4)
            struct.pack_into("<i", self.code, offset, rel32)

    # MOV
    def mov_reg_imm64(self, reg, imm):
        rex_b = 0x49 if reg >= 8 else 0x48
        reg_enc = reg & 7
        self.emit(rex_b, 0xB8 | reg_enc)
        self.emit(struct.pack("<q", imm))

    def mov_reg_imm32(self, reg, imm):
        if reg >= 8:
            self.emit(0x41, 0xB8 | (reg & 7))
        else:
            self.emit(0xB8 | reg)
        self.emit(struct.pack("<I", imm & 0xFFFFFFFF))

    def mov_reg_reg(self, dst, src):
        """mov dst, src"""
        rex = 0x4C if (dst >= 8 or src >= 8) else 0x48
        modrm = 0xC0 | ((src & 7) << 3) | (dst & 7)
        self.emit(rex, 0x89, modrm)

    def mov_mem_reg(self, base_reg, offset, src_reg):
        """mov [base_reg + offset], src_reg"""
        rex = 0x48
        modrm = 0x80 | ((src_reg & 7) << 3) | (base_reg & 7)
        self.emit(rex, 0x89, modrm)
        self.emit(struct.pack("<i", offset))

    def mov_reg_mem(self, dst_reg, base_reg, offset):
        """mov dst_reg, [base_reg + offset]"""
        rex = 0x48
        modrm = 0x80 | ((dst_reg & 7) << 3) | (base_reg & 7)
        self.emit(rex, 0x8B, modrm)
        self.emit(struct.pack("<i", offset))

    def lea_reg_rip(self, reg, label):
        """lea reg, [rip + label_offset] — for string addresses"""
        rex = 0x48
        modrm = 0x05 | ((reg & 7) << 3)
        self.emit(rex, 0x8D, modrm)
        self.patches.append((self.pos(), f"__rip_{label}"))
        self.emit(0, 0, 0, 0)

    def add_reg_reg(self, dst, src):
        """add dst, src"""
        rex = 0x48
        modrm = 0xC0 | ((src & 7) << 3) | (dst & 7)
        self.emit(rex, 0x01, modrm)

    def add_reg_imm32(self, reg, imm):
        """add reg, imm32"""
        modrm = 0xC0 | reg
        self.emit(0x48, 0x81, modrm)
        self.emit(struct.pack("<i", imm))

    def sub_reg_reg(self, dst, src):
        """sub dst, src"""
        rex = 0x48
        modrm = 0xC0 | ((src & 7) << 3) | (dst & 7)
        self.emit(rex, 0x29, modrm)

    def sub_reg_imm32(self, reg, imm):
        """sub reg, imm32"""
        modrm = 0xC0 | reg
        self.emit(0x48, 0x81, 0xE8 | (modrm & 7))
        self.emit(struct.pack("<i", imm))

    def imul_reg_reg(self, dst, src):
        """imul dst, src"""
        rex = 0x48
        modrm = 0xC0 | ((dst & 7) << 3) | (src & 7)
        self.emit(rex, 0x0F, 0xAF, modrm)

    def idiv_reg(self, reg):
        """idiv reg — divides rdx:rax by reg"""
        self.emit(0x48, 0xF7, 0xF8 | (reg & 7))

    def cqo(self):
        """cqo — sign extend rax into rdx:rax"""
        self.emit(0x48, 0x99)

    # STACK
    def push_reg(self, reg):
        if reg >= 8:
            self.emit(0x41, 0x50 | (reg & 7))
        else:
            self.emit(0x50 | reg)

    def pop_reg(self, reg):
        if reg >= 8:
            self.emit(0x41, 0x58 | (reg & 7))
        else:
            self.emit(0x58 | reg)

    def push_rbp(self):
        self.push_reg(RBP)

    def pop_rbp(self):
        self.pop_reg(RBP)

    def sub_rsp(self, n):
        """sub rsp, n — allocate stack space"""
        self.emit(0x48, 0x81, 0xEC)
        self.emit(struct.pack("<I", n))

    def add_rsp(self, n):
        """add rsp, n — deallocate stack space"""
        self.emit(0x48, 0x81, 0xC4)
        self.emit(struct.pack("<I", n))

    # CMP && JMP
    def cmp_reg_reg(self, a, b):
        """cmp a, b"""
        rex = 0x48
        modrm = 0xC0 | ((b & 7) << 3) | (a & 7)
        self.emit(rex, 0x39, modrm)

    def cmp_reg_imm32(self, reg, imm):
        """cmp reg, imm32"""
        self.emit(0x48, 0x81, 0xF8 | (reg & 7))
        self.emit(struct.pack("<i", imm))

    def jmp(self, label):
        """jmp label (rel32)"""
        self.emit(0xE9)
        self.patches.append((self.pos(), label))
        self.emit(0, 0, 0, 0)

    def je(self, label):
        """je label"""
        self.emit(0x0F, 0x84)
        self.patches.append((self.pos(), label))
        self.emit(0, 0, 0, 0)

    def jne(self, label):
        self.emit(0x0F, 0x85)
        self.patches.append((self.pos(), label))
        self.emit(0, 0, 0, 0)

    def jl(self, label):
        self.emit(0x0F, 0x8C)
        self.patches.append((self.pos(), label))
        self.emit(0, 0, 0, 0)

    def jg(self, label):
        self.emit(0x0F, 0x8F)
        self.patches.append((self.pos(), label))
        self.emit(0, 0, 0, 0)

    def jle(self, label):
        self.emit(0x0F, 0x8E)
        self.patches.append((self.pos(), label))
        self.emit(0, 0, 0, 0)

    def jge(self, label):
        self.emit(0x0F, 0x8D)
        self.patches.append((self.pos(), label))
        self.emit(0, 0, 0, 0)

    # FUNC CALLS
    def call(self, label):
        self.emit(0xE8)
        self.patches.append((self.pos(), label))
        self.emit(0, 0, 0, 0)

    def ret(self):
        self.emit(0xC3)

    # SYS CALLS
    def syscall(self):
        self.emit(0x0F, 0x05)

    def xor_reg_reg(self, a, b):
        rex = 0x48
        modrm = 0xC0 | ((b & 7) << 3) | (a & 7)
        self.emit(rex, 0x31, modrm)


# Registers
RAX, RCX, RDX, RBX = 0, 1, 2, 3
RSP, RBP, RSI, RDI = 4, 5, 6, 7
R8, R9, R10, R11 = 8, 9, 10, 11
R12, R13, R14, R15 = 12, 13, 14, 15

# Linux x86-64 syscall numbers
SYS_READ = 0
SYS_WRITE = 1
SYS_EXIT = 60


# ELF writer
def write_elf(code_bytes, data_bytes, output_path):
    load_addr = LOAD_ADDR
    text_offset = TEXT_OFF
    data_offset = text_offset + len(code_bytes)
    data_addr = load_addr + data_offset
    entry_point = load_addr + text_offset

    total_size = data_offset + len(data_bytes)

    # ELF header (64 bytes)
    elf_header = struct.pack(
        "<4sBBBBBxxxxxxx",
        b"\x7fELF",  # magic
        2,  # 64-bit
        1,  # little endian
        1,  # ELF version
        0,  # OS/ABI: System V
        0,  # ABI version
    )
    elf_header += struct.pack(
        "<HHIQQQIHHHHHH",
        2,  # e_type: ET_EXEC
        0x3E,  # e_machine: x86-64
        1,  # e_version
        entry_point,  # e_entry
        0x40,  # e_phoff: program header offset (right after ELF header)
        0,  # e_shoff: no section headers
        0,  # e_flags
        0x40,  # e_ehsize: 64 bytes
        0x38,  # e_phentsize: 56 bytes
        2,  # e_phnum: 2 program headers (text + data)
        0x40,  # e_shentsize
        0,  # e_shnum
        0,  # e_shstrndx
    )

    # Program header, text segment (56 bytes)
    ph_text = struct.pack(
        "<IIQQQQQQ",
        1,  # p_type: PT_LOAD
        5,  # p_flags: PF_R | PF_X (read + execute)
        0,  # p_offset: from start of file
        load_addr,  # p_vaddr
        load_addr,  # p_paddr
        text_offset + len(code_bytes),  # p_filesz
        text_offset + len(code_bytes),  # p_memsz
        0x200000,  # p_align: 2MB
    )

    # Program header, data segment
    ph_data = struct.pack(
        "<IIQQQQQQ",
        1,  # p_type: PT_LOAD
        6,  # p_flags: PF_R | PF_W (read + write)
        data_offset,  # p_offset
        data_addr,  # p_vaddr
        data_addr,  # p_paddr
        len(data_bytes),  # p_filesz
        len(data_bytes),  # p_memsz
        0x200000,  # p_align
    )

    with open(output_path, "wb") as f:
        f.write(elf_header)
        f.write(ph_text)
        f.write(ph_data)
        f.write(code_bytes)
        f.write(data_bytes)

    os.chmod(output_path, 0o755)
    print(f"GLC compiled: {output_path}")
    print(f" |  Code: {len(code_bytes)} bytes")
    print(f" |  Data: {len(data_bytes)} bytes")
    print(f" |  Total: {total_size} bytes")
    print(f" |  Entry: 0x{entry_point:x}")


# GLC Compiler
class GlcError(Exception):
    pass


class GLC:
    """
    Girls Love to Compile,
    YuriLang -> ELF x86-64 native binary :p
    """

    def __init__(self):
        self.emit = Emitter()
        self.variables = {}  # name → stack offset (rbp-relative)
        self.functions = {}  # name → label
        self.stack_size = 0  # current frame size
        self.label_count = 0  # unique label counter
        self.strings = {}  # string content → data label
        self.str_count = 0

    def new_label(self, prefix="L"):
        self.label_count += 1
        return f"{prefix}_{self.label_count}"

    # String data
    def intern_string(self, s):
        """Store string in data section, return label."""
        if s in self.strings:
            return self.strings[s]
        label = f"str_{self.str_count}"
        self.str_count += 1
        self.strings[s] = label
        return label

    # VAR management
    def alloc_var(self, name):
        """Allocate 8 bytes on stack for a variable."""
        self.stack_size += 8
        self.variables[name] = -self.stack_size
        return self.variables[name]

    def var_offset(self, name):
        if name not in self.variables:
            raise GlcError(
                f"\n💔 GLC — undefined variable '{name}'\n"
                f"  She wasn't @bond-ed before use.\n"
            )
        return self.variables[name]

    # EXPR compiler
    def compile_expr(self, expr):
        """
        Compile expression, results in RAX.
        """
        if isinstance(expr, int):
            self.emit.mov_reg_imm64(RAX, expr)
            return

        if isinstance(expr, str):
            expr = expr.strip()

            # integer literal
            if expr.lstrip("-").isdigit():
                self.emit.mov_reg_imm64(RAX, int(expr))
                return

            # boolean literals
            if expr == "love":
                self.emit.mov_reg_imm32(RAX, 1)
                return
            if expr == "ache":
                self.emit.xor_reg_reg(RAX, RAX)
                return

            # inline binary ("a plus b")
            for op, handler in [
                (" plus ", self._emit_add),
                (" minus ", self._emit_sub),
                (" times ", self._emit_mul),
                (" over ", self._emit_div),
            ]:
                if op in expr:
                    parts = expr.split(op, 1)
                    self.compile_expr(parts[0].strip())
                    self.emit.push_reg(RAX)
                    self.compile_expr(parts[1].strip())
                    self.emit.mov_reg_reg(RCX, RAX)
                    self.emit.pop_reg(RAX)
                    handler(RAX, RCX)
                    return

            # function call (e.g @add 5 3)
            if expr.startswith("@"):
                parts = expr.split()
                fname = parts[0][1:]
                args = parts[1:]
                self._emit_call(fname, args)
                return

            # variable lookup
            if expr in self.variables:
                offset = self.var_offset(expr)
                self.emit.mov_reg_mem(RAX, RBP, offset)
                return

            raise GlcError(f"Cannot compile expression: {repr(expr)}")

    def _emit_add(self, dst, src):
        self.emit.add_reg_reg(dst, src)

    def _emit_sub(self, dst, src):
        self.emit.sub_reg_reg(dst, src)

    def _emit_mul(self, dst, src):
        self.emit.imul_reg_reg(dst, src)

    def _emit_div(self, dst, src):
        self.emit.cqo()
        self.emit.idiv_reg(src)

    def _emit_call(self, fname, args):
        arg_regs = [RDI, RSI, RDX, RCX, R8, R9]
        for i, arg in enumerate(args[:6]):
            self.compile_expr(arg)
            if i > 0:
                self.emit.mov_reg_reg(arg_regs[i], RAX)
            else:
                self.emit.push_reg(RAX)

        if args:
            self.emit.pop_reg(RDI)

        self.emit.call(f"func_{fname}")

    def compile_node(self, node):
        if node.type in ("root", "entry"):
            for child in node.children:
                self.compile_node(child)

        # @bond (declares a var)
        elif node.type == "assign":
            name, val = node.value
            self.compile_expr(val)
            if name not in self.variables:
                self.alloc_var(name)
            offset = self.var_offset(name)
            self.emit.mov_mem_reg(RBP, offset, RAX)

        # @confess (print)
        elif node.type == "print":
            for token in node.value:
                token = token.strip()

                if token.startswith('"') and token.endswith('"'):
                    s = token[1:-1] + "\n"
                    label = self.intern_string(s)
                    self._emit_print_str(label, len(s))

                elif token in self.variables:
                    offset = self.var_offset(token)
                    self.emit.mov_reg_mem(RDI, RBP, offset)
                    self.emit.call("__print_int")

        # @jealous (if/else)
        elif node.type == "if":
            left, op, right = node.value[0], node.value[1], node.value[2]
            else_label = self.new_label("else")
            end_label = self.new_label("endif")

            self.compile_expr(left)
            self.emit.push_reg(RAX)
            self.compile_expr(right)
            self.emit.mov_reg_reg(RCX, RAX)
            self.emit.pop_reg(RAX)
            self.emit.cmp_reg_reg(RAX, RCX)

            if_body, else_body = [], []
            in_else = False
            for child in node.children:
                if child.type == "else":
                    in_else = True
                    continue
                (else_body if in_else else if_body).append(child)

            jmp_map = {
                "==": self.emit.jne,
                "!=": self.emit.je,
                ">": self.emit.jle,
                "<": self.emit.jge,
                ">=": self.emit.jl,
                "<=": self.emit.jg,
            }
            jmp_map.get(op, self.emit.jne)(else_label if else_body else end_label)

            for child in if_body:
                self.compile_node(child)

            if else_body:
                self.emit.jmp(end_label)
                self.emit.label(else_label)
                for child in else_body:
                    self.compile_node(child)

            self.emit.label(end_label)

        # @cling (basic loop)
        elif node.type == "loop":
            count_expr = node.value[-1]
            loop_label = self.new_label("loop")
            end_label = self.new_label("endloop")
            counter = f"__loop_{self.label_count}"

            self.compile_expr(count_expr)
            self.alloc_var(counter)
            self.emit.mov_mem_reg(RBP, self.var_offset(counter), RAX)

            self.emit.label(loop_label)
            self.emit.mov_reg_mem(RAX, RBP, self.var_offset(counter))
            self.emit.cmp_reg_imm32(RAX, 0)
            self.emit.jle(end_label)

            for child in node.children:
                self.compile_node(child)

            self.emit.mov_reg_mem(RAX, RBP, self.var_offset(counter))
            self.emit.sub_reg_imm32(RAX, 1)
            self.emit.mov_mem_reg(RBP, self.var_offset(counter), RAX)
            self.emit.jmp(loop_label)
            self.emit.label(end_label)

        # @fate (while loops)
        elif node.type == "while":
            left, op, right = node.value[0], node.value[1], node.value[2]
            loop_label = self.new_label("while")
            end_label = self.new_label("endwhile")

            self.emit.label(loop_label)
            self.compile_expr(left)
            self.emit.push_reg(RAX)
            self.compile_expr(right)
            self.emit.mov_reg_reg(RCX, RAX)
            self.emit.pop_reg(RAX)
            self.emit.cmp_reg_reg(RAX, RCX)

            jmp_map = {
                "==": self.emit.jne,
                "!=": self.emit.je,
                ">": self.emit.jle,
                "<": self.emit.jge,
                ">=": self.emit.jl,
                "<=": self.emit.jg,
            }
            jmp_map.get(op, self.emit.jne)(end_label)

            for child in node.children:
                self.compile_node(child)

            self.emit.jmp(loop_label)
            self.emit.label(end_label)

        # @ship (functions)
        elif node.type == "function":
            name, params = node.value
            end_label = self.new_label(f"end_{name}")

            self.emit.jmp(end_label)
            self.emit.label(f"func_{name}")

            self.emit.push_rbp()
            self.emit.mov_reg_reg(RBP, RSP)

            old_vars = self.variables.copy()
            old_stack = self.stack_size
            self.variables = {}
            self.stack_size = 0

            arg_regs = [RDI, RSI, RDX, RCX, R8, R9]
            for i, param in enumerate(params[:6]):
                self.alloc_var(param)
                self.emit.mov_mem_reg(RBP, self.var_offset(param), arg_regs[i])

            self.emit.sub_rsp(256)

            for child in node.children:
                self.compile_node(child)

            self.emit.add_rsp(256)
            self.emit.pop_rbp()
            self.emit.ret()
            self.emit.label(end_label)

            self.variables = old_vars
            self.stack_size = old_stack
            self.functions[name] = f"func_{name}"

        # @promise (return)
        elif node.type == "return":
            val = node.value
            if isinstance(val, list):
                val = " ".join(val)
            self.compile_expr(val)
            self.emit.add_rsp(256)
            self.emit.pop_rbp()
            self.emit.ret()

        else:
            pass

    # Print/Write headers
    def _emit_print_str(self, label, length):
        self.emit.mov_reg_imm32(RAX, SYS_WRITE)
        self.emit.mov_reg_imm32(RDI, 1)
        # rsi = address of string
        self.emit.emit(0x48, 0x8D, 0x35)
        # lea rsi, [rip+?]
        self.emit.patches.append((self.emit.pos(), f"__data_{label}"))
        self.emit.emit(0, 0, 0, 0)
        self.emit.mov_reg_imm32(RDX, length)
        self.emit.syscall()

    def _emit_print_int_helper(self):
        self.emit.label("__print_int")
        self.emit.push_rbp()
        self.emit.mov_reg_reg(RBP, RSP)
        self.emit.sub_rsp(32)

        # buffer on stack [rbp-24] to [rbp-4]
        # writes digits right to left
        # rdi = number to print

        # store newline at end of buffer
        self.emit.emit(
            0xC6,
            0x45,
            0xE8,
            0x0A,  # mov byte [rbp-24], 10 (newline)
        )

        # rax = abs(rdi)
        self.emit.mov_reg_reg(RAX, RDI)
        # rcx = buffer position
        self.emit.mov_reg_imm32(RCX, 1)
        self.emit.mov_reg_imm32(RDX, 10)

        # conversion loop
        self.emit.label("__print_int_loop")
        self.emit.cqo()
        self.emit.idiv_reg(RDX)
        self.emit.emit(0x80, 0xC2, 0x30)

        # store digit: mov [rbp + rcx*1 - 25], dl
        self.emit.emit(
            0x88,
            0x54,
            0x0D,
            0xE7,  # mov [rbp+rcx-25], dl
        )
        self.emit.emit(0x48, 0xFF, 0xC1)  # inc rcx
        self.emit.emit(0x48, 0x85, 0xC0)  # test rax, rax
        self.emit.jne("__print_int_loop")

        self.emit.mov_reg_imm32(RAX, SYS_WRITE)
        self.emit.mov_reg_imm32(RDI, 1)

        self.emit.emit(0x48, 0x8D, 0x74, 0x0D, 0xE7)  # lea rsi, [rbp+rcx-25]
        self.emit.mov_reg_reg(RDX, RCX)
        self.emit.syscall()

        self.emit.add_rsp(32)
        self.emit.pop_rbp()
        self.emit.ret()

    # MAIN compilation entry_oint
    def compile(self, source, output_path):
        """
        Full compilation pipeline:
        YuriLang source → ELF binary
        """
        print("🌸 GLC — Girls Love to Compile")
        print(f"   Compiling {output_path}...")

        tree = parse(source)

        self.emit.label("_start")
        self.emit.push_rbp()
        self.emit.mov_reg_reg(RBP, RSP)
        self.emit.sub_rsp(512)

        # compiles all nodes
        for node in tree.children:
            self.compile_node(node)

        self.emit.mov_reg_imm32(RAX, SYS_EXIT)
        self.emit.xor_reg_reg(RDI, RDI)
        self.emit.syscall()

        self._emit_print_int_helper()

        # finalize data section
        data = bytearray()
        data_map = {}

        for s, label in self.strings.items():
            data_map[label] = len(data)
            data.extend(s.encode("utf-8"))

        code_len = len(self.emit.code)
        text_start = LOAD_ADDR + TEXT_OFF

        for i, (offset, label) in enumerate(self.emit.patches):
            if label.startswith("__data_"):
                str_label = label[7:]
                if str_label in data_map:
                    data_section_addr = LOAD_ADDR + TEXT_OFF + code_len
                    str_addr = data_section_addr + data_map[str_label]
                    rip_after_patch = text_start + offset + 4
                    rel32 = str_addr - rip_after_patch
                    struct.pack_into("<i", self.emit.code, offset, rel32)
                    self.emit.patches[i] = (offset, None)

        # patch remaining jumps/calls
        self.emit.patch_jumps()

        # write ELF
        write_elf(bytes(self.emit.code), bytes(data), output_path)


def glc_compile(source, output_path):
    GLC().compile(source, output_path)
