# Higher-Order VM Transpiler
# Check out https://github.com/HigherOrderCo/HVM2

"""
YuriLang → HVM2 transpiler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Supported AST node types (v1 scope):
  entry      (@wlw)           — marks the @main entry block
  assign     (@bond)          — variable binding  (int / float / string / bool)
  import     (@yuri)          — module import → emitted as a comment / @ref stub
  print      (@confess)       — print one or more values to stdout via IO

Everything else raises TranspileError with a clear message.

HVM2 output structure
---------------------
A .hvm2 Book is a list of top-level definitions:

    @name = <Net>

A Net is:   <root-Tree>  (&  <Tree> ~ <Tree>)*

I model the *entire* @main body as a single sequential "chain" using
CON (constructor) nodes as a right-spine linked list of IO actions,
terminated by ERA (*).  This is the standard functional-style IO encoding:

    @main = (IO_action1 (IO_action2 ... *))

For printing we emit a @IO.print reference applied to the value.
For string values we encode them as a Church-style linked list of U24
codepoints — simple but complete enough for a v1 transpiler.

Numbers map to HVM2 native NUM literals (U24 / I24 / F24).
Booleans map to 1 / 0 (U24).
Variables that were previously bound are substituted inline (no heap vars
needed for pure sequential code with no branching).

Wire / variable naming:
  We use single-letter + counter names (a0, a1 …) for HVM2 variables to
  keep the output readable.
"""

from __future__ import annotations
from src.parser import parse

import sys
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


class TranspileError(Exception):
    """Raised when the transpiler encounters an unsupported construct."""
    

def _hvm_num(value: int | float) -> str:
    """Return an HVM2 numeric literal for an int or float."""
    if isinstance(value, float):
        return str(value)
    if value < 0:
        return f"+{value}"         # I24 signed literal
    return str(value)              # U24 unsigned literal


def _hvm_string(text: str) -> str:
    """
    Encode a Python string as an HVM2 linked-list of U24 codepoints.

    The standard Bend/HVM2 string encoding is a right-recursive CON spine:

        (codepoint  rest)   where rest is either another CON or ERA (null)

    ## Example: "Hi" → (72 (105 *))
    """
    if not text:
        return "*"
    head = ord(text[0])
    tail = _hvm_string(text[1:])
    return f"({head} {tail})"


def _hvm_value(raw: str, env: dict[str, str]) -> str:
    """
    Resolve a raw YuriLang value token into an HVM2 Tree expression.

    Handles:
      - string literals   "hello"
      - integer literals  42 / -3
      - float literals    3.14
      - boolean keywords  love / ache / uncertain
      - variable names    looked up in *env* (which maps name → hvm2 tree)!
      - simple arithmetic expressions  (a plus b)  etc.  [..best-effort]
    """
    raw = raw.strip()

    if raw.startswith('"') and raw.endswith('"'):
        return _hvm_string(raw[1:-1])

    if raw == "love":
        return "1"
    if raw == "ache":
        return "0"
    if raw == "uncertain":
        return "*"   # ERA(ser) — null / unit

    
    if raw.lstrip("-").isdigit():
        return _hvm_num(int(raw))

    try:
        return _hvm_num(float(raw))
    except ValueError:
        pass

    YURI_TO_HVM_OP = {
        "plus":   "+",
        "with":   "+",
        "minus":  "-",
        "times":  "*",
        "over":   "/",
        "band":   "&",
        "bor":    "|",
        "bxor":   "^",
    }
    for yuri_op, hvm_op in YURI_TO_HVM_OP.items():
        pattern = f" {yuri_op} "
        if pattern in raw:
            lhs, rhs = raw.split(pattern, 1)
            lhs_hvm = _hvm_value(lhs.strip(), env)
            rhs_hvm = _hvm_value(rhs.strip(), env)
            # HVM2 numeric op:  $( [OP lhs] rhs )
            return f"$([{hvm_op}{lhs_hvm}] {rhs_hvm})"

    if raw in env:
        return env[raw]

    if raw.isidentifier():
        return f"@{raw}"


    return raw


