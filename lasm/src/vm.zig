const std = @import("std");
const Instruction = @import("instruction.zig").Instruction;
const Register = @import("instruction.zig").Register;

pub const VM = struct {
    regs: [3]i32,

    pub fn init() VM {
        return VM{ .regs = .{0, 0, 0} };
    }

    fn getIndex(reg: Register) usize {
        return switch (reg) {
            .A => 0,
            .B => 1,
            .C => 2,
        };
    }

    pub fn exec(self: *VM, instr: Instruction) void {
        switch (instr) {
            .mov => |m| {
                self.regs[getIndex(m.reg)] = m.value;
            },
            .add => |a| {
                self.regs[getIndex(a.dst)] += self.regs[getIndex(a.src)];
            },
            .sub => |s| {
                self.regs[getIndex(s.dst)] -= self.regs[getIndex(s.src)];
            },
            .prt => |r| {
                std.debug.print("{}\n", .{self.regs[getIndex(r)]});
            },
        }
    }
};

