// C-ABI surface for libLASM.
//
// main.zig is untouched and still builds the `lasm` executable.
// This file is a second root: points a shared-library build target at it
// (see notes at the bottom) to get a Windows DLL / .so / .dylib that
// exposes the same parser + VM to any C-compatible caller.
//
// Everything below uses plain pointers, lengths, and opaque handles
// instead of Zig slices/optionals/error unions/tagged unions, since those
// aren't part of the C ABI. `Instruction` programs are handed back as
// opaque blobs: callers pass the pointer+len back into lasm_vm_run /
// lasm_free_program rather than poking at the bytes themselves.

const std = @import("std");
const VM = @import("vm.zig").VM;
const parser = @import("parser.zig");
const Instruction = @import("instruction.zig").Instruction;

// One allocator backs every allocation made through this API. page_allocator
// has no per-instance state to thread across the DLL boundary, which keeps
// create/destroy pairs simple for callers in C, C#, Python (ctypes), etc.
const allocator = std.heap.page_allocator;

// Lifecycle
/// Allocate and initialize a VM. Returns null on allocation failure.
/// Caller owns the pointer and must release it with lasm_vm_destroy.
export fn lasm_vm_create() ?*VM {
    const vm = allocator.create(VM) catch return null;
    vm.* = VM.init();
    return vm;
}

/// Free a VM created with lasm_vm_create. Safe to call with null.
export fn lasm_vm_destroy(vm: ?*VM) void {
    if (vm) |v| allocator.destroy(v);
}

/// Reset an existing VM to its initial state (regs zeroed, flags cleared)
/// without reallocating. Handy for running several programs back-to-back.
export fn lasm_vm_reset(vm: ?*VM) void {
    const v = vm orelse return;
    v.* = VM.init();
}

// Parsing 
/// Parse LASM source into a program. `source_ptr`/`source_len` need not be
/// null-terminated. On success, returns a pointer to the instruction array
/// and writes its length to `out_len`. On failure (e.g. OOM) returns null
/// and sets out_len to 0. The returned memory is owned by the caller and
/// must be released with lasm_free_program.
export fn lasm_parse(source_ptr: [*]const u8, source_len: usize, out_len: *usize) ?[*]Instruction {
    const source = source_ptr[0..source_len];
    const program = parser.parseProgram(allocator, source) catch {
        out_len.* = 0;
        return null;
    };
    out_len.* = program.len;
    return program.ptr;
}

export fn lasm_free_program(ptr: ?[*]Instruction, len: usize) void {
    if (ptr) |p| allocator.free(p[0..len]);
}

// Execution
/// Run `len` instructions starting at `ptr` on `vm`.
export fn lasm_vm_run(vm: ?*VM, ptr: ?[*]const Instruction, len: usize) void {
    const v = vm orelse return;
    const p = ptr orelse return;
    v.run(p[0..len]);
}

/// Convenience one-shot: parse `source` and run it on `vm` immediately,
/// freeing the intermediate program automatically. Returns false on
/// parse failure (vm state is left unchanged in that case).
export fn lasm_run_source(vm: ?*VM, source_ptr: [*]const u8, source_len: usize) bool {
    const v = vm orelse return false;
    const source = source_ptr[0..source_len];
    const program = parser.parseProgram(allocator, source) catch return false;
    defer allocator.free(program);
    v.run(program);
    return true;
}

// Register / flag access

export fn lasm_reg_count() usize {
    const v: VM = undefined;
    return v.regs.len;
}

/// Read register `index` (0 .. lasm_reg_count()-1). Out-of-range returns 0.
/// Index order matches the Register enum's declaration order in
/// instruction.zig (A, B, C, T0, T1, T2, S0, S1, R).
export fn lasm_vm_get_reg(vm: ?*const VM, index: usize) i32 {
    const v = vm orelse return 0;
    if (index >= v.regs.len) return 0;
    return v.regs[index];
}

/// Write register `index` directly, bypassing the parser/VM logic.
/// Useful for seeding inputs before calling lasm_vm_run.
export fn lasm_vm_set_reg(vm: ?*VM, index: usize, value: i32) void {
    const v = vm orelse return;
    if (index >= v.regs.len) return;
    v.regs[index] = value;
}

/// Read the comparison flags set by the last CMP. Either out-pointer may
/// be null if you only care about one of them.
export fn lasm_vm_get_flags(vm: ?*const VM, eq_out: ?*bool, lt_out: ?*bool) void {
    const v = vm orelse return;
    if (eq_out) |p| p.* = v.flags.eq;
    if (lt_out) |p| p.* = v.flags.lt;
}
