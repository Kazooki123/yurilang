const std = @import("std");
const Instruction = @import("instruction.zig").Instruction;
const Register = @import("instruction.zig").Register;

fn parseRegister(token: []const u8) Register {
    if (std.mem.eql(u8, token, "A")) return .A;
    if (std.mem.eql(u8, token, "B")) return .B;
    if (std.mem.eql(u8, token, "C")) return .C;
    if (std.mem.eql(u8, token, "T0")) return .T0;
    if (std.mem.eql(u8, token, "T1")) return .T1;
    if (std.mem.eql(u8, token, "T2")) return .T2;
    if (std.mem.eql(u8, token, "S0")) return .S0;
    if (std.mem.eql(u8, token, "S1")) return .S1;
    if (std.mem.eql(u8, token, "R")) return .R;
    unreachable;
}

// via ';'
fn stripComments(line: []const u8) []const u8 {
    if (std.mem.indexOfScalar(u8, line, ';')) |pos| {
        return std.mem.trim(u8, line[0..pos], " \t\r\n");
    }
    return std.mem.trim(u8, line, " \t\r\n");
}

fn isLabel(line: []const u8) bool {
    return line.len > 1 and line[line.len - 1] == ':';
}

pub fn parseProgram(
    allocator: std.mem.Allocator,
    source: []const u8,
) ![]Instruction {
    var instructions = std.ArrayList(Instruction).init(allocator);
    var labels = std.StringHashMap(usize).init(allocator);
    defer labels.deinit();
    
    var instrCount: usize = 0;
    var lines = std.mem.tokenizeAny(u8, source, "\n");
    while (lines.next()) |raw| {
        const line = stripComments(raw);
        if (line.len == 0) continue;
        if (isLabel(line)) {
            const name = line[0 .. line.len - 1];
            try labels.put(name, instrCount);
        } else {
            instrCount += 1;
        }
    }
    
    lines = std.mem.tokenizeAny(u8, source, "\n");
    while (lines.next()) |raw| {
        const line = stripComments(raw);
        if (line.len == 0) continue;
        if (isLabel(line)) continue;
        
        var parts = std.mem.tokenizeAny(u8, line, " ,\t");
        const op = parts.next() orelse continue;
        
        if (std.mem.eql(u8, op, "MOV")) {
            const reg = parseRegister(parts.next().?);
            const value = std.fmt.parseInt(i32, parts.next().?, 10) catch 0;
            try instructions.append(.{ .mov = .{ .reg = reg, .value = value } });
        } else if (std.mem.eql(u8, op, "ADD")) {
            const dst = parseRegister(parts.next().?);
            const src = parseRegister(parts.next().?);
            try instructions.append(.{ .add = .{ .dst = dst, .src = src } });
        } else if (std.mem.eql(u8, op, "SUB")) {
            const dst = parseRegister(parts.next().?);
            const src = parseRegister(parts.next().?);
            try instructions.append(.{ .sub = .{ .dst = dst, .src = src } });
        } else if (std.mem.eql(u8, op, "MUL")) {
            const dst = parseRegister(parts.next().?);
            const src = parseRegister(parts.next().?);
            try instructions.append(.{ .mul = .{ .dst = dst, .src = src } });
        } else if (std.mem.eql(u8, op, "DIV")) {
            const dst = parseRegister(parts.next().?);
            const src = parseRegister(parts.next().?);
            try instructions.append(.{ .div = .{ .dst = dst, .src = src } });
        } else if (std.mem.eql(u8, op, "MOD")) {
            const dst = parseRegister(parts.next().?);
            const src = parseRegister(parts.next().?);
            try instructions.append(.{ .mod = .{ .dst = dst, .src = src } });
        } else if (std.mem.eql(u8, op, "NEG")) {
            const reg = parseRegister(parts.next().?);
            try instructions.append(.{ .neg = reg });
        } else if (std.mem.eql(u8, op, "AND")) {
            const dst = parseRegister(parts.next().?);
            const src = parseRegister(parts.next().?);
            try instructions.append(.{ .band = .{ .dst = dst, .src = src } });
        } else if (std.mem.eql(u8, op, "OR")) {
            const dst = parseRegister(parts.next().?);
            const src = parseRegister(parts.next().?);
            try instructions.append(.{ .bor = .{ .dst = dst, .src = src } });
        } else if (std.mem.eql(u8, op, "XOR")) {
            const dst = parseRegister(parts.next().?);
            const src = parseRegister(parts.next().?);
            try instructions.append(.{ .xor = .{ .dst = dst, .src = src } });
        } else if (std.mem.eql(u8, op, "CMP")) {
            const a = parseRegister(parts.next().?);
            const b = parseRegister(parts.next().?);
            try instructions.append(.{ .cmp = .{ .a = a, .b = b } });
        } else if (std.mem.eql(u8, op, "PRT")) {
            const reg = parseRegister(parts.next().?);
            try instructions.append(.{ .prt = reg });
        } else if (std.mem.eql(u8, op, "JMP")) {
            const label = parts.next().?;
            const target = labels.get(label) orelse {
                std.debug.print("Unknown label: {s}\n", .{label});
                continue;
            };
            try instructions.append(.{ .jmp = target });
        } else if (std.mem.eql(u8, op, "JEQ")) {
            const label = parts.next().?;
            const target = labels.get(label) orelse {
                std.debug.print("Unknown label: {s}\n", .{label});
                continue;
            };
            try instructions.append(.{ .jeq = target });
        } else if (std.mem.eql(u8, op, "JNE")) {
            const label = parts.next().?;
            const target = labels.get(label) orelse {
                std.debug.print("Unknown label: {s}\n", .{label});
                continue;
            };
            try instructions.append(.{ .jne = target });
        } else if (std.mem.eql(u8, op, "JLT")) {
            const label = parts.next().?;
            const target = labels.get(label) orelse {
                std.debug.print("Unknown label: {s}\n", .{label});
                continue;
            };
            try instructions.append(.{ .jlt = target });
        } else if (std.mem.eql(u8, op, "JGT")) {
            const label = parts.next().?;
            const target = labels.get(label) orelse {
                std.debug.print("Unknown label: {s}\n", .{label});
                continue;
            };
            try instructions.append(.{ .jgt = target });
        } else if (std.mem.eql(u8, op, "HLT")) {
            try instructions.append(.hlt);
        }
    }
    
    return instructions.toOwnedSlice();
}
