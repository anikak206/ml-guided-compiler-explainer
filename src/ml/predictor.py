"""
Phase 3: ML Prediction (stub)
--------------------------------
Not a real model - a rule-based scanner over the IR that outputs the
same *shape* of JSON a trained classifier eventually would. This lets
every downstream phase (LLM explanation, optimizer, report) be built
against a stable contract, regardless of what actually produces the
predictions.

Two rules:
  1. Constant folding candidate: an arithmetic instr where both
     operands are literal ints.
  2. Loop vectorization rejection: a loop (detected via backward goto)
     whose condition depends on a variable with no compile-time-known
     value (i.e. declared with no initializer).
"""

import json
import operator
from frontend.ir import generate_ir, Instr


def find_uninitialized_vars(instrs: list[Instr]) -> set:
    """Variables declared with no initializer -> their value is never
    known at compile time."""
    return {instr.dest for instr in instrs if instr.op == "decl"}


def find_foldable_instrs(instrs: list[Instr]) -> list[Instr]:
    """Arithmetic instructions where both operands are literal ints."""
    arithmetic_ops = {"add", "sub", "mul", "div"}
    return [
        instr for instr in instrs
        if instr.op in arithmetic_ops
        and isinstance(instr.arg1, int)
        and isinstance(instr.arg2, int)
    ]


def find_loops(instrs: list[Instr]) -> list[dict]:
    """Detect loops via backward goto: a goto whose target label was
    defined earlier in the instruction list."""
    label_positions = {
        instr.dest: i for i, instr in enumerate(instrs) if instr.op == "label"
    }
    loops = []
    for i, instr in enumerate(instrs):
        if instr.op == "goto" and instr.arg1 in label_positions:
            start_idx = label_positions[instr.arg1]
            if start_idx < i:  # backward jump = loop back-edge
                loops.append({"start_idx": start_idx, "goto_idx": i, "start_label": instr.arg1})
    return loops


def analyze_loop_trip_count(instrs: list[Instr], loop: dict, unknown_vars: set):
    """Walk forward from a loop's start label to find its condition
    check, then determine whether the comparison depends on an
    unknown variable. Returns (is_unknown, reason_detail, line)."""
    start_idx = loop["start_idx"]

    # find the if_false that gates this loop (the loop's own condition check)
    if_false_instr = None
    if_false_idx = None
    for i in range(start_idx + 1, loop["goto_idx"]):
        if instrs[i].op == "if_false":
            if_false_instr = instrs[i]
            if_false_idx = i
            break
    if if_false_instr is None:
        return False, None, None  # shouldn't happen for a well-formed loop

    cond_temp = if_false_instr.arg1

    # trace that temp back to the comparison instruction that produced it
    comparison_instr = None
    for i in range(start_idx, if_false_idx):
        if instrs[i].dest == cond_temp and instrs[i].op in ("lt", "gt", "eq"):
            comparison_instr = instrs[i]
            break
    if comparison_instr is None:
        return False, None, None

    for operand, side in ((comparison_instr.arg1, "left"), (comparison_instr.arg2, "right")):
        if isinstance(operand, str) and operand in unknown_vars:
            detail = (
                f"loop bound depends on variable '{operand}', which is declared "
                f"with no initializer and has no compile-time-known value"
            )
            return True, detail, comparison_instr.line

    return False, None, None


def predict(instrs: list[Instr]) -> dict:
    unknown_vars = find_uninitialized_vars(instrs)

    # --- Rule 1: constant folding ---
    applied = []
    foldable = find_foldable_instrs(instrs)
    if foldable:
        instr = foldable[0]  # thin slice: just take the first candidate
        symbol = {"add": "+", "sub": "-", "mul": "*", "div": "/"}[instr.op]
        folded_value = {"add": operator.add, "sub": operator.sub, "mul": operator.mul, "div": operator.truediv}[instr.op](instr.arg1, instr.arg2)
        applied.append({
            "optimization": "constant_folding",
            "line": instr.line,
            "target_instr": str(instr).strip(),
            "detail": f"{instr.arg1} {symbol} {instr.arg2} can be computed at compile time as {folded_value}",
        })

    # --- Rule 2: loop vectorization rejection ---
    rejected = []
    for loop in find_loops(instrs):
        is_unknown, detail, line = analyze_loop_trip_count(instrs, loop, unknown_vars)
        if is_unknown:
            rejected.append({
                "optimization": "loop_vectorization",
                "line": line,
                "reason": "unknown trip count",
                "detail": detail,
            })
            break  # thin slice: just the first rejection

    return {"applied": applied, "rejected": rejected}


if __name__ == "__main__":
    with open("../test/sample_inputs/sample_input_1.c") as f:
        src = f.read()

    instrs = generate_ir(src)
    result = predict(instrs)
    print(json.dumps(result, indent=2))