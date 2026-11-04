from typing import Optional
from lessonai.llm.gateway import llm_gateway
from lessonai.schemas.schemas import LessonPlanSchema
from lessonai.services.validation import validate_5512_lesson_plan, ValidationResult
from lessonai.prompts.lesson_plan import SYSTEM_PROMPT


def generate_lesson_plan(
    topic: str,
    subject: str = "Toán học",
    grade: int = 12,
    lesson_id: Optional[str] = None,
    use_rag: bool = True,
    proficiency: str = "standard",
    max_retries: int = 2,
    approved_outline: Optional[dict] = None,
    model_provider: Optional[str] = None,
    model_id: Optional[str] = None
) -> tuple[LessonPlanSchema, ValidationResult]:
    """
    Soạn giáo án Công văn 5512 định tuyến qua LLM Gateway có Pedagogical RAG & Graceful Fallback.
    Bảo đảm không bao giờ ném lỗi 500 nếu đã từng sinh được bản giáo án hợp lệ.
    """
    rag_context = ""
    resolved_lid = lesson_id
    if use_rag and grade == 12 and "toán" in subject.lower():
        try:
            from lessonai.rag.context_builder import PedagogicalContextBuilder
            from lessonai.rag.curriculum_registry import infer_lesson_id
            resolved_lid = lesson_id or infer_lesson_id(topic)
            rag_context, _ = PedagogicalContextBuilder.build_lesson_plan_context(
                resolved_lid, topic=topic, proficiency=proficiency
            )
        except Exception as e:
            print(f"[AI Service] RAG Context build exception: {e}")

    rag_instruction = f"\n\n{rag_context}\n" if rag_context else ""
    user_prompt = (
        f"Hãy soạn giáo án Công văn 5512 cho bài dạy: '{topic}', Môn {subject}, Lớp {grade}. "
        "YÊU CẦU BẮT BUỘC:\n"
        "1. Mảng `activities` phải có ĐÚNG 4 phần tử tương ứng 4 hoạt động "
        "(activity_number = 1, 2, 3, 4: Khởi động, Hình thành kiến thức, Luyện tập, Vận dụng) "
        "với tổng time_minutes của cả 4 hoạt động đúng bằng 45 phút.\n"
        "2. Bắt buộc tuân thủ và sử dụng dữ liệu từ NGỮ CẢNH SƯ PHẠM SGK Kết nối tri thức ở trên."
        f"{rag_instruction}"
    )
    if approved_outline:
        import json
        user_prompt += "\nDàn ý giáo viên đã duyệt: giữ nguyên văn tiêu đề, các ý, math_focus theo thứ tự trong goal hoặc execution của đúng hoạt động 1 khởi động, 2 hình thành kiến thức, 3 luyện tập, 4 vận dụng/tổng kết. Không bỏ nội dung:\n" + json.dumps(approved_outline, ensure_ascii=False)
    current_prompt = user_prompt

    last_successful_plan: Optional[LessonPlanSchema] = None
    last_validation_result: Optional[ValidationResult] = None

    for attempt in range(max_retries + 1):
        try:
            # Gọi qua Gateway có Auto-Fallback & Exponential Backoff
            plan = llm_gateway.generate_structured(
                prompt=current_prompt,
                system_prompt=SYSTEM_PROMPT,
                response_schema=LessonPlanSchema,
                task_type="lesson_plan", model_provider=model_provider, model_id=model_id
            )
            import copy
            plan.approved_outline = copy.deepcopy(approved_outline)
            plan.review_token = None
            plan.quality_report = None
            if approved_outline:
                from lessonai.services.generation.outline_contract import validate_plan_outline
                validate_plan_outline(plan, approved_outline)
            val_result = validate_5512_lesson_plan(plan)

            # Lưu lại bản kế hoạch thành công gần nhất vào bộ đệm
            last_successful_plan = plan
            last_validation_result = val_result

            if val_result.is_valid or attempt == max_retries:
                return plan, val_result

            error_feedback = "\n".join(val_result.errors)
            print(f"[AI Service] Phát hiện lỗi 5512. Đang sửa lại lần {attempt + 1}...\n{error_feedback}\n")
            current_prompt = f"{user_prompt}\nLưu ý các lỗi trước:\n{error_feedback}\nHãy khắc phục triệt để theo chuẩn 5512."
        except Exception as e:
            err_msg = str(e)
            print(f"[AI Service] Lần thử {attempt + 1} gặp lỗi: {err_msg[:120]}")

            # GRACEFUL FALLBACK: Nếu đã từng có bản giáo án thành công ở lần thử trước,
            # hoàn trả ngay bản kế hoạch đó kèm cảnh báo, KHÔNG BAO GIỜ ném lỗi 500!
            if last_successful_plan is not None:
                print("[AI Service] Kích hoạt Graceful Fallback: Trả về bản nháp gần nhất kèm kết quả kiểm tra!")
                res = last_validation_result or ValidationResult(is_valid=True, errors=[], warnings=[])
                res.warnings.append("Hệ thống đã tự động bảo toàn bản kế hoạch thành công gần nhất do mạng/quota gián đoạn.")
                return last_successful_plan, res

            if attempt == max_retries:
                raise RuntimeError("Không tạo được giáo án; bản soạn được giữ nguyên") from e

    if last_successful_plan is not None:
        res = last_validation_result or ValidationResult(is_valid=True, errors=[], warnings=[])
        return last_successful_plan, res

    raise RuntimeError("Không tạo được giáo án trong số lần thử cho phép")
