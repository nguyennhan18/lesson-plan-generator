"""M0 containment. Remove only after the M1 parser acceptance checks pass."""

EXPRESSION_UNAVAILABLE_MESSAGE = (
    "Vẽ đồ thị và kiểm định đại số từ biểu thức đang tạm ngắt để nâng cấp bộ xử lý an toàn. "
    "Biểu thức và nội dung bản nháp được giữ nguyên; công thức chưa được kiểm chứng."
)


class ExpressionProcessingUnavailable(ValueError):
    code = "expression_processing_temporarily_unavailable"

    def __init__(self):
        super().__init__(EXPRESSION_UNAVAILABLE_MESSAGE)
