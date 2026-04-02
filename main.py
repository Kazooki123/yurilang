import sys
from src.interpreter import run
from src.repl import repl


def main():
    if len(sys.argv) == 1:
        repl()
    else:
        filename = sys.argv[1]

        try:
            with open(filename, "r") as f:
                code = f.read()
                run(code)
        except FileNotFoundError:
            print(f"File not found: {filename}")


if __name__ == "__main__":
    main()