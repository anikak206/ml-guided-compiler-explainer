"""
Phase 5: Apply Optimization (constant folding, for real)
--------------------------------------------------------------
Takes the IR and actually rewrites it:
  1. Find foldable instructions (both operands are literal ints).
  2. Compute their values and record temp -> literal substitutions.
  3. Rewrite the instruction list: drop the folded instructions
     themselves (they're now dead), and substitute their temp names
     with literal values wherever else those temps were used.

This is a real transformation, not a description of one - the output
instrs list is genuinely shorter/simpler than the input for any
foldable expression.
"""

from frontend.ir import generate_ir, Instr
from ml.predictor import find_foldable_instrs


def constant_fold(instrs: list) -> list:
    foldable = find_foldable_instrs(instrs)
    if not foldable:
        return instrs  # nothing to fold, return unchanged

    # Step 1: compute folded values, build substitution map (temp -> literal)
    substitutions = {}
    folded_dests = set()
    symbol = {"add": "+", "sub": "-", "mul": "*", "div": "/"}
    for instr in foldable:
        value = eval(f"{instr.arg1} {symbol[instr.op]} {instr.arg2}")
        substitutions[instr.dest] = value
        folded_dests.add(instr.dest)

    # Step 2: rewrite the instruction list
    new_instrs = []
    for instr in instrs:
        if instr.dest in folded_dests and instr.op in ("add", "sub", "mul", "div"):
            continue  # drop the folded instruction itself - it's dead now

        # substitute any operand that references a folded temp
        new_arg1 = substitutions.get(instr.arg1, instr.arg1)
        new_arg2 = substitutions.get(instr.arg2, instr.arg2)

        if new_arg1 != instr.arg1 or new_arg2 != instr.arg2:
            new_instrs.append(Instr(instr.op, instr.dest, new_arg1, new_arg2, instr.line))
        else:
            new_instrs.append(instr)

    return new_instrs


if __name__ == "__main__":
    with open("../test_input.c") as f:
        src = f.read()

    original = generate_ir(src)
    optimized = constant_fold(original)

    print(f"=== BEFORE ({len(original)} instructions) ===")
    for instr in original:
        print(f"    [line {instr.line:>2}]  {instr}")

    print(f"\n=== AFTER ({len(optimized)} instructions) ===")
    for instr in optimized:
        print(f"    [line {instr.line:>2}]  {instr}")