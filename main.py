from src.interpreter import run

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("ERR!")
        print("Usage: python main.py <file.yuri>")
        exit()

    # Testing
    with open("test.yuri", "r") as f:
        code = f.read()

    with open(sys.argv[1], "r") as f:
        code = f.read()

    run(code)
