const std = @import("std");

pub const Register = enum {
    A,
    B,
    C,
};

pub const Instruction = union(enum) {
    mov: struct { reg: Register, value: i32 },
    add: struct { dst: Register, src: Register },
    sub: struct { dst: Register, src: Register },
    prt: Register,
};

