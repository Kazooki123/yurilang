import sys
from src.interpreter import run
from src.repl import repl
from src.asm.compiler import compile_yuri
from src.asm.wasm import compile_to_yasm
from src.vm.compiler import compile_to_bytecode
from src.vm.bytecode import YuriVM
from src.vm.serializer import save_yuric, load_yuric
from glc.py.compile import glc_compile
from src.llvm.llvm import llvm_compile
from src.hvm.hvm import transpile_hvm
from src.misc.flags import random_flag
from src.misc.verifyiso import verify_iso
from install import uninstall

def main():
    args = sys.argv[1:]

    if "--version" in args or "-v" in args:
        print(f"""
    YuriLang v1.7.0
    Yuring Complete since 2026 🧡🤍🩷
    Python {sys.version.split()[0]}
    GPL-3.0 License
""")
        return

    if "--help" in args or "-h" in args:
        print("""
    Usage: yuri [file] [options]

    yuri program.yuri             interpret
    --bytecode                    Compile to .yuric
    --vm                          Run bytecode
    --asm                         Compile to x86-64 ASM
    --wasm                        Compile to WebAssembly
    --crush                       Type annotation flag
    --itmye                       Runs the ITMYE checker 
    --glc                         Compiles it to binary
    --llvm                        Compile to LLVM IR (.ll) 
    -llvm-obj                     Compile to a LLVM object file (.o)
    yuri                          Launch REPL

    MISC:
    --flag                        Prints flags from LGBTQ+ to real life flags.
    [.iso] --verify               Verifies an ISO or CHD format file.

    Options:
    -v --version    show version
    -h --help       show this message
    --user          install to user directory
    --uninstall     remove YuriLang

    Yuring Complete since 2026 🍰
    """)
        return
    
    if "--uninstall" in args:
        uninstall()
        return

    if "--crush" in args:
        from src.etc.crush import crush_summary

        filename = next(arg for arg in args if arg.endswith(".yuri"))

        with open(filename) as f:
            run(f.read())
        print("\n🌸 YuriLang Type Hints (@crush)\n")
        print(crush_summary())
        return

    if "--flag" in args:
        random_flag()
        return

    if "--verify" in args:
        idx = args.index("--verify")
        if idx + 1 >= len(args):
            print("Usage: yuri --verify <file.iso> [expected_hash]")
            return
        path     = args[idx + 1]
        expected = args[idx + 1] if len(args) > idx + 2 else None
        verify_iso(path, expected) 
        return

    if "--itmye" in args:
        try:
            filename = next(arg for arg in args if arg.endswith(".yuri"))
            with open(filename) as f:
                code = f.read()

            run(code)

            from src.interpreter import (
                variables,
                awakened,
                owned,
                shared_ptrs,
                glances,
                reaches,
                functions,
            )
            from src.etc.itmye_check import run_itmye

            run_itmye(
                variables, awakened, owned, shared_ptrs, glances, reaches, functions
            )

        except StopIteration:
            print("No .yuri file provided.")
            return

    if "--asm" in args:
        try:
            filename = next(arg for arg in args if arg.endswith(".yuri"))
            with open(filename) as f:
                code = f.read()
            asm = compile_yuri(code)
            out = filename.replace(".yuri", ".asm")
            with open(out, "w") as f:
                f.write(asm)
            print(f"Compiled to {out}")
            print("Run with:")
            print(
                f"  nasm -f elf64 {out} -o program.o && ld program.o -o program && ./program"
            )
        except StopIteration:
            print("No .yuri file provided.")
        except FileNotFoundError:
            print("File not found.")
        return

    if "--glc" in args:
        try:
            filename = next(arg for arg in args if arg.endswith(".yuri"))
            with open(filename) as f:
                code = f.read()
            out = filename.replace(".yuri", "")
            glc_compile(code, out)
            print(f"Run with: ./{out}")
        except StopIteration:
            print("No .yuri file provided.")
        return

    if "--llvm" in args:
        try:
            filename = next(arg for arg in args if arg.endswith(".yuri"))
            with open(filename) as f:
                code = f.read()

            # .ll IR file
            out_ll = filename.replace(".yuri", ".ll")
            llvm_compile(code, out_ll, mode="ir")

        except StopIteration:
            print("No .yuri file provided.")
        return

    if "--llvm-obj" in args:
        try:
            filename = next(arg for arg in args if arg.endswith(".yuri"))
            with open(filename) as f:
                code = f.read()

            # native .o object file
            out_obj = filename.replace(".yuri", ".o")
            llvm_compile(code, out_obj, mode="object")
            print(f"Link with: gcc {out_obj} -o program")

        except StopIteration:
            print("No .yuri file provided.")
        return
        
    if "--hvm" in args:
        try:
            filename = next(arg for arg in args if arg.endswith(".yuri"))
            with open(filename) as f:
                code = f.read()

            hvm = transpile_hvm(code)
            out = filename.replace(".yuri", ".hvm")
            with open(out, "w") as f:
                f.write(hvm)
                
        except StopIteration as e:
            print(f"No .yuri file provided: {e}")
        except FileNotFoundError as e2:
            print(f"File not found! {e2}\n")
        return

    if "--bytecode" in args:
        try:
            filename = next(arg for arg in args if arg.endswith(".yuri"))
            with open(filename) as f:
                code = f.read()
            instructions = compile_to_bytecode(code)
            out = filename.replace(".yuri", ".yuric")
            save_yuric(instructions, out)
        except StopIteration:
            print("No .yuri file provided.")
        except FileNotFoundError:
            print("File not found.")
        return

    if "--vm" in args:
        try:
            filename = next(arg for arg in args if arg.endswith(".yuric"))
            instructions = load_yuric(filename)
            vm = YuriVM()
            vm.run(instructions)
        except StopIteration:
            print("No .yuric file provided.")
        except FileNotFoundError:
            print("File not found.")
        return

    if "--wasm" in args:
        try:
            filename = next(arg for arg in args if arg.endswith(".yuri"))
            with open(filename) as f:
                code = f.read()
            wat = compile_to_yasm(code)
            out = filename.replace(".yuri", ".wat")
            with open(out, "w") as f:
                f.write(wat)
            print(f"YASM compiled to {out}")
            print(f"Convert with: wat2wasm {out} -o {out.replace('.wat', '.wasm')}")
            print(f"Run with: wasmtime {out.replace('.wat', '.wasm')}")
        except StopIteration:
            print("No .yuri file provided.")
        return

    if len(args) == 0:
        repl()
        return

    filename = args[0]
    try:
        with open(filename) as f:
            run(f.read())
    except FileNotFoundError:
        print(f"File not found: {filename}")


if __name__ == "__main__":
    main()
