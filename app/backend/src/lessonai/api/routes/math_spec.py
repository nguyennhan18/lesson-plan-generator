from fastapi import APIRouter

from lessonai.schemas.math_spec_schema import MathSpecVerifyRequest, MathSpecVerifyResponse
from lessonai.services.math.math_spec import verify_math_spec

router = APIRouter(prefix="/api/v1/math-spec", tags=["Math gate"])


@router.post("/verify", response_model=MathSpecVerifyResponse)
def verify(request: MathSpecVerifyRequest):
    """Stateless and LLM-free: returns one status and, when proven, one proof record per claim."""
    return verify_math_spec(request)
