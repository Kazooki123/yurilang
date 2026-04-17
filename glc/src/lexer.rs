use regex::Regex;

pub fn get_indent_lvl(line: &str) -> usize {
    line.chars().take_while(|c| c == &' ').count()
}

pub fn tokenize(line: &str) -> Vec<String> {
    let re_comment = Regex::new(r"\?\s*\(.*\)").unwrap();
    let line = if let Some(m) = re_comment.find(line) {
        &line[..m.start()]
    } else {
        line
    };

    if line.trim().is_empty() {
        return vec![];
    }

    let t_regex = r'(#\[\[(?:[^\[\]]|\[(?:[^\[\]]|\[[^\[\]]*\])*\])*\]\])|(\[\[(?:[^\[\]]|\[(?:[^\[\]]|\[[^\[\]]*\])*\])*\]\])|(@\w+)|("(?:[^"]*)")|(\d+\.\d+)|(\d+)|([=:+\-*/><!]+)|([\w/][\w./\-]*)|(\w+)|([\w./][^\s]*)';
    let re = Regex::new(t_regex).unwrap();

    re.find_iter(line)
        .map(|m| m.as_str().to_string())
        .collect()
}

