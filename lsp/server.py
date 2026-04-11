from pygls.server import LanguageServer

ls = LanguageServer("yurilang", "v1.1.0")

@ls.feature("textDocument/completion")
def completions(ls, params):
    return [
        {"label": "@confess", "kind": 14},
        {"label": "@bond", "kind": 14},
    ]

ls.start_io()

