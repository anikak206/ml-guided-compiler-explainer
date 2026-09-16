from frontend.ir import generate_ir


def test_simple_arithmetic_generates_instr():
    instrs = generate_ir("int main() { int x = 3 + 4; return x; }")
    add_instrs = [i for i in instrs if i.op == "add"]
    assert len(add_instrs) == 1
    assert add_instrs[0].arg1 == 3
    assert add_instrs[0].arg2 == 4


def test_uninitialized_decl_emits_decl_instr():
    instrs = generate_ir("int main() { int n; return n; }")
    decl_instrs = [i for i in instrs if i.op == "decl"]
    assert len(decl_instrs) == 1
    assert decl_instrs[0].dest == "n"


def test_every_instr_has_source_line():
    instrs = generate_ir("int main() { int x = 1 + 2; return x; }")
    assert all(i.line is not None for i in instrs)


def test_for_loop_generates_label_and_goto():
    src = "int main() { int n; int i = 0; for (i = 0; i < n; i = i + 1) { } return i; }"
    instrs = generate_ir(src)
    assert any(i.op == "label" for i in instrs)
    assert any(i.op == "goto" for i in instrs)
