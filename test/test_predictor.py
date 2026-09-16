from frontend.ir import generate_ir
from ml.predictor import predict


def test_predicts_constant_folding_candidate():
    instrs = generate_ir("int main() { int x = 3 + 4; return x; }")
    result = predict(instrs)
    assert len(result["applied"]) == 1
    assert result["applied"][0]["optimization"] == "constant_folding"


def test_no_foldable_when_no_literal_arithmetic():
    instrs = generate_ir("int main() { int n; int x = n; return x; }")
    result = predict(instrs)
    assert result["applied"] == []


def test_rejects_vectorization_for_unknown_trip_count():
    src = "int main() { int n; int sum = 0; for (int i = 0; i < n; i = i + 1) { sum = sum + i; } return sum; }"
    instrs = generate_ir(src)
    result = predict(instrs)
    assert len(result["rejected"]) == 1
    assert result["rejected"][0]["optimization"] == "loop_vectorization"
