# YuriLang ❤️🧡🤍

![Logo](https://github.com/Kazooki123/yurilang/blob/main/logo.png)

![version](https://img.shields.io/badge/version-v1.0.0-pink)

YuriLang (Yuri + Language) is an esoteric programming language with Yuri characteristic as functions, operators, syntaxes, etc. Written in Python 🌀

- **Docs:** `Coming Soon...`

> [!IMPORTANT]
> 💜 Still in development, new keywords and features will be added one by one, and the language isn't stabilize *yet*.

## Setup

> [!NOTE]
> For Windows, the exe file will be released soon once pyinstaller has done setting up.

Prerequisites:

- Python (3.13)
- NASM (if you're using this language with it's assembly feature)
- wat2wasm (if you're testing it for wasm - experimental)

Simply type this in your terminal:

```
curl -sSL https://raw.githubusercontent.com/Kazooki123/yurilang/main/install.sh | bash
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

**General Rules**

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

```
@wlw:
    @confess "Hello, world!"
```

---

@bond — Variable Declaration

Creates and assigns a variable.

```
@bond x = 10
@bond name = "Aki"
```

---

@confess — Output

Prints values or text.

```
@confess "Hello 💖"
@confess "Value is" x
```

---

@ship — Functions

Declares a function (also supports parameters :p)

```
@ship YuuIsGoated:
    @confess "Peak!"

@ship bloom_into_you:
    @confess "More Peak!"
```

---

@promise — Return

Returns a value after exiting

```
@choose nums with x:
    @promise x > 2
```

---

@jam — Break/Pass

Used to break out a loop.

```
@cling 10:
    @jealous x == 5:
        @jam
```

---

@affect — Mapping

Returns the provided typed map unchanged.

```
@wlw:
    @bond feelings = [["distant", "confused", "realizing", "confessing"]]
    feelings @> @affect yuu_reacts
```

---

@sappho / @poet — Pattern matching

Used for pattern matching. You can learn what pattern matchings are [here.](https://en.wikipedia.org/wiki/Pattern_matching)

```
@sappho x:
    @poet 1:
        @confess "one"
    @poet 2:
        @confess "two"
```

---

@luna / @bloom - Lambda function

Anonymous functions used for inline.

```
@wlw:
    @bond double = @luna x: x times 2
    @confess @double 5

    @bond double = @bloom x: x times 2
```

---

@awaken - Immutable

In Yurilang, variables are mutable by default, so to make them permanent or unchangeable, use the `@awaken` keyword.

```
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

```
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

```
@wlw:
    @jealous a > 5:
        @confess "Greater than five."
    @forgive:
        @confess "Five or less."
```

---

@cling — Loop (Basic)

Repeats an action a number of times.

```
@cling "Woosh!" 3
@cling "yay!" 5
```
---

@fate — While Loops

Repeats a block of code over and over again as long as a specific condition remains true.

```
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

```
@yuri math
@yuri json

@yuri bloomintoyou
```

---

@sempai — Import C functions

Loads and binds a function from a C shared library, callable like any other `@ship` function.

```
@sempai libm.so.6 sqrt double
@bond result = @sqrt 144
@confess result
```

Supported return types: `int`, `double`, `float`, `string`. If omitted, defaults to `int`.


---

@spectrum — Enums

A data type that lets you define a value as one of several possible variants.

```
@spectrum Feeling:
    confused
    curious
    nervous
    inlove
    certain
```

---

@persona — Structs

A custom data type that lets you group related data together under one name

```
@persona Character
    name
    age
    hobby
    crush
```

---

### 🍞 Operators

> [!WARNING]
> Some of these operators & **special symbols** are planned meaning they're not implemented *yet*

```
@
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
#
$
&
!
?
```

---

### Example Program

```
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

A Rust written compiler made for YuriLang, it will be released soon and if it does expect bugs or errors at it's first released.

## WASM

You can generate a `.wat` file in YuriLang with this command:

> [!NOTE]
> 🩵 You would need **wat2wasm** for this

```bash
python main.py yourfile.yuri --wasm
```

Then convert it to `.wasm` with **wat2wasm**:

```bash
wat2wasm yourfile.wat -o program.wasm
```

## Packages / Libraries / Stores

Most modules or libraries of yurilang right now is placed in `store/`, containing story driven code from **Yuri media**, but as the language evolves so as its modular system, later on the module system will import modules, libs, and packages whenever it is placed.

## Issues and Bugs

If you encounter a bug, error, or any issues, please immediately contact me or create a pull request (PR) and explain what's wrong or for making suggestions and feedbacks, Thank you!! 🧡 >.<

## Contribution

**Everyone is absolutely welcome!** If you're interested, you can freely fork the repository and refer to the [Contribution](CONTRIBUTION.md) guide for contribution information and more 🩷

## LICENSE 

Under the **GNU Public License** <3

![girlkisser](https://cdn.discordapp.com/emojis/1406933370570801197.png)

<img src="https://cdn.discordapp.com/emojis/915366171262451784.gif" width="32">