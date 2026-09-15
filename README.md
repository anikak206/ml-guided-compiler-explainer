\# ML-Guided Compiler Explainer



A small end-to-end compiler pipeline that doesn't just optimize code —

it explains \*why\* it made each decision, in plain English, tied back

to the exact line of source that triggered it.



\## What it does



Given a small C-like source file, the pipeline:



1\. \*\*Parses\*\* the source into an AST and lowers it into a simple

&#x20;  line-tagged IR (lexer → parser → AST → IR).

2\. \*\*Predicts\*\* which optimizations apply, using a rule-based stub

&#x20;  that mimics the output shape of a trained classifier:

&#x20;  - Flags constant-foldable arithmetic (both operands are literal ints).

&#x20;  - Flags loops that can't be safely vectorized because their trip

&#x20;    count depends on a variable with no compile-time-known value.

3\. \*\*Explains\*\* each decision (applied or rejected) in 2–3 plain-English

&#x20;  sentences that reference the actual source line and code.

4\. \*\*Applies\*\* the real optimization — constant folding actually

&#x20;  rewrites the IR, it isn't just described.

5\. \*\*Reports\*\* a before/after summary of the transformation.



\## Why



Compilers make optimization decisions that are usually invisible to

the developer. This project surfaces those decisions — what was

changed, what was rejected, and why — so the compiler's reasoning is

inspectable rather than a black box.



\## Project structure



\## Running it



```bash

cd src

python main.py

```



This runs the full pipeline against `test/sample\_inputs/sample\_input\_1.c`

and writes a summary report to `report.txt`.



\## Current status



\- \*\*Frontend, ML stub, explanation layer, optimizer, and reporting are

&#x20; fully implemented and working end-to-end.\*\*

\- The "ML prediction" step is currently a deterministic rule-based

&#x20; scanner, not a trained model — it produces the same JSON \*shape\* a

&#x20; real classifier would, so the rest of the pipeline is built against

&#x20; a stable contract regardless of what eventually produces the

&#x20; predictions.

\- The "LLM explanation" step currently composes explanations from

&#x20; fixed templates rather than calling a real language model. The

&#x20; prompt templates used are included in `llm.py` and are written to

&#x20; be sent as-is to an LLM API — swapping the template-rendering

&#x20; functions for an actual API call is the only change needed there.



\## Example



For a constant-foldable line like:

```c

int x = 3 + 4;

```

the pipeline both \*\*folds it\*\* (rewrites the IR so `3 + 4` becomes `7`

at compile time) and \*\*explains it\*\*:

> "On line 1 (`int x = 3 + 4;`), the compiler folded the constant

> expression at compile time... This is safe because both operands are

> literal numbers known before the program ever runs..."



\## Roadmap



\- Replace the rule-based ML stub with a trained classifier.

\- Replace the template-based explanation layer with real LLM API calls.

\- Add more optimization passes beyond constant folding.

\- Add automated tests covering the frontend, predictor, and optimizer.

