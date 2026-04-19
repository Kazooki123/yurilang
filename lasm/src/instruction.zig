const std = @import("std");

pub const Register = enum {
    A, B, C,
    T0, T1, T2,
    S0, S1,
    R, // Return
};

pub const Instruction = union(enum) {
    mov: struct { reg: Register, value: i32 },
    add: struct { dst: Register, src: Register },
    sub: struct { dst: Register, src: Register },
    mul: struct { dst: Register, src: Register },
    div: struct { dst: Register, src: Register },
    mod: struct { dst: Register, src: Register },
    band: struct { dst: Register, src: Register }, // bitwise 'and'
    bor: struct { dst: Register, src: Register }, // bitwise 'or'
    xor: struct { dst: Register, src: Register },
    cmp: struct { a: Register, b: Register },
    prt: Register,
    neg: Register,
    jmp: usize, // jump
    jeq: usize, // if equal
    jne: usize, // if not equal
    jlt: usize, // if less than
    jgt: usize, // if greater than
    hlt,
};
