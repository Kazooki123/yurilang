const std = @import("std");
const Instruction = @import("instruction.zig").Instruction;
const Register = @import("instruction.zig").Register;

fn parseRegister(token: []const u8) Register {
    return switch (token[0]) {
        'A' => .A,
        'B' => .B,
        'C' => .C,
        else => unreachable,
    };
}

pub fn parseLine(line: []const u8) ?Instruction {
    var parts = std.mem.tokenizeAny(u8, line, " ,\n");

    const op = parts.next() orelse return null;

    if (std.mem.eql(u8, op, "MOV")) {
        const reg = parseRegister(parts.next().?);
        const val_str = parts.next().?;
        const value = std.fmt.parseInt(i32, val_str, 10) catch 0;

        return Instruction{ .mov = .{ .reg = reg, .value = value } };
    }

    if (std.mem.eql(u8, op, "ADD")) {
        const dst = parseRegister(parts.next().?);
        const src = parseRegister(parts.next().?);

        return Instruction{ .add = .{ .dst = dst, .src = src } };
    }

    if (std.mem.eql(u8, op, "SUB")) {
        const dst = parseRegister(parts.next().?);
        const src = parseRegister(parts.next().?);

        return Instruction{ .sub = .{ .dst = dst, .src = src } };
    }

    if (std.mem.eql(u8, op, "PRT")) {
        const reg = parseRegister(parts.next().?);
        return Instruction{ .prt = reg };
    }

    return null;
}
