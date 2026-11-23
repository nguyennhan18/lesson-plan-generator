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
