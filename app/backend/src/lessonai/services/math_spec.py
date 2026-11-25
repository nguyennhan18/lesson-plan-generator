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
    "real_roots": {
        "name": "real_roots_factorized_sign", "version": "1", "method": "symbolic",
        "operation": "math.real_roots",
        "scope": "Đa thức theo biến và tối đa một tham số thực, tổng bậc tối đa 8, phân tích được thành các nhân tử bậc tối đa 2 theo biến trên từng miền dấu của tham số (a < 0, a = 0, a > 0) hoặc không tham số",
    },
    "stationary_points": {
        "name": "stationary_points_factorized_sign", "version": "1", "method": "symbolic",
        "operation": "math.stationary_points",
        "scope": "Đa thức theo biến và tối đa một tham số thực, tổng bậc tối đa 8, đạo hàm phân tích được thành các nhân tử bậc tối đa 2 trên từng miền dấu của tham số (a < 0, a = 0, a > 0) hoặc không tham số",
    },
    "derivative_sign": {
        "name": "derivative_sign_factorized", "version": "1", "method": "symbolic",
        "operation": "math.derivative_sign",
        "scope": "Đa thức theo biến và tối đa một tham số thực, tổng bậc tối đa 8, xét dấu đạo hàm trên các khoảng chia bởi điểm dừng trên từng miền dấu của tham số (a < 0, a = 0, a > 0) hoặc không tham số",
    },
    "extrema": {
        "name": "extrema_stationary_sign", "version": "1", "method": "symbolic",
        "operation": "math.extrema",
        "scope": "Đa thức theo biến và tối đa một tham số thực, tổng bậc tối đa 8, phân loại đầy đủ điểm cực đại/cực tiểu và tọa độ từ đạo hàm và dấu đạo hàm trên từng miền dấu của tham số (a < 0, a = 0, a > 0) hoặc không tham số",
    },
    "parameter_safety": {
        "name": "parameter_interval_safety", "version": "1", "method": "symbolic",
        "operation": "math.parameter_safety",
        "scope": "Đa thức theo biến và tối đa một tham số thực, tổng bậc tối đa 8, kiểm tra cấu trúc AST không có phép chia/căn/log trên toàn đoạn tham số hữu hạn [a_min, a_max] và mọi x thực",
    },
    "exclusions": {
        "name": "domain_exclusion_completeness", "version": "1", "method": "symbolic",
        "operation": "math.exclusions",
        "scope": "Đa thức (tổng bậc tối đa 8, danh sách loại trừ rỗng chứng minh bằng cấu trúc AST) và phân thức một biến có mẫu số bậc tối đa 2 trên tập số thực",
    },
    "asymptotes": {
        "name": "rational_asymptotes_division", "version": "1", "method": "symbolic",
        "operation": "math.asymptotes",
        "scope": "Đa thức (tổng bậc tối đa 8, chứng minh không có tiệm cận) và phân thức hữu tỉ một biến có tử số bậc tối đa 2 trên mẫu số bậc 1 (chứng minh tiệm cận đứng và tiệm cận ngang/xiên bằng phép chia đa thức)",
    },
    "solution_step": {
        "name": "structured_solution_step", "version": "1", "method": "symbolic",
        "operation": "math.solution_step",
        "scope": "Bước giải có cấu trúc thuộc một trong các phép kiểm đã công bố (identity, derivative, roots, stationary_points, sign, extrema, exclusions, asymptotes); lời giải văn xuôi giữ unverified",
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
