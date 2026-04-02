import sys
from src.interpreter import run
from src.repl import repl
from src.compiler import compile_yuri


def main():
    args = sys.argv[1:]

    if "--compile" in args:
        try:
            filename = next(arg for arg in args if arg.endswith(".yuri"))

            with open(filename, "r") as f:
                code = f.read()

            asm = compile_yuri(code)

            out = filename.replace(".yuri", ".asm")

            with open(out, "w") as f:
                f.write(asm)

            print(f"Compiled to {out}")
            print(f"Run with:")
            print(f"nasm -f elf64 {out} && ld {out.replace('.asm', '.o')} -o program && ./program")

        except StopIteration:
            print("No .yuri file provided for compilation.")

        except FileNotFoundError:
            print(f"File not found: {filename}")

        return

    if len(args) == 0:
        repl()
    else:
        filename = args[0]

        try:
            with open(filename, "r") as f:
                code = f.read()
                run(code)
        except FileNotFoundError:
            print(f"File not found: {filename}")


if __name__ == "__main__":
    main()
