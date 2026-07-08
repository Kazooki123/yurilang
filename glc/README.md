# Girls Love to Compile

A real native compiler for the Yurilang v0.1.

> [!NOTE]
> For now the compiler is recently implemented in **Python**, but once the Rust version is finished, it'll be the primarily compiler for yurilang.

## Example (0.1)

```yuri
? (Happy Yuri!!)
@wlw:
    @bond x = 1 plus 2
    @bond y = 2 times 3
    @confess x, y ? (Result: 3 6)

    @bond a = 7
    @jealous a > 5:
        @confess "Greater than five!"
    @forgive:
        @confess "Five or less.."

    @cling 5:
        @confess "Hi!"
```

## Build

You need a Rust toolchain (`rustup`) and a C compiler (`cc`/`gcc`/`clang`)
on `$PATH` for linking.

```sh
cargo build --release
```

## Run

```sh
./target/release/glc examples/hello.yuri
./hello
```

## License

Under the **GNU Public License**
