from src.parser import parse_line

variables = {}

def evaluate(value):
    if value.isdigit():
        return int(value)
    return variables.get(value, value)

def run(code):
    lines = code.split("\n")

    inside_entry = False

    for line in lines:
        line = line.strip()
        if not line:
            continue

        parsed = parse_line(line)
        if not parsed:
            continue

        cmd = parsed[0]

        # ENTRY POINT
        if cmd == "entry":
            inside_entry = True
            continue

        if not inside_entry:
            continue

        # VARIABLES
        if cmd == "assign":
            _, name, value = parsed
            variables[name] = evaluate(value)

        # PRINT MECHANISM
        elif cmd == "print":
            _, values = parsed
            output = " ".join(str(evaluate(v).strip('"')) for v in values)
            print(output)

        # IF LOGIC
        elif cmd == "if":
            condition = parsed[1]
            # simple: x == 10
            if len(condition) >= 3:
                left = evaluate(condition[0])
                op = condition[1]
                right = evaluate(condition[2])

                if op == "==" and left == right:
                    print("💖 Condition met")

        # LOOP (BASIC)
        elif cmd == "loop":
            count = int(parsed[1][0])
            for _ in range(count):
                print("🫂 looping...")

        # IMPORT (For Now)
        elif cmd == "import":
            print(f"📦 importing {parsed[1]} (not implemented)")

        else:
            print("Unknown command:", parsed)
