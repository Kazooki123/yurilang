/// LASM - Lesbian Assembly Interpreter
/// A RISC-V based language
/// AUTHOR: Kazooki123 <mgamerdinge146@gmail.com>
/// LICENSE: Apache 2.0

const std = @import("std");
const VM = @import("vm.zig").VM;
const parser = @import("parser.zig");

pub fn main() !void {
    var gpa = std.heap.DebugAllocator(.{}){};
    const allocator = gpa.allocator();

    const args = try std.process.args(allocator);
    defer std.process.argsFree(allocator, args);

    if (args.len < 2) {
        std.debug.print("Usage: lasm <file.lasm>\n", .{});
        return;
    }

    const path = args[1];
    const file = try std.fs.cwd().openFile(path, .{});
    defer file.close();

    const content = try file.readToEndAlloc(allocator, 1024 * 10);
    defer allocator.free(content);

    const program = try parser.parseProgram(allocator, content);
    defer allocator.free(program);
    
    var vm = VM.init();
    vm.run(program);
}
