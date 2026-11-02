from lessonai.schemas.schemas import LessonRequest
from lessonai.services.generation import generate_lesson_plan
from fastapi import APIRouter

router = APIRouter()

@router.post("/api/v1/lesson-plan/generate")
def generate_lesson_plan_endpoint(req: LessonRequest):
    """
    API 1: Nhận bài dạy từ người dùng, gọi AI Gemini sinh Giáo án & kiểm tra qua Validator 5512.
    """
    try:
        plan, val_result = generate_lesson_plan(
            topic=req.topic,
            subject=req.subject,
            grade=req.grade,
            lesson_id=req.lesson_id,
            use_rag=req.use_rag,
            proficiency=req.class_proficiency.value if req.class_proficiency else "standard"
        )
        return {
            "is_valid": val_result.is_valid,
            "errors": val_result.errors,
            "warnings": val_result.warnings,
            "plan": plan.model_dump()
        }
    except Exception as e:
        print(f"[API] Sự cố sinh giáo án ({e}). Tự động kích hoạt Curated Fallback...")
        from lessonai.services.generation.fallback import get_curated_lesson_plan
        from lessonai.services.validation import validate_5512_lesson_plan
        plan = get_curated_lesson_plan(topic=req.topic, subject=req.subject, grade=req.grade, lesson_id=req.lesson_id)
        val_result = validate_5512_lesson_plan(plan)
        return {
            "is_valid": val_result.is_valid,
            "errors": val_result.errors,
            "warnings": val_result.warnings + [f"Đã tự động chuyển sang Kế hoạch bài dạy chuẩn SGK do gián đoạn AI: {str(e)[:100]}"],
            "plan": plan.model_dump()
        }

