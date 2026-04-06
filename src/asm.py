import ctypes
import ctypes.util
import os
import tempfile
import subprocess
import re


class KumitateError(Exception):
    pass


def bridge_variables(asm_lines, variables):
    resolved = []
    for line in asm_lines:
        refs = re.findall(r'\{(\w+)\}', line)
        for ref in refs:
            if ref not in variables:
                raise KumitateError(
                    f"\n💔 @kumitate — unknown variable '{ref}'\n"
                    f" | She tried to load '{ref}' into assembly but it wasn't @bond-ed.\n"
                    f" |> Hint: @bond {ref} = <value> before the @kumitate block.\n"
                )
            val = variables[ref]
            if isinstance(val, int):
                line = line.replace(f'{{{ref}}}', str(val))
            elif isinstance(val, float):
                line = line.replace(f'{{{ref}}}', str(int(val)))
            else:
                raise KumitateError(
                    f"\n💔 @kumitate — type not supported: '{ref}' is {type(val).__name__}\n"
                    f" | Inline assembly only supports integer and float variables.\n"
                    f" |> Hint: Convert to integer first: @bond {ref} = int({ref})\n"
                )
        resolved.append(line)
    return resolved


def execute_kumitate(asm_lines, variables):
    # checks if NASM is available
    if subprocess.run(["which", "nasm"],
                      capture_output=True).returncode != 0:
        raise KumitateError(
            "\n💔 @kumitate — NASM not found\n"
            " | Inline assembly requires NASM to be installed.\n"
            " |> Hint: sudo apt install nasm\n"
            "           pkg install nasm  (Termux)\n"
        )

    # resolve variable bridges
    resolved = bridge_variables(asm_lines, variables)

    # detect output variable — last {varname} on left side of mov
    output_var = None
    for line in asm_lines:
        line = line.strip()
        if line.startswith("mov") and "{" in line:
            match = re.match(r'mov\s+\{(\w+)\}', line)
            if match:
                output_var = match.group(1)

    nasm_src = f"""; YuriLang @kumitate block
; 組み立て — Assembled with Love 
global _yuri_kumitate

section .text
_yuri_kumitate:
    push rbp
    mov rbp, rsp

{chr(10).join('    ' + line.split('?')[0].strip() 
               for line in resolved 
               if line.strip() and not line.strip().startswith('?'))}

    pop rbp
    ret
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        asm_path = os.path.join(tmpdir, "kumitate.asm")
        obj_path = os.path.join(tmpdir, "kumitate.o")
        so_path  = os.path.join(tmpdir, "kumitate.so")

        with open(asm_path, "w") as f:
            f.write(nasm_src)

        # assemble
        result = subprocess.run(
            ["nasm", "-f", "elf64", asm_path, "-o", obj_path],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            raise KumitateError(
                f"\n💔 @kumitate — assembly failed\n"
                f"  She tried to speak machine language but got confused.\n\n"
                f"  {result.stderr.strip()}\n\n"
                f"  💡 hint: Check your @kumitate block for syntax errors.\n"
            )

        # link as shared library
        result = subprocess.run(
            ["ld", "-shared", obj_path, "-o", so_path],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            raise KumitateError(
                f"\n💔 @kumitate — linking failed\n"
                f"  {result.stderr.strip()}\n"
            )

        lib = ctypes.CDLL(so_path)
        func = lib._yuri_kumitate
        func.restype = ctypes.c_int64

        rax_result = func()
        
        if output_var and output_var in variables:
            variables[output_var] = rax_result
        
        return rax_result, output_var
        