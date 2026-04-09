use clap::Parser;
use colored::*;
use std::fs;
use std::process::Command;

mod lexer;
mod parser;
mod codegen;

#[derive(Parser)]
#[command(name = "glc", about = "Girls Love to Compile 🌸")]
struct Args {
    file: String,

    #[arg(long)]
    emit_ast: bool,

    #[arg(long)]
    emit_rs: bool,

    #[arg(long)]
    steps: bool,

    #[arg(long)]
    run: bool,
}

fn main() {
    let args = Args::parse();

    println!("{} glc v0.1.0 — @wlw to binary", "🌸".bright_magenta());

    if args.steps {
        println!("{} 1. Reading {}", "🟢".bright_cyan(), args.file);
    }

    let code = fs::read_to_string(&args.file).expect("Could not read file 💔");

    if args.steps {
        println!("{} 2. Parsing with your exact lexer + parser...", "🥹".bright_cyan());
    }

    let tree = parser::parse(&code);

    if args.emit_ast {
        println!("{:#?}", tree);
        return;
    }

    if args.steps {
        println!("{} 3. Generating Rust code...", "🦀".bright_cyan());
    }

    let rust_code = codegen::generate_rust(&tree);

    let rs_path = "temp_main.rs";
    fs::write(rs_path, rust_code).unwrap();

    if args.emit_rs || args.steps {
        println!("{} 4. Rust source written to {}", "🩷".bright_cyan(), rs_path);
        if args.emit_rs {
            println!("\n{}", rust_code);
            return;
        }
    }

    if args.steps {
        println!("{} 5. Calling rustc...", "🩷".bright_cyan());
    }

    let status = Command::new("rustc")
        .arg(rs_path)
        .arg("-o")
        .arg("program")
        .status()
        .expect("rustc not found — install Rust!");

    if status.success() {
        println!("{} Compiled successfully!", "✔️".bright_green());
        println!("   Run with: ./program");

        if args.run {
            println!("{} Running binary...", "🏃".bright_yellow());
            let _ = Command::new("./program").status();
        }
    } else {
        println!("{} rustc failed!! (check temp_main.rs)", "💔".bright_red());
    }
}

