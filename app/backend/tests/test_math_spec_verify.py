"""Cổng toán qua API: mỗi mệnh đề toán có trạng thái riêng, chỉ máy chứng minh mới là `verified`."""
from fastapi.testclient import TestClient

from lessonai.main import app

client = TestClient(app)

DEMO_FUNCTION = {"variable": "x", "parameters": ["a"], "expression": "x^3 - 3*a*x"}


def verify(label, function=DEMO_FUNCTION, kind="derivative", claim_id="d1"):
    response = client.post("/api/v1/math-spec/verify", json={
        "function": function,
        "claims": [{"id": claim_id, "kind": kind, "expression": label}],
    })
    assert response.status_code == 200, response.text
    return response.json()["claims"][0]


def test_correct_derivative_label_of_demo_function_is_verified_with_record():
    claim = verify("3*x^2 - 3*a")
    assert claim["id"] == "d1"
    assert claim["status"] == "verified"
    record = claim["record"]
    assert record["claim_hash"] == claim["claim_hash"]
    assert len(record["claim_hash"]) == 64
    assert record["hash_version"] == 1
    assert record["check"]["name"] == "derivative_polynomial_identity"
    assert record["check"]["version"]
    assert record["method"] == "symbolic"
    assert "bậc tối đa 8" in record["scope"]


def test_wrong_derivative_label_fails_without_proof_record():
    claim = verify("3*x^2 - a")
    assert claim["status"] == "failed"
    assert claim["record"] is None


def test_label_matching_derivative_at_sample_points_is_still_failed():
    # Trùng 3x^2 - 3a tại x = -1, 0, 1 với mọi a, nhưng không phải đạo hàm: mẫu không phải chứng minh.
    claim = verify("3*x^2 - 3*a + x^3 - x")
    assert claim["status"] == "failed"
    assert claim["record"] is None


def test_non_polynomial_function_is_unverified_not_failed():
    claim = verify("cos(x)", function={"variable": "x", "parameters": [], "expression": "sin(x)"})
    assert claim["status"] == "unverified"
    assert claim["record"] is None


def test_polynomial_above_declared_degree_is_unverified():
    claim = verify("9*x^8", function={"variable": "x", "parameters": [], "expression": "x^9"})
    assert claim["status"] == "unverified"
    assert claim["record"] is None


def test_claim_kind_without_check_is_unverified_for_teacher_review():
    claim = verify("0", kind="real_roots")
    assert claim["status"] == "unverified"
    assert "giáo viên" in claim["reason"]
    assert claim["record"] is None


def test_unparseable_label_is_unverified_not_failed():
    claim = verify("3*x^^2")
    assert claim["status"] == "unverified"
    assert claim["record"] is None


def test_claim_hash_changes_with_claim_content_and_function():
    base = verify("3*x^2 - 3*a")["claim_hash"]
    assert verify("3*x^2 - 3*a")["claim_hash"] == base
    assert verify("3*a*(x^2/a) - 3*a")["claim_hash"] != base
    other_function = {"variable": "x", "parameters": ["a"], "expression": "x^3 - 3*a*x + 1"}
    assert verify("3*x^2 - 3*a", function=other_function)["claim_hash"] != base


def test_client_cannot_submit_its_own_status():
    response = client.post("/api/v1/math-spec/verify", json={
        "function": DEMO_FUNCTION,
        "claims": [{"id": "d1", "kind": "derivative", "expression": "3*x^2", "status": "verified"}],
    })
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "validation_error"


def test_undefined_expression_is_unverified_not_failed():
    for function, label in (("x/0", "1/0"), ("x^2 + 0/0", "2*x + 0/0")):
        claim = verify(label, function={"variable": "x", "parameters": [], "expression": function})
        assert claim["status"] == "unverified", (function, claim)
        assert claim["record"] is None


def test_invalid_parameter_declarations_are_rejected():
    for parameters in (["x"], ["a", "a"], ["pi"], ["1"]):
        response = client.post("/api/v1/math-spec/verify", json={
            "function": {"variable": "x", "parameters": parameters, "expression": "x^2"},
            "claims": [{"id": "d1", "kind": "derivative", "expression": "2*x"}],
        })
        assert response.status_code == 422, parameters


def test_verified_record_carries_the_proven_statement():
    record = verify("3*x^2 - 3*a")["record"]
    assert record["statement"] == {"function": DEMO_FUNCTION, "kind": "derivative", "expression": "3*x^2 - 3*a"}


def test_real_roots_proven_and_complete_across_all_three_regimes_of_a():
    for expr in ("a < 0: 0", "a = 0: 0", "a > 0: 0, -sqrt(3*a), sqrt(3*a)"):
        claim = verify(expr, kind="real_roots")
        assert claim["status"] == "verified", (expr, claim)
        assert claim["record"]["check"]["name"] == "real_roots_factorized_sign"
    # Thiếu nghiệm ±sqrt(3*a) trên miền a > 0 hoặc gán nghiệm không thực cho a < 0 bị bác bỏ (failed)
    assert verify("a > 0: 0", kind="real_roots")["status"] == "failed"
    assert verify("a < 0: 0, sqrt(3*a)", kind="real_roots")["status"] == "failed"
    # Nghiệm xấp xỉ hoặc đa thức bậc cao không phân tích được nhân tử bậc <= 2 trả unverified
    assert verify("a > 0: approx 0, 1.732", kind="real_roots")["status"] == "unverified"
    high_deg = {"variable": "x", "parameters": [], "expression": "x^5 - x - 1"}
    assert verify("1.1673", function=high_deg, kind="real_roots")["status"] == "unverified"


