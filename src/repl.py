import os
from src.interpreter import run
# from PIL import Image

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


def print_help():
    print("""
YuriLang REPL Help ☀️

Commands:
  help        Show this help menu
  exit/quit   Exit REPL
  amy         Easter egg 👀

Normal input:
  Any YuriLang code will be executed normally
""")


def trigger_amy_easter_egg():
    print("\n🥞 Amy mode activated...\n")

    # install chafa first so it can work
    os.system("chafa amy.png")

    # try:
    #    img = Image.open("amy.png")
    #    img = img.resize((80, 40))
    #    img = img.convert("L")

    #    chars = " .:-=+*#%@"

    #    for y in range(img.height):
    #        line = ""
    #        for x in range(img.width):
    #            pixel = img.getpixel((x, y))
    #            line += chars[pixel * len(chars) // 256]
    #        print(line)

    # except Exception as e:
    #    print("Couldn't load amy image:", e)



def shoutouts():
    print("Shout Outs!!")

    names = [
        "@jamiw (1024ping)", "@gseppo", "@lunalapigeonne",
        "@anormalwintrovert", "@hexagonos", "@theophilus_dev", "@iiiangel", "@asciixd", "@themackabu", "@solaenum (luci)", "@vt_d (vitam1n)", "@aleks_minecraft1", "@akiradiv"
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
            code = input(">>> ").strip()

            if code in ("exit", "quit"):
                print("bye bye! :<")
                break

            if code == "help":
                print_help()
                continue

            if code == "amy":
               trigger_amy_easter_egg()
               continue

            run(code)

        except Exception as e:
            print("Error:", e)
