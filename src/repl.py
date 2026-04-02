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

def shoutouts():
    print("Shout Outs!!")

    names = [
        "@jamiw (1024ping)", "@gseppo", "@lunalapigeonne",
        "@anormalwintrovert", "@hexagonos", "@theophilus_dev", "@iiiangel", "@asciixd", "@themackabu", "@solaenum (luci)", "@vt_d (vitam1n)", "@aleks_minecraft1"
    ]

    for i in range(0, len(names), 2):
        left = names[i]
        right = names[i+1] if i+1 < len(names) else ""
        print(f"   {left:<30} {right}")

    print()


def repl():
    print_yuri()
    print("Made with Love by StarloExoliz!")
    shoutouts()
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
