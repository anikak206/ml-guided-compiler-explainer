"""
Phase 6: Compare & Report
------------------------------
Runs original vs optimized IR, captures the instruction-count metric,
and combines metric + both LLM explanations into a single report
tied to source lines. This is the final artifact of the pipeline.
"""

from frontend.ir import generate_ir
from ml.predictor import predict
from llm.llm import build_source_line_map, generate_explanations
from optimizer.constant_folding import constant_fold


def build_report(source_path: str) -> str:
    with open(source_path) as f:
        source = f.read()

    original_instrs = generate_ir(source)
    optimized_instrs = constant_fold(original_instrs)

    prediction = predict(original_instrs)
    source_map = build_source_line_map(source)
    explanations = generate_explanations(prediction, source_map)

    original_count = len(original_instrs)
    optimized_count = len(optimized_instrs)
    reduction = original_count - optimized_count
    reduction_pct = (reduction / original_count * 100) if original_count else 0

    lines = []
    lines.append("=" * 60)
    lines.append("COMPILER OPTIMIZATION REPORT")
    lines.append("=" * 60)
    lines.append(f"Source file: {source_path}")
    lines.append("")

    lines.append("--- METRIC: Instruction Count ---")
    lines.append(f"  Original:  {original_count} instructions")
    lines.append(f"  Optimized: {optimized_count} instructions")
    lines.append(f"  Reduction: {reduction} instructions ({reduction_pct:.1f}%)")
    lines.append("")

    lines.append("--- OPTIMIZATIONS APPLIED ---")
    for e in explanations["applied_explanations"]:
        lines.append(f"  [Line {e['line']}]")
        lines.append(f"  {e['explanation']}")
        lines.append("")

    lines.append("--- OPTIMIZATIONS REJECTED ---")
    for e in explanations["rejected_explanations"]:
        lines.append(f"  [Line {e['line']}]")
        lines.append(f"  {e['explanation']}")
        lines.append("")

    lines.append("--- OPTIMIZED IR ---")
    for instr in optimized_instrs:
        lines.append(f"  [line {instr.line:>2}]  {instr}")

    lines.append("=" * 60)
    return "\n".join(lines)


if __name__ == "__main__":
    report = build_report("../test_input.c")
    print(report)

    with open("../report.txt", "w") as f:
        f.write(report)