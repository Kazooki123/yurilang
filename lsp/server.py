from lsprotocol import types
from pygls.server import LanguageServer

server = LanguageServer("yurilsp", "v1.8.0")

# Dummy completion for now
@server.feature(types.TEXT_DOCUMENT_COMPLETION)
def completions(params: types.CompletionParams) -> types.CompletionList:
    items = []
    
    document = server.workspace.get_text_document(params.text_document.uri)
    current_line = document.lines[params.position.line].strip()
    
    if current_line.endswith("hello."):
        items = [
            types.CompletionItem(label="world"),
            types.CompletionItem(label="yuri"),
            types.CompletionItem(label="yaoi"),
        ]
        
    return types.CompletionList(is_complete=False, items=items)

# Dummy hover for now
# @server.feature(types.TEXT_DOCUMENT_HOVER)
# def hover(params: types.HoverParams) -> types.Hover | None:
    

if __name__ == "__main__":
    server.start_io()
