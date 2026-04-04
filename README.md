# YuriLang ❤️🧡🤍

![Logo](https://github.com/Kazooki123/yurilang/blob/main/IMG_20260401_200938.png)

YuriLang (Yuri + Language) is an esoteric programming language with Yuri characteristic as functions, operators, syntaxes, etc. Written in Python 🌀

> [!IMPORTANT]
> 💜 Still in development, new keywords and features will be added one by one, and the language isn't stabilize *yet*.

## Syntax

**General Rules**

- Every statement starts with "@"
- Code executes only inside "@wlw" (entry point) :3
- Strings must be wrapped in quotes ""...""
- Variables are **mutable** by default, unless awakened.
- You can do comments with `? (your comment)`

---

💖 Available Keywords (v0.1)

@wlw — Entry Point

Defines where the program begins.

```
@wlw:
    @confess "Hello, world 💖"
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

@luna - Lambda function

Anonymous functions used for inline.

> [!WARNING]
> This feature hasn't been fully implemented *yet*

```
@wlw:
    @bond double = @luna x -> x times 2
    @confess @double 5
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

@spectrum — Enums

A data type that lets you define a value as one of several possible variants.

> [!WARNING]
> This feature hasn't been fully implemented *yet*

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

## Compiler

[Coming Soon]

## Packages / Libraries / Stores

[Coming Soon]

## Issues and Bugs

If you encounter a bug, error, or any issues, please immediately contact me or create a pull request (PR) and explain what's wrong or for making suggestions and feedbacks, Thank you!! 🧡 >.<

## Contribution

**Everyone is absolutely welcome!** If you're interested, you can freely fork the repository and refer to the [Contribution](CONTRIBUTION.md) guide for contribution information and more 🩷

## LICENSE 

Under the **GNU Public License** <3

