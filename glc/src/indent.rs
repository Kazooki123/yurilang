//! Converts Yuri's indentation-based blocks into an explicit,
//! brace-delimited form before pest ever sees the source.
//!
//! Pest has no native concept of significant whitespace, so this pass
//! does the Python-style indent/dedent bookkeeping once, up front. It
//! also strips `?` comments here rather than in the grammar, because
//! comment-stripping needs to be aware of string literals (a `?` inside
//! a string isn't a comment), and a comment-only line must not affect
//! indentation tracking.

use anyhow::{bail, Result};

pub fn preprocess(source: &str) -> Result<String> {
    let mut out = String::with_capacity(source.len());
    let mut indent_stack: Vec<usize> = vec![0];

    for raw_line in source.lines() {
        let stripped = strip_comment(raw_line);
        let content = stripped.trim_end();
        if content.trim().is_empty() {
            continue;
        }

        let indent = leading_whitespace(content);
        let trimmed = content[indent..].trim_end();
        let current = *indent_stack.last().expect("stack always has a base level");

        if indent > current {
            indent_stack.push(indent);
            out.push_str("{\n");
        } else if indent < current {
            while *indent_stack.last().unwrap() > indent {
                indent_stack.pop();
                out.push_str("}\n");
            }
            if *indent_stack.last().unwrap() != indent {
                bail!(
                    "inconsistent indentation near: {trimmed:?} (indent {indent} doesn't match any enclosing block)"
                );
            }
        }

        out.push_str(trimmed);
        out.push('\n');
    }

    while indent_stack.len() > 1 {
        indent_stack.pop();
        out.push_str("}\n");
    }

    Ok(out)
}

/// Strips a `?` comment from a line, staying aware of string literals so
/// `@bond x = "a ? b"` keeps its string intact.
fn strip_comment(line: &str) -> &str {
    let bytes = line.as_bytes();
    let mut in_string = false;
    let mut escaped = false;

    for (i, &b) in bytes.iter().enumerate() {
        if in_string {
            if escaped {
                escaped = false;
            } else if b == b'\\' {
                escaped = true;
            } else if b == b'"' {
                in_string = false;
            }
        } else if b == b'"' {
            in_string = true;
        } else if b == b'?' {
            return &line[..i];
        }
    }

    line
}

fn leading_whitespace(s: &str) -> usize {
    s.len() - s.trim_start_matches([' ', '\t']).len()
}
