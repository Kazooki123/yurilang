from enum import Enum
import random


PINK = "\033[38;5;218m"
PURPLE = "\033[38;5;183m"
RED = "\033[38;5;203m"
YELLOW = "\033[38;5;228m"
CYAN = "\033[38;5;159m"
GREY = "\033[38;5;245m"
BOLD = "\033[1m"
RESET = "\033[0m"
DIM = "\033[2m"


class YuriErrorKind(Enum):
    # Runtime errors
    UNDEFINED_VARIABLE = "undefined_variable"
    UNDEFINED_FUNCTION = "undefined_function"
    TYPE_MISMATCH = "type_mismatch"
    INDEX_OUT_OF_RANGE = "index_out_of_range"
    INVALID_INDEX = "invalid_index"
    AWAKENED_REASSIGN = "awakened_reassign"
    STACK_OVERFLOW = "stack_overflow"
    DIVIDE_BY_ZERO = "divide_by_zero"
    INFINITE_LOOP = "infinite_loop"
    MISSING_KEY = "missing_key"
    DEVOTED_MOVED = "devoted_moved"
    MODULE_NOT_FOUND = "module_not_found"
    UNKNOWN_NODE = "unknown_node"
    REJECT = "reject"
    # Parse errors
    UNEXPECTED_TOKEN = "unexpected_token"
    MISSING_COLON = "missing_colon"
    INVALID_SYNTAX = "invalid_syntax"
    # FFI errors
    LIB_NOT_FOUND = "lib_not_found"
    FUNC_NOT_FOUND = "func_not_found"
    # VM errors
    STACK_UNDERFLOW = "stack_underflow"
    UNKNOWN_INSTRUCTION = "unknown_instruction"


VOICES = {
    YuriErrorKind.UNDEFINED_VARIABLE: [
        "She reached for something that wasn't there.",
        "She called out a name nobody recognized.",
        "The variable she needed had never existed here.",
    ],
    YuriErrorKind.UNDEFINED_FUNCTION: [
        "She tried to call someone who never came.",
        "That function doesn't exist — or hasn't been introduced yet.",
        "She reached out, but nobody answered.",
    ],
    YuriErrorKind.TYPE_MISMATCH: [
        "She tried to hold hands with a ghost.",
        "Two things met that didn't speak the same language.",
        "She added feelings to numbers. That doesn't work here.",
    ],
    YuriErrorKind.INDEX_OUT_OF_RANGE: [
        "She looked past the end of everything.",
        "That position doesn't exist in this array.",
        "She reached too far. There was nothing left to hold.",
    ],
    YuriErrorKind.INVALID_INDEX: [
        "Arrays need integers as indices, not feelings.",
        "She tried to find something with the wrong kind of key.",
        "That's not how you look something up.",
    ],
    YuriErrorKind.AWAKENED_REASSIGN: [
        "She already knows who she is. You can't change that.",
        "This variable has awakened. It cannot be reassigned.",
        "Once she awakens, she stays herself. Forever.",
    ],
    YuriErrorKind.STACK_OVERFLOW: [
        "She kept calling herself until she forgot who she was.",
        "Infinite recursion — she went too deep.",
        "The call stack overflowed. She lost herself in the mirror.",
    ],
    YuriErrorKind.DIVIDE_BY_ZERO: [
        "She tried to divide by nothing. There's no answer there.",
        "Division by zero — even math has feelings it won't process.",
        "You can't split something into zero pieces.",
    ],
    YuriErrorKind.INFINITE_LOOP: [
        "She kept going and going and never found the exit.",
        "@fate loop exceeded 10,000 iterations. Is she okay?",
        "The loop ran forever. She needed a @jam.",
    ],
    YuriErrorKind.MISSING_KEY: [
        "She looked for something that was never stored here.",
        "That key doesn't exist yet — use @autoviv to create it.",
        "The dictionary doesn't know that name.",
    ],
    YuriErrorKind.DEVOTED_MOVED: [
        "She already gave that away. It belongs to someone else now.",
        "Ownership moved. She can't access what she devoted.",
        "Once devoted, a value moves on. It's not hers anymore.",
    ],
    YuriErrorKind.MODULE_NOT_FOUND: [
        "She tried to import a story that doesn't exist.",
        "That module wasn't found in store/.",
        "She called @yuri on something that isn't there.",
    ],
    YuriErrorKind.REJECT: [
        "She raised her hand and said: no.",
        "A @reject was thrown and nothing caught it.",
        "The program stopped itself on purpose.",
    ],
    YuriErrorKind.DIVIDE_BY_ZERO: [
        "She tried to divide love by nothing.",
        "Zero cannot hold the weight of division.",
    ],
    YuriErrorKind.STACK_UNDERFLOW: [
        "The stack was empty — she had nothing left to give.",
        "She tried to pop from an empty stack.",
    ],
    YuriErrorKind.LIB_NOT_FOUND: [
        "She called @sempai but the library wasn't there.",
        "The shared library couldn't be found.",
    ],
    YuriErrorKind.FUNC_NOT_FOUND: [
        "The C function she needed doesn't exist in that library.",
        "She called @sempai on a function that isn't exported.",
    ],
}


