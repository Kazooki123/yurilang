const std = @import("std");
const VM = @import("vm.zig").VM;
const parser = @import("parser.zig");

pub fn main() !void {
    var vm = VM.init();

    // Test 
    const program = [_][]const u8{
        "MOV A, 5",
        "MOV B, 10",
        "ADD A, B",
        "PRT A",
    };

    for (program) |line| {
        if (parser.parseLine(line)) |instr| {
            vm.exec(instr);
        }
    }
}

