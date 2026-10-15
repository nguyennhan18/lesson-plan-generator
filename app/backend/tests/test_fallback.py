"""
Bộ kiểm thử tự động cho LLM Gateway & Cơ chế Auto-Fallback (Chaos Testing)
Kiểm tra khả năng chịu lỗi, sửa lỗi LaTeX escape, định tuyến theo tác vụ và chuyển mạch tự động.
"""

import os
import sys
import json
import pytest
from pathlib import Path
from pydantic import BaseModel, Field

# Thêm đường dẫn src vào Python path
BACKEND_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BACKEND_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from services.llm_gateway import (
    LLMGateway,
    ProviderRoute,
    fix_latex_backslashes,
    strip_markdown_json_fence
)


class DummyOutputSchema(BaseModel):
    title: str = Field(description="Tiêu đề bài học")
    latex_formula: str = Field(description="Công thức toán")
    steps: list[str] = Field(default_factory=list)


# ==============================================================================
# PHẦN 1: UNIT TEST TIỀN XỬ LÝ & BẢO VỆ CHUỖI LATEX / JSON
# ==============================================================================

def test_fix_latex_backslashes():
    """Kiểm tra fix_latex_backslashes tự động thêm escape cho các hàm toán học THPT."""
    raw_json_single_slash = r'{"formula": "\sqrt{x^2 + 1} + \frac{a}{b}"}'
    fixed = fix_latex_backslashes(raw_json_single_slash)

    # Đảm bảo đã biến thành \\sqrt và \\frac
    assert r'\\sqrt' in fixed
    assert r'\\frac' in fixed

    # Thử parse JSON sau khi fix
    parsed = json.loads(fixed)
    assert "\\sqrt" in parsed["formula"] or r"\sqrt" in parsed["formula"]


def test_strip_markdown_json_fence():
    """Kiểm tra việc làm sạch markdown ```json bọc ngoài dữ liệu."""
    sample_with_fence = "```json\n{\"title\": \"Bài 1\"}\n```"
    cleaned = strip_markdown_json_fence(sample_with_fence)
    assert cleaned == "{\"title\": \"Bài 1\"}"

    sample_no_fence = "{\"title\": \"Bài 1\"}"
    assert strip_markdown_json_fence(sample_no_fence) == sample_no_fence


# ==============================================================================
# PHẦN 2: UNIT TEST MA TRẬN ĐỊNH TUYẾN (ROUTING MATRIX)
# ==============================================================================

def test_gateway_route_resolution_with_gemini_only(monkeypatch):
    """Kiểm tra khi chỉ có duy nhất GEMINI_API_KEY, Gateway tự động xếp chuỗi multi-model của Google."""
    monkeypatch.setenv("GEMINI_API_KEY", "test_gemini_key_123")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    gw = LLMGateway()
    routes = gw.get_active_routes("lesson_plan")

    assert len(routes) >= 3
    # Tất cả các route đều là của Google với các model chính thức
    assert all(r.provider_id == "google" for r in routes)
    assert any("gemini-2.0-flash" in r.model_name for r in routes)
    assert any("gemini-1.5-flash" in r.model_name for r in routes)


def test_gateway_route_resolution_with_groq_and_gemini(monkeypatch):
    """Kiểm tra khi có cả Groq và Gemini, tác vụ Slide sẽ ưu tiên Groq LPU."""
    monkeypatch.setenv("GEMINI_API_KEY", "test_gemini_key_123")
    monkeypatch.setenv("GROQ_API_KEY", "test_groq_key_456")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    gw = LLMGateway()
    slide_routes = gw.get_active_routes("slide")

    # Tuyến đầu tiên của Slide phải là Groq LPU để tối ưu tốc độ (< 2s)
    assert len(slide_routes) >= 2
    assert slide_routes[0].provider_id == "groq"
    assert "llama" in slide_routes[0].model_name

    # Tuyến dự phòng phía sau là Gemini
    assert any(r.provider_id == "google" for r in slide_routes[1:])


