use anyhow::{Context, Result};
use clap::{Parser, Subcommand};
use std::fs;
use std::path::Path;

#[derive(Parser)]
#[command(name = "yuu")]
#[command(about = "YuriLang package manager 💕", long_about = None)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    Init(InitArgs),
}
                    
#[derive(clap::Args)]
struct InitArgs {
    name: Option<String>,
}

fn main() -> Result<()> {
    let cli = Cli::parse();
                    
    match cli.command {
        Commands::Init(args) => init_command(args)?,
    }
                    
    Ok(())
}

fn init_command(args: InitArgs) -> Result<()> {
    let current_dir = std::env::current_dir().context("Failed to get current directory")?;
                    
    let (project_dir, project_name) = if let Some(name) = args.name {
        let dir = current_dir.join(&name);
        if dir.exists() {
            anyhow::bail!("Directory {} already exists!", name);
        }
        fs::create_dir_all(&dir)?;
        (dir, name)
    } else {
        // `yuu init` (no name) → init the current folder
        let name = current_dir
            .file_name()
            .and_then(|n| n.to_str())
            .unwrap_or("yuri-project")
            .to_string();
        (current_dir, name)
    };
                    
    create_yuu_project(&project_dir, &project_name)?;
    println!("Initialized new YuriLang project in");
    println!("   {}", project_dir.display());
    println!("\nNext steps:");
    println!("   cd {}", project_name);
    println!("   yuu build     # (coming soon)");
    println!("   yuu run       # (coming soon)");
    Ok(())
}

fn create_yuu_project(project_dir: &Path, name: &str) -> Result<()> {
    // 1. Creates Yuu.toml
    let manifest = format!(
        r#"[package]
name = "{name}"
version = "0.1.0"
authors = ["Your Name <you@example.com>"]
edition = "yuri-2026"

# Dependencies go here later
[dependencies]
# example-dep = "1.0"
    "#
    );

    fs::write(project_dir.join("Yuu.toml"), manifest)
        .context("Failed to write Yuu.toml")?;
                    
    // Create src/ directory
    let src_dir = project_dir.join("src");
    fs::create_dir_all(&src_dir)?;
                    
    let hello_world = r#"// Welcome to YuriLang! >3
    @wlw:
        @confess "Hello, World!"
    "#;

    fs::write(src_dir.join("main.yuri"), hello_world)
        .context("Failed to write src/main.yuri")?;

    fs::write(project_dir.join("README.md"), format!("# {}\n\nA YuriLang project.", name))?;
                    
    Ok(())
}