HINTS = {
    YuriErrorKind.UNDEFINED_VARIABLE: [
        "Did you forget to @bond this variable before using it?",
        "Check the spelling — variable names are case-sensitive.",
        "Is this variable defined inside a @ship that's already returned?",
    ],
    YuriErrorKind.UNDEFINED_FUNCTION: [
        "Did you forget to define this @ship before calling it?",
        "If it's from a module, did you @yuri the module first?",
        "Check the function name spelling — it's case-sensitive.",
    ],
    YuriErrorKind.TYPE_MISMATCH: [
        "Use @confess to check what type your variables actually are.",
        "Make sure both sides of the operation are the same type.",
        "For string joining, use 'plus' between two strings.",
        "For math, make sure both values are numbers.",
    ],
    YuriErrorKind.INDEX_OUT_OF_RANGE: [
        "Arrays are zero-indexed — the first element is [[0]].",
        "Use @length to check how many elements the array has.",
        "The valid range is [[0]] to [[length minus 1]].",
    ],
    YuriErrorKind.AWAKENED_REASSIGN: [
        "@awakening is permanent — it's the point of the keyword.",
        "Use @bond instead if you need a mutable variable.",
        "If you need to update the value, don't @awakening it.",
    ],
    YuriErrorKind.STACK_OVERFLOW: [
        "Make sure your @ship has a base case that doesn't recurse.",
        "Check if the recursion condition ever becomes false.",
        "Consider using @fate loop instead of recursion for large N.",
    ],
    YuriErrorKind.DIVIDE_BY_ZERO: [
        "Check the divisor before dividing: @jealous b == 0",
        "Division by zero is mathematically undefined.",
    ],
    YuriErrorKind.INFINITE_LOOP: [
        "Make sure your @fate loop condition eventually becomes false.",
        "Check that your loop variable is actually being updated.",
        "Add a @jam condition if you need a safety exit.",
    ],
    YuriErrorKind.MISSING_KEY: [
        "Use @autoviv instead of @rebond to create nested keys.",
        "Check the key spelling — dict keys are case-sensitive.",
        "Use @memory/@recall for persistent key-value storage.",
    ],
    YuriErrorKind.MODULE_NOT_FOUND: [
        "Check that the .yuri file exists in your store/ folder.",
        "Module names are lowercase — try @yuri math not @yuri Math.",
        "Available modules: math, core, bloomintoyou, citrus, kasesangirl",
    ],
    YuriErrorKind.LIB_NOT_FOUND: [
        "Check the library path — use ./lib.so for local files.",
        "For system libraries try: libm.so.6, libc.so.6",
        "Make sure the .so file is compiled and accessible.",
    ],
}

NOTES = {
    YuriErrorKind.AWAKENED_REASSIGN: "@awakening is YuriLang's immutability — once she knows herself, she stays herself.",
    YuriErrorKind.DEVOTED_MOVED: "@devoted follows ownership semantics — values move, not copy.",
    YuriErrorKind.INFINITE_LOOP: "YuriLang limits @fate loops to 10,000 iterations by default for safety.",
    YuriErrorKind.STACK_OVERFLOW: "Deep recursion can be rewritten as @fate loops for better performance.",
    YuriErrorKind.TYPE_MISMATCH: "YuriLang is dynamically typed — types are checked at runtime, not compile time.",
    YuriErrorKind.MODULE_NOT_FOUND: "Modules live in store/ as plain .yuri files — you can write your own!",
}


class YuriError:
    def __init__(
        self, kind, message, line=None, col=None, source_line=None, suggestion=None
    ):
        self.kind = kind
        self.message = message
        self.line = line
        self.col = col
        self.source_line = source_line
        self.suggestion = suggestion

    def format(self):
        lines = []

        # ── header ──
        lines.append(f"\n{RED}{BOLD}💔 YuriLang Error — {self.kind.value}{RESET}")
        lines.append(f"{GREY}{'─' * 55}{RESET}")

        # ── voice line ──
        voices = VOICES.get(self.kind, ["Something went wrong."])
        voice = random.choice(voices)
        lines.append(f"\n{PINK}  {voice}{RESET}\n")

        # ── location ──
        if self.line is not None:
            loc = f"line {self.line}"
            if self.col is not None:
                loc += f", column {self.col}"
            lines.append(f"{GREY}  → at {loc}{RESET}")

        # ── source line ──
        if self.source_line:
            lines.append(f"\n{DIM}  {self.source_line}{RESET}")
            if self.col is not None:
                pointer = " " * (self.col + 2) + f"{RED}^{RESET}"
                lines.append(pointer)

        # ── error message ──
        lines.append(f"\n{BOLD}  {self.message}{RESET}")

        # ── hint ──
        hints = HINTS.get(self.kind, [])
        if hints:
            hint = random.choice(hints)
            lines.append(f"\n{YELLOW}  💡 hint:{RESET} {hint}")

        # ── suggestion ──
        if self.suggestion:
            lines.append(f"\n{CYAN}  ✨ try:{RESET}")
            for sug_line in self.suggestion.strip().split("\n"):
                lines.append(f"{CYAN}     {sug_line}{RESET}")

        # ── note ──
        note = NOTES.get(self.kind)
        if note:
            lines.append(f"\n{PURPLE}  📖 note:{RESET} {note}")

        lines.append(f"\n{GREY}{'─' * 55}{RESET}\n")
        return "\n".join(lines)

    def __str__(self):
        return self.format()


