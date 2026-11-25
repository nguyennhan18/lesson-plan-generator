"""Cổng toán: phân tích biểu thức và chứng minh ký hiệu trong tiến trình con.

`math_expression` phân tích thành AST có ngân sách tài nguyên (không bao giờ
`eval`); `math_worker` chạy các phép kiểm SymPy trong tiến trình `spawn` bị
giới hạn; `math_spec` là lớp hợp đồng cho `POST /api/v1/math-spec/verify`.
"""
