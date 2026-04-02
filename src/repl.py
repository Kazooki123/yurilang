from src.interpreter import run

def repl():
    print("YuriLang REPL 💖 (type 'exit' to quit)\n")

    while True:
        try:
            code = input(">>> ")

            if code.strip() in ("exit", "quit"):
                print("bye bye! :<")
                break

            run(code)

        except Exception as e:
            print("Error:", e)