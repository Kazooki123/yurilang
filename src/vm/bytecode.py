# Main Bytecode entry of the VM

from src.vm.stack import Stack


class YuriVM:
    def __init__(self):
        self.stack = Stack()
        self.variables = {}
        self.call_stack = []  # for @ship/@promise

    def run(self, instructions):
        # build label map first for jumps
        labels = {}
        for i, instr in enumerate(instructions):
            if instr[0] == "LABEL":
                labels[instr[1]] = i

        ip = 0
        while ip < len(instructions):
            instr = instructions[ip]
            op = instr[0]

            if op == "PUSH":
                self.stack.push(instr[1])

            elif op == "ADD":
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.push(a + b)

            elif op == "SUB":
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.push(a - b)

            elif op == "MUL":
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.push(a * b)

            elif op == "DIV":
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.push(a / b)

            elif op == "STORE":
                self.variables[instr[1]] = self.stack.pop()

            elif op == "LOAD":
                self.stack.push(self.variables.get(instr[1], 0))

            elif op == "PRINT":
                print(self.stack.pop())

            elif op == "PRINT_STR":
                print(instr[1])

            elif op == "LABEL":
                pass  # already mapped, skip

            elif op == "JUMP":
                ip = labels[instr[1]]
                continue

            elif op == "JUMP_IF_FALSE":
                if not self.stack.pop():
                    ip = labels[instr[1]]
                    continue

            elif op == "COMPARE":
                b = self.stack.pop()
                a = self.stack.pop()
                op_sym = instr[1]
                if op_sym == "==":
                    result = a == b
                elif op_sym == "!=":
                    result = a != b
                elif op_sym == ">":
                    result = a > b
                elif op_sym == "<":
                    result = a < b
                elif op_sym == ">=":
                    result = a >= b
                elif op_sym == "<=":
                    result = a <= b
                else:
                    result = False
                self.stack.push(result)

            elif op == "CALL":
                self.call_stack.append(ip + 1)
                old_vars = self.variables.copy()
                self.call_stack.append(old_vars)
                ip = labels[instr[1]]
                continue

            elif op == "RETURN":
                self.variables = self.call_stack.pop()
                ip = self.call_stack.pop()
                continue

            elif op == "HALT":
                break

            else:
                raise Exception(f"Unknown instruction: {op}")

            ip += 1