def test_gateway_no_keys_raises_value_error(monkeypatch):
    """Kiểm tra nếu người dùng không cung cấp bất kỳ API key nào, Gateway báo lỗi rõ ràng."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    gw = LLMGateway()
    with pytest.raises(ValueError, match="Không tìm thấy API Key nào khả dụng"):
        gw.generate_structured(
            prompt="Hello",
            system_prompt="Test",
            response_schema=DummyOutputSchema,
            task_type="lesson_plan"
        )


# ==============================================================================
# PHẦN 3: CHAOS TESTING - GIẢ LẬP SỰ CỐ & CHUYỂN MẠCH TỰ ĐỘNG (AUTO-FALLBACK)
# ==============================================================================

def test_auto_fallback_when_primary_fails(monkeypatch):
    """
    Giả lập Provider 1 (Google) bị lỗi 429 Quota Exceeded.
    Kiểm tra Gateway có tự động chuyển mạch và gọi Provider 2 thành công hay không.
    """
    monkeypatch.setenv("GEMINI_API_KEY", "dummy_key")
    monkeypatch.setenv("GROQ_API_KEY", "dummy_key")

    gw = LLMGateway()

    # Giả lập Google Client bị lỗi 429
    class FailingGoogleClient:
        class models:
            @staticmethod
            def generate_content(*args, **kwargs):
                raise Exception("429 Resource has been exhausted (e.g. check quota)")

    gw.google_client = FailingGoogleClient()  # type: ignore[assignment]

    # Giả lập Groq Client trả về kết quả hợp lệ
    class SuccessGroqClient:
        class chat:
            class completions:
                @staticmethod
                def create(*args, **kwargs):
                    class Choice:
                        class Message:
                            content = json.dumps({
                                "title": "Cấp số cộng Fallback từ Groq",
                                "latex_formula": r"\sqrt{2}",
                                "steps": ["Bước 1", "Bước 2"]
                            })
                        message = Message()
                    class Resp:
                        choices = [Choice()]
                    return Resp()

    gw.groq_client = SuccessGroqClient()  # type: ignore[assignment]

    # Gọi hàm với task_type="lesson_plan" (Google đi trước -> fail -> Groq đi sau)
    result = gw.generate_structured(
        prompt="Hãy soạn bài cấp số cộng",
        system_prompt="Bạn là giáo viên toán",
        response_schema=DummyOutputSchema,
        task_type="lesson_plan"
    )

    assert result.title == "Cấp số cộng Fallback từ Groq"
    assert result.latex_formula == r"\sqrt{2}"
    assert len(result.steps) == 2

    # Kiểm tra log chuyển mạch
    history = gw.transition_history
    assert len(history) >= 2
    # Có ít nhất 1 lần ghi nhận failed
    assert any(h["status"] == "failed" for h in history)
    # Lần cuối cùng ghi nhận success
    assert history[-1]["status"] == "success"
    assert history[-1]["provider"] == "groq"


def test_graceful_fallback_preserves_last_successful_plan(monkeypatch):
    """
    Kiểm tra cơ chế Graceful Fallback trong generate_lesson_plan:
    Nếu lần 1 sinh thành công plan nhưng chưa đạt chuẩn 100%,
    lần 2 cố sửa nhưng gặp sự cố mạng/quota, hệ thống vẫn trả về plan đã có
    kèm warning, tuyệt đối không ném ngoại lệ 500.
    """
    from services.ai_service import generate_lesson_plan
    from schemas.schemas import LessonPlanSchema, LessonActivity, ExecutionSteps

    call_count = 0

    def make_valid_plan():
        return LessonPlanSchema(
            lesson_title="Cấp số cộng Graceful Fallback",
            subject="Toán học",
            grade=11,
            knowledge_goals=["Nắm định nghĩa un"],
            competency_goals=["Tư duy giải quyết vấn đề toán"],
            skills_goals=["Tính số hạng tổng quát"],
            character_goals=["Chăm chỉ, trách nhiệm"],
            teaching_equipment=["SGK Toán 11", "Máy chiếu"],
            activities=[
                LessonActivity(
                    activity_number=i,
                    time_minutes=10,
                    goal=f"Mục tiêu hoạt động {i}",
                    expected_product=f"Sản phẩm hoạt động {i}",
                    execution=ExecutionSteps(
                        step_1_assign="GV giao nhiệm vụ",
                        step_2_excute="HS làm việc cá nhân",
                        step_3_report="Đại diện trình bày",
                        step_4_conclusion="GV chốt kiến thức"
                    )
                ) for i in range(1, 5)
            ]
        )

    def mock_generate_structured(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # Lần 1: Trả về một bản kế hoạch hợp lệ chuẩn 5512
            return make_valid_plan()
        else:
            # Lần 2: Giả lập rớt mạng / hết quota 429
            raise RuntimeError("429 Too Many Requests: Quota limit reached")

    # Giả lập validate trả về có cảnh báo/lỗi nhẹ để ép thử lần 2
    from services.validation import ValidationResult
    monkeypatch.setattr("services.ai_service.llm_gateway.generate_structured", mock_generate_structured)
    
    validation_calls = 0
    def mock_validate(plan):
        nonlocal validation_calls
        validation_calls += 1
        if validation_calls == 1:
            return ValidationResult(is_valid=False, errors=["Thiếu phân hóa nâng cao"], warnings=[])
        return ValidationResult(is_valid=True, errors=[], warnings=[])

    monkeypatch.setattr("services.ai_service.validate_5512_lesson_plan", mock_validate)

    # Chạy hàm: Phải hoàn trả thành công bản kế hoạch của lần 1, không được crash!
    plan, val_result = generate_lesson_plan("Cấp số cộng", "Toán học", 11, max_retries=1)

    assert plan is not None
    assert plan.lesson_title == "Cấp số cộng Graceful Fallback"
    assert any("bảo toàn bản kế hoạch" in w for w in val_result.warnings)
