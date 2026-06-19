/// LASM Compiler
/// This simple compiler generates LLVM-IR and compiles it to machine code
/// that can be executed
/// Happy Pride lads :3

const std = @import("std");
const Instruction = @import("instruction.zig").Instruction;
const Register = @import("instruction.zig").Register;


