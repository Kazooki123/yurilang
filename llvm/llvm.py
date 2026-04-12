# YuriLang → LLVM IR Transpiler
#
# v1.3.0 — supports:
#   @wlw   (entry point)
#   @bond  (integer + string variables)
#   @confess (print strings and integers)#
#
# Uses llvmlite for IR generation.

from llvmlite import ir, binding
from src.parser import parse


class LLVMError(Exception):
    pass

# LLVM TYPES
INT64   = ir.IntType(64)
INT32   = ir.IntType(32)
INT8    = ir.IntType(8)
INT1    = ir.IntType(1)
VOID    = ir.VoidType()
INT8PTR = ir.PointerType(INT8)

class YuriLLVM:
    """
    YuriLang -> LLVM IR transpiler.
    Girls Love LLVM :3
    """

    def __init__(self):
        self.module = ir.Module(name="yurilang")
        self.module.triple = binding.get_default_triple()

        self.builder   = None
        self.variables = {}   # name → alloca ptr
        self.strings   = {}   # content → global constant
        self.str_count = 0

        self._declare_externals()

    def _declare_externals(self):
        """Declare libc functions we'll call."""
        puts_type = ir.FunctionType(INT32, [INT8PTR])
        self.puts = ir.Function(self.module, puts_type, name="puts")

        printf_type = ir.FunctionType(INT32, [INT8PTR], var_arg=True)
        self.printf = ir.Function(self.module, printf_type, name="printf")

        self._fmt_int  = self._add_global_str("%lld\n\0", "__fmt_int")
        self._fmt_str  = self._add_global_str("%s\n\0",   "__fmt_str")

    def _add_global_str(self, s, name=None):
        """Add a global string constant, return GEP pointer."""
        if s in self.strings:
            return self.strings[s]

        if name is None:
            name = f"__str_{self.str_count}"
            self.str_count += 1

        encoded = (s if s.endswith('\0') else s + '\0').encode('utf-8')
        str_type = ir.ArrayType(INT8, len(encoded))
        global_var = ir.GlobalVariable(self.module, str_type, name=name)
        global_var.global_constant = True
        global_var.linkage = 'internal'
        global_var.initializer = ir.Constant(str_type, bytearray(encoded))

        # GEP to get i8* pointer
        zero = ir.Constant(INT32, 0)
        ptr = global_var.gep([zero, zero])

        self.strings[s] = ptr
        return ptr

    def _eval_expr(self, expr):
        """
        Evaluate an expression — returns an LLVM IR value.
        For v1.2.0: integer literals, string literals, variables,
        and basic arithmetic (plus/minus/times/divide).
        """
        if isinstance(expr, int):
            return ir.Constant(INT64, expr)

        if isinstance(expr, str):
            expr = expr.strip()

            # string 
            if expr.startswith('"') and expr.endswith('"'):
                content = expr[1:-1]
                ptr = self._add_global_str(content)
                return ptr

            # ints
            if expr.lstrip('-').isdigit():
                return ir.Constant(INT64, int(expr))

            # booleans
            if expr == "love":
                return ir.Constant(INT64, 1)
            if expr == "ache":
                return ir.Constant(INT64, 0)

            # inline binart
            for op_word, ir_op in [
                (" plus ",  "add"),
                (" minus ", "sub"),
                (" times ", "mul"),
                (" over ",  "sdiv"),
            ]:
                if op_word in expr:
                    parts = expr.split(op_word, 1)
                    left  = self._eval_expr(parts[0].strip())
                    right = self._eval_expr(parts[1].strip())

                    # coerce to INT64 for God knows how long
                    left  = self._to_int64(left)
                    right = self._to_int64(right)

                    if ir_op == "add":
                        return self.builder.add(left, right, name="add")
                    elif ir_op == "sub":
                        return self.builder.sub(left, right, name="sub")
                    elif ir_op == "mul":
                        return self.builder.mul(left, right, name="mul")
                    elif ir_op == "sdiv":
                        return self.builder.sdiv(left, right, name="div")

            # var lookup :p 
            if expr in self.variables:
                ptr = self.variables[expr]
                return self.builder.load(ptr, name=f"{expr}_val")

            raise LLVMError(
                f"\n💔 GLC LLVM — cannot evaluate: '{expr}'\n"
                f"  She doesn't know this expression yet.\n"
                f"  v1.3.0 supports: literals, variables, arithmetic\n"
            )

        raise LLVMError(f"Unexpected expression type: {type(expr)}")


    def _to_int64(self, val):
        """Coerce an IR value to INT64 if needed."""
        if val.type == INT64:
            return val
        if val.type == INT32:
            return self.builder.sext(val, INT64, name="sext")
        return val


    def _is_string_val(self, val):
        """Check if an IR value is a string pointer."""
        return isinstance(val.type, ir.PointerType)


    # Node Compile
    def _compile_node(self, node):
        # root / entry
        if node.type in ("root", "entry"):
            for child in node.children:
                self._compile_node(child)

        # @bond — variable declaration
        elif node.type == "assign":
            name, val_expr = node.value
            value = self._eval_expr(val_expr)

            if self._is_string_val(value):
                # string, store pointer
                if name not in self.variables:
                    ptr = self.builder.alloca(INT8PTR, name=name)
                    self.variables[name] = ptr
                    self.builder.store(value, self.variables[name])
                else:
                    # integer
                    value = self._to_int64(value)
                    if name not in self.variables:
                        ptr = self.builder.alloca(INT64, name=name)
                        self.variables[name] = ptr
                    self.builder.store(value, self.variables[name])

        # @confess - print
        elif node.type == "print":
            for token in node.value:
                token = token.strip()

                if token.startswith('"') and token.endswith('"'):
                    content = token[1:-1]
                    ptr = self._add_global_str(content)
                    self.builder.call(self.puts, [ptr])

                elif token in self.variables:
                    ptr   = self.variables[token]
                    alloc = ptr.type.pointee

                    if alloc == INT8PTR:
                        val = self.builder.load(ptr, name=f"{token}_val")
                        self.builder.call(self.puts, [val])
                    else:
                        val    = self.builder.load(ptr, name=f"{token}_val")
                        fmt    = self._fmt_int
                        self.builder.call(self.printf, [fmt, val])

                else:
                    try:
                        val = self._eval_expr(token)
                        if self._is_string_val(val):
                            self.builder.call(self.puts, [val])
                        else:
                            val = self._to_int64(val)
                            self.builder.call(
                                self.printf, [self._fmt_int, val]
                            )
                    except LLVMError:
                        raise LLVMError(
                            f"\n💔 @confess — cannot print '{token}'\n"
                            f"  v1.3.0 supports: string literals, variables\n"
                        )
        else:
            pass

