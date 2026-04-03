import sys
from src.interpreter import run
from src.repl import repl
from src.compiler import compile_yuri
from vm.compiler import compile_to_bytecode
from vm.bytecode import YuriVM
from vm.serializer import save_yuric, load_yuric


def main():
    args = sys.argv[1:]

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