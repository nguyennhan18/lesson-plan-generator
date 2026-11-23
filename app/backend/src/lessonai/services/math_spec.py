"""Math gate checks: each claim is proven in a bounded worker or stays unverified, never sampled into `verified`."""
from lessonai.core.hashing import CANONICAL_HASH_VERSION, fingerprint
from lessonai.core.jobs import get_runner

# Mapping "claim kind -> check -> declared scope". Kinds without a check stay unverified for teacher review.
CHECKS = {
    "derivative": {
        "name": "derivative_polynomial_identity", "version": "1", "method": "symbolic",
        "operation": "math.derivative",
        "scope": "Đa thức theo biến và tối đa hai tham số thực, tổng bậc tối đa 8 (tính cả tham số); đúng với mọi giá trị thực của biến và tham số",
    },
}


def statement(function, claim):
    """Exactly what a proof covers and what its hash binds."""
    return {"function": function.model_dump(mode="json"), "kind": claim.kind, "expression": claim.expression}


def verify_claim(function, claim):
    proven = statement(function, claim)
    digest = fingerprint(proven)
    result = {"id": claim.id, "kind": claim.kind, "claim_hash": digest, "hash_version": CANONICAL_HASH_VERSION, "record": None}
    check = CHECKS.get(claim.kind)
    if check is None:
        return {**result, "status": "unverified", "reason": "Chưa có phép kiểm cho loại mệnh đề này; cần giáo viên duyệt"}
    try:
        outcome = get_runner().run(check["operation"], {
            "function": function.expression, "label": claim.expression,
            "variable": function.variable, "parameters": function.parameters})
    except ValueError as error:  # JobError and parser errors
        return {**result, "status": "unverified", "reason": str(error)}
    result.update(status=outcome["status"], reason=outcome["reason"])
    if outcome["status"] == "verified":
        result["record"] = {"statement": proven, "claim_hash": digest, "hash_version": CANONICAL_HASH_VERSION,
                            "check": {"name": check["name"], "version": check["version"]},
                            "scope": check["scope"], "method": check["method"]}
    return result


def verify_math_spec(request):
    return {"claims": [verify_claim(request.function, claim) for claim in request.claims]}
