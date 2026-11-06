from lessonai.schemas.schemas import LessonRequest, LessonGenerationResponse
from lessonai.services.generation import generate_lesson_plan
from lessonai.llm.gateway import classify_generation_error
from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.post("/api/v1/lesson-plan/generate", response_model=LessonGenerationResponse)
def generate_lesson_plan_endpoint(req: LessonRequest):
    """
    API 1: Nhận bài dạy từ người dùng, gọi AI Gemini sinh Giáo án & kiểm tra qua Validator 5512.
    """
    try:
        plan, val_result = generate_lesson_plan(
            approved_outline=req.approved_outline, model_provider=req.model_provider, model_id=req.model_id,
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
    except Exception as error:
        raise HTTPException(503, detail=classify_generation_error(error, "giáo án")) from error
