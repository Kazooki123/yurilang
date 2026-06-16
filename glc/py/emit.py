# GLC Emitter

import struct

# Registers
RAX, RCX, RDX, RBX = 0, 1, 2, 3
RSP, RBP, RSI, RDI = 4, 5, 6, 7
R8, R9, R10, R11 = 8, 9, 10, 11
R12, R13, R14, R15 = 12, 13, 14, 15

class GlcError(Exception):
    pass


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
