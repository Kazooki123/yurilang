//! Turns Yuri source text into an [`ast::Program`].
//!
//! Source is first run through `indent::preprocess`, which turns
//! indentation into explicit `{`/`}` and strips comments; the pest
//! grammar in `grammar.pest` only ever sees that cleaned-up form.

use anyhow::{anyhow, bail, Result};
use pest::iterators::Pair;
use pest::Parser;
use pest_derive::Parser;

use crate::ast::{BinOp, CmpOp, Expr, Program, ShipDef, Stmt};
use crate::indent;

#[derive(Parser)]
#[grammar = "grammar.pest"]
struct YuriParser;

pub fn parse_program(source: &str) -> Result<Program> {
    let preprocessed = indent::preprocess(source)?;

    let mut pairs =
        YuriParser::parse(Rule::program, &preprocessed).map_err(|e| anyhow!("{e}"))?;
    let program_pair = pairs
        .next()
        .expect("grammar guarantees a `program` pair on success");

    let mut functions = Vec::new();
    let mut entry: Option<Vec<Stmt>> = None;

    for item_or_eoi in program_pair.into_inner() {
        match item_or_eoi.as_rule() {
            Rule::item => {
                let inner = item_or_eoi
                    .into_inner()
                    .next()
                    .expect("item always wraps ship_def or entry_block");
                match inner.as_rule() {
                    Rule::ship_def => functions.push(parse_ship_def(inner)?),
                    Rule::entry_block => {
                        let block_pair = inner
                            .into_inner()
                            .find(|p| p.as_rule() == Rule::block)
                            .expect("entry_block always contains a block");
                        if entry.is_some() {
                            bail!("only one @wlw entry point is allowed");
                        }
                        entry = Some(parse_block(block_pair)?);
                    }
                    other => bail!("unexpected item rule: {:?}", other),
                }
            }
            Rule::EOI => {}
            other => bail!("unexpected top-level rule: {:?}", other),
        }
    }

    let entry = entry.ok_or_else(|| anyhow!("no @wlw entry point found"))?;
    Ok(Program { functions, entry })
}

fn parse_ship_def(pair: Pair<Rule>) -> Result<ShipDef> {
    let mut parts = pair.into_inner();
    let name = parts
        .next()
        .expect("ship_def always has a name")
        .as_str()
        .to_string();
    let param_list = parts.next().expect("ship_def always has a param_list");
    let params: Vec<String> = param_list
        .into_inner()
        .map(|p| p.as_str().to_string())
        .collect();
    let block_pair = parts.next().expect("ship_def always has a block");
    let body = parse_block(block_pair)?;
    Ok(ShipDef { name, params, body })
}

fn parse_block(pair: Pair<Rule>) -> Result<Vec<Stmt>> {
    let mut stmts = Vec::new();
    for p in pair.into_inner() {
        if p.as_rule() == Rule::statement {
            stmts.push(parse_statement(p)?);
        }
    }
    Ok(stmts)
}

fn parse_statement(pair: Pair<Rule>) -> Result<Stmt> {
    let inner = pair
        .into_inner()
        .next()
        .expect("statement always wraps exactly one alternative");

    match inner.as_rule() {
        Rule::bond_stmt => {
            let mut parts = inner.into_inner();
            let name = parts
                .next()
                .expect("bond_stmt always has an ident")
                .as_str()
                .to_string();
            let value = parse_expr(parts.next().expect("bond_stmt always has an expr"))?;
            Ok(Stmt::Bond { name, value })
        }
        Rule::confess_stmt => {
            let values = inner
                .into_inner()
                .map(parse_expr)
                .collect::<Result<Vec<_>>>()?;
            Ok(Stmt::Confess { values })
        }
        Rule::if_stmt => {
            let mut parts = inner.into_inner();
            let cond = parse_expr(parts.next().expect("if_stmt always has a condition"))?;
            let then_block = parts.next().expect("if_stmt always has a then-block");
            let then_body = parse_block(then_block)?;
            let else_body = match parts.next() {
                Some(else_block) => Some(parse_block(else_block)?),
                None => None,
            };
            Ok(Stmt::If {
                cond,
                then_body,
                else_body,
            })
        }
        Rule::cling_stmt => {
            let mut parts = inner.into_inner();
            let count = parse_expr(parts.next().expect("cling_stmt always has a count expr"))?;
            let body_block = parts.next().expect("cling_stmt always has a block");
            let body = parse_block(body_block)?;
            Ok(Stmt::Cling { count, body })
        }
        Rule::awaken_stmt => {
            let name = inner
                .into_inner()
                .next()
                .expect("awaken_stmt always has an ident")
                .as_str()
                .to_string();
            Ok(Stmt::Awaken(name))
        }
        Rule::promise_stmt => {
            let value = parse_expr(
                inner
                    .into_inner()
                    .next()
                    .expect("promise_stmt always has an expr"),
            )?;
            Ok(Stmt::Promise(value))
        }
        Rule::call_stmt => {
            let call = inner
                .into_inner()
                .next()
                .expect("call_stmt always wraps a call_expr");
            let (name, args) = parse_call(call)?;
            Ok(Stmt::CallStmt { name, args })
        }
        other => bail!("unexpected statement rule: {:?}", other),
    }
}

