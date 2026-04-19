const std = @import("std");
const Instruction = @import("instruction.zig").Instruction;
const Register = @import("instruction.zig").Register;

pub const VM = struct {
    regs: [9]i32,
    flags: struct { eq: bool, lt: bool },

    pub fn init() VM {
        return VM{ 
            .regs = .{0, 0, 0, 0, 0, 0, 0, 0, 0},
            .flags = .{ .eq = false, .lt = false },
        };
    }

    fn getIndex(reg: Register) usize {
        return switch (reg) {
            .A => 0,
            .B => 1,
            .C => 2,
            .T0 => 3,
            .T1 => 4,
            .T2 => 5,
            .S0 => 6, 
            .S1 => 7,
            .R => 8,
        };
    }

    pub fn run(self: *VM, program: []const Instruction) void {
        var pc: usize = 0;
        while (pc < program.len) {
            const instr = program[pc];
            switch (instr) {
                .mov => |m| {
                    self.regs[getIndex(m.reg)] = m.value;
                    pc += 1;
                },
                .add => |a| {
                    self.regs[getIndex(a.dst)] += self.regs[getIndex(a.src)];
                    pc += 1;
                },
                .sub => |s| {
                    self.regs[getIndex(s.dst)] -= self.regs[getIndex(s.src)];
                    pc += 1;
                },
                .mul => |ml| {
                    self.regs[getIndex(ml.dst)] *= self.regs[getIndex(ml.src)];
                    pc += 1;
                },
                .div => |d| {
                    const divisor = self.regs[getIndex(d.src)];
                    if (divisor == 0) {
                        std.debug.print("Error: division by zero!\n", .{});
                        return;
                    }
                    self.regs[getIndex(d.dst)] = @divTrunc(
                        self.regs[getIndex(d.dst)],
                        divisor,
                    );
                    pc += 1;
                },
                .cmp => |c| {
                    const a = self.regs[getIndex(c.a)];
                    const b = self.regs[getIndex(c.b)];
                    self.flags.eq = a == b;
                    self.flags.lt = a < b;
                    pc += 1;
                },
                .mod => |m| {
                    const divisor = self.regs[getIndex(m.src)];
                    if (divisor == 0) {
                        std.debug.print("Error: modulo by zero!\n", .{});
                        return;
                    }
                    self.regs[getIndex(m.dst)] = @mod(
                        self.regs[getIndex(m.dst)],
                        divisor,
                    );
                    pc += 1;
                },
                .neg => |r| {
                    self.regs[getIndex(r)] = -self.regs[getIndex(r)];
                    pc += 1;
                },
                .band => |a| {
                    self.regs[getIndex(a.dst)] &= self.regs[getIndex(a.src)];
                    pc += 1;
                },
                .bor=> |o| {
                    self.regs[getIndex(o.dst)] |= self.regs[getIndex(o.src)];
                    pc += 1;
                },
                .xor => |x| {
                    self.regs[getIndex(x.dst)] ^= self.regs[getIndex(x.src)];
                    pc += 1;
                },
                .prt => |r| {
                    std.debug.print("{}\n", .{self.regs[getIndex(r)]});
                    pc += 1;
                },
                .jmp => |target| {
                    pc = target;
                },
                .jeq => |target| {
                    if (self.flags.eq) { pc = target; } else { pc += 1; }
                },
                .jne => |target| {
                    if (!self.flags.eq) { pc = target; } else { pc += 1; }
                },
                .jlt => |target| {
                    if (self.flags.lt) { pc = target; } else { pc += 1; }
                },
                .jgt => |target| {
                    if (!self.flags.lt) { pc = target; } else { pc += 1; }
                },
                .hlt => {
                    return;
                },
            }
        }
    }
};

