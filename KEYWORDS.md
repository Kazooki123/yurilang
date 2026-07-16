# Keywords Guide

Here you'll learn how keywords and statements work in Yurilang!

## General Rules

- Every statement starts with "@"
- Code executes only inside "@wlw" (entry point) :3
- Strings must be wrapped in quotes ""...""
- Variables are **mutable** by default, unless awakened.
- You can do comments with `? (your comment)`
- Logic / Data types exists using `love`, `ache`, and `uncertain`

---

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

@bloom - Lambda function

Anonymous functions used for inline.

```yuri
@wlw:
    @bond double = @bloom x: x times 2
    @confess @@double 5    
```

---

@dream — Asynchronous (async)

Allows a program to start a (new) task and then move on to another work before that task finishes.

```yuri
@wlw:
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

@memory / @recall / @forget - Key-Value storing

Stores assigned values into `yuri.db`, you can wipe them out with `@forget`.

```yuri
@memory "test" = "hello" ? (key=test, val=hello)
@recall "test"
@confess test ? (Outputs: hello)

? (wipe the key-value)
@forget "test"
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

@cling — Loop

Repeats an action a number of times.

> [!NOTE]
> as of `v1.8`, @cling has a different rule in the compiler (glc)

```yuri
? (Interpreter)
@cling "Woosh!" 3
@cling "yay!" 5

? (Compiler)
@cling 10:
    "Hello!"
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
> This feature is compiler-only.

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

> Kumitate (組み立て) means **assembly** in Japanese.

---

@lua - **Inline Lua**

> Inline Lua is a feature where you write lua code and the program runs it on the fly without needing a `.lua` file, though it may still uses the lua VM, but in later versions it'll execute without needing one (hopefully)

```yuri
@wlw:
    @yuri bloomintoyou

    @lua:
        confess("Hello From Lua!!")

    @bond chapter = 7

    @lua:
        -- LUA
        local chapter = yuri.chapter
        if chapter < 5 then
            yuri.touko_state = "performing"
        elseif chapter < 10 then
            yuri.touko_state = "inlove"
        else
            yuri.touko_state = "certain"
        end

    @touk_reacts touko_state
```

---

@novel - Macros

Macros are a way for a code, to write more code. It is a part of **Metaprogramming**.

```yuri
@novel repeatThree(block):
    block
    block
    block

@repeatThree():
    @confess "Hi!"
```

---

@spectrum — Enums

A data type that lets you define a value as one of several possible variants.

```yuri
@spectrum Feeling:
    Confused,
    Curious,
    Nervous,
    Love,
    Certain
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

### Operators

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
