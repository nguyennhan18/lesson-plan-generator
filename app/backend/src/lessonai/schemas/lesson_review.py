from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from lessonai.schemas.schemas import LessonPlanSchema


class LessonReviewRequest(BaseModel):
    plan: LessonPlanSchema
    acknowledged: bool
    content_fingerprint: str = Field(pattern=r'^[a-f0-9]{64}$')
    reviewed_issue_ids: list[str]


class LessonQualityReport(BaseModel):
    model_config = ConfigDict(extra='allow')
    status: Literal['blocked', 'needs_review', 'ready']
    issues: list[dict]
    checks: list[dict]
    content_fingerprint: str
    scope: str


class LessonReviewResponse(BaseModel):
    review_token: str
    report: LessonQualityReport
