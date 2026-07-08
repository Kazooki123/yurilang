mod ast;
mod codegen;
mod indent;
mod parser;

use std::env;
use std::fs;
use std::path::PathBuf;
use std::process::Command;

use anyhow::{bail, Context, Result};

const RUNTIME_C: &str = include_str!("runtime.c");

fn main() -> Result<()> {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        bail!(
            "usage: {} <input.yuri> [-o <output>]",
            args.first().map(String::as_str).unwrap_or("yuric")
        );
    }

    let input_path = PathBuf::from(&args[1]);
    let mut output_path = input_path.with_extension("");

    let mut i = 2;
    while i < args.len() {
        if args[i] == "-o" && i + 1 < args.len() {
            output_path = PathBuf::from(&args[i + 1]);
            i += 2;
        } else {
            i += 1;
        }
    }

    let source = fs::read_to_string(&input_path)
        .with_context(|| format!("failed to read source file: {}", input_path.display()))?;

    let program = parser::parse_program(&source).context("parse error")?;
    let object_bytes = codegen::compile_to_object(&program).context("codegen error")?;

    let obj_path = output_path.with_extension("o");
    fs::write(&obj_path, &object_bytes)
        .with_context(|| format!("failed to write object file: {}", obj_path.display()))?;

    let runtime_c_path = output_path.with_extension("runtime.c");
    let runtime_o_path = output_path.with_extension("runtime.o");
    fs::write(&runtime_c_path, RUNTIME_C)
        .with_context(|| format!("failed to write {}", runtime_c_path.display()))?;

    let cc_compile = Command::new("cc")
        .arg("-c")
        .arg(&runtime_c_path)
        .arg("-o")
        .arg(&runtime_o_path)
        .status()
        .context("failed to invoke `cc` to build the print runtime -- is a C toolchain installed?")?;
    if !cc_compile.success() {
        bail!("failed to compile the Yuri print runtime");
    }

    let status = Command::new("cc")
        .arg(&obj_path)
        .arg(&runtime_o_path)
        .arg("-o")
        .arg(&output_path)
        .status()
        .context("failed to invoke system linker `cc`")?;

    if !status.success() {
        bail!("linking failed (cc exited with {status})");
    }

    let _ = fs::remove_file(&obj_path);
    let _ = fs::remove_file(&runtime_c_path);
    let _ = fs::remove_file(&runtime_o_path);

    println!("Compiled: {}", output_path.display());
    Ok(())
}