fn parse_call(pair: Pair<Rule>) -> Result<(String, Vec<Expr>)> {
    let mut parts = pair.into_inner();
    let name = parts
        .next()
        .expect("call_expr always has a function name")
        .as_str()
        .to_string();
    let args = match parts.next() {
        Some(arg_list) => arg_list
            .into_inner()
            .map(parse_expr)
            .collect::<Result<Vec<_>>>()?,
        None => Vec::new(),
    };
    Ok((name, args))
}

fn parse_expr(pair: Pair<Rule>) -> Result<Expr> {
    let inner = pair
        .into_inner()
        .next()
        .expect("expr always wraps a comparison");
    parse_comparison(inner)
}

fn parse_comparison(pair: Pair<Rule>) -> Result<Expr> {
    let mut parts = pair.into_inner();
    let lhs = parse_arith(parts.next().expect("comparison always has an lhs"))?;

    if let Some(op_pair) = parts.next() {
        let op = match op_pair.as_str() {
            ">=" => CmpOp::Ge,
            "<=" => CmpOp::Le,
            "==" => CmpOp::Eq,
            "!=" => CmpOp::Ne,
            ">" => CmpOp::Gt,
            "<" => CmpOp::Lt,
            other => bail!("unknown comparison operator: {other}"),
        };
        let rhs = parse_arith(parts.next().expect("comparison always has an rhs after an op"))?;
        Ok(Expr::Cmp(op, Box::new(lhs), Box::new(rhs)))
    } else {
        Ok(lhs)
    }
}

fn parse_arith(pair: Pair<Rule>) -> Result<Expr> {
    let mut parts = pair.into_inner();
    let mut lhs = parse_term(parts.next().expect("arith always has a first term"))?;

    loop {
        let Some(op_pair) = parts.next() else { break };
        let op = match op_pair.as_str() {
            "plus" => BinOp::Add,
            "minus" => BinOp::Sub,
            other => bail!("unknown additive operator: {other}"),
        };
        let rhs = parse_term(parts.next().expect("add_op always followed by a term"))?;
        lhs = Expr::Bin(op, Box::new(lhs), Box::new(rhs));
    }

    Ok(lhs)
}

fn parse_term(pair: Pair<Rule>) -> Result<Expr> {
    let mut parts = pair.into_inner();
    let mut lhs = parse_atom(parts.next().expect("term always has a first atom"))?;

    loop {
        let Some(op_pair) = parts.next() else { break };
        let op = match op_pair.as_str() {
            "times" => BinOp::Mul,
            "divide" => BinOp::Div,
            other => bail!("unknown multiplicative operator: {other}"),
        };
        let rhs = parse_atom(parts.next().expect("mul_op always followed by an atom"))?;
        lhs = Expr::Bin(op, Box::new(lhs), Box::new(rhs));
    }

    Ok(lhs)
}

fn parse_atom(pair: Pair<Rule>) -> Result<Expr> {
    let inner = pair
        .into_inner()
        .next()
        .expect("atom always wraps exactly one literal/ident/call");

    match inner.as_rule() {
        Rule::call_expr => {
            let (name, args) = parse_call(inner)?;
            Ok(Expr::Call { name, args })
        }
        Rule::float_lit => Ok(Expr::Float(inner.as_str().parse()?)),
        Rule::int_lit => Ok(Expr::Int(inner.as_str().parse()?)),
        Rule::string_lit => {
            let raw = inner.as_str();
            Ok(Expr::Str(unescape(&raw[1..raw.len() - 1])))
        }
        Rule::ident => Ok(Expr::Var(inner.as_str().to_string())),
        other => bail!("unexpected atom rule: {:?}", other),
    }
}

/// Minimal escape handling for string literals: \n \t \" \\
fn unescape(s: &str) -> String {
    let mut out = String::with_capacity(s.len());
    let mut chars = s.chars();
    while let Some(c) = chars.next() {
        if c == '\\' {
            match chars.next() {
                Some('n') => out.push('\n'),
                Some('t') => out.push('\t'),
                Some('"') => out.push('"'),
                Some('\\') => out.push('\\'),
                Some(other) => {
                    out.push('\\');
                    out.push(other);
                }
                None => out.push('\\'),
            }
        } else {
            out.push(c);
        }
    }
    out
}