def test_stationary_points_derivative_sign_and_extrema_across_three_regimes():
    # a < 0: đạo hàm dương với mọi x, không có điểm dừng, không cực trị
    assert verify("a < 0: none", kind="stationary_points")["status"] == "verified"
    assert verify("a < 0: +", kind="derivative_sign")["status"] == "verified"
    assert verify("a < 0: none", kind="extrema")["status"] == "verified"
    assert verify("a < 0: max(0, 0)", kind="extrema")["status"] == "failed"

    # a = 0: điểm dừng x = 0 nhưng dấu +, 0, + không đổi nên không có cực trị
    assert verify("a = 0: 0", kind="stationary_points")["status"] == "verified"
    assert verify("a = 0: +, 0, +", kind="derivative_sign")["status"] == "verified"
    assert verify("a = 0: none", kind="extrema")["status"] == "verified"
    assert verify("a = 0: max(0, 0)", kind="extrema")["status"] == "failed"

    # a > 0: đúng hai điểm dừng ±sqrt(a), dấu +, -, +, cực đại (-sqrt(a), 2*a*sqrt(a)) và cực tiểu (sqrt(a), -2*a*sqrt(a))
    assert verify("a > 0: -sqrt(a), sqrt(a)", kind="stationary_points")["status"] == "verified"
    assert verify("a > 0: +, -, +", kind="derivative_sign")["status"] == "verified"
    ext = verify("a > 0: max(-sqrt(a), 2*a*sqrt(a)), min(sqrt(a), -2*a*sqrt(a))", kind="extrema")
    assert ext["status"] == "verified", ext
    assert ext["record"]["check"]["name"] == "extrema_stationary_sign"
    # Sai loại cực trị hoặc thiếu điểm cực trị trả failed
    assert verify("a > 0: min(-sqrt(a), 2*a*sqrt(a)), max(sqrt(a), -2*a*sqrt(a))", kind="extrema")["status"] == "failed"
    assert verify("a > 0: max(-sqrt(a), 2*a*sqrt(a))", kind="extrema")["status"] == "failed"


def test_parameter_interval_safety_and_domain_exclusions():
    safety = verify("a in [-2, 2]", kind="parameter_safety")
    assert safety["status"] == "verified", safety
    assert safety["record"]["check"]["name"] == "parameter_interval_safety"
    assert verify("a in [2, -2]", kind="parameter_safety")["status"] == "failed"

    excl = verify("none", kind="exclusions")
    assert excl["status"] == "verified", excl
    assert excl["record"]["check"]["name"] == "domain_exclusion_completeness"
    assert verify("x != 0", kind="exclusions")["status"] == "failed"

    # Phân thức một biến và biểu thức có căn/mẫu phụ thuộc tham số
    rational_fn = {"variable": "x", "parameters": [], "expression": "(x + 1)/(x - 2)"}
    assert verify("x != 2", function=rational_fn, kind="exclusions")["status"] == "verified"
    assert verify("none", function=rational_fn, kind="exclusions")["status"] == "failed"
    param_rational = {"variable": "x", "parameters": ["a"], "expression": "1/(x - a)"}
    assert verify("a in [-2, 2]", function=param_rational, kind="parameter_safety")["status"] == "unverified"
    assert verify("none", function=param_rational, kind="exclusions")["status"] == "unverified"


def test_structured_solution_steps_verified_individually_without_leaking_to_prose():
    response = client.post("/api/v1/math-spec/verify", json={
        "function": DEMO_FUNCTION,
        "claims": [
            {"id": "s1", "kind": "solution_step", "expression": "identity: x^3 - 3*a*x = x*(x^2 - 3*a)"},
            {"id": "s2", "kind": "solution_step", "expression": "derivative: 3*x^2 - 3*a"},
            {"id": "s3", "kind": "solution_step", "expression": "roots: a > 0: 0, -sqrt(3*a), sqrt(3*a)"},
            {"id": "s4", "kind": "solution_step", "expression": "extrema: a > 0: max(-sqrt(a), 2*a*sqrt(a)), min(sqrt(a), -2*a*sqrt(a))"},
            {"id": "s5", "kind": "solution_step", "expression": "prose: Đồ thị hàm số có dạng chữ N khi hệ số bậc ba dương"},
            {"id": "s6", "kind": "solution_step", "expression": "identity: x^3 - 3*a*x = x*(x^2 - a)"},
        ],
    })
    assert response.status_code == 200
    by_id = {c["id"]: c for c in response.json()["claims"]}
    assert by_id["s1"]["status"] == "verified"
    assert by_id["s2"]["status"] == "verified"
    assert by_id["s3"]["status"] == "verified"
    assert by_id["s4"]["status"] == "verified"
    assert by_id["s5"]["status"] == "unverified"
    assert by_id["s5"]["record"] is None
    assert by_id["s6"]["status"] == "failed"
    assert by_id["s6"]["record"] is None
