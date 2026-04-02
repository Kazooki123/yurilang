from src.interpreter import run

def print_yuri():
    COLORS = [
        "\033[38;5;166m",  # dark orange
        "\033[38;5;208m",  # orange
        "\033[38;5;223m",  # cream
        "\033[38;5;212m",  # pink
        "\033[38;5;197m",  # dark pink
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
        color = COLORS[int(i * len(COLORS) / len(text))]
        print(color + line + RESET)

    print("🧡 YuriLang REPL 🩷\n")

def repl():
    print_yuri()
    print("Made with Love by StarloExoliz!")
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