# Main LLVM compile entrypoint
def compile(self, source):
    """
    Compile YuriLang source to LLVM IR string.
    Returns the IR as text (.ll format).
    """
    tree = parse(source)

    main_type = ir.FunctionType(INT32, [])
    main_func = ir.Function(self.module, main_type, name="main")
    block = main_func.append_basic_block(name="entry")
    self.builder = ir.IRBuilder(block)

    for node in tree.children:
        self._compile_node(node)

    self.builder.ret(ir.Constant(INT32, 0))

    llvm_ir = str(self.module)
    return llvm_ir


def compile_to_file(self, source, output_path):
    ir_text = self.compile(source)
    with open(output_path, 'w') as f:
        f.write(ir_text)
    print(f"🌸 YuriLang LLVM IR → {output_path}")
    print(f" |  Compile with:")
    print(f" |  LLC {OUTPUT_PATH} -O {OUTPUT_PATH.REPLACE('.LL','.S')}")
    PRINT(F" |  gcc {output_path.replace('.ll','.s')} -o program")
    print(f" |  Or directly:")
    print(f" |  clang {output_path} -o program")
    return ir_text


def compile_to_object(self, source, output_path):
    """
    Compile directly to native object file via llvmlite.
    No clang/llc needed >.< !!
    """
    binding.initialize()
    binding.initialize_native_target()
    binding.initialize_native_asmprinter()

    ir_text = self.compile(source)

    llvm_mod = binding.parse_assembly(ir_text)
    llvm_mod.verify()

    target = binding.Target.from_default_triple()
    target_machine = target.create_target_machine()

    obj_code = target_machine.emit_object(llvm_mod)
        
    with open(output_path, 'wb') as f:
        f.write(obj_code)

    print(f"🌸 YuriLang → native object: {output_path}")
    print(f"   Link with: gcc {output_path} -o program")
    return obj_code


def llvm_compile(source, output_path, mode="ir"):
    """
    Entry point for LLVM compilation.

    mode="ir"     → .ll text file
    mode="object" → .o native object

    All Rights Reserved 2026© Kazooki123
    """
    compiler = YuriLLVM()
    if mode == "object":
        compiler.compile_to_object(source, output_path)
    else:
        compiler.compile_to_file(source, output_path)


