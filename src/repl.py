import os
import time
import sys

from src.interpreter import run
# from PIL import Image

def detect_morse(code):
    TARGET = "-.-- ..- .-. .. -.-. --- .-. ."  # ???????

    normalized = " ".join(code.strip().split())

    if normalized == TARGET:
        return True

    return False

COLORS = [
    "\033[38;5;166m",  # dark orange
    "\033[38;5;208m",  # orange
    "\033[38;5;223m",  # cream
    "\033[38;5;212m",  # pink
    "\033[38;5;197m",  # dark pink
]

RESET = "\033[0m"

def color_line(text, i):
    return COLORS[i % len(COLORS)] + text + RESET


def print_yuri():
    text = [
        "██╗   ██╗██╗   ██╗██████╗ ██╗",
        "╚██╗ ██╔╝██║   ██║██╔══██╗██║",
        " ╚████╔╝ ██║   ██║██████╔╝██║",
        "  ╚██╔╝  ██║   ██║██╔══██╗██║",
        "   ██║   ╚██████╔╝██║  ██║██║",
        "   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝",
    ]

    for i, line in enumerate(text):
        print(color_line(line, i))

    print("🧡 YuriLang REPL 🩷\n")


def print_help():
    print("""
YuriLang REPL Help ☀️

Commands:
  help        → show this message
  exit        → exit REPL
  edit        → enters an editor
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

def show_license():
    print("\nOpening LICENSE (press 'q' to exit)\n")

    try:
        with open("LICENSE", "r") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print("LICENSE file not found.\n")
        return

    index = 0
    page_size = 15  # lines per page

    while True:
        os.system("clear")  # use "cls" if Windows later

        print("LICENSE (press 'q' to exit)\n")

        for line in lines[index:index + page_size]:
            print(line.rstrip())

        print("\n[Enter = next | q = quit]")

        cmd = input().strip().lower()

        if cmd == "q":
            print("\nClosing license...\n")
            break

        index += page_size
        if index >= len(lines):
            print("\nEnd of license.\n")
            break

def show_credits():
    print("\n⭐ YuriLang Credits\n")

    print("Creator:")
    print("  StarloExoliz / Kazooki\n")

    print("Contributors:")
    names = [
        "@themackabu    → JS-Port",
        "@@douxx.tech   → Added C callers"
    ]

    for i, name in enumerate(names):
        print(f"  {color_line(name, i)}")


def yuri_editor():
    print("🤍 Yuri Editor (type ':wq' to save & exit)\n")

    lines = []

    while True:
        line = input(color_line("~ ", len(lines)))

        if line == ":wq":
            break

        lines.append(line)

    filename = input("Save as: ")

    with open(filename, "w") as f:
        f.write("\n".join(lines))

    print(f"Saved to {filename}! 🫧🍮")

def spin_globe():
    frames = [
        "🌍",
        "🌎",
        "🌏",
    ]

    for i in range(20):
        frame = frames[i % len(frames)]
        color = color_line(frame, i)

        sys.stdout.write(f"\r{color}{frame} Loading Yuri energy... \033[0m")
        sys.stdout.flush()
        time.sleep(0.1)

    print("\n⛅ Done!")


def yuri_prompt():
    text = ">>> "
    colored = ""

    for i, ch in enumerate(text):
        colored += COLORS[i % len(COLORS)] + ch

    return colored + RESET


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
        "@anormalwintrovert", "@hexagonos", "@theophilus_dev", "@iiiangel", "@asciixd", "@themackabu", "@solaenum (luci)", "@vt_d (vitam1n)", "@aleks_minecraft1", "@akiradiv", "@yazn.iso", "@turtlovesturtles", "@ditherdude", "@itsthatonejack", "@douxx.tech"
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

            if detect_morse(code):
                print("\n🍄 Signal accepted...\n")

                import time
                time.sleep(1)

                print("Decoding transmission...\n")
                time.sleep(1)

                print("https://pastebin.com/zzS2RQcH")
                print("The password is: 8mgS5erYEL")
                continue

            if code == "help":
                print_help()
                continue

            if code == "world":
                spin_globe()
                continue

            if code == "edit":
                yuri_editor()
                continue

            if code == "credits":
                show_credits()
                continue

            if code == "license":
                show_license()
                continue

            if code == "amy":
               trigger_amy_easter_egg()
               continue

            run(code)

        except Exception as e:
            print("Error:", e)