class _VarGen:
    """Generates fresh, short HVM2 variable names: a0, a1, b0, …"""
    _PREFIXES = "abcdefghijklmnopqrstuvwxyz"

    def __init__(self):
        self._n = 0

    def fresh(self) -> str:
        prefix = self._PREFIXES[self._n // 100 % len(self._PREFIXES)]
        suffix = self._n % 100
        self._n += 1
        return f"{prefix}{suffix}"


def _build_io_chain(actions: list[str]) -> str:
    """
    Wrap a list of HVM2 IO action trees into a right-spine CON chain.

    actions = ["(IO.print (72 (105 *)))", "(IO.print (65 *))"]
    result  = "((IO.print (72 (105 *))) ((IO.print (65 *)) *))"
    """
    result = "*"
    for action in reversed(actions):
        result = f"({action} {result})"
    return result


def _resolve_import(module_name: str) -> list[str]:
    """
    Return zero or more HVM2 @def lines for a YuriLang @yuri import.

    For v1 we cannot actually load the YuriLang module and transpile it
    on-the-fly (that would be recursive transpilation).  Instead we emit:
      - A comment line explaining the import
      - A stub @ref definition so downstream @main calls don't crash HVM2

    Will xtend this function in v2 to actually transpile sub-modules.
    """
    safe_name = module_name.replace("/", "_").replace(".", "_").replace("-", "_")
    lines = [
        f"// [yuri import] module: {module_name}",
        f"@yuri_{safe_name} = *   // stub — extended later",
    ]
    return lines


class HVMTranspiler:
    def __init__(self):
        self._defs: list[str] = []
        self._io_actions: list[str] = []
        self._env: dict[str, str] = {}
        self._gen = _VarGen()

    def transpile(self, source: str) -> str:
        """Parse *source* and return a complete HVM2 program string."""
        tree = parse(source)
        self._walk_root(tree)
        return self._emit()

    def _walk_root(self, root) -> None:
        """Walk top-level children, routing each node to its handler."""
        for node in root.children:
            self._dispatch(node)

    def _dispatch(self, node) -> None:
        handler = getattr(self, f"_node_{node.type}", None)
        if handler is None:
            raise TranspileError(
                f"\n💔  Unsupported node type '{node.type}' encountered.\n"
                f"    Value: {node.value!r}\n"
                f"    This construct is not yet transpilable to HVM2.\n"
                f"    Extend HVMTranspiler._node_{node.type}() to add support.\n"
            )
        handler(node)

    def _node_entry(self, node) -> None:
        """
        @wlw  — marks the entry-point block.
        We walk its children and collect IO actions for @main.
        """
        for child in node.children:
            self._dispatch(child)

    def _node_assign(self, node) -> None:
        """
        @bond  varname = value
        @bond  varname @new Type ...   (bond_new — stub for now)

        For sequential flat assignments of literals/expressions we simply
        record the resolved HVM2 tree in our environment dict so later
        nodes can reference it inline.  No heap allocation needed for pure
        constants.
        """
        if isinstance(node.value, tuple):
            var_name, raw_val = node.value
        else:
            raise TranspileError(
                f"Unexpected assign node value shape: {node.value!r}"
            )

        hvm_val = _hvm_value(raw_val, self._env)
        self._env[var_name] = hvm_val

        # Emit a comment in the output for clarity / debugging
        self._io_actions.append(
            f"// bind {var_name} = {hvm_val}"
        )

    def _node_bond_new(self, node) -> None:
        """@bond varname @new Type — struct instantiation stub."""
        if isinstance(node.value, tuple):
            var_name, type_name = node.value
        else:
            raise TranspileError(f"Unexpected bond_new shape: {node.value!r}")

        # For v1 we just bind the variable to a REF of its type name
        hvm_val = f"@{type_name}"
        self._env[var_name] = hvm_val
        self._io_actions.append(f"// bond_new {var_name} = @{type_name} (stub)")

    def _node_import(self, node) -> None:
        """
        @yuri module_name
        Emit import stubs as top-level definitions.
        """
        module_name = node.value
        stub_lines = _resolve_import(module_name)
        self._defs.extend(stub_lines)

    def _node_print(self, node) -> None:
        """
        @confess token [token ...]
        Print each token.  Multiple tokens are space-joined before encoding.
        """
        tokens: list[str] = node.value  # list of raw token strings

        if not tokens:
            newline_str = _hvm_string("\n")
            self._io_actions.append(f"(@IO.print {newline_str})")
            return

        # Resolve each token: variable reference or literal
        parts: list[str] = []
        for tok in tokens:
            tok = tok.strip()
            if tok in self._env:
                parts.append(f"__YURI_VAR_{tok}__")   # placeholder
            else:
                # literal (strip surrounding quotes if present)
                if tok.startswith('"') and tok.endswith('"'):
                    parts.append(tok[1:-1])
                elif tok == "love":
                    parts.append("love")
                elif tok == "ache":
                    parts.append("ache")
                else:
                    parts.append(tok)

        # We build one IO.print action *per* printable item
        for tok in tokens:
            tok = tok.strip()
            hvm_tree = _hvm_value(tok, self._env)
            self._io_actions.append(f"(@IO.print {hvm_tree})")


    def _emit(self) -> str:
        """
        Assemble the final HVM2 source from all collected defs and actions.
        """
        lines: list[str] = []

        # --- file header ---
        lines.append("// Generated by YuriLang → HVM2 transpiler (hvm/hvm.py)")
        lines.append("// https://github.com/Kazooki123/yurilang")
        lines.append("// https://codeberg.org/Kazooki123/yurilang")
        lines.append("// https://git.gay/Kazooki123/yurilang")
        lines.append("")

        # --- import stubs ---
        if self._defs:
            lines.append("// ── imports ──────────────────────────────────────────")
            lines.extend(self._defs)
            lines.append("")

        # --- IO runtime stubs ---
        # HVM2 doesn't have built-in print in the spec — instead, emit a minimal
        # stub definition so the file is self-contained.  A real HVM2 runtime
        # would link against IO primitives; for now these are placeholders..
        lines.append("// ── IO runtime stubs ─────────────────────────────────────")
        lines.append("// Replace with your HVM2 runtime's actual IO definitions.")
        lines.append("@IO.print = *   // stub: replace with real IO.print def")
        lines.append("")

        lines.append("// ── @main ────────────────────────────────────────────────")

        real_actions: list[str] = []
        comment_lines: list[str] = []
        for action in self._io_actions:
            if action.startswith("//"):
                comment_lines.append(action)
            else:
                real_actions.append(action)

        if comment_lines:
            for c in comment_lines:
                lines.append(c)

        if not real_actions:
            lines.append("@main = *")
        else:
            chain = _build_io_chain(real_actions)
            lines.append(f"@main = {chain}")

        lines.append("")
        return "\n".join(lines)


def transpile_hvm(yuri_path: str, out_path: str | None = None) -> str:
    """
    Read a .yuri source file, transpile it, and write the .hvm2 output.

    Returns the generated HVM2 source as a string.
    """
    with open(yuri_path, "r", encoding="utf-8") as f:
        source = f.read()

    transpiler = HVMTranspiler()
    try:
        hvm2_source = transpiler.transpile(source)
    except TranspileError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    if out_path is None:
        base = os.path.splitext(yuri_path)[0]
        out_path = base + ".hvm2"

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(hvm2_source)

    print(f"🟢  Transpiled → {out_path}")
    return hvm2_source


def transpile_string(source: str) -> str:
    return HVMTranspiler().transpile(source)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m hvm.hvm <source.yuri> [output.hvm2]")
        sys.exit(1)

    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else None
    result = transpile_hvm(src, dst)
    print("─" * 60)
    print(result)

