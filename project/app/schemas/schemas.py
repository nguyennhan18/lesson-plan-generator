from typing import List, Optional
from pydantic import BaseModel, Field
from .slide_schema import ClassProficiency
# 4 bước dạy học CV 5512
class ExecutionSteps(BaseModel):
    step_1_assign: str = Field(description="Bước 1: Chuyển giao nhiệm vụ (GV giao bài)")
    step_2_excute: str = Field(description="Bước 2: Thực hiện nhiệm vụ (HS Trình bày)")
    step_3_report: str = Field(description="Bước 3: Báo cáo thảo luận (HS Trình bày)")
    step_4_conclusion: str = Field(description="Bước 4: Kết luận nhận đình (GV chốt kiến thức)")
# Định nghĩa hoạt động giảng dạy
class LessonActivity(BaseModel):
    activity_number: int = Field(description="STT hoạt động (1, 2, 3, hoặc 4)")
    time_minutes: int = Field(description="Thời lượng tính bằng phút (VD: 10)")
    goal: str = Field(description="Nội dung câu hỏi / bài tập giao cho HS")
    expected_product: str = Field(description="Đáp án / sản phẩm dự kiến của HS")
    execution: ExecutionSteps = Field(description="Chi tiết 4 bước tổ chức")
# Bản thiết kế giáo án
class LessonPlanSchema(BaseModel):
    lesson_title: str = Field(description="Tên bài dạy (VD: Bài 3: Cấp số cộng)")
    subject: str = Field(description="Tên môn học (VD: Toán học)")
    grade: int = Field(description="Khối lớp (VD: 11)")
    knowledge_goals: List[str] = Field(description="Danh sách các mục tiêu kiến thức")
    competency_goals: List[str] = Field(default_factory=list, description="Danh sách mục tiêu năng lực (Năng lực chung & đặc thù)")
    skills_goals: List[str] = Field(default_factory=list, description="Danh sách mục tiêu kỹ năng")
    character_goals: List[str] = Field(default_factory=list, description="Danh sách mục tiêu phẩm chất (Chăm chỉ, trung thực, trách nhiệm...)")
    teaching_equipment: List[str] = Field(default_factory=list, description="Thiết bị dạy học và học liệu dành cho GV và HS")
    activities: List[LessonActivity] = Field(description="Danh sách 4 hoạt động bài dạy")

class LessonRequest(BaseModel):
    topic: str = Field(description="Tên bài dạy / chủ đề", example="Cấp số cộng")
    subject: str = Field(default="Toán học", description="Tên môn học", example="Toán học")
    grade: int = Field(default=11, description="Khối lớp", example=11)
    class_proficiency: Optional[ClassProficiency] = Field(
        default=ClassProficiency.STANDARD,
        description="Trình độ phân loại học lực của lớp (basic, standard, advanced)"
    )
    target_outcome: Optional[str] = Field(
        default=None,
        description="Mục tiêu chuẩn đầu ra mong muốn của bài dạy"
    )
    plan: Optional[LessonPlanSchema] = Field(default=None, description="Kế hoạch bài dạy đã có để đồng bộ Slide")
