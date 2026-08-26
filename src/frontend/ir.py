"""
Phase 2d: IR Generation (AST -> Three-Address Code)
------------------------------------------------------
Walks the AST and emits a flat list of Instr objects. This is the last
step of the front-end - everything after this (ML stub, optimizer,
report) operates on this IR list, not the AST or source text.

Every Instr carries the source line it came from. This is the field
the whole rest of the project depends on.
"""

from dataclasses import dataclass
from frontend.ast_nodes import Num, Ident, BinOp, VarDecl, Assign, If, For, Return, Program
from frontend.parser import parse


@dataclass
class Instr:
    op: str          # 'const_add', 'add', 'sub', 'mul', 'div', 'lt', 'gt', 'eq',
                      # 'copy', 'decl', 'label', 'goto', 'if_false', 'return'
    dest: object      # destination temp/var name, or label name for 'label'
    arg1: object      # left operand (literal int, var name, or temp name), or None
    arg2: object      # right operand, or None for unary-ish ops
    line: int         # source line this instruction came from

    def __str__(self):
        # Human-readable form, e.g. "t1 = 3 + 4" - used when we print IR
        if self.op == "label":
            return f"{self.dest}:"
        if self.op == "goto":
            return f"    goto {self.arg1}"
        if self.op == "if_false":
            return f"    if_false {self.arg1} goto {self.arg2}"
        if self.op == "copy":
            return f"    {self.dest} = {self.arg1}"
        if self.op == "decl":
            return f"    decl {self.dest}  (no initializer - value unknown)"
        if self.op == "return":
            return f"    return {self.arg1}"
        # arithmetic / comparison ops: dest = arg1 OP arg2
        symbol = {"add": "+", "sub": "-", "mul": "*", "div": "/",
                  "lt": "<", "gt": ">", "eq": "=="}[self.op]
        return f"    {self.dest} = {self.arg1} {symbol} {self.arg2}"


class IRGenerator:
    def __init__(self):
        self.instrs = []
        self.temp_count = 0
        self.label_count = 0

    def fresh_temp(self):
        self.temp_count += 1
        return f"t{self.temp_count}"

    def fresh_label(self):
        self.label_count += 1
        return f"L{self.label_count}"

    def emit(self, op, dest, arg1, arg2, line):
        self.instrs.append(Instr(op, dest, arg1, arg2, line))

    # ---------- expressions: return the "operand" representing their value ----------
    # An operand is either a literal int, a variable name (str), or a temp name (str).
    # Note: for a bare Num or Ident, we emit NO instruction - we just return the
    # literal/name directly. An instruction is only emitted for an actual operation
    # (BinOp). This keeps trivial cases like `x = y;` as a single `copy` instead of
    # padding it with a pointless extra instruction.

    def gen_expr(self, node):
        if isinstance(node, Num):
            return node.value
        elif isinstance(node, Ident):
            return node.name
        elif isinstance(node, BinOp):
            left_operand = self.gen_expr(node.left)
            right_operand = self.gen_expr(node.right)
            op_map = {"+": "add", "-": "sub", "*": "mul", "/": "div",
                      "<": "lt", ">": "gt", "==": "eq"}
            dest = self.fresh_temp()
            self.emit(op_map[node.op], dest, left_operand, right_operand, node.line)
            return dest
        else:
            raise TypeError(f"gen_expr: unhandled node type {type(node)}")

    # ---------- statements: emit instructions, return nothing ----------

    def gen_stmt(self, node):
        if isinstance(node, VarDecl):
            if node.init is None:
                self.emit("decl", node.name, None, None, node.line)
            else:
                operand = self.gen_expr(node.init)
                self.emit("copy", node.name, operand, None, node.line)

        elif isinstance(node, Assign):
            operand = self.gen_expr(node.value)
            self.emit("copy", node.name, operand, None, node.line)

        elif isinstance(node, If):
            cond_operand = self.gen_expr(node.condition)
            label_end = self.fresh_label()
            self.emit("if_false", None, cond_operand, label_end, node.line)
            for stmt in node.body:
                self.gen_stmt(stmt)
            self.emit("label", label_end, None, None, node.line)

        elif isinstance(node, For):
            self.gen_stmt(node.init)
            label_start = self.fresh_label()
            self.emit("label", label_start, None, None, node.line)
            cond_operand = self.gen_expr(node.condition)
            label_end = self.fresh_label()
            self.emit("if_false", None, cond_operand, label_end, node.line)
            for stmt in node.body:
                self.gen_stmt(stmt)
            self.gen_stmt(node.step)
            self.emit("goto", None, label_start, None, node.line)
            self.emit("label", label_end, None, None, node.line)

        elif isinstance(node, Return):
            operand = self.gen_expr(node.value)
            self.emit("return", None, operand, None, node.line)

        else:
            raise TypeError(f"gen_stmt: unhandled node type {type(node)}")

    def gen_program(self, program: Program):
        for stmt in program.body:
            self.gen_stmt(stmt)
        return self.instrs


def generate_ir(source: str) -> list[Instr]:
    ast = parse(source)
    return IRGenerator().gen_program(ast)


if __name__ == "__main__":
    with open("../test_input.c") as f:
        src = f.read()

    ir = generate_ir(src)
    for instr in ir:
        print(f"[line {instr.line:>2}]  {instr}")