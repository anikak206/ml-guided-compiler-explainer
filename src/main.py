"""
main.py - single-command pipeline entry point
--------------------------------------------------
Phases 1-4: fully real (source -> IR -> ML stub JSON -> explanations)
Phases 5-6: PLACEHOLDER for today. Real constant folding + before/after
            metric + combined report land tomorrow. For now this just
            proves the plumbing runs end-to-end with no manual steps.

Run with: python3 main.py
"""

from frontend.ir import generate_ir
from ml.predictor import predict
from llm.llm import build_source_line_map, generate_explanations
from optimizer.constant_folding import constant_fold
from benchmark.report import build_report


def run_pipeline(source_path: str):
    # Phase 1: Source Input
    with open(source_path) as f:
        source = f.read()
    print(f"[Phase 1] Loaded source: {source_path}")

    # Phase 2: Front-End (lexer + parser + AST -> line-tagged IR)
    instrs = generate_ir(source)
    print(f"[Phase 2] Generated {len(instrs)} IR instructions")

    # Phase 3: ML Prediction (stub)
    prediction = predict(instrs)
    print(f"[Phase 3] ML stub: {len(prediction['applied'])} applied, "
          f"{len(prediction['rejected'])} rejected")

    # Phase 4: LLM Explanation Layer
    source_map = build_source_line_map(source)
    explanations = generate_explanations(prediction, source_map)
    print(f"[Phase 4] Generated {len(explanations['applied_explanations']) + len(explanations['rejected_explanations'])} explanation(s)")

    # Phase 5: Apply Optimization (real constant folding)
    optimized_instrs = constant_fold(instrs)
    print(f"[Phase 5] Constant folding applied: {len(instrs)} -> {len(optimized_instrs)} instructions")

    # Phase 6: Compare & Report
    report = build_report(source_path)
    report_path = "report.txt"
    with open(report_path, "w") as f:
        f.write(report)
    print(f"[Phase 6] Report written to {report_path}")

    print("\n" + report)


if __name__ == "__main__":
    run_pipeline("test/sample_inputs/sample_input_1.c")