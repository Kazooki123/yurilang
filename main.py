import sys
from src.interpreter import run
from src.repl import repl
from src.compiler import compile_yuri
from src.wasm import compile_to_yasm
from vm.compiler import compile_to_bytecode
from vm.bytecode import YuriVM
from vm.serializer import save_yuric, load_yuric


def main():
    args = sys.argv[1:]

    if "--version" in args:
        print(f"""
    YuriLang v1.0.0
    Yuring Complete since 2026 🧡🤍🩷
    Python {sys.version.split()[0]}
    GPL-3.0 License
""")
        return

    if "--help" in args or "-h" in args:
        print(f"""
    Usage: yuri [file] [options]

    yuri program.yuri             interpret
    yuri program.yuri --bytecode  compile to .yuric
    yuri program.yuric --vm       run bytecode  
    yuri program.yuri --compile   compile to x86-64 ASM
    yuri program.yuri --wasm      compile to WebAssembly
    yuri progrwm.yuri --crush     type annotation flag
    yuri                          launch REPL

    Options:
    --version    show version
    --help       show this message
    --user       install to user directory
    --uninstall  remove YuriLang

    "Yuring Complete since 2026" 🍰
    """)
        return

    if "--crush" in args:
        from src.types import crush_summary

        with open(filename) as f:
            run(f.read())
        print("\n🌸 YuriLang Type Hints (@crush)\n")
        print(crush_summary())
        return

    if "--compile" in args:
        try:
            filename = next(arg for arg in args if arg.endswith(".yuri"))
            with open(filename) as f:
                code = f.read()
            asm = compile_yuri(code)
            out = filename.replace(".yuri", ".asm")
            with open(out, "w") as f:
                f.write(asm)
            print(f"Compiled to {out}")
            print(f"Run with:")
            print(f"  nasm -f elf64 {out} -o program.o && ld program.o -o program && ./program")
        except StopIteration:
            print("No .yuri file provided.")
        except FileNotFoundError:
            print(f"File not found.")
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
            print(f"File not found.")
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
            print(f"File not found.")
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

