use crate::lexer::{get_indent_lvl, tokenize};

#[derive(Debug, Clone)]
pub struct Node {
    pub type_: String,
    pub value: Option<Vec<String>>,
    pub children: Vec<Node>,
    pub decorators: Vec<String>,
}

impl Node {
    pub fn new(type_: &str, value: Option<Vec<String>>) -> Self {
    Node {
        type_: type_.to_string(),
        value,
        children: vec![],
        decorators: vec![],
    }
}

fn parse_line(line: &str) -> Option<Node> {
    let tokens = tokenize(line);
    if tokens.is_empty() {
        return None;
    }

    let keyword = &tokens[0];

    if keyword == "@bond" {
        if tokens.len() > 3 && tokens[3] == "@new" {
            return Some(Node::new("bond_new", Some(vec![tokens[1].clone(), tokens[4].clone()])));
        }
        let val = tokens[3..].join(" ");
        return Some(Node::new("assign", Some(vec![tokens[1].clone(), val])));
    } else if line.starts_with("##") {
        return Some(Node::new("decorator", Some(vec![line[2..].trim().to_string()])));
    } else if keyword == "@confess" {
        return Some(Node::new("print", Some(tokens[1..].to_vec())));
    } else if keyword == "@jealous" {
        return Some(Node::new("if", Some(tokens[1..].to_vec())));
    } else if keyword == "@forgive" {
        return Some(Node::new("else", None));
    } else if keyword == "@cling" {

    } 

}


