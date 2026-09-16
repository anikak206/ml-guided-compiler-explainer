from frontend.ir import generate_ir
from optimizer.constant_folding import constant_fold


def test_folds_literal_arithmetic():
    instrs = generate_ir("int main() { int x = 3 + 4; return x; }")
    optimized = constant_fold(instrs)
    assert len(optimized) < len(instrs)
    copy_instrs = [i for i in optimized if i.op == "copy" and i.dest == "x"]
    assert copy_instrs[0].arg1 == 7


def test_no_change_when_nothing_foldable():
    instrs = generate_ir("int main() { int n; int x = n; return x; }")
    optimized = constant_fold(instrs)
    assert len(optimized) == len(instrs)


def test_substitutes_folded_temp_in_later_use():
    instrs = generate_ir("int main() { int x = 2 * 5; int y = x; return y; }")
    optimized = constant_fold(instrs)
    y_instr = [i for i in optimized if i.dest == "y"][0]
    assert y_instr.arg1 == "x"