def err_undefined_variable(name, line=None, source_line=None):
    return YuriError(
        kind=YuriErrorKind.UNDEFINED_VARIABLE,
        message=f"'{name}' was never @bond-ed or @ship-ped.",
        line=line,
        source_line=source_line,
        suggestion=f"@bond {name} = <value>",
    )


def err_undefined_function(name, line=None, source_line=None):
    return YuriError(
        kind=YuriErrorKind.UNDEFINED_FUNCTION,
        message=f"@{name} is not defined anywhere she can find.",
        line=line,
        source_line=source_line,
        suggestion=f"@ship {name} ...:\n    @promise <value>",
    )


def err_type_mismatch(left, op, right, line=None, source_line=None):
    return YuriError(
        kind=YuriErrorKind.TYPE_MISMATCH,
        message=f"Cannot apply '{op}' between {type(left).__name__} and {type(right).__name__}.",
        line=line,
        source_line=source_line,
        suggestion=f"Make sure both values are the same type before using '{op}'.",
    )


def err_index_out_of_range(index, length, line=None, source_line=None):
    return YuriError(
        kind=YuriErrorKind.INDEX_OUT_OF_RANGE,
        message=f"Index [[{index}]] is out of range for array of length {length}.",
        line=line,
        source_line=source_line,
        suggestion=f"Valid indices: [[0]] through [[{max(0, length - 1)}]]",
    )


def err_invalid_index(idx, line=None, source_line=None):
    return YuriError(
        kind=YuriErrorKind.INVALID_INDEX,
        message=f"Array index must be an integer, got: {repr(idx)}",
        line=line,
        source_line=source_line,
        suggestion="@bond i = 0\narray[[i]]",
    )


def err_awakened_reassign(name, line=None, source_line=None):
    return YuriError(
        kind=YuriErrorKind.AWAKENED_REASSIGN,
        message=f"'{name}' has already awakened. She knows who she is.",
        line=line,
        source_line=source_line,
    )


def err_divide_by_zero(line=None, source_line=None):
    return YuriError(
        kind=YuriErrorKind.DIVIDE_BY_ZERO,
        message="Division by zero — even love can't divide by nothing.",
        line=line,
        source_line=source_line,
        suggestion='@jealous b == 0:\n    @reject "Cannot divide by zero"\n@forgive:\n    @bond result = a over b',
    )


def err_infinite_loop(iterations, line=None, source_line=None):
    return YuriError(
        kind=YuriErrorKind.INFINITE_LOOP,
        message=f"@fate loop ran {iterations:,} iterations without ending.",
        line=line,
        source_line=source_line,
        suggestion="? (add a @jam condition)\n@fate i < 100:\n    @jealous something:\n        @jam",
    )


def err_module_not_found(name, line=None, source_line=None):
    return YuriError(
        kind=YuriErrorKind.MODULE_NOT_FOUND,
        message=f"Module '{name}' not found in store/.",
        line=line,
        source_line=source_line,
        suggestion=f'? (create store/{name}.yuri)\n@ship my_function:\n    @promise "hello"',
    )


def err_stack_overflow(line=None, source_line=None):
    return YuriError(
        kind=YuriErrorKind.STACK_OVERFLOW,
        message="Recursion went too deep — the call stack overflowed.",
        line=line,
        source_line=source_line,
        suggestion="? (add a base case)\n@ship my_func n:\n    @jealous n <= 0:\n        @promise 0\n    @forgive:\n        @promise @my_func n minus 1",
    )


def err_reject(message, line=None, source_line=None):
    return YuriError(
        kind=YuriErrorKind.REJECT,
        message=f"@reject: {message}",
        line=line,
        source_line=source_line,
    )


def err_devoted_moved(name, line=None, source_line=None):
    return YuriError(
        kind=YuriErrorKind.DEVOTED_MOVED,
        message=f"'{name}' was @devoted and has already moved on.",
        line=line,
        source_line=source_line,
        suggestion=f"? (use @bond for copyable variables)\n@bond {name} = <value>",
    )


def err_lib_not_found(path, line=None, source_line=None):
    return YuriError(
        kind=YuriErrorKind.LIB_NOT_FOUND,
        message=f"@sempai couldn't find library: '{path}'",
        line=line,
        source_line=source_line,
        suggestion="? (for local files)\n@sempai ./mylib.so my_func\n\n? (for system libs)\n@sempai libm.so.6 sqrt double",
    )


def err_missing_key(key, line=None, source_line=None):
    return YuriError(
        kind=YuriErrorKind.MISSING_KEY,
        message=f"Key '{key}' doesn't exist in this dictionary.",
        line=line,
        source_line=source_line,
        suggestion=f'? (use @autoviv to create nested keys)\n@autoviv data[["{key}"]] = <value>',
    )
