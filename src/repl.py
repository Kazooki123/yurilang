from src.interpreter import run

def print_yuri():
    COLORS = [
        "\033[38;5;203m", # dark pink
        "\033[38;5;210m", # pink
        "\033[38;5;217m", # light pink
        "\033[38;5;224m", # cream
        "\033[38;5;181m", # light orange
        "\033[38;5;173m", # orange
    ]
    RESET = "\033[0m"

    text = [
        "██╗   ██╗██╗   ██╗██████╗ ██╗",
        "╚██╗ ██╔╝██║   ██║██╔══██╗██║",
        " ╚████╔╝ ██║   ██║██████╔╝██║",
        "  ╚██╔╝  ██║   ██║██╔══██╗██║",
        "   ██║   ╚██████╔╝██║  ██║██║",
        "   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝",
    ]

    for i, line in enumerate(text):
        color = COLORS[i % len(COLORS)]
        print(color + line + RESET)

    print("🧡 YuriLang REPL 🩷\n")

def repl():
    print_yuri()
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
