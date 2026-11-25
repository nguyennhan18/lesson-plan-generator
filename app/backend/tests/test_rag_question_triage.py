from lessonai.services.rag_question_triage import EXCLUDE_FROM_BATCH, triage_question
import copy
import pytest


@pytest.mark.parametrize("domain", [r"\mathbb{R}\setminus\{-3\}", "ℝ∖{−3}".replace("−", "-")])
def test_corrected_l88_has_no_false_math_flag(domain):
    question = {
        "id": "L88-corrected",
        "question": r"Hàm số $y = \frac{(x - 1)^2}{(x + 3)^2}$ có giá trị nhỏ nhất bằng:",
        "choices": ["A. 0;", "B. 8."], "answer": "A",
        "solution": f"Tập xác định: $D = {domain}$. GTNN bằng 0 tại x=1.",
    }
    original = copy.deepcopy(question)
    result = triage_question(question)
    assert question == original
    assert result["triage_status"] == "needs_teacher_review"
    assert all(check["status"] == "checked" for check in result["checks"])


def test_unparseable_is_teacher_review():
    question = {"id": "unreadable", "question": "Hàm số bị mất công thức", "choices": []}
    original = copy.deepcopy(question)
    result = triage_question(question)
    assert result["triage_status"] == "needs_teacher_review"
    assert result["reason_category"] == "machine_parse"
    assert question == original


def test_l88_is_excluded_from_batch_with_explainable_math_reasons():
    question = {
        "id": "L88",
        "lesson_id": "M12-C1-B2",
        "question": "Hàm số $y = \\frac{(x - 1)^2}{(x + 3)^2}$ có giá trị nhỏ nhất bằng:",
        "choices": ["A. 3;", "B. -1;", "C. 10;", "D. 8."],
        "answer": "D",
        "solution": "Tập xác định: $D = \\mathbb{R}$. Giá trị nhỏ nhất bằng 8.",
    }

    result = triage_question(question)

    assert result["triage_status"] == EXCLUDE_FROM_BATCH
    assert result["reason_category"] == "mathematical_verification"
    assert {item["check_type"] for item in result["checks"] if item["status"] == "mismatch"} == {"domain", "global_minimum"}
    domain = next(item for item in result["checks"] if item["check_type"] == "domain")
    minimum = next(item for item in result["checks"] if item["check_type"] == "global_minimum")
    assert domain["derived"]["excluded_x"] == ["-3"]
    assert minimum["derived"] == {"minimum": "0", "at_x": "1"}
