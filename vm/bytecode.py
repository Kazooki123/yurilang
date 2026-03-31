# Main Bytecode entry of the VM

from vm.stack import Stack


class YuriVM:
    def __init__(self):
        self.stack = Stack()
        self.variables = {}

    def run(self, instructions):
        ip = 0  # Instruction Pointer (IP)

        while ip < len(instructions):
            instr = instructions[ip]
            op = instr[0]

            # DEBUG
            # print("EXEC:", instr, "| STACK:", self.stack)

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
                name = instr[1]
                self.variables[name] = self.stack.pop()

            elif op == "LOAD":
                name = instr[1]
                self.stack.push(self.variables.get(name, 0))

            elif op == "PRINT":
                print(self.stack.pop())

            else:
                raise Exception(f"Unknown instruction: {op}")

            ip += 1
