# YuriLang ❤️🧡🤍

<p align="center">
  <img src="icons/logo.png" alt="logo" width="500">
</p>

![version](https://img.shields.io/github/v/release/Kazooki123/yurilang?color=pink) ![GitHub License](https://img.shields.io/github/license/Kazooki123/yurilang?color=pink) ![GitHub Repo stars](https://img.shields.io/github/stars/Kazooki123/yurilang?logoColor=pink&color=pink) ![Endpoint Badge](https://img.shields.io/endpoint?url=https%3A%2F%2Floc-counter.onrender.com%2F%3Frepo%3DKazooki123%2Fyurilang%26branch%3Dmain%26stat%3Dlines&logo=github&color=pink) ![GitHub contributors](https://img.shields.io/github/contributors/Kazooki123/yurilang?color=pink) ![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/Kazooki123/yurilang/run.yml?branch=main&color=pink) ![GitHub Issues or Pull Requests](https://img.shields.io/github/issues-pr/Kazooki123/yurilang?logo=github&logoColor=pink&color=pink) [![Telegram](https://img.shields.io/badge/telegram-2CA5E0?style=flat&logo=telegram&logoColor=white&color=pink)](https://t.me/+UQ449T4ApJliNzJl) [![Matrix](https://img.shields.io/badge/matrix-join-pink?style=flat&logo=matrix&logoColor=white)](https://matrix.to/#/!DUcTGkqyDkXQvtVDyU:matrix.org?via=matrix.org) [![Fluxer](https://img.shields.io/badge/join-fluxer?style=flat&logo=apple&logoColor=white&label=fluxer&color=pink)
![Discord](https://img.shields.io/discord/1460115593775681539?logo=discord&logoColor=pink&color=pink)](https://fluxer.gg/CVDSiGmT) ![Bluesky followers](https://img.shields.io/bluesky/followers/starloexoliz123.bsky.social?logo=bluesky&logoColor=pink&color=pink) ![Python](https://img.shields.io/badge/python-3670A0?style=flat&logo=python&logoColor=white&label=3.14&color=pink) ![LLVM](https://img.shields.io/badge/llvm-262D3A?style=flat&logo=llvm&logoColor=white&label=22.1.3&color=pink) ![llvmworks](https://img.shields.io/badge/frontend-llvm%20toolchain-pink?logo=llvm) ![Target](https://img.shields.io/badge/target-x86--64-pink?logo=amd&style=flat&labelColor=black) ![FutureTargets](https://img.shields.io/badge/future-ARM64%20%7C%20RISC--V-pink?logo=llvm&style=flat&labelColor=black)


YuriLang (Yuri + Language) is an esoteric programming language with Yuri characteristic (and **aesthetics**) as functions, operators, syntaxes, etc. Written in Python 🌀

### **Yuri (/ˈjʊəri/)**

- **Shiny Certificate :3**

![Yuri Certificate](https://img.shields.io/badge/YURI%20CERTIFICATE-ffc0cb?style=flat&logo=github&logoColor=white)

> [!IMPORTANT]
> 💜 Still in development, new keywords and features will be added one by one, and the language isn't stabilize *yet*.

### Shoutouts

Shoutout to these language projects from my fellow friends!!

- [Yaoilang](https://github.com/caelondev/garrote) by **caelondev**
- [bbodu](https://codeberg.org/qofqoflop/bbodu) by **Hexagonos**

## Setup

Prerequisites:

- Python (3.14+)
- NASM (if you're using this language with it's assembly feature)
- wat2wasm (if you're testing it for wasm - experimental)

Simply type this in your terminal:

```bash
curl -sSL https://raw.githubusercontent.com/Kazooki123/yurilang/main/install.sh | bash
```

- 🪟 Windows:

> [!NOTE]
> Make sure you have `pyinstaller` installed.

```bash
pyinstaller --onefile --icon='icons/icon.ico' --add-data "store/*.yuri;store" yuri.py

# if you want to include DLL files
pyinstaller --onefile --icon='icons/icon.ico' --add-binary "bin/*.dll;." yuri.py
```

- 🔗 From Source:

```bash
git clone https://github.com/Kazooki123/yurilang
cd yurilang
python install.py          # Linux/Mac (may need sudo :/)
python install.py --user   # no sudo needed
install.bat                # Windows (double click or run as admin)
```

## Syntax

Checkout the [keywords](KEYWORDS.md) guide! </3

### Example Program

```yuri
@wlw:
    @bond x = 10
    @bond name = "Aki"

    @confess "Hello" name
    @confess "Value of x is" x

    @jealous x == 10

    @cling "yahoo!" 3
```

---

## Yuri References

- [Sappho - Wikipedia](https://en.wikipedia.org/wiki/Sappho)
- [Bloom Into You](https://m.imdb.com/title/tt8993464/)
- [Citrus](https://yuripedia.fandom.com/wiki/Category:Citrus)
- [Kase-San](https://m.imdb.com/title/tt7456468/)

## Compiler

**glc** - [Girls Love to Compile](https://codeberg.org/Kazooki123/glc)

A Rust written compiler made for YuriLang, it will be released soon and if it does expect bugs or errors at it's first released.

## LLVM

> [!WARNING]
> Some bugs and error may still occur btw

As of `v1.3.0`, yurilang can **transpile** to a LLVM IR (Intermediate Representation) file `(.ll)` with the help of the `--llvm` flag, while native object files `(.o)` are done with the `--llvm-obj` flag.

## WASM

You can generate a `.wat` file in YuriLang with this command:

> [!NOTE]
> 🩵 You would need **wat2wasm** for this

```bash
python yuri.py yourfile.yuri --wasm
```

Then convert it to `.wasm` with **wat2wasm**:

```bash
wat2wasm yourfile.wat -o program.wasm
```

## Amy

[Amy](https://codeberg.org/Kazooki123/amy) is a  `TUI`-based editor primarily written in **Go**.

Named after **Amy** from **I Love Amy**, a South Korean yuri manhwa story.

Most contribution is **thanks to** [Angel Miku](https://github.com/iiAngel)

## Packages / Libraries / Stores

Most modules or libraries of yurilang right now is placed in `store/`, containing story driven code from **Yuri media**, but as the language evolves so as its modular system, later on the module system will import modules, libs, and packages whenever it is placed.

## DLLs (Windows)

Yurilang now has built-in features / libs thanks to the **Dynamic Link Libraries** listed here:

- `libant.dll`
- `libflac.dll`
- `libcurl.dll`
- `ffmpeg.dll`
- `raylib.dll`
- `zlib.dll`
- `glfw3.dll`

## Codeberg

<a href="https://codeberg.org/Kazooki123/yurilang">
    <img alt="Get it on Codeberg" src="https://get-it-on.codeberg.org/get-it-on-white-on-black.png" height="60">
</a>

## Community

- [Discord](https://discord.gg/BhbZzkPPym)

## Issues and Bugs

If you encounter a bug, error, or any issues, please immediately contact me or create a pull request (PR) and explain what's wrong or for making suggestions and feedbacks, Thank you!! 🧡 >.<

## Contribution

**Everyone is absolutely welcome!** If you're interested, you can freely fork the repository and refer to the [Contribution](CONTRIBUTING.md) guide for contribution information and more 🩷

## LICENSE

Under the **GNU Public License** <3

![girlkisser](https://cdn.discordapp.com/emojis/1406933370570801197.png)

<img alt="heart" src="https://cdn.discordapp.com/emojis/915366171262451784.gif" width="32">
