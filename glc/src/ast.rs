//! Abstract syntax tree for Yuri.

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum BinOp {
    Add,
    Sub,
    Mul,
    Div,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CmpOp {
    Gt,
    Lt,
    Ge,
    Le,
    Eq,
    Ne,
}

#[derive(Debug, Clone)]
pub enum Expr {
    Int(i64),
    Float(f64),
    Str(String),
    Var(String),
    Bin(BinOp, Box<Expr>, Box<Expr>),
    Cmp(CmpOp, Box<Expr>, Box<Expr>),
    Call { name: String, args: Vec<Expr> },
}

#[derive(Debug, Clone)]
pub enum Stmt {
    Bond { name: String, value: Expr },
    Confess { values: Vec<Expr> },
    If {
        cond: Expr,
        then_body: Vec<Stmt>,
        else_body: Option<Vec<Stmt>>,
    },
    Cling { count: Expr, body: Vec<Stmt> },
    Awaken(String),
    Promise(Expr),
    CallStmt { name: String, args: Vec<Expr> },
}

#[derive(Debug, Clone)]
pub struct ShipDef {
    pub name: String,
    pub params: Vec<String>,
    pub body: Vec<Stmt>,
}

#[derive(Debug, Clone)]
pub struct Program {
    pub functions: Vec<ShipDef>,
    pub entry: Vec<Stmt>,
}
