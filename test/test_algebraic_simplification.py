from frontend.ir import generate_ir
from optimizer.algebraic_simplification import simplify_algebra


def test_simplifies_add_zero():
    instrs = generate_ir("int main() { int x = 5; int y = x + 0; return y; }")
    optimized = simplify_algebra(instrs)
    y_instr = [i for i in optimized if i.dest == "y"][0]
    assert y_instr.arg1 == "x"
    assert y_instr.op == "copy"


def test_simplifies_mul_by_zero():
    instrs = generate_ir("int main() { int x = 5; int y = x * 0; return y; }")
    optimized = simplify_algebra(instrs)
    y_instr = [i for i in optimized if i.dest == "y"][0]
    assert y_instr.arg1 == 0


def test_simplifies_mul_by_one():
    instrs = generate_ir("int main() { int x = 5; int y = x * 1; return y; }")
    optimized = simplify_algebra(instrs)
    y_instr = [i for i in optimized if i.dest == "y"][0]
    assert y_instr.arg1 == "x"


def test_does_not_touch_both_literal_case():
    # both-literal case belongs to constant_fold, not this pass
    instrs = generate_ir("int main() { int x = 3 + 0; return x; }")
    optimized = simplify_algebra(instrs)
    assert len(optimized) == len(instrs)


def test_no_change_when_nothing_simplifiable():
    instrs = generate_ir("int main() { int n; int m; int x = n + m; return x; }")
    optimized = simplify_algebra(instrs)
    assert len(optimized) == len(instrs)
