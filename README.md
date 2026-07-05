# YuriLang ❤️🧡🤍

<img src="icons/logo.png" alt="logo" width="500">

![version](https://img.shields.io/github/v/release/Kazooki123/yurilang?color=pink) ![GitHub License](https://img.shields.io/github/license/Kazooki123/yurilang?color=pink) ![GitHub Repo stars](https://img.shields.io/github/stars/Kazooki123/yurilang?logoColor=pink&color=pink) ![Endpoint Badge](https://img.shields.io/endpoint?url=https%3A%2F%2Floc-counter.onrender.com%2F%3Frepo%3DKazooki123%2Fyurilang%26branch%3Dmain%26stat%3Dlines&logo=github&color=pink) ![GitHub contributors](https://img.shields.io/github/contributors/Kazooki123/yurilang?color=pink) ![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/Kazooki123/yurilang/run.yml?branch=main&color=pink) ![GitHub Issues or Pull Requests](https://img.shields.io/github/issues-pr/Kazooki123/yurilang?logo=github&logoColor=pink&color=pink) [![Telegram](https://img.shields.io/badge/telegram-2CA5E0?style=flat&logo=telegram&logoColor=white&color=pink)](https://t.me/+UQ449T4ApJliNzJl) [![Matrix](https://img.shields.io/badge/matrix-join-pink?style=flat&logo=matrix&logoColor=white)](https://matrix.to/#/!DUcTGkqyDkXQvtVDyU:matrix.org?via=matrix.org) [![Fluxer](https://img.shields.io/badge/join-fluxer?style=flat&logo=apple&logoColor=white&label=fluxer&color=pink)
![Discord](https://img.shields.io/discord/1460115593775681539?logo=discord&logoColor=pink&color=pink)](https://fluxer.gg/CVDSiGmT) ![Bluesky followers](https://img.shields.io/bluesky/followers/starloexoliz123.bsky.social?logo=bluesky&logoColor=pink&color=pink) ![Python](https://img.shields.io/badge/python-3670A0?style=flat&logo=python&logoColor=white&label=3.14&color=pink) ![LLVM](https://img.shields.io/badge/llvm-262D3A?style=flat&logo=llvm&logoColor=white&label=22.1.3&color=pink) ![llvmworks](https://img.shields.io/badge/backend-llvm%20toolchain-pink?logo=llvm) ![Target](https://img.shields.io/badge/target-x86--64-pink?logo=amd&style=flat&labelColor=black) ![FutureTargets](https://img.shields.io/badge/future-ARM64%20%7C%20RISC--V-pink?logo=llvm&style=flat&labelColor=black)


YuriLang (Yuri + Language) is an esoteric programming language with Yuri characteristic (and **aesthetics**) as functions, operators, syntaxes, etc. Written in Python 🌀

### **Yuri (/ˈjʊəri/)**

- **Shiny Certificate :3**

![Yuri Certificate](https://img.shields.io/badge/YURI%20CERTIFICATE-ffc0cb?style=flat&logo=github&logoColor=white)

- **Docs:** `Coming Soon...`

> [!IMPORTANT]
> 💜 Still in development, new keywords and features will be added one by one, and the language isn't stabilize *yet*.

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

### General Rules

- Every statement starts with "@"
- Code executes only inside "@wlw" (entry point) :3
- Strings must be wrapped in quotes ""...""
- Variables are **mutable** by default, unless awakened.
- You can do comments with `? (your comment)`
- Logic / Data types exists using `love`, `ache`, and `uncertain`

---

### 🥞 Available Keywords

@wlw — Entry Point

Defines where the program begins.

```yuri
@wlw:
    @confess "Hello, world!"
```

---

@bond — Variable Declaration

Creates and assigns a variable.

```yuri
@bond x = 10
@bond name = "Aki"
```

---

@confess — Output

Prints values or text.

```yuri
@confess "Hello 💖"
@confess "Value is" x
```

---

@ship — Functions

Declares a function (also supports parameters :p)

```yuri
@ship YuuIsGoated:
    @confess "Peak!"

@ship bloom_into_you:
    @confess "More Peak!"
```

---

@promise — Return

Returns a value after exiting

```yuri
@choose nums with x:
    @promise x > 2
```

---

@jam — Break/Pass

Used to break out a loop.

```yuri
@cling 10:
    @jealous x == 5:
        @jam
```

---

@affect — Mapping

Returns the provided typed map unchanged.

```yuri
@wlw:
    @bond feelings = [["distant", "confused", "realizing", "confessing"]]
    feelings @> @affect yuu_reacts
```

---

@choose - Filter

Extracts an element from a collection (like a list) based on a condition.

```yuri
@ship is_even x:
    @bond rem = @band x 1
    @jealous rem == 0:
        @promise love
    @forgive:
        @promise ache

@bond evens = @choose nums is_even
@confess evens
```

---

@slice - Slicing

A technique to extract a specific portion or "subset" of data from a sequence.

```yuri
@bond part = @slice nums 2 5
@confess part
```

---

@sappho / @poet — Pattern matching

Used for pattern matching. You can learn what [pattern matching is here](https://en.wikipedia.org/wiki/Pattern_matching).

```yuri
@sappho x:
    @poet 1:
        @confess "one"
    @poet 2:
        @confess "two"
```

---

@luna / @bloom - Lambda function

Anonymous functions used for inline.

```yuri
@wlw:
    @bond double = @luna x: x times 2
    @confess @double 5

    @bond double = @bloom x: x times 2
```

---

@dream — Asynchronous (async)

Allows a program to start a (new) task and then move on to another work before that task finishes.

```yuri
@wlw:
    ##async
    @ship fetch_feeling url:
        @dream slept = @sleep 0.5
        @wake slept
        @promise "feelings arrived from " plus url

    @dream result = @fetch_feeling "her heart"
    @wake result
    @confess result
```

`@wake` being `await`.

---

@awaken - Immutable

In Yurilang, variables are mutable by default, so to make them permanent or unchangeable, use the `@awaken` keyword.

```yuri
@wlw:
    @bond x = 10
    @awaken x
```

Trying to modify an already **awakened** variable throws an Runtime Error:

```bash
Error: 'x' has already awakened. It is permanent.
```

---

@choose — Filtering

Filters or choose a specific element from a list based on the conditions.

```yuri
@wlw:
    @bond nums = [[1,2,3,4]]

    @bond result = @choose nums with x:
        @promise x > 2

    @confess result
```

---

@jealous — Conditional (Basic)

Checks a condition.

`@jealous` -> if
`@forgive` -> else

```yuri
@wlw:
    @jealous a > 5:
        @confess "Greater than five."
    @forgive:
        @confess "Five or less."
```

---

@cling — Loop (Basic)

Repeats an action a number of times.

```yuri
@cling "Woosh!" 3
@cling "yay!" 5
```

---

@fate — While Loops

Repeats a block of code over and over again as long as a specific condition remains true.

```yuri
@fate y < 10:
    @jealous y == 5:
        @jam
    @confess y
    @rebond y = y plus 1
```

---

@yuri — Import

For importing modules.

> [!NOTE]
> Modules in yurilang are still unstable and may break in future updates or changes.

```yuri
@yuri math
@yuri json

@yuri bloomintoyou
```

---

@crush - Types

Declares a **type**

- strings -> `heart`
- numbers -> `int`
- float -> `float`
- boolean -> `bloom`
- lists -> `list`

> [!IMPORTANT]
> Types in this language is **never** enforced.

```yuri
@wlw:
    @crush name = heart
    @crush age = int
    @crush score = float
    @crush is_inlove = bloom
    @crush friends = list
    @crush mystery = uncertain
```

**Note:** you can use the `--crush` flag for this feature.

---

@sempai — Import C functions

Loads and binds a function from a C shared library, callable like any other `@ship` function.

```yuri
@sempai libm.so.6 sqrt double
@bond result = @sqrt 144
@confess result
```

Supported return types: `int`, `double`, `float`, `string`. If omitted, defaults to `int`.

---

@kumitate — **Inline Assembly**

Allows users to embed low-level assembly language instructions directly within high-level code.

> [!WARNING]
> This feature is very experimental, we'll add a `--experiment` flag later on, but this feature hasn't been fully stabilize *yet*.
> Status: `HALTED` - Compile feature only.

```yuri
@wlw:
    ? (basic arithmetic in assembly)
    @bond x = 5
    @bond y = 3
    @bond result = 0

    @kumitate:
        """
        mov rax, {x}
        add rax, {y}
        mov {result}, rax
        """

    @confess result         ? (-> 8)
```

---

@spectrum — Enums

A data type that lets you define a value as one of several possible variants.

```yuri
@spectrum Feeling:
    confused,
    curious,
    nervous,
    inlove,
    certain
```

---

@persona — Structs

A custom data type that lets you group related data together under one name

```yuri
@persona Character:
    name,
    age,
    hobby,
    crush
```

---

### 🍞 Operators

> [!WARNING]
> Some of these operators & **special symbols** are planned meaning they're not implemented *yet*

```bash
>
<
=>
<-
->
()
{}
~
~>
|x|
:
^
^^
#
$
&
!
?
```

---

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

**glc** - Girls Love to Compile

An Odin written compiler made for YuriLang, it will be released soon and if it does expect bugs or errors at it's first released.

**Note:** The compiler is currently implemented in Python.

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
