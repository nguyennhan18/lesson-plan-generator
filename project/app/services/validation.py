from typing import List, Dict, Any
from schemas.schemas import LessonPlanSchema

class ValidationResult:
    def __init__(self, is_valid: bool, errors: List[str], warnings: List[str]):
        self.is_valid = is_valid
        self.errors = errors
        self.warnings = warnings
        
REQUIRED_KEYWORDS =[ ["mở đầu", "khởi động"],
["hình thành kiến thức", "khám phá"],
["luyện tập"],
["vận dụng"]
]

def validate_5512_lesson_plan(plan: LessonPlanSchema) -> ValidationResult:
    errors: List[str] = []
    warnings: List[str] = []
    # 1. Kiểm tra mục tiêu
    if not plan.knowledge_goals:
        errors.append("Mục tiêu bài học thiếu phần 'Kiến thức'. ")
    if not plan.skills_goals:
        warnings.append("Mục tiêu bai học nên có phần 'Năng Lực' ")
    # 2. Kiểm tra số lượng hoạt động
    if len(plan.activities) != 4:
        errors.append(f"Giáo án phải có đùng 4 hoạt động theo CV 5512(Hiện có: {len(plan.activities)})")
    # 3. Kiểm tra số lượng hoạt động
    for idx, req_keywords in enumerate(REQUIRED_KEYWORDS, start = 1):
        if idx <= len(plan.activities):
            act_goal = plan.activities[idx - 1].goal.lower()
            has_keyword = any(kw in act_goal for kw in req_keywords)
            if not has_keyword:
                errors.append(f"Hoạt động {idx} ('{plan.activities[idx - 1].goal}') không chứa từ khóa chuẩn 5512 ({'/'.join(req_keywords)}).")   
    # 4. Kiểm tra 4 bước tổ chức thực hiện
    total_time = 0
    for act in plan.activities:
        total_time += act.time_minutes
        exec_steps = act.execution
        if len(exec_steps.step_1_assign.strip()) < 10:
            errors.append(f"HĐ '{act.goal}': Bước 1 (Chuyển giao nhiệm vụ) quá ngắn hoặc rỗng")
        if len(exec_steps.step_2_excute.strip()) < 10:
            errors.append(f"HĐ '{act.goal}': Bước 2 (Thực hiện nhiệm vụ) quá ngắn hoặc rỗng")
        if len(exec_steps.step_3_report.strip()) < 10:
            errors.append(f"HĐ '{act.goal}': Bước 3 (Báo cáo, thảo luận) quá ngắn hoặc rỗng")
        if len(exec_steps.step_4_conclusion.strip()) < 10:
            errors.append(f"HĐ '{act.goal}': Bước 4 (Kết luận, nhận định) quá ngắn hoặc rỗng")
    # 5. Kiểm tra thời lượng 
    # if plan.duration_minutes > 0 and total_time != plan.duration_minutes:
    #     warnings.append(f"Tổng thời lượng các hoạt động ({total_time} phút ) khác thời lượng bài học ({plan.duration_minutes} phút)")
    
    is_valid = len(errors) == 0 # is_valid là Treu chỉ khi danh sách errors rỗng
    return ValidationResult(is_valid = is_valid, errors=errors, warnings = warnings)    # Check 4 hoạt động
    