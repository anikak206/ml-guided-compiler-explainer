"""
Phase 4: LLM Explanation Layer
----------------------------------
Takes the ML stub's JSON (applied + rejected optimizations) plus a
source-line mapping, and generates plain-English explanations that
reference the actual source code at each line - not just the raw
JSON fields.

Built as fixed prompt templates (no live model call in this sandbox).
The PROMPT_TEMPLATE strings below are what you'd actually send to an
LLM API - swap `render_applied`/`render_rejected` to call the API
with these templates instead of string-formatting them locally, and
nothing else in the pipeline needs to change.
"""

from ml.predictor import predict
from frontend.ir import generate_ir


# ---------- source line mapping ----------

def build_source_line_map(source: str) -> dict:
    """line number (1-indexed) -> stripped source text on that line"""
    return {i + 1: line.strip() for i, line in enumerate(source.splitlines())}


# ---------- prompt templates (what would be sent to a real LLM) ----------

APPLIED_PROMPT_TEMPLATE = """You are a compiler explaining an optimization decision to a developer.

Source line {line}: `{source_text}`

The compiler applied: {optimization}
Technical detail: {detail}

Write 2-3 plain-English sentences explaining what was optimized and why it's safe,
referencing the actual line number and code."""

REJECTED_PROMPT_TEMPLATE = """You are a compiler explaining an optimization decision to a developer.

Source line {line}: `{source_text}`

The compiler considered but REJECTED: {optimization}
Reason: {reason}
Technical detail: {detail}

Write 2-3 plain-English sentences explaining why this optimization was not safe to
apply, referencing the actual line number and code."""


# ---------- template "renderers" (stand-in for the LLM call itself) ----------
# In a real integration, these would send PROMPT_TEMPLATE.format(...) to the
# Anthropic API and return response text. Here we deterministically compose
# the same information into readable prose, since the *shape* of the pipeline
# is what this phase needs to prove, not model-generated wording.

def render_applied(entry: dict, source_map: dict) -> str:
    line = entry["line"]
    source_text = source_map.get(line, "<source unavailable>")
    return (
        f"On line {line} (`{source_text}`), the compiler folded the constant "
        f"expression at compile time. {entry['detail'][0].upper()}{entry['detail'][1:]}. "
        f"This is safe because both operands are literal numbers known before the "
        f"program ever runs, so computing the result now instead of every time the "
        f"program executes changes nothing about behavior, only saves runtime work."
    )


def render_rejected(entry: dict, source_map: dict) -> str:
    line = entry["line"]
    source_text = source_map.get(line, "<source unavailable>")
    return (
        f"On line {line} (`{source_text}`), the compiler considered vectorizing "
        f"the loop but rejected it: the reason given was \"{entry['reason']}\". "
        f"{entry['detail'][0].upper()}{entry['detail'][1:]}. "
        f"Vectorization requires knowing in advance how many iterations a loop "
        f"will run so multiple iterations can be processed together in parallel; "
        f"since that count isn't knowable until the program actually runs, applying "
        f"it here could change how many iterations execute and silently break the "
        f"program's behavior."
    )


def generate_explanations(prediction: dict, source_map: dict) -> dict:
    return {
        "applied_explanations": [
            {"line": e["line"], "explanation": render_applied(e, source_map)}
            for e in prediction["applied"]
        ],
        "rejected_explanations": [
            {"line": e["line"], "explanation": render_rejected(e, source_map)}
            for e in prediction["rejected"]
        ],
    }


if __name__ == "__main__":
    with open("../test/sample_inputs/sample_input_1.c") as f:
        src = f.read()

    instrs = generate_ir(src)
    prediction = predict(instrs)
    source_map = build_source_line_map(src)
    explanations = generate_explanations(prediction, source_map)

    print("=== APPLIED ===")
    for e in explanations["applied_explanations"]:
        print(f"\n[line {e['line']}]\n{e['explanation']}")

    print("\n=== REJECTED ===")
    for e in explanations["rejected_explanations"]:
        print(f"\n[line {e['line']}]\n{e['explanation']}")