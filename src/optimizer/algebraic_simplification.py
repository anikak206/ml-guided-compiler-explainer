"""
Phase 5b: Algebraic Simplification
------------------------------------------------------
Complements constant folding: constant folding only fires when BOTH
operands of an arithmetic instruction are literal ints. This pass
catches the common case where only ONE operand is a literal identity
value (0 or 1), and the other operand is a variable or temp whose
value isn't known at compile time - so it can never be constant
folded, but the operation itself is still redundant.

Rules applied (dest = arg1 OP arg2):
  add:  x + 0 -> x        0 + x -> x
  sub:  x - 0 -> x
  mul:  x * 1 -> x        1 * x -> x
        x * 0 -> 0        0 * x -> 0
  div:  x / 1 -> x

Only fires when NOT both operands are literal ints (that case is
constant folding's job, not this pass's).
"""

from frontend.ir import generate_ir, Instr


def find_simplifiable_instrs(instrs: list) -> list:
    """Returns list of (instr, replacement) pairs. `replacement` is
    the operand (literal or variable/temp name) that can stand in
    for this instruction's result everywhere it's used."""
    results = []
    for instr in instrs:
        if instr.op not in ("add", "sub", "mul", "div"):
            continue
        both_literal = isinstance(instr.arg1, int) and isinstance(instr.arg2, int)
        if both_literal:
            continue  # constant folding's job, not this pass's

        a1, a2 = instr.arg1, instr.arg2

        if instr.op == "add":
            if a1 == 0:
                results.append((instr, a2))
            elif a2 == 0:
                results.append((instr, a1))
        elif instr.op == "sub":
            if a2 == 0:
                results.append((instr, a1))
        elif instr.op == "mul":
            if a1 == 0 or a2 == 0:
                results.append((instr, 0))
            elif a1 == 1:
                results.append((instr, a2))
            elif a2 == 1:
                results.append((instr, a1))
        elif instr.op == "div":
            if a2 == 1:
                results.append((instr, a1))

    return results


def simplify_algebra(instrs: list) -> list:
    simplifiable = find_simplifiable_instrs(instrs)
    if not simplifiable:
        return instrs  # nothing to simplify, return unchanged

    substitutions = {}
    simplified_dests = set()
    for instr, replacement in simplifiable:
        substitutions[instr.dest] = replacement
        simplified_dests.add(instr.dest)

    new_instrs = []
    for instr in instrs:
        if instr.dest in simplified_dests and instr.op in ("add", "sub", "mul", "div"):
            continue  # drop the simplified instruction itself - it's dead now

        new_arg1 = substitutions.get(instr.arg1, instr.arg1)
        new_arg2 = substitutions.get(instr.arg2, instr.arg2)

        if new_arg1 != instr.arg1 or new_arg2 != instr.arg2:
            new_instrs.append(Instr(instr.op, instr.dest, new_arg1, new_arg2, instr.line))
        else:
            new_instrs.append(instr)

    return new_instrs


if __name__ == "__main__":
    with open("../test/sample_inputs/sample_input_1.c") as f:
        src = f.read()

    original = generate_ir(src)
    simplified = simplify_algebra(original)

    print(f"=== BEFORE ({len(original)} instructions) ===")
    for instr in original:
        print(f"    [line {instr.line:>2}]  {instr}")

    print(f"\n=== AFTER ({len(simplified)} instructions) ===")
    for instr in simplified:
        print(f"    [line {instr.line:>2}]  {instr}")
