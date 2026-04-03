import os
import time
import sys

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
  help        → show this message
  exit        → exit REPL
  amy         → ??? 👀
  morse       → try something mysterious...

Flags:
  yuri file.yuri           → run file
  yuri --compile file      → compile to ASM
  yuri --bytecode file     → compile to bytecode
  yuri --vm file.yuric     → run VM

Tips:
  Use @confess to print 🩷
  Use @ship to define love (functions)
""")


def spin_globe():
    frames = [
        "🌍",
        "🌎",
        "🌏",
    ]

    colors = [
        "\033[38;5;166m",  
        "\033[38;5;208m",  
        "\033[38;5;223m",  
        "\033[38;5;212m",  
        "\033[38;5;197m",  
    ]

    for i in range(20):
        frame = frames[i % len(frames)]
        color = colors[i % len(colors)]

        sys.stdout.write(f"\r{color}{frame} Loading Yuri energy... \033[0m")
        sys.stdout.flush()
        time.sleep(0.1)

    print("\n⛅ Done!")


def yuri_prompt():
    colors = [
        "\033[38;5;166m",  
        "\033[38;5;208m",  
        "\033[38;5;223m", 
        "\033[38;5;212m",  
        "\033[38;5;197m",
    ]
    text = ">>> "
    colored = ""

    for i, ch in enumerate(text):
        color = colors[i % len(colors)]
        colored += f"{color}{ch}"

    return colored + "\033[0m"


def trigger_amy_easter_egg():
    print("\n🥞 Amy mode activated...\n")

    # install chafa first so it can work
    os.system("chafa amy.png")
    os.system("chafa amy2.png")

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
        "@anormalwintrovert", "@hexagonos", "@theophilus_dev", "@iiiangel", "@asciixd", "@themackabu", "@solaenum (luci)", "@vt_d (vitam1n)", "@aleks_minecraft1", "@akiradiv", "@yazn.iso", "@turtlovesturtles", "@ditherdude"
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
            code = input(yuri_prompt()).strip()

            if code in ("exit", "quit"):
                print("bye bye! :<")
                break

            if code == "help":
                print_help()
                continue

            if code == "world":
                spin_globe()
                continue

            if code == "amy":
               trigger_amy_easter_egg()
               continue

            run(code)

        except Exception as e:
            print("Error:", e)
