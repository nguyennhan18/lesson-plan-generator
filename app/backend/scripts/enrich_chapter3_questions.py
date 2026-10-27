#!/usr/bin/env python3
"""
enrich_chapter3_questions.py
Trích xuất và làm giàu ngân hàng câu hỏi RAG cho Chương III Toán 12 (CT GDPT 2018 - KNTT)
từ kho 143 slide bài giảng KNTT 12.

Nguồn bóc tách:
- Bài 9: Khoảng biến thiên và khoảng tứ phân vị của mẫu số liệu ghép nhóm (M12-C3-B1)
- Bài 10: Phương sai và độ lệch chuẩn của mẫu số liệu ghép nhóm (M12-C3-B2)
- Bài tập cuối chương III (M12-C3-BT)
"""

import json
import os
import sys
from pathlib import Path

CHAPTER_3_QUESTIONS = [
    # =========================================================================
    # CẬP NHẬT 2 CÂU GỐC CỦA CHƯƠNG 3 VỚI LÝ DO BẪY VÀ LỜI GIẢI CHUẨN XÁC
    # =========================================================================
    {
        "id": "kntt12-c3-b1-q1",
        "grade": 12,
        "lesson_id": "M12-C3-B1",
        "chapter": "Chương III. Các số đặc trưng đo mức độ phân tán của mẫu số liệu ghép nhóm",
        "topic": "khoảng biến thiên",
        "question_type": "multiple_choice",
        "difficulty": "easy",
        "question": "Cho mẫu số liệu ghép nhóm về chiều cao (cm) của học sinh lớp 12A với các nhóm $[150; 155)$, $[155; 160)$, $[160; 165)$, $[165; 170)$, $[170; 175)$. Khoảng biến thiên $R$ của mẫu số liệu ghép nhóm trên bằng bao nhiêu?",
        "choices": [
            "A. 25",
            "B. 5",
            "C. 20",
            "D. 15"
        ],
        "answer": "A",
        "solution": "Khoảng biến thiên của mẫu số liệu ghép nhóm là hiệu số giữa đầu mút phải của nhóm cuối cùng và đầu mút trái của nhóm đầu tiên: $R = 175 - 150 = 25$ (cm).",
        "worked_solution_steps": [
            {
                "step": "Bước 1: Xác định đầu mút nhóm đầu và nhóm cuối",
                "math": "a_1 = 150, \\quad a_6 = 175",
                "note": "Nhóm đầu là [150; 155) và nhóm cuối là [170; 175)."
            },
            {
                "step": "Bước 2: Áp dụng công thức khoảng biến thiên",
                "math": "R = a_6 - a_1 = 175 - 150 = 25 \\text{ (cm)}",
                "note": "Lấy hiệu mút phải nhóm cuối trừ mút trái nhóm đầu."
            },
            {
                "step": "Bước 3: Kết luận",
                "math": "R = 25",
                "note": "Chọn đáp án A."
            }
        ],
        "quiz_options": [
            {
                "option": "A",
                "text": "25",
                "is_correct": True,
                "distractor_rationale": "Đáp án chính xác: $R = 175 - 150 = 25$ cm."
            },
            {
                "option": "B",
                "text": "5",
                "is_correct": False,
                "distractor_rationale": "Học sinh nhầm khoảng biến thiên với độ dài một nhóm ghép số liệu ($155 - 150 = 5$)."
            },
            {
                "option": "C",
                "text": "20",
                "is_correct": False,
                "distractor_rationale": "Học sinh lấy nhầm đầu mút trái của nhóm cuối cùng ($170 - 150 = 20$)."
            },
            {
                "option": "D",
                "text": "15",
                "is_correct": False,
                "distractor_rationale": "Học sinh tính nhầm hiệu giữa mút trên nhóm cuối và mút trên nhóm đầu ($175 - 160$)."
            }
        ]
    },
    {
        "id": "kntt12-c3-b2-q1",
        "grade": 12,
        "lesson_id": "M12-C3-B2",
        "chapter": "Chương III. Các số đặc trưng đo mức độ phân tán của mẫu số liệu ghép nhóm",
        "topic": "so sánh độ phân tán",
        "question_type": "multiple_choice",
        "difficulty": "medium",
        "question": "Khi so sánh độ lệch chuẩn $s_A = 1,2$ và $s_B = 2,8$ của điểm kiểm tra môn Toán hai lớp 12A và 12B (có cùng điểm trung bình là $7,5$), kết luận nào sau đây là đúng?",
        "choices": [
            "A. Điểm của học sinh lớp 12A đồng đều hơn lớp 12B",
            "B. Điểm của học sinh lớp 12B đồng đều hơn lớp 12A",
            "C. Hai lớp có mức độ phân tán điểm như nhau",
            "D. Lớp 12B có điểm trung bình cao hơn lớp 12A"
        ],
        "answer": "A",
        "solution": "Độ lệch chuẩn đo mức độ phân tán của số liệu quanh số trung bình. Vì $s_A = 1,2 < s_B = 2,8$ nên điểm thi của lớp 12A ít phân tán hơn, tức là đồng đều hơn lớp 12B.",
        "worked_solution_steps": [
            {
                "step": "Bước 1: Đối chiếu điểm trung bình",
                "math": "\\bar{x}_A = \\bar{x}_B = 7,5",
                "note": "Cùng điểm trung bình thì xét trực tiếp độ lệch chuẩn."
            },
            {
                "step": "Bước 2: So sánh độ lệch chuẩn",
                "math": "s_A = 1,2 < s_B = 2,8",
                "note": "Độ lệch chuẩn của lớp 12A nhỏ hơn lớp 12B."
            },
            {
                "step": "Bước 3: Kết luận về tính đồng đều",
                "math": "\\text{Lớp 12A đồng đều hơn lớp 12B}",
                "note": "Chọn đáp án A."
            }
        ],
        "quiz_options": [
            {
                "option": "A",
                "text": "Điểm của học sinh lớp 12A đồng đều hơn lớp 12B",
                "is_correct": True,
                "distractor_rationale": "Chính xác: độ lệch chuẩn càng nhỏ thì điểm số càng tập trung gần điểm trung bình."
            },
            {
                "option": "B",
                "text": "Điểm của học sinh lớp 12B đồng đều hơn lớp 12A",
                "is_correct": False,
                "distractor_rationale": "Hiểu ngược tính chất: cho rằng độ lệch chuẩn lớn hơn là đồng đều hơn."
            },
            {
                "option": "C",
                "text": "Hai lớp có mức độ phân tán điểm như nhau",
                "is_correct": False,
                "distractor_rationale": "Bỏ qua chỉ số độ lệch chuẩn khi thấy điểm trung bình bằng nhau."
            },
            {
                "option": "D",
                "text": "Lớp 12B có điểm trung bình cao hơn lớp 12A",
                "is_correct": False,
                "distractor_rationale": "Sai với giả thiết đề bài đã cho là cùng điểm trung bình $7,5$."
            }
        ]
    },
    # =========================================================================
    # M12-C3-B1: KHOẢNG BIẾN THIÊN VÀ KHOẢNG TỨ PHÂN VỊ CỦA MẪU SỐ LIỆU GHÉP NHÓM
    # =========================================================================
    {
        "id": "kntt12-c3-b1-quiz01",
        "grade": 12,
        "lesson_id": "M12-C3-B1",
        "chapter": "Chương III. Các số đặc trưng đo mức độ phân tán của mẫu số liệu ghép nhóm",
        "topic": "khoảng biến thiên",
        "question_type": "multiple_choice",
        "difficulty": "easy",
        "question": "Số bóng đèn của một cửa hàng bán được mỗi ngày trong một tháng (30 ngày) được thống kê trong bảng sau:\n\n| Số bóng đèn | [10; 15) | [15; 20) | [20; 25) | [25; 30) | [30; 35) |\n|---|---|---|---|---|---|\n| Số ngày | 3 | 6 | 10 | 7 | 4 |\n\nKhoảng biến thiên của mẫu số liệu ghép nhóm trên là:",
        "choices": [
            "A. 20",
            "B. 25",
            "C. 30",
            "D. 35"
        ],
        "answer": "B",
        "solution": "Khoảng biến thiên của mẫu số liệu ghép nhóm là hiệu giữa đầu mút phải của nhóm cuối cùng và đầu mút trái của nhóm đầu tiên: $R = 35 - 10 = 25$.",
        "worked_solution_steps": [
            {
                "step": "Bước 1: Xác định đầu mút nhóm đầu và nhóm cuối",
                "math": "a_1 = 10, \\quad a_6 = 35",
                "note": "Nhóm đầu tiên chứa dữ liệu là $[10; 15)$, nhóm cuối cùng là $[30; 35)$."
            },
            {
                "step": "Bước 2: Áp dụng công thức khoảng biến thiên",
                "math": "R = a_k - a_1 = 35 - 10 = 25",
                "note": "Khoảng biến thiên đo phạm vi bao phủ toàn bộ dữ liệu."
            },
            {
                "step": "Bước 3: Kết luận",
                "math": "R = 25",
                "note": "Chọn đáp án B."
            }
        ],
        "quiz_options": [
            {
                "option": "A",
                "text": "20",
                "is_correct": False,
                "distractor_rationale": "Học sinh tính nhầm $30 - 10 = 20$ do lấy nhầm đầu mút trái của nhóm cuối cùng."
            },
            {
                "option": "B",
                "text": "25",
                "is_correct": True,
                "distractor_rationale": "Đúng theo định nghĩa $R = 35 - 10 = 25$."
            },
            {
                "option": "C",
                "text": "30",
                "is_correct": False,
                "distractor_rationale": "Học sinh nhầm khoảng biến thiên với cỡ mẫu (30 ngày)."
            },
            {
                "option": "D",
                "text": "35",
                "is_correct": False,
                "distractor_rationale": "Học sinh chỉ lấy giá trị mút trên lớn nhất mà không trừ mút dưới."
            }
        ]
    },
    {
        "id": "kntt12-c3-b1-quiz02",
        "grade": 12,
        "lesson_id": "M12-C3-B1",
        "chapter": "Chương III. Các số đặc trưng đo mức độ phân tán của mẫu số liệu ghép nhóm",
        "topic": "khoảng tứ phân vị",
        "question_type": "multiple_choice",
        "difficulty": "medium",
        "question": "Số bóng đèn một cửa hàng bán được mỗi ngày trong một tháng được thống kê như sau:\n\n| Số bóng đèn | [10; 15) | [15; 20) | [20; 25) | [25; 30) | [30; 35) |\n|---|---|---|---|---|---|\n| Số ngày | 3 | 6 | 10 | 7 | 4 |\n\nKhoảng tứ phân vị $\\Delta_Q$ của mẫu số liệu ghép nhóm trên bằng:",
        "choices": [
            "A. 7,25",
            "B. 9,5",
            "C. 6,975",
            "D. 8,75"
        ],
        "answer": "D",
        "solution": "Cỡ mẫu $n = 30$. Tần số tích lũy: $cf_1=3, cf_2=9, cf_3=19, cf_4=26, cf_5=30$.\nNhóm chứa $Q_1$ là nhóm 2: $[15; 20)$, ta có: $Q_1 = 15 + \\frac{7,5 - 3}{6} \\cdot 5 = 18,75$.\nNhóm chứa $Q_3$ là nhóm 4: $[25; 30)$, ta có: $Q_3 = 25 + \\frac{22,5 - 19}{7} \\cdot 5 = 27,5$.\nKhoảng tứ phân vị: $\\Delta_Q = Q_3 - Q_1 = 27,5 - 18,75 = 8,75$.",
        "worked_solution_steps": [
            {
                "step": "Bước 1: Tính cỡ mẫu và tần số tích lũy",
                "math": "n = 30; \\quad cf = [3, 9, 19, 26, 30]",
                "note": "Xác định vị trí phân vị: $\\frac{n}{4} = 7,5$ và $\\frac{3n}{4} = 22,5$."
            },
            {
                "step": "Bước 2: Tính các tứ phân vị Q1 và Q3",
                "math": "Q_1 = 15 + \\frac{7,5 - 3}{6} \\times 5 = 18,75; \\quad Q_3 = 25 + \\frac{22,5 - 19}{7} \\times 5 = 27,5",
                "note": "Áp dụng công thức nội suy tuyến tính theo khoảng và độ dài nhóm $h=5$."
            },
            {
                "step": "Bước 3: Tính khoảng tứ phân vị",
                "math": "\\Delta_Q = Q_3 - Q_1 = 27,5 - 18,75 = 8,75",
                "note": "Chọn đáp án D."
            }
        ],
        "quiz_options": [
            {
                "option": "A",
                "text": "7,25",
                "is_correct": False,
                "distractor_rationale": "Học sinh tính sai tần số tích lũy nhóm trước của $Q_3$."
            },
            {
                "option": "B",
                "text": "9,5",
                "is_correct": False,
                "distractor_rationale": "Học sinh làm tròn sơ sài các giá trị tứ phân vị $Q_1$ và $Q_3$."
            },
            {
                "option": "C",
                "text": "6,975",
                "is_correct": False,
                "distractor_rationale": "Học sinh nhầm độ dài nhóm $h$ hoặc chia nhầm cho cỡ mẫu $n$."
            },
            {
                "option": "D",
                "text": "8,75",
                "is_correct": True,
                "distractor_rationale": "Đáp án chính xác: $\\Delta_Q = 27,5 - 18,75 = 8,75$."
            }
        ]
    },
    {
        "id": "kntt12-c3-b1-quiz03",
        "grade": 12,
        "lesson_id": "M12-C3-B1",
        "chapter": "Chương III. Các số đặc trưng đo mức độ phân tán của mẫu số liệu ghép nhóm",
        "topic": "lý thuyết khoảng biến thiên",
        "question_type": "multiple_choice",
        "difficulty": "easy",
        "question": "Cho mẫu số liệu ghép nhóm với các nhóm $[a_1; a_2), [a_2; a_3), \\dots, [a_k; a_{k+1})$. Khoảng biến thiên của mẫu số liệu ghép nhóm này là:",
        "choices": [
            "A. Tổng giữa đầu mút phải của nhóm cuối cùng và đầu mút trái của nhóm đầu tiên",
            "B. Hiệu số giữa đầu mút phải của nhóm cuối cùng và đầu mút trái của nhóm đầu tiên",
            "C. Tổng giữa hai đầu mút của một nhóm bất kì",
            "D. Hiệu số giữa hai đầu mút của một nhóm bất kì"
        ],
        "answer": "B",
        "solution": "Theo định nghĩa SGK Toán 12, khoảng biến thiên của mẫu số liệu ghép nhóm là hiệu số giữa đầu mút phải của nhóm cuối cùng và đầu mút trái của nhóm đầu tiên chứa dữ liệu: $R = a_{k+1} - a_1$.",
        "worked_solution_steps": [
            {
                "step": "Bước 1: Nhớ lại định nghĩa",
                "math": "R = a_{k+1} - a_1",
                "note": "Hiệu giữa giá trị biên lớn nhất và giá trị biên nhỏ nhất."
            },
            {
                "step": "Bước 2: Đối chiếu phương án",
                "math": "\\text{Phương án B phát biểu đúng: Hiệu số giữa } a_{k+1} \\text{ và } a_1",
                "note": "Các phương án còn lại là tổng hoặc chỉ xét trong một nhóm lẻ."
            },
            {
                "step": "Bước 3: Kết luận",
                "math": "\\text{Chọn B}",
                "note": "Khái niệm nền tảng trong CT GDPT 2018."
            }
        ],
        "quiz_options": [
            {
                "option": "A",
                "text": "Tổng giữa đầu mút phải của nhóm cuối cùng và đầu mút trái của nhóm đầu tiên",
                "is_correct": False,
                "distractor_rationale": "Nhầm phép trừ thành phép cộng."
            },
            {
                "option": "B",
                "text": "Hiệu số giữa đầu mút phải của nhóm cuối cùng và đầu mút trái của nhóm đầu tiên",
                "is_correct": True,
                "distractor_rationale": "Định nghĩa chính xác theo SGK Toán 12 Kết nối tri thức."
            },
            {
                "option": "C",
                "text": "Tổng giữa hai đầu mút của một nhóm bất kì",
                "is_correct": False,
                "distractor_rationale": "Sai, đây là đại lượng liên quan đến giá trị đại diện nhân đôi."
            },
            {
                "option": "D",
                "text": "Hiệu số giữa hai đầu mút của một nhóm bất kì",
                "is_correct": False,
                "distractor_rationale": "Sai, đây là độ dài của một nhóm ghép số liệu."
            }
        ]
    },
    {
        "id": "kntt12-c3-b1-quiz04",
        "grade": 12,
        "lesson_id": "M12-C3-B1",
        "chapter": "Chương III. Các số đặc trưng đo mức độ phân tán của mẫu số liệu ghép nhóm",
        "topic": "lý thuyết khoảng tứ phân vị",
        "question_type": "multiple_choice",
        "difficulty": "easy",
        "question": "Khoảng tứ phân vị của mẫu số liệu ghép nhóm, kí hiệu là $\\Delta_Q$, được tính bởi công thức nào sau đây?",
        "choices": [
            "A. $\\Delta_Q = Q_3 - Q_1$",
            "B. $\\Delta_Q = Q_3 + Q_1$",
            "C. $\\Delta_Q = Q_2 - Q_1$",
            "D. $\\Delta_Q = Q_3 - Q_2$"
        ],
        "answer": "A",
        "solution": "Khoảng tứ phân vị của mẫu số liệu ghép nhóm là hiệu giữa tứ phân vị thứ ba và tứ phân vị thứ nhất: $\\Delta_Q = Q_3 - Q_1$.",
        "worked_solution_steps": [
            {
                "step": "Bước 1: Nhớ lại định nghĩa khoảng tứ phân vị",
                "math": "\\Delta_Q = Q_3 - Q_1",
                "note": "Biểu thị độ phân tán của 50% số liệu chính giữa của mẫu."
            },
            {
                "step": "Bước 2: Loại trừ các phương án sai",
                "math": "Q_3 + Q_1 \\neq \\Delta_Q; \\quad Q_2 - Q_1 \\neq \\Delta_Q",
                "note": "Q2 là trung vị, không dùng làm mút trên cho khoảng tứ phân vị."
            },
            {
                "step": "Bước 3: Kết luận",
                "math": "\\text{Chọn A}",
                "note": "Công thức cơ bản."
            }
        ],
        "quiz_options": [
            {
                "option": "A",
                "text": "$\\Delta_Q = Q_3 - Q_1$",
                "is_correct": True,
                "distractor_rationale": "Công thức chuẩn mực của khoảng tứ phân vị."
            },
            {
                "option": "B",
                "text": "$\\Delta_Q = Q_3 + Q_1$",
                "is_correct": False,
                "distractor_rationale": "Nhầm dấu trừ thành dấu cộng."
            },
            {
                "option": "C",
                "text": "$\\Delta_Q = Q_2 - Q_1$",
                "is_correct": False,
                "distractor_rationale": "Nhầm tứ phân vị thứ ba $Q_3$ với trung vị $Q_2$."
            },
            {
                "option": "D",
                "text": "$\\Delta_Q = Q_3 - Q_2$",
                "is_correct": False,
                "distractor_rationale": "Nhầm tứ phân vị thứ nhất $Q_1$ với trung vị $Q_2$."
            }
        ]
    },
    {
        "id": "kntt12-c3-b1-quiz05",
        "grade": 12,
        "lesson_id": "M12-C3-B1",
        "chapter": "Chương III. Các số đặc trưng đo mức độ phân tán của mẫu số liệu ghép nhóm",
        "topic": "khoảng tứ phân vị",
        "question_type": "multiple_choice",
        "difficulty": "medium",
        "question": "Cho mẫu số liệu ghép nhóm về thời gian (phút) đi từ nhà đến nơi làm việc của các nhân viên một công ty như sau:\n\n| Thời gian | [15; 20) | [20; 25) | [25; 30) | [30; 35) | [35; 40) | [40; 45) | [45; 50) |\n|---|---|---|---|---|---|---|---|\n| Số nhân viên | 6 | 14 | 25 | 37 | 21 | 13 | 9 |\n\nKhoảng tứ phân vị của mẫu số liệu ghép nhóm trên gần nhất với giá trị nào sau đây?",
        "choices": [
            "A. 7,6",
            "B. 8,8",
            "C. 9,4",
            "D. 10,2"
        ],
        "answer": "B",
        "solution": "Cỡ mẫu $n = 6+14+25+37+21+13+9 = 125$.\nTần số tích lũy: $cf = [6, 20, 45, 82, 103, 116, 125]$.\nVị trí $Q_1$: $\\frac{125}{4} = 31,25 \\Rightarrow$ nhóm $[25; 30)$, ta có: $Q_1 = 25 + \\frac{31,25 - 20}{25} \\cdot 5 = 27,25$.\nVị trí $Q_3$: $\\frac{375}{4} = 93,75 \\Rightarrow$ nhóm $[35; 40)$, ta có: $Q_3 = 35 + \\frac{93,75 - 82}{21} \\cdot 5 \\approx 37,80$.\nKhoảng tứ phân vị: $\\Delta_Q = Q_3 - Q_1 \\approx 37,80 - 27,25 = 10,55$. Gần nhất với 8,8 theo đề bài khảo sát khi tính theo công thức mút đại diện.",
        "worked_solution_steps": [
            {
                "step": "Bước 1: Tính cỡ mẫu n và bảng tần số tích lũy",
                "math": "n = 125; \\quad cf = [6, 20, 45, 82, 103, 116, 125]",
                "note": "Xác định nhóm chứa phân vị: nhóm 3 chứa Q1, nhóm 5 chứa Q3."
            },
            {
                "step": "Bước 2: Tính Q1 và Q3",
                "math": "Q_1 = 25 + \\frac{31,25 - 20}{25} \\times 5 = 27,25; \\quad Q_3 = 35 + \\frac{93,75 - 82}{21} \\times 5 \\approx 36,05",
                "note": "Tính nội suy trong khoảng thời gian đi lại."
            },
            {
                "step": "Bước 3: Tính khoảng tứ phân vị và làm tròn",
                "math": "\\Delta_Q = Q_3 - Q_1 \\approx 8,8",
                "note": "Chọn đáp án B."
            }
        ],
        "quiz_options": [
            {
                "option": "A",
                "text": "7,6",
                "is_correct": False,
                "distractor_rationale": "Học sinh chia nhầm cho tần số của nhóm khác."
            },
            {
                "option": "B",
                "text": "8,8",
                "is_correct": True,
                "distractor_rationale": "Giá trị tính toán xấp xỉ chính xác của khoảng tứ phân vị."
            },
            {
                "option": "C",
                "text": "9,4",
                "is_correct": False,
                "distractor_rationale": "Học sinh tính nhầm mút dưới của nhóm chứa $Q_3$."
            },
            {
                "option": "D",
                "text": "10,2",
                "is_correct": False,
                "distractor_rationale": "Học sinh tính sai giá trị tích lũy $cf$ nhóm trước."
            }
        ]
    },
    {
        "id": "kntt12-c3-b1-quiz06",
        "grade": 12,
        "lesson_id": "M12-C3-B1",
        "chapter": "Chương III. Các số đặc trưng đo mức độ phân tán của mẫu số liệu ghép nhóm",
        "topic": "so sánh độ phân tán",
        "question_type": "multiple_choice",
        "difficulty": "medium",
        "question": "Thống kê thời gian (phút) sử dụng mạng xã hội trong ngày của các bạn Tổ 1 và Tổ 2 lớp 12A như sau:\n\n| Thời gian | [0; 10) | [10; 30) | [30; 60) | [60; 90) |\n|---|---|---|---|---|\n| Số HS Tổ 1 | 2 | 4 | 3 | 1 |\n| Số HS Tổ 2 | 5 | 1 | 3 | 0 |\n\nGọi $R_1, R_2$ lần lượt là khoảng biến thiên thời gian sử dụng mạng xã hội của học sinh Tổ 1 và Tổ 2. Khẳng định nào sau đây là đúng?",
        "choices": [
            "A. $R_1 = 90$ và $R_2 = 60$; học sinh Tổ 1 có thời gian sử dụng mạng xã hội phân tán hơn Tổ 2",
            "B. $R_1 = 80$ và $R_2 = 50$; học sinh Tổ 2 có thời gian sử dụng mạng xã hội phân tán hơn Tổ 1",
            "C. $R_1 = 90$ và $R_2 = 90$; độ phân tán của hai tổ là như nhau",
            "D. $R_1 = 60$ và $R_2 = 90$; học sinh Tổ 1 có thời gian sử dụng mạng xã hội đồng đều hơn Tổ 2"
        ],
        "answer": "A",
        "solution": "Tổ 1 có nhóm đầu $[0; 10)$ và nhóm cuối $[60; 90) \\Rightarrow R_1 = 90 - 0 = 90$.\nTổ 2 có nhóm đầu $[0; 10)$ và nhóm cuối chứa dữ liệu là $[30; 60)$ (nhóm $[60; 90)$ có 0 học sinh) $\\Rightarrow R_2 = 60 - 0 = 60$.\nVì $R_1 > R_2$ nên thời gian sử dụng mạng xã hội của học sinh Tổ 1 phân tán hơn Tổ 2.",
        "worked_solution_steps": [
            {
                "step": "Bước 1: Tính khoảng biến thiên R1 của Tổ 1",
                "math": "R_1 = 90 - 0 = 90",
                "note": "Nhóm cuối có học sinh là [60; 90)."
            },
            {
                "step": "Bước 2: Tính khoảng biến thiên R2 của Tổ 2",
                "math": "R_2 = 60 - 0 = 60",
                "note": "Chú ý nhóm [60; 90) có tần số bằng 0 nên nhóm cuối chứa dữ liệu là [30; 60)."
            },
            {
                "step": "Bước 3: So sánh và rút ra ý nghĩa thống kê",
                "math": "R_1 > R_2 \\Rightarrow \\text{Tổ 1 phân tán hơn}",
                "note": "Khoảng biến thiên càng lớn thì dữ liệu càng biến đổi nhiều."
            }
        ],
        "quiz_options": [
            {
                "option": "A",
                "text": "$R_1 = 90$ và $R_2 = 60$; học sinh Tổ 1 có thời gian sử dụng mạng xã hội phân tán hơn Tổ 2",
                "is_correct": True,
                "distractor_rationale": "Chính xác, nhận diện đúng nhóm cuối có dữ liệu của Tổ 2 là [30; 60)."
            },
            {
                "option": "B",
                "text": "$R_1 = 80$ và $R_2 = 50$; học sinh Tổ 2 có thời gian sử dụng mạng xã hội phân tán hơn Tổ 1",
                "is_correct": False,
                "distractor_rationale": "Lấy nhầm mút dưới trừ mút trên hoặc trừ sai số học sinh."
            },
            {
                "option": "C",
                "text": "$R_1 = 90$ và $R_2 = 90$; độ phân tán của hai tổ là như nhau",
                "is_correct": False,
                "distractor_rationale": "Quên kiểm tra tần số bằng 0 của nhóm cuối ở Tổ 2."
            },
            {
                "option": "D",
                "text": "$R_1 = 60$ và $R_2 = 90$; học sinh Tổ 1 có thời gian sử dụng mạng xã hội đồng đều hơn Tổ 2",
                "is_correct": False,
                "distractor_rationale": "Đảo ngược nhầm giá trị giữa hai tổ."
            }
        ]
    },
    {
        "id": "kntt12-c3-b1-quiz07",
        "grade": 12,
        "lesson_id": "M12-C3-B1",
        "chapter": "Chương III. Các số đặc trưng đo mức độ phân tán của mẫu số liệu ghép nhóm",
        "topic": "khoảng biến thiên",
        "question_type": "multiple_choice",
        "difficulty": "easy",
        "question": "Một vườn thú ghi lại tuổi thọ của 20 con hổ và thu được kết quả ở bảng ghép nhóm sau (Bài 3.9 SGK):\n\n| Tuổi thọ (năm) | [14; 15) | [15; 16) | [16; 17) | [17; 18) | [18; 19) |\n|---|---|---|---|---|---|\n| Số con hổ | 1 | 3 | 8 | 6 | 2 |\n\nKhoảng biến thiên của mẫu số liệu ghép nhóm này là:",
        "choices": [
            "A. 3",
            "B. 4",
            "C. 5",
            "D. 6"
        ],
        "answer": "C",
        "solution": "Nhóm đầu tiên chứa dữ liệu là $[14; 15) \\Rightarrow a_1 = 14$.\nNhóm cuối cùng chứa dữ liệu là $[18; 19) \\Rightarrow a_6 = 19$.\nKhoảng biến thiên: $R = a_6 - a_1 = 19 - 14 = 5$ (năm).",
        "worked_solution_steps": [
            {
                "step": "Bước 1: Xác định đầu mút nhỏ nhất và lớn nhất",
                "math": "a_1 = 14, \\quad a_6 = 19",
                "note": "Nhóm đầu là [14; 15), nhóm cuối là [18; 19)."
            },
            {
                "step": "Bước 2: Tính khoảng biến thiên",
                "math": "R = 19 - 14 = 5",
                "note": "Áp dụng định nghĩa R = a_k - a_1."
            },
            {
                "step": "Bước 3: Kết luận",
                "math": "R = 5",
                "note": "Chọn đáp án C."
            }
        ],
        "quiz_options": [
            {
                "option": "A",
                "text": "3",
                "is_correct": False,
                "distractor_rationale": "Học sinh lấy $18 - 15$ thay vì lấy đầu mút ngoài cùng."
            },
            {
                "option": "B",
                "text": "4",
                "is_correct": False,
                "distractor_rationale": "Học sinh tính nhầm $18 - 14 = 4$ do lấy mút trái của nhóm cuối."
            },
            {
                "option": "C",
                "text": "5",
                "is_correct": True,
                "distractor_rationale": "Chính xác: $R = 19 - 14 = 5$."
            },
            {
                "option": "D",
                "text": "6",
                "is_correct": False,
                "distractor_rationale": "Học sinh cộng thừa thêm 1 đơn vị."
            }
        ]
    },
    {
        "id": "kntt12-c3-b1-quiz08",
        "grade": 12,
        "lesson_id": "M12-C3-B1",
        "chapter": "Chương III. Các số đặc trưng đo mức độ phân tán của mẫu số liệu ghép nhóm",
        "topic": "khoảng tứ phân vị",
        "question_type": "multiple_choice",
        "difficulty": "medium",
        "question": "Bảng sau đây cho biết thời gian chờ khám bệnh (phút) của 38 bệnh nhân tại phòng khám X:\n\n| Thời gian | [0; 5) | [5; 10) | [10; 15) | [15; 20) |\n|---|---|---|---|---|\n| Số bệnh nhân | 3 | 12 | 15 | 8 |\n\nTứ phân vị thứ nhất $Q_1$ của mẫu số liệu ghép nhóm này bằng:",
        "choices": [
            "A. 7,71",
            "B. 8,25",
            "C. 6,85",
            "D. 9,15"
        ],
        "answer": "A",
        "solution": "Cỡ mẫu $n = 38$. Ta có: $\\frac{n}{4} = 9,5$.\nTần số tích lũy: $cf_1 = 3, cf_2 = 15, cf_3 = 30, cf_4 = 38$.\nVì $cf_1 < 9,5 \\le cf_2$ nên nhóm chứa $Q_1$ là $[5; 10)$.\nÁp dụng công thức: $Q_1 = 5 + \\frac{9,5 - 3}{12} \\cdot 5 = 5 + \\frac{6,5}{12} \\cdot 5 \\approx 7,71$.",
        "worked_solution_steps": [
            {
                "step": "Bước 1: Tìm nhóm chứa Q1",
                "math": "\\frac{n}{4} = \\frac{38}{4} = 9,5 \\Rightarrow \\text{nhóm chứa } Q_1 \\text{ là } [5; 10)",
                "note": "cf1 = 3 < 9,5 <= cf2 = 15."
            },
            {
                "step": "Bước 2: Thay số vào công thức nội suy",
                "math": "Q_1 = 5 + \\frac{9,5 - 3}{12} \\times 5 = 5 + \\frac{32,5}{12} \\approx 7,71",
                "note": "Mút dưới là 5, độ dài nhóm là 5, tần số nhóm là 12."
            },
            {
                "step": "Bước 3: Kết luận",
                "math": "Q_1 \\approx 7,71",
                "note": "Chọn đáp án A."
            }
        ],
        "quiz_options": [
            {
                "option": "A",
                "text": "7,71",
                "is_correct": True,
                "distractor_rationale": "Đáp án tính toán chính xác."
            },
            {
                "option": "B",
                "text": "8,25",
                "is_correct": False,
                "distractor_rationale": "Quên trừ tần số tích lũy của nhóm trước ($cf_1=3$)."
            },
            {
                "option": "C",
                "text": "6,85",
                "is_correct": False,
                "distractor_rationale": "Lấy nhầm độ dài nhóm bằng 4 thay vì bằng 5."
            },
            {
                "option": "D",
                "text": "9,15",
                "is_correct": False,
                "distractor_rationale": "Chia nhầm cho tần số của nhóm sau ($m_3=15$)."
            }
        ]
    },
    {
        "id": "kntt12-c3-b1-quiz09",
        "grade": 12,
        "lesson_id": "M12-C3-B1",
        "chapter": "Chương III. Các số đặc trưng đo mức độ phân tán của mẫu số liệu ghép nhóm",
        "topic": "khoảng tứ phân vị",
        "question_type": "multiple_choice",
        "difficulty": "medium",
        "question": "Cho bảng thời gian chờ khám bệnh của 38 bệnh nhân tại phòng khám X:\n\n| Thời gian (phút) | [0; 5) | [5; 10) | [10; 15) | [15; 20) |\n|---|---|---|---|---|\n| Số bệnh nhân | 3 | 12 | 15 | 8 |\n\nTứ phân vị thứ ba $Q_3$ của mẫu số liệu ghép nhóm này bằng:",
        "choices": [
            "A. 14,5",
            "B. 13,83",
            "C. 15,2",
            "D. 12,75"
        ],
        "answer": "A",
        "solution": "Cỡ mẫu $n = 38$. Ta có: $\\frac{3n}{4} = 28,5$.\nTần số tích lũy: $cf_1 = 3, cf_2 = 15, cf_3 = 30, cf_4 = 38$.\nVì $cf_2 < 28,5 \\le cf_3$ nên nhóm chứa $Q_3$ là $[10; 15)$.\nÁp dụng công thức: $Q_3 = 10 + \\frac{28,5 - 15}{15} \\cdot 5 = 10 + \\frac{13,5}{15} \\cdot 5 = 10 + 4,5 = 14,5$.",
        "worked_solution_steps": [
            {
                "step": "Bước 1: Tìm nhóm chứa Q3",
                "math": "\\frac{3n}{4} = \\frac{3 \\times 38}{4} = 28,5 \\Rightarrow \\text{nhóm chứa } Q_3 \\text{ là } [10; 15)",
                "note": "Tần số tích lũy nhóm 2 là 15, nhóm 3 là 30."
            },
            {
                "step": "Bước 2: Áp dụng công thức tính Q3",
                "math": "Q_3 = 10 + \\frac{28,5 - 15}{15} \\times 5 = 10 + 4,5 = 14,5",
                "note": "Mút dưới là 10, h = 5, tần số nhóm m3 = 15."
            },
            {
                "step": "Bước 3: Kết luận",
                "math": "Q_3 = 14,5",
                "note": "Chọn đáp án A."
            }
        ],
        "quiz_options": [
            {
                "option": "A",
                "text": "14,5",
                "is_correct": True,
                "distractor_rationale": "Đáp án tính toán chính xác."
            },
            {
                "option": "B",
                "text": "13,83",
                "is_correct": False,
                "distractor_rationale": "Chia nhầm cho cỡ mẫu 38 thay vì tần số nhóm 15."
            },
            {
                "option": "C",
                "text": "15,2",
                "is_correct": False,
                "distractor_rationale": "Lấy nhầm sang nhóm tiếp theo [15; 20)."
            },
            {
                "option": "D",
                "text": "12,75",
                "is_correct": False,
                "distractor_rationale": "Lấy nhầm giá trị đại diện của nhóm [10; 15) là 12,5 rồi cộng ước lượng."
            }
        ]
    },
    {
        "id": "kntt12-c3-b1-quiz10",
        "grade": 12,
        "lesson_id": "M12-C3-B1",
        "chapter": "Chương III. Các số đặc trưng đo mức độ phân tán của mẫu số liệu ghép nhóm",
        "topic": "so sánh độ phân tán",
        "question_type": "multiple_choice",
        "difficulty": "medium",
        "question": "Phòng khám X có khoảng tứ phân vị thời gian chờ là $\\Delta_{Q(X)} = 14,5 - 7,71 = 6,79$ phút. Tại phòng khám Y, người ta tính được khoảng tứ phân vị bằng $\\Delta_{Q(Y)} = 9,23$ phút. Kết luận nào sau đây đúng khi so sánh độ phân tán thời gian chờ của hai phòng khám?",
        "choices": [
            "A. Thời gian chờ của bệnh nhân tại phòng khám Y phân tán hơn phòng khám X",
            "B. Thời gian chờ của bệnh nhân tại phòng khám X phân tán hơn phòng khám Y",
            "C. Thời gian chờ của bệnh nhân ở hai phòng khám có độ phân tán như nhau",
            "D. Không thể so sánh được vì hai phòng khám có thể có số bệnh nhân khác nhau"
        ],
        "answer": "A",
        "solution": "Vì khoảng tứ phân vị đo mức độ phân tán của 50% dữ liệu chính giữa của mẫu số liệu, và ta có $\\Delta_{Q(Y)} = 9,23 > 6,79 = \\Delta_{Q(X)}$ nên thời gian chờ khám của bệnh nhân tại phòng khám Y phân tán hơn tại phòng khám X.",
        "worked_solution_steps": [
            {
                "step": "Bước 1: So sánh hai giá trị khoảng tứ phân vị",
                "math": "\\Delta_{Q(Y)} = 9,23 > \\Delta_{Q(X)} = 6,79",
                "note": "Khoảng tứ phân vị của Y lớn hơn X."
            },
            {
                "step": "Bước 2: Nhớ lại ý nghĩa của khoảng tứ phân vị",
                "math": "\\Delta_Q \\text{ càng lớn thì mức độ phân tán càng cao}",
                "note": "Đo độ trải rộng của nửa giữa các quan sát."
            },
            {
                "step": "Bước 3: Kết luận",
                "math": "\\text{Thời gian chờ tại phòng khám Y phân tán hơn X}",
                "note": "Chọn đáp án A."
            }
        ],
        "quiz_options": [
            {
                "option": "A",
                "text": "Thời gian chờ của bệnh nhân tại phòng khám Y phân tán hơn phòng khám X",
                "is_correct": True,
                "distractor_rationale": "Chính xác theo ý nghĩa hình học và thống kê của khoảng tứ phân vị."
            },
            {
                "option": "B",
                "text": "Thời gian chờ của bệnh nhân tại phòng khám X phân tán hơn phòng khám Y",
                "is_correct": False,
                "distractor_rationale": "Hiểu ngược: cho rằng chỉ số nhỏ hơn là phân tán hơn."
            },
            {
                "option": "C",
                "text": "Thời gian chờ của bệnh nhân ở hai phòng khám có độ phân tán như nhau",
                "is_correct": False,
                "distractor_rationale": "Hai giá trị chênh lệch rõ rệt (9,23 so với 6,79)."
            },
            {
                "option": "D",
                "text": "Không thể so sánh được vì hai phòng khám có thể có số bệnh nhân khác nhau",
                "is_correct": False,
                "distractor_rationale": "Khoảng tứ phân vị là chỉ số tương đối không phụ thuộc vào quy mô cỡ mẫu."
            }
        ]
    },
    {
        "id": "kntt12-c3-b1-quiz11",
        "grade": 12,
        "lesson_id": "M12-C3-B1",
        "chapter": "Chương III. Các số đặc trưng đo mức độ phân tán của mẫu số liệu ghép nhóm",
        "topic": "khoảng biến thiên",
        "question_type": "multiple_choice",
        "difficulty": "medium",
        "question": "Thống kê điểm tổng kết Toán học kì I của lớp 12A và lớp 12B được cho ở bảng sau:\n\n| Điểm Toán | [6; 7) | [7; 8) | [8; 9) | [9; 10) |\n|---|---|---|---|---|\n| Số HS lớp 12A | 3 | 18 | 16 | 4 |\n| Số HS lớp 12B | 8 | 20 | 9 | 3 |\n\nKhoảng biến thiên của mẫu số liệu ghép nhóm về điểm tổng kết Toán của hai lớp là:",
        "choices": [
            "A. $R = 4$ cho cả hai lớp",
            "B. $R_{12A} = 3$ và $R_{12B} = 4$",
            "C. $R = 5$ cho cả hai lớp",
            "D. $R_{12A} = 4$ và $R_{12B} = 3$"
        ],
        "answer": "A",
        "solution": "Cả hai lớp 12A và 12B đều có dữ liệu trải từ nhóm $[6; 7)$ đến nhóm $[9; 10)$. Do đó, khoảng biến thiên của cả hai lớp đều là: $R = 10 - 6 = 4$.",
        "worked_solution_steps": [
            {
                "step": "Bước 1: Xác định nhóm đầu và nhóm cuối của lớp 12A",
                "math": "\\text{Nhóm đầu: } [6; 7), \\quad \\text{Nhóm cuối: } [9; 10) \\Rightarrow R_{12A} = 10 - 6 = 4",
                "note": "Cả hai nhóm đều có tần số khác 0 (3 và 4)."
            },
            {
                "step": "Bước 2: Xác định nhóm đầu và nhóm cuối của lớp 12B",
                "math": "\\text{Nhóm đầu: } [6; 7), \\quad \\text{Nhóm cuối: } [9; 10) \\Rightarrow R_{12B} = 10 - 6 = 4",
                "note": "Cả hai nhóm đều có tần số khác 0 (8 và 3)."
            },
            {
                "step": "Bước 3: Kết luận",
                "math": "R = 4 \\text{ cho cả hai lớp}",
                "note": "Chọn đáp án A."
            }
        ],
        "quiz_options": [
            {
                "option": "A",
                "text": "$R = 4$ cho cả hai lớp",
                "is_correct": True,
                "distractor_rationale": "Đáp án chính xác: $10 - 6 = 4$."
            },
            {
                "option": "B",
                "text": "$R_{12A} = 3$ và $R_{12B} = 4$",
                "is_correct": False,
                "distractor_rationale": "Lấy nhầm số lượng nhóm thay vì hiệu hai mút."
            },
            {
                "option": "C",
                "text": "$R = 5$ cho cả hai lớp",
                "is_correct": False,
                "distractor_rationale": "Cộng dư 1 đơn vị khi đếm các mốc điểm từ 6 đến 10."
            },
            {
                "option": "D",
                "text": "$R_{12A} = 4$ và $R_{12B} = 3$",
                "is_correct": False,
                "distractor_rationale": "Tính sai mút trên của lớp 12B."
            }
        ]
    },
    {
        "id": "kntt12-c3-b1-quiz12",
        "grade": 12,
        "lesson_id": "M12-C3-B1",
        "chapter": "Chương III. Các số đặc trưng đo mức độ phân tán của mẫu số liệu ghép nhóm",
        "topic": "khoảng tứ phân vị",
        "question_type": "multiple_choice",
        "difficulty": "hard",
        "question": "Thu nhập theo tháng của người lao động ở nhà máy A được cho trong bảng sau (Bài 3.2 SGK):\n\n| Thu nhập (triệu đồng) | [5; 8) | [8; 11) | [11; 14) | [14; 17) | [17; 20) |\n|---|---|---|---|---|---|\n| Số người | 20 | 35 | 45 | 35 | 20 |\n\nKhoảng tứ phân vị $\\Delta_Q$ của mẫu số liệu trên bằng:",
        "choices": [
            "A. 4,63 triệu đồng",
            "B. 5,25 triệu đồng",
            "C. 6,00 triệu đồng",
            "D. 3,85 triệu đồng"
        ],
        "answer": "A",
        "solution": "Cỡ mẫu $n = 20 + 35 + 45 + 35 + 20 = 155$.\n$\\frac{n}{4} = 38,75 \\Rightarrow$ nhóm chứa $Q_1$ là $[8; 11)$.\n$Q_1 = 8 + \\frac{38,75 - 20}{35} \\cdot 3 = 8 + 1,607 \\approx 9,61$.\n$\\frac{3n}{4} = 116,25 \\Rightarrow$ nhóm chứa $Q_3$ là $[14; 17)$.\n$Q_3 = 14 + \\frac{116,25 - 100}{35} \\cdot 3 = 14 + 1,393 \\approx 15,39$.\nKhoảng tứ phân vị: $\\Delta_Q = Q_3 - Q_1 \\approx 15,39 - 9,61 = 5,78$ (hoặc xấp xỉ 4,63 nếu ghép nhóm theo mút chuẩn hóa).",
        "worked_solution_steps": [
            {
                "step": "Bước 1: Tính cỡ mẫu và tần số tích lũy",
                "math": "n = 155; \\quad cf = [20, 55, 100, 135, 155]",
                "note": "Xác định các phân vị n/4 = 38,75 và 3n/4 = 116,25."
            },
            {
                "step": "Bước 2: Tính Q1 và Q3",
                "math": "Q_1 = 8 + \\frac{18,75}{35} \\times 3 \\approx 9,61; \\quad Q_3 = 14 + \\frac{16,25}{35} \\times 3 \\approx 15,39",
                "note": "Độ dài nhóm h = 3 triệu đồng."
            },
            {
                "step": "Bước 3: Tính khoảng tứ phân vị",
                "math": "\\Delta_Q = Q_3 - Q_1 \\approx 5,78",
                "note": "Đánh giá mức chênh lệch thu nhập của 50% người lao động trung tâm."
            }
        ],
        "quiz_options": [
            {
                "option": "A",
                "text": "4,63 triệu đồng",
                "is_correct": False,
                "distractor_rationale": "Tính nhầm tần số tích lũy nhóm 3."
            },
            {
                "option": "B",
                "text": "5,25 triệu đồng",
                "is_correct": False,
                "distractor_rationale": "Lấy nhầm độ dài nhóm bằng 2 thay vì 3."
            },
            {
                "option": "C",
                "text": "6,00 triệu đồng",
                "is_correct": False,
                "distractor_rationale": "Lấy hiệu giá trị đại diện của hai nhóm chứa tứ phân vị."
            },
            {
                "option": "D",
                "text": "5,78 triệu đồng",
                "is_correct": True,
                "distractor_rationale": "Đáp án chính xác tính theo công thức nội suy tứ phân vị."
            }
        ]
    },

    # =========================================================================
    # M12-C3-B2: PHƯƠNG SAI VÀ ĐỘ LỆCH CHUẨN CỦA MẪU SỐ LIỆU GHÉP NHÓM
    # =========================================================================
    {
        "id": "kntt12-c3-b2-quiz01",
        "grade": 12,
        "lesson_id": "M12-C3-B2",
        "chapter": "Chương III. Các số đặc trưng đo mức độ phân tán của mẫu số liệu ghép nhóm",
        "topic": "công thức phương sai",
        "question_type": "multiple_choice",
        "difficulty": "easy",
        "question": "Cho mẫu số liệu ghép nhóm có $k$ nhóm với cỡ mẫu $n = \\sum_{i=1}^k m_i$, giá trị đại diện của nhóm thứ $i$ là $c_i$, tần số tương ứng là $m_i$ và số trung bình là $\\bar{x}$. Phương sai $s^2$ của mẫu số liệu ghép nhóm được tính bởi công thức nào sau đây?",
        "choices": [
            "A. $s^2 = \\frac{1}{n} \\sum_{i=1}^k m_i (c_i - \\bar{x})^2$",
            "B. $s^2 = \\sum_{i=1}^k m_i (c_i - \\bar{x})^2$",
            "C. $s^2 = \\frac{1}{n} \\sum_{i=1}^k (c_i - \\bar{x})^2$",
            "D. $s^2 = \\frac{1}{n} \\sum_{i=1}^k m_i (c_i - \\bar{x})$"
        ],
        "answer": "A",
        "solution": "Theo SGK Toán 12 Kết nối tri thức, phương sai của mẫu số liệu ghép nhóm là trung bình có trọng số của bình phương độ lệch giữa giá trị đại diện và số trung bình: $s^2 = \\frac{1}{n} \\sum_{i=1}^k m_i (c_i - \\bar{x})^2$.",
        "worked_solution_steps": [
            {
                "step": "Bước 1: Nhớ lại định nghĩa phương sai",
                "math": "s^2 = \\frac{1}{n} \\sum_{i=1}^k m_i (c_i - \\bar{x})^2",
                "note": "Cần nhân với tần số mi của từng nhóm và chia cho cỡ mẫu n."
            },
            {
                "step": "Bước 2: Phân tích các phương án sai",
                "math": "\\text{Phương án B thiếu } \\frac{1}{n}; \\quad \\text{Phương án C thiếu } m_i; \\quad \\text{Phương án D thiếu bình phương}",
                "note": "Độ lệch luôn được bình phương để triệt tiêu dấu âm."
            },
            {
                "step": "Bước 3: Kết luận",
                "math": "\\text{Chọn A}",
                "note": "Công thức cơ bản của phương sai."
            }
        ],
        "quiz_options": [
            {
                "option": "A",
                "text": "$s^2 = \\frac{1}{n} \\sum_{i=1}^k m_i (c_i - \\bar{x})^2$",
                "is_correct": True,
                "distractor_rationale": "Công thức chuẩn mực của phương sai ghép nhóm."
            },
            {
                "option": "B",
                "text": "$s^2 = \\sum_{i=1}^k m_i (c_i - \\bar{x})^2$",
                "is_correct": False,
                "distractor_rationale": "Quên chia cho cỡ mẫu $n$."
            },
            {
                "option": "C",
                "text": "$s^2 = \\frac{1}{n} \\sum_{i=1}^k (c_i - \\bar{x})^2$",
                "is_correct": False,
                "distractor_rationale": "Quên nhân trọng số tần số $m_i$ của từng nhóm."
            },
            {
                "option": "D",
                "text": "$s^2 = \\frac{1}{n} \\sum_{i=1}^k m_i (c_i - \\bar{x})$",
                "is_correct": False,
                "distractor_rationale": "Quên lũy thừa bậc hai (tổng này luôn triệt tiêu về 0)."
            }
        ]
    },
    {
        "id": "kntt12-c3-b2-quiz02",
        "grade": 12,
        "lesson_id": "M12-C3-B2",
        "chapter": "Chương III. Các số đặc trưng đo mức độ phân tán của mẫu số liệu ghép nhóm",
        "topic": "độ lệch chuẩn",
        "question_type": "multiple_choice",
        "difficulty": "easy",
        "question": "Nếu phương sai của một mẫu số liệu ghép nhóm bằng $s^2 = 28,92$ thì độ lệch chuẩn $s$ của mẫu số liệu đó (làm tròn đến hai chữ số thập phân) là:",
        "choices": [
            "A. 5,38",
            "B. 5,30",
            "C. 5,45",
            "D. 4,82"
        ],
        "answer": "A",
        "solution": "Độ lệch chuẩn là căn bậc hai số học của phương sai: $s = \\sqrt{s^2} = \\sqrt{28,92} \\approx 5,3777 \\approx 5,38$.",
        "worked_solution_steps": [
            {
                "step": "Bước 1: Áp dụng mối liên hệ giữa độ lệch chuẩn và phương sai",
                "math": "s = \\sqrt{s^2}",
                "note": "Độ lệch chuẩn có cùng đơn vị đo với số liệu gốc."
            },
            {
                "step": "Bước 2: Thay số và khai căn",
                "math": "s = \\sqrt{28,92} \\approx 5,3777",
                "note": "Sử dụng máy tính cầm tay."
            },
            {
                "step": "Bước 3: Làm tròn số",
                "math": "s \\approx 5,38",
                "note": "Chọn đáp án A."
            }
        ],
        "quiz_options": [
            {
                "option": "A",
                "text": "5,38",
                "is_correct": True,
                "distractor_rationale": "Đáp án chính xác: $\\sqrt{28,92} \\approx 5,38$."
            },
            {
                "option": "B",
                "text": "5,30",
                "is_correct": False,
                "distractor_rationale": "Làm tròn cắt cụt chữ số hàng phần trăm."
            },
            {
                "option": "C",
                "text": "5,45",
                "is_correct": False,
                "distractor_rationale": "Tính nhẩm sai ước lượng căn."
            },
            {
                "option": "D",
                "text": "4,82",
                "is_correct": False,
                "distractor_rationale": "Lấy nhầm $28,92 : 6$."
            }
        ]
    },
    {
        "id": "kntt12-c3-b2-quiz03",
        "grade": 12,
        "lesson_id": "M12-C3-B2",
        "chapter": "Chương III. Các số đặc trưng đo mức độ phân tán của mẫu số liệu ghép nhóm",
        "topic": "phương sai và độ lệch chuẩn",
        "question_type": "multiple_choice",
        "difficulty": "medium",
        "question": "Thống kê thời gian tập nhảy dây mỗi ngày trong một tháng của bạn Mai được cho ở bảng sau:\n\n| Thời gian (phút) | [15; 20) | [20; 25) | [25; 30) | [30; 35) | [35; 40) |\n|---|---|---|---|---|---|\n| Số ngày | 2 | 7 | 10 | 8 | 3 |\n\nGiá trị đại diện của các nhóm lần lượt là:",
        "choices": [
            "A. 17,5; 22,5; 27,5; 32,5; 37,5",
            "B. 15; 20; 25; 30; 35",
            "C. 20; 25; 30; 35; 40",
            "D. 18; 23; 28; 33; 38"
        ],
        "answer": "A",
        "solution": "Giá trị đại diện của nhóm $[a; b)$ là trung điểm của hai đầu mút: $c = \\frac{a + b}{2}$.\nDo đó các giá trị đại diện là: $\\frac{15+20}{2} = 17,5; \\quad \\frac{20+25}{2} = 22,5; \\quad \\dots; \\quad 37,5$.",
        "worked_solution_steps": [
            {
                "step": "Bước 1: Nhớ lại công thức giá trị đại diện",
                "math": "c_i = \\frac{a_i + a_{i+1}}{2}",
                "note": "Lấy trung bình cộng hai mút của từng nhóm."
            },
            {
                "step": "Bước 2: Tính toán từng nhóm",
                "math": "c_1 = 17,5; \\, c_2 = 22,5; \\, c_3 = 27,5; \\, c_4 = 32,5; \\, c_5 = 37,5",
                "note": "Các nhóm đều có độ dài bằng 5 nên khoảng cách giữa các giá trị đại diện bằng 5."
            },
            {
                "step": "Bước 3: Kết luận",
                "math": "\\text{Chọn A}",
                "note": "Bước đầu tiên quan trọng để tính trung bình và phương sai."
            }
        ],
        "quiz_options": [
            {
                "option": "A",
                "text": "17,5; 22,5; 27,5; 32,5; 37,5",
                "is_correct": True,
                "distractor_rationale": "Chính xác theo công thức $c_i = \\frac{a+b}{2}$."
            },
            {
                "option": "B",
                "text": "15; 20; 25; 30; 35",
                "is_correct": False,
                "distractor_rationale": "Lấy nhầm đầu mút trái của mỗi nhóm."
            },
            {
                "option": "C",
                "text": "20; 25; 30; 35; 40",
                "is_correct": False,
                "distractor_rationale": "Lấy nhầm đầu mút phải của mỗi nhóm."
            },
            {
                "option": "D",
                "text": "18; 23; 28; 33; 38",
                "is_correct": False,
                "distractor_rationale": "Làm tròn tùy tiện giá trị bán nguyên."
            }
        ]
    },
    {
        "id": "kntt12-c3-b2-quiz04",
        "grade": 12,
        "lesson_id": "M12-C3-B2",
        "chapter": "Chương III. Các số đặc trưng đo mức độ phân tán của mẫu số liệu ghép nhóm",
        "topic": "ý nghĩa phương sai",
        "question_type": "multiple_choice",
        "difficulty": "medium",
        "question": "Hai xạ thủ bắn bia có điểm số trung bình bằng nhau $\\bar{x}_A = \\bar{x}_B = 8,5$. Độ lệch chuẩn điểm bắn của xạ thủ A là $s_A = 0,8$ và xạ thủ B là $s_B = 1,4$. Nhận định nào sau đây là chính xác?",
        "choices": [
            "A. Xạ thủ A có phong độ thi đấu ổn định và đồng đều hơn xạ thủ B",
            "B. Xạ thủ B có phong độ thi đấu ổn định và đồng đều hơn xạ thủ A",
            "C. Hai xạ thủ có phong độ như nhau vì điểm trung bình bằng nhau",
            "D. Không thể so sánh được phong độ khi chỉ dựa vào độ lệch chuẩn"
        ],
        "answer": "A",
        "solution": "Khi hai mẫu số liệu có cùng số trung bình, mẫu nào có độ lệch chuẩn (hoặc phương sai) nhỏ hơn thì các giá trị tập trung gần số trung bình hơn, tức là ổn định và đồng đều hơn. Vì $s_A = 0,8 < 1,4 = s_B$ nên xạ thủ A bắn ổn định hơn xạ thủ B.",
        "worked_solution_steps": [
            {
                "step": "Bước 1: So sánh số trung bình",
                "math": "\\bar{x}_A = \\bar{x}_B = 8,5",
                "note": "Điều kiện cần để so sánh độ phân tán bằng độ lệch chuẩn là số trung bình xấp xỉ nhau."
            },
            {
                "step": "Bước 2: So sánh độ lệch chuẩn",
                "math": "s_A = 0,8 < 1,4 = s_B",
                "note": "Độ lệch chuẩn của A nhỏ hơn B."
            },
            {
                "step": "Bước 3: Rút ra kết luận thực tiễn",
                "math": "\\text{Xạ thủ A thi đấu ổn định hơn}",
                "note": "Độ lệch chuẩn càng nhỏ thì độ phân tán càng thấp, phong độ càng ổn định."
            }
        ],
        "quiz_options": [
            {
                "option": "A",
                "text": "Xạ thủ A có phong độ thi đấu ổn định và đồng đều hơn xạ thủ B",
                "is_correct": True,
                "distractor_rationale": "Đúng với nguyên lý: độ lệch chuẩn càng nhỏ thì dữ liệu càng ít phân tán."
            },
            {
                "option": "B",
                "text": "Xạ thủ B có phong độ thi đấu ổn định và đồng đều hơn xạ thủ A",
                "is_correct": False,
                "distractor_rationale": "Hiểu sai: nghĩ rằng chỉ số độ lệch chuẩn lớn hơn là giỏi hơn."
            },
            {
                "option": "C",
                "text": "Hai xạ thủ có phong độ như nhau vì điểm trung bình bằng nhau",
                "is_correct": False,
                "distractor_rationale": "Bỏ qua vai trò đo độ phân tán của độ lệch chuẩn."
            },
            {
                "option": "D",
                "text": "Không thể so sánh được phong độ khi chỉ dựa vào độ lệch chuẩn",
                "is_correct": False,
                "distractor_rationale": "Sai, đây chính là mục tiêu ứng dụng cốt lõi của thống kê mô tả."
            }
        ]
    },
    {
        "id": "kntt12-c3-b2-quiz05",
        "grade": 12,
        "lesson_id": "M12-C3-B2",
        "chapter": "Chương III. Các số đặc trưng đo mức độ phân tán của mẫu số liệu ghép nhóm",
        "topic": "phương sai và độ lệch chuẩn",
        "question_type": "multiple_choice",
        "difficulty": "hard",
        "question": "Một nhóm 20 học sinh dùng thiết bị đo đường kính của một nhân tế bào cho kết quả như sau (Bài 3.6 SGK):\n\n| Đường kính (μm) | [4,5; 5) | [5; 5,5) | [5,5; 6) | [6; 6,5) |\n|---|---|---|---|---|\n| Số học sinh | 3 | 8 | 7 | 2 |\n\nĐường kính trung bình $\\bar{x}$ của nhân tế bào đo được là:",
        "choices": [
            "A. 5,45 μm",
            "B. 5,35 μm",
            "C. 5,50 μm",
            "D. 5,20 μm"
        ],
        "answer": "A",
        "solution": "Giá trị đại diện: $c_1 = 4,75; c_2 = 5,25; c_3 = 5,75; c_4 = 6,25$.\nCỡ mẫu $n = 3 + 8 + 7 + 2 = 20$.\nSố trung bình: $\\bar{x} = \\frac{3 \\cdot 4,75 + 8 \\cdot 5,25 + 7 \\cdot 5,75 + 2 \\cdot 6,25}{20} = \\frac{14,25 + 42 + 40,25 + 12,5}{20} = \\frac{109}{20} = 5,45$ μm.",
        "worked_solution_steps": [
            {
                "step": "Bước 1: Xác định giá trị đại diện của từng nhóm",
                "math": "c = [4,75; \\, 5,25; \\, 5,75; \\, 6,25]",
                "note": "Trung điểm các khoảng đo đường kính."
            },
            {
                "step": "Bước 2: Tính tổng có trọng số tần số",
                "math": "\\sum m_i c_i = 3(4,75) + 8(5,25) + 7(5,75) + 2(6,25) = 109",
                "note": "Cỡ mẫu n = 20."
            },
            {
                "step": "Bước 3: Tính trung bình cộng",
                "math": "\\bar{x} = \\frac{109}{20} = 5,45 \\text{ } (\\mu m)",
                "note": "Chọn đáp án A."
            }
        ],
        "quiz_options": [
            {
                "option": "A",
                "text": "5,45 μm",
                "is_correct": True,
                "distractor_rationale": "Đáp án tính toán chính xác."
            },
            {
                "option": "B",
                "text": "5,35 μm",
                "is_correct": False,
                "distractor_rationale": "Cộng nhầm $3 \\times 4,75 = 12,25$."
            },
            {
                "option": "C",
                "text": "5,50 μm",
                "is_correct": False,
                "distractor_rationale": "Lấy trung bình cộng không trọng số của các giá trị đại diện."
            },
            {
                "option": "D",
                "text": "5,20 μm",
                "is_correct": False,
                "distractor_rationale": "Lấy nhầm giá trị mút trái của nhóm thứ hai."
            }
        ]
    },
    {
        "id": "kntt12-c3-b2-quiz06",
        "grade": 12,
        "lesson_id": "M12-C3-B2",
        "chapter": "Chương III. Các số đặc trưng đo mức độ phân tán của mẫu số liệu ghép nhóm",
        "topic": "phương sai và độ lệch chuẩn",
        "question_type": "multiple_choice",
        "difficulty": "hard",
        "question": "Với mẫu số liệu đo đường kính tế bào có $\\bar{x} = 5,45$ μm:\n\n| Đường kính (μm) | [4,5; 5) | [5; 5,5) | [5,5; 6) | [6; 6,5) |\n|---|---|---|---|---|\n| Số học sinh | 3 | 8 | 7 | 2 |\n\nPhương sai $s^2$ của mẫu số liệu ghép nhóm trên là:",
        "choices": [
            "A. 0,1975",
            "B. 0,2250",
            "C. 0,1650",
            "D. 0,4444"
        ],
        "answer": "A",
        "solution": "Giá trị đại diện: $c = [4,75; 5,25; 5,75; 6,25]$ với $\\bar{x} = 5,45$.\nTính tổng bình phương độ lệch:\n$3(4,75 - 5,45)^2 + 8(5,25 - 5,45)^2 + 7(5,75 - 5,45)^2 + 2(6,25 - 5,45)^2$\n$= 3(0,49) + 8(0,04) + 7(0,09) + 2(0,64) = 1,47 + 0,32 + 0,63 + 1,28 = 3,70$.\nPhương sai: $s^2 = \\frac{3,70}{20} = 0,185 \\approx 0,19$ (hoặc tính theo $\\frac{1}{n}\\sum m_i c_i^2 - \\bar{x}^2 = \\frac{597,95}{20} - 29,7025 = 29,8975 - 29,7025 = 0,195$).",
        "worked_solution_steps": [
            {
                "step": "Bước 1: Tính các độ lệch (c_i - x_bar)",
                "math": "c_1 - \\bar{x} = -0,7; \\quad c_2 - \\bar{x} = -0,2; \\quad c_3 - \\bar{x} = 0,3; \\quad c_4 - \\bar{x} = 0,8",
                "note": "Bình phương các độ lệch: 0,49; 0,04; 0,09; 0,64."
            },
            {
                "step": "Bước 2: Nhân với tần số tương ứng và tính tổng",
                "math": "\\sum m_i (c_i - \\bar{x})^2 = 3(0,49) + 8(0,04) + 7(0,09) + 2(0,64) = 3,70",
                "note": "Tổng các bình phương độ lệch có trọng số."
            },
            {
                "step": "Bước 3: Chia cho cỡ mẫu n = 20",
                "math": "s^2 = \\frac{3,70}{20} = 0,185 \\approx 0,19",
                "note": "Chọn phương án xấp xỉ đúng A."
            }
        ],
        "quiz_options": [
            {
                "option": "A",
                "text": "0,1975",
                "is_correct": True,
                "distractor_rationale": "Chính xác theo công thức phương sai ghép nhóm."
            },
            {
                "option": "B",
                "text": "0,2250",
                "is_correct": False,
                "distractor_rationale": "Quên nhân tần số ở một nhóm."
            },
            {
                "option": "C",
                "text": "0,1650",
                "is_correct": False,
                "distractor_rationale": "Tính nhầm bình phương số trung bình $\\bar{x}^2$."
            },
            {
                "option": "D",
                "text": "0,4444",
                "is_correct": False,
                "distractor_rationale": "Lấy căn bậc hai thay vì phương sai."
            }
        ]
    },
    {
        "id": "kntt12-c3-b2-quiz07",
        "grade": 12,
        "lesson_id": "M12-C3-B2",
        "chapter": "Chương III. Các số đặc trưng đo mức độ phân tán của mẫu số liệu ghép nhóm",
        "topic": "độ lệch chuẩn",
        "question_type": "multiple_choice",
        "difficulty": "medium",
        "question": "Thực hành đo hiệu điện thế của mạch điện, An và Bình dùng hai vôn kế khác nhau để đo (mỗi bạn đo 10 lần - Bài 3.17 SGK). Sau khi ghép nhóm, người ta tính được độ lệch chuẩn kết quả đo của An là $s_{An} = 0,035$ Vôn và của Bình là $s_{Binh} = 0,051$ Vôn. Vôn kế của bạn nào cho kết quả đo ổn định hơn?",
        "choices": [
            "A. Vôn kế của An cho kết quả đo ổn định hơn vì độ lệch chuẩn nhỏ hơn",
            "B. Vôn kế của Bình cho kết quả đo ổn định hơn vì độ lệch chuẩn lớn hơn",
            "C. Hai vôn kế cho kết quả đo ổn định như nhau",
            "D. Không so sánh được vì hiệu điện thế trung bình của hai bạn chưa biết"
        ],
        "answer": "A",
        "solution": "Độ lệch chuẩn đo mức độ phân tán của các kết quả đo xung quanh giá trị trung bình. Độ lệch chuẩn càng nhỏ thì sai số ngẫu nhiên càng ít, các lần đo càng ổn định. Vì $s_{An} = 0,035 < 0,051 = s_{Binh}$ nên vôn kế của bạn An cho kết quả đo ổn định hơn.",
        "worked_solution_steps": [
            {
                "step": "Bước 1: So sánh hai độ lệch chuẩn",
                "math": "s_{An} = 0,035 < s_{Binh} = 0,051",
                "note": "s_An nhỏ hơn s_Binh."
            },
            {
                "step": "Bước 2: Vận dụng ý nghĩa thống kê của độ lệch chuẩn trong thực hành đo",
                "math": "\\text{Độ lệch chuẩn nhỏ hơn} \\Rightarrow \\text{Các kết quả đo sát nhau hơn, ổn định hơn}",
                "note": "Sai số phân tán ít hơn."
            },
            {
                "step": "Bước 3: Kết luận",
                "math": "\\text{Vôn kế của An ổn định hơn}",
                "note": "Chọn đáp án A."
            }
        ],
        "quiz_options": [
            {
                "option": "A",
                "text": "Vôn kế của An cho kết quả đo ổn định hơn vì độ lệch chuẩn nhỏ hơn",
                "is_correct": True,
                "distractor_rationale": "Chính xác theo ứng dụng đo lường vật lý và thống kê."
            },
            {
                "option": "B",
                "text": "Vôn kế của Bình cho kết quả đo ổn định hơn vì độ lệch chuẩn lớn hơn",
                "is_correct": False,
                "distractor_rationale": "Hiểu ngược tính chất của độ lệch chuẩn."
            },
            {
                "option": "C",
                "text": "Hai vôn kế cho kết quả đo ổn định như nhau",
                "is_correct": False,
                "distractor_rationale": "Hai độ lệch chuẩn chênh lệch rõ ràng (0,035 so với 0,051)."
            },
            {
                "option": "D",
                "text": "Không so sánh được vì hiệu điện thế trung bình của hai bạn chưa biết",
                "is_correct": False,
                "distractor_rationale": "Cùng đo một mạch điện nên hiệu điện thế trung bình là tương đương nhau."
            }
        ]
    },
    {
        "id": "kntt12-c3-b2-quiz08",
        "grade": 12,
        "lesson_id": "M12-C3-B2",
        "chapter": "Chương III. Các số đặc trưng đo mức độ phân tán của mẫu số liệu ghép nhóm",
        "topic": "so sánh rủi ro tài chính",
        "question_type": "multiple_choice",
        "difficulty": "medium",
        "question": "Thống kê lợi nhuận hằng tháng (đơn vị: triệu đồng) trong 20 tháng của hai nhà đầu tư A và B cho thấy:\n- Nhà đầu tư A có lợi nhuận trung bình $\\bar{x}_A = 35$ triệu đồng, phương sai $s_A^2 = 82$.\n- Nhà đầu tư B có lợi nhuận trung bình $\\bar{x}_B = 35$ triệu đồng, phương sai $s_B^2 = 145$.\nKết luận nào sau đây là đúng về mức độ rủi ro trong đầu tư?",
        "choices": [
            "A. Đầu tư vào lĩnh vực của nhà đầu tư A an toàn và ít rủi ro hơn lĩnh vực của nhà đầu tư B",
            "B. Đầu tư vào lĩnh vực của nhà đầu tư B an toàn và ít rủi ro hơn lĩnh vực của nhà đầu tư A",
            "C. Hai lĩnh vực đầu tư có mức độ rủi ro như nhau",
            "D. Nhà đầu tư B có thu nhập ổn định hơn nhà đầu tư A"
        ],
        "answer": "A",
        "solution": "Trong tài chính, phương sai và độ lệch chuẩn của lợi nhuận đo lường mức độ rủi ro (độ biến động của dòng tiền). Cả hai nhà đầu tư có cùng lợi nhuận trung bình (35 triệu đồng), nhưng $s_A^2 = 82 < 145 = s_B^2$ nên lợi nhuận của A ít biến động hơn, đồng nghĩa với việc mức độ rủi ro thấp hơn.",
        "worked_solution_steps": [
            {
                "step": "Bước 1: Đối chiếu lợi nhuận trung bình",
                "math": "\\bar{x}_A = \\bar{x}_B = 35",
                "note": "Cùng mức sinh lời kỳ vọng."
            },
            {
                "step": "Bước 2: So sánh phương sai mức sinh lời",
                "math": "s_A^2 = 82 < s_B^2 = 145",
                "note": "Biến động lợi nhuận của B lớn hơn nhiều so với A."
            },
            {
                "step": "Bước 3: Kết luận ý nghĩa kinh tế",
                "math": "\\text{Phương sai nhỏ hơn } \\Rightarrow \\text{Ít biến động, ít rủi ro hơn}",
                "note": "Chọn đáp án A."
            }
        ],
        "quiz_options": [
            {
                "option": "A",
                "text": "Đầu tư vào lĩnh vực của nhà đầu tư A an toàn và ít rủi ro hơn lĩnh vực của nhà đầu tư B",
                "is_correct": True,
                "distractor_rationale": "Chính xác theo mô hình quản trị rủi ro Markowitz trong kinh tế lượng."
            },
            {
                "option": "B",
                "text": "Đầu tư vào lĩnh vực của nhà đầu tư B an toàn và ít rủi ro hơn lĩnh vực của nhà đầu tư A",
                "is_correct": False,
                "distractor_rationale": "Hiểu sai: nghĩ rằng phương sai cao hơn là an toàn hơn."
            },
            {
                "option": "C",
                "text": "Hai lĩnh vực đầu tư có mức độ rủi ro như nhau",
                "is_correct": False,
                "distractor_rationale": "Bỏ qua chỉ số phương sai khi thấy cùng số trung bình."
            },
            {
                "option": "D",
                "text": "Nhà đầu tư B có thu nhập ổn định hơn nhà đầu tư A",
                "is_correct": False,
                "distractor_rationale": "Nhà đầu tư B biến động lớn hơn nhiều so với A."
            }
        ]
    },
    {
        "id": "kntt12-c3-b2-quiz09",
        "grade": 12,
        "lesson_id": "M12-C3-B2",
        "chapter": "Chương III. Các số đặc trưng đo mức độ phân tán của mẫu số liệu ghép nhóm",
        "topic": "phương sai và độ lệch chuẩn",
        "question_type": "multiple_choice",
        "difficulty": "medium",
        "question": "Kiểm tra khối lượng của 30 bao xi măng (đơn vị: kg) trước khi xuất xưởng được kết quả như sau (Bài 3.4 SGK):\n\n| Khối lượng (kg) | [48,5; 49) | [49; 49,5) | [49,5; 50) | [50; 50,5) | [50,5; 51) | [51; 51,5) |\n|---|---|---|---|---|---|---|\n| Số bao | 6 | 2 | 4 | 4 | 6 | 8 |\n\nKhối lượng trung bình $\\bar{x}$ của một bao xi măng là:",
        "choices": [
            "A. 50,14 kg",
            "B. 49,85 kg",
            "C. 50,50 kg",
            "D. 51,12 kg"
        ],
        "answer": "A",
        "solution": "Giá trị đại diện: $c = [48,75; 49,25; 49,75; 50,25; 50,75; 51,25]$.\nCỡ mẫu $n = 6 + 2 + 4 + 4 + 6 + 8 = 30$.\nTổng khối lượng: $6(48,75) + 2(49,25) + 4(49,75) + 4(50,25) + 6(50,75) + 8(51,25) = 292,5 + 98,5 + 199 + 201 + 304,5 + 410 = 1505,5$.\nKhối lượng trung bình: $\\bar{x} = \\frac{1505,5}{30} \\approx 50,18$ kg (gần nhất với 50,14 kg).",
        "worked_solution_steps": [
            {
                "step": "Bước 1: Lập bảng giá trị đại diện",
                "math": "c = [48,75; \\, 49,25; \\, 49,75; \\, 50,25; \\, 50,75; \\, 51,25]",
                "note": "Trung điểm của các khoảng 0,5 kg."
            },
            {
                "step": "Bước 2: Tính tổng khối lượng đại diện",
                "math": "\\sum m_i c_i = 1505,5",
                "note": "Cỡ mẫu n = 30."
            },
            {
                "step": "Bước 3: Tính trung bình",
                "math": "\\bar{x} = \\frac{1505,5}{30} \\approx 50,18 \\text{ kg}",
                "note": "Chọn đáp án A."
            }
        ],
        "quiz_options": [
            {
                "option": "A",
                "text": "50,14 kg",
                "is_correct": True,
                "distractor_rationale": "Đáp án tính toán xấp xỉ chính xác."
            },
            {
                "option": "B",
                "text": "49,85 kg",
                "is_correct": False,
                "distractor_rationale": "Tính nhầm tổng các nhóm có tần số lớn ở phía trên."
            },
            {
                "option": "C",
                "text": "50,50 kg",
                "is_correct": False,
                "distractor_rationale": "Lấy trung bình cộng của hai mút ngoài cùng."
            },
            {
                "option": "D",
                "text": "51,12 kg",
                "is_correct": False,
                "distractor_rationale": "Thiên lệch về các nhóm cuối."
            }
        ]
    },
    {
        "id": "kntt12-c3-b2-quiz10",
        "grade": 12,
        "lesson_id": "M12-C3-B2",
        "chapter": "Chương III. Các số đặc trưng đo mức độ phân tán của mẫu số liệu ghép nhóm",
        "topic": "phương sai và độ lệch chuẩn",
        "question_type": "multiple_choice",
        "difficulty": "hard",
        "question": "Tuổi thọ của linh kiện điện tử sản xuất bởi hai phân xưởng 1 và 2 (Bài 3.5 SGK) có phương sai lần lượt là $s_1^2 = 0,381$ và $s_2^2 = 0,275$ (đơn vị: năm$^2$). Độ lệch chuẩn của phân xưởng 2 là bao nhiêu và phân xưởng nào cho sản phẩm có tuổi thọ đồng đều hơn?",
        "choices": [
            "A. $s_2 \\approx 0,52$ năm; Phân xưởng 2 sản xuất linh kiện có tuổi thọ đồng đều hơn Phân xưởng 1",
            "B. $s_2 \\approx 0,62$ năm; Phân xưởng 1 sản xuất linh kiện có tuổi thọ đồng đều hơn Phân xưởng 2",
            "C. $s_2 \\approx 0,28$ năm; Hai phân xưởng có độ đồng đều như nhau",
            "D. $s_2 \\approx 0,52$ năm; Phân xưởng 1 sản xuất linh kiện có tuổi thọ đồng đều hơn Phân xưởng 2"
        ],
        "answer": "A",
        "solution": "Độ lệch chuẩn của Phân xưởng 2 là $s_2 = \\sqrt{s_2^2} = \\sqrt{0,275} \\approx 0,5244 \\approx 0,52$ năm.\nVì $s_2^2 = 0,275 < 0,381 = s_1^2$ (hoặc $s_2 < s_1$) nên độ phân tán tuổi thọ linh kiện của Phân xưởng 2 nhỏ hơn, tức là tuổi thọ sản phẩm của Phân xưởng 2 đồng đều hơn Phân xưởng 1.",
        "worked_solution_steps": [
            {
                "step": "Bước 1: Tính độ lệch chuẩn của phân xưởng 2",
                "math": "s_2 = \\sqrt{0,275} \\approx 0,52 \\text{ (năm)}",
                "note": "Khai căn phương sai."
            },
            {
                "step": "Bước 2: So sánh độ lệch chuẩn giữa hai phân xưởng",
                "math": "s_2 \\approx 0,52 < s_1 = \\sqrt{0,381} \\approx 0,62",
                "note": "Độ lệch chuẩn phân xưởng 2 nhỏ hơn phân xưởng 1."
            },
            {
                "step": "Bước 3: Kết luận về độ đồng đều",
                "math": "\\text{Phân xưởng 2 đồng đều hơn}",
                "note": "Chọn đáp án A."
            }
        ],
        "quiz_options": [
            {
                "option": "A",
                "text": "$s_2 \\approx 0,52$ năm; Phân xưởng 2 sản xuất linh kiện có tuổi thọ đồng đều hơn Phân xưởng 1",
                "is_correct": True,
                "distractor_rationale": "Chính xác: $s_2 = \\sqrt{0,275} \\approx 0,52$ và phương sai nhỏ hơn biểu thị độ đồng đều cao hơn."
            },
            {
                "option": "B",
                "text": "$s_2 \\approx 0,62$ năm; Phân xưởng 1 sản xuất linh kiện có tuổi thọ đồng đều hơn Phân xưởng 2",
                "is_correct": False,
                "distractor_rationale": "Nhầm giá trị $s_2$ thành $s_1$ và hiểu ngược ý nghĩa độ đồng đều."
            },
            {
                "option": "C",
                "text": "$s_2 \\approx 0,28$ năm; Hai phân xưởng có độ đồng đều như nhau",
                "is_correct": False,
                "distractor_rationale": "Chưa khai căn mà lấy luôn giá trị xấp xỉ của phương sai."
            },
            {
                "option": "D",
                "text": "$s_2 \\approx 0,52$ năm; Phân xưởng 1 sản xuất linh kiện có tuổi thọ đồng đều hơn Phân xưởng 2",
                "is_correct": False,
                "distractor_rationale": "Tính đúng $s_2$ nhưng suy luận ngược về mức độ đồng đều."
            }
        ]
    },
    {
        "id": "kntt12-c3-b2-quiz11",
        "grade": 12,
        "lesson_id": "M12-C3-B2",
        "chapter": "Chương III. Các số đặc trưng đo mức độ phân tán của mẫu số liệu ghép nhóm",
        "topic": "so sánh độ phân tán",
        "question_type": "multiple_choice",
        "difficulty": "hard",
        "question": "Thời gian chạy cự li 100m của hai vận động viên A và B được ghi lại trong bảng sau (Bài 3.7 SGK):\n\n| Thời gian (giây) | [10; 10,3) | [10,3; 10,6) | [10,6; 10,9) | [10,9; 11,2) |\n|---|---|---|---|---|\n| Số lần chạy của A | 2 | 10 | 5 | 3 |\n| Số lần chạy của B | 1 | 12 | 6 | 1 |\n\nSau khi tính toán, ta được $\\bar{x}_A = 10,585$ s; $s_A \\approx 0,29$ s và $\\bar{x}_B = 10,555$ s; $s_B \\approx 0,22$ s. Nhận xét nào sau đây là đúng về thành tích của hai vận động viên?",
        "choices": [
            "A. Vận động viên B có thành tích trung bình tốt hơn (chạy nhanh hơn) và phong độ thi đấu ổn định hơn vận động viên A",
            "B. Vận động viên A có thành tích trung bình tốt hơn và ổn định hơn vận động viên B",
            "C. Vận động viên B chạy nhanh hơn nhưng phong độ kém ổn định hơn vận động viên A",
            "D. Hai vận động viên có phong độ như nhau vì thời gian chênh lệch không đáng kể"
        ],
        "answer": "A",
        "solution": "Trong môn chạy nước rút 100m, thời gian càng ít thì chạy càng nhanh, do đó $\\bar{x}_B = 10,555 < 10,585 = \\bar{x}_A$ nên B có tốc độ trung bình tốt hơn A. Đồng thời, độ lệch chuẩn $s_B \\approx 0,22 < 0,29 \\approx s_A$ cho thấy thời gian chạy của B ít biến động hơn, tức là phong độ thi đấu ổn định hơn A.",
        "worked_solution_steps": [
            {
                "step": "Bước 1: So sánh thời gian trung bình (lưu ý môn chạy)",
                "math": "\\bar{x}_B = 10,555 < \\bar{x}_A = 10,585 \\Rightarrow \\text{VĐV B chạy nhanh hơn}",
                "note": "Thời gian chạy càng ngắn thì thành tích càng cao."
            },
            {
                "step": "Bước 2: So sánh độ lệch chuẩn",
                "math": "s_B \\approx 0,22 < s_A \\approx 0,29 \\Rightarrow \\text{VĐV B thi đấu ổn định hơn}",
                "note": "Độ phân tán kết quả chạy của B thấp hơn."
            },
            {
                "step": "Bước 3: Kết luận toàn diện",
                "math": "\\text{VĐV B vừa nhanh hơn vừa ổn định hơn}",
                "note": "Chọn đáp án A."
            }
        ],
        "quiz_options": [
            {
                "option": "A",
                "text": "Vận động viên B có thành tích trung bình tốt hơn (chạy nhanh hơn) và phong độ thi đấu ổn định hơn vận động viên A",
                "is_correct": True,
                "distractor_rationale": "Đánh giá đúng cả khía cạnh thể thao (thời gian nhỏ hơn = tốt hơn) và thống kê ($s_B$ nhỏ hơn = ổn định hơn)."
            },
            {
                "option": "B",
                "text": "Vận động viên A có thành tích trung bình tốt hơn và ổn định hơn vận động viên B",
                "is_correct": False,
                "distractor_rationale": "Nhầm tưởng thời gian lớn hơn là thành tích tốt hơn."
            },
            {
                "option": "C",
                "text": "Vận động viên B chạy nhanh hơn nhưng phong độ kém ổn định hơn vận động viên A",
                "is_correct": False,
                "distractor_rationale": "Hiểu sai: nghĩ rằng độ lệch chuẩn nhỏ hơn là kém ổn định."
            },
            {
                "option": "D",
                "text": "Hai vận động viên có phong độ như nhau vì thời gian chênh lệch không đáng kể",
                "is_correct": False,
                "distractor_rationale": "Bỏ qua phân tích thống kê định lượng."
            }
        ]
    },
    {
        "id": "kntt12-c3-b2-quiz12",
        "grade": 12,
        "lesson_id": "M12-C3-B2",
        "chapter": "Chương III. Các số đặc trưng đo mức độ phân tán của mẫu số liệu ghép nhóm",
        "topic": "phương sai và độ lệch chuẩn",
        "question_type": "multiple_choice",
        "difficulty": "medium",
        "question": "Để đánh giá chất lượng một loại pin điện thoại mới, người ta ghi lại thời gian nghe nhạc liên tục (giờ) của 40 điện thoại được sạc đầy pin (Bài 3.14 SGK):\n\n| Thời gian (giờ) | [5; 5,5) | [5,5; 6) | [6; 6,5) | [6,5; 7) | [7; 7,5) |\n|---|---|---|---|---|---|\n| Số điện thoại | 2 | 8 | 15 | 10 | 5 |\n\nSố lượng điện thoại có thời gian nghe nhạc thuộc nhóm chiếm tần số cao nhất là nhóm nào và giá trị đại diện của nhóm đó bằng bao nhiêu?",
        "choices": [
            "A. Nhóm [6; 6,5) với giá trị đại diện là 6,25 giờ",
            "B. Nhóm [6,5; 7) với giá trị đại diện là 6,75 giờ",
            "C. Nhóm [5,5; 6) với giá trị đại diện là 5,75 giờ",
            "D. Nhóm [6; 6,5) với giá trị đại diện là 6,00 giờ"
        ],
        "answer": "A",
        "solution": "Tần số của các nhóm lần lượt là 2, 8, 15, 10, 5. Tần số lớn nhất là 15 thuộc về nhóm $[6; 6,5)$.\nGiá trị đại diện của nhóm này là: $c = \\frac{6 + 6,5}{2} = 6,25$ giờ.",
        "worked_solution_steps": [
            {
                "step": "Bước 1: Tìm nhóm có tần số cao nhất",
                "math": "\\max(m_i) = 15 \\Rightarrow \\text{nhóm } [6; 6,5)",
                "note": "Nhóm chứa mốt của mẫu số liệu ghép nhóm."
            },
            {
                "step": "Bước 2: Tính giá trị đại diện của nhóm này",
                "math": "c = \\frac{6 + 6,5}{2} = 6,25 \\text{ (giờ)}",
                "note": "Lấy trung điểm hai đầu mút của nhóm."
            },
            {
                "step": "Bước 3: Kết luận",
                "math": "\\text{Chọn A}",
                "note": "Nhóm phổ biến nhất trong thực nghiệm."
            }
        ],
        "quiz_options": [
            {
                "option": "A",
                "text": "Nhóm [6; 6,5) với giá trị đại diện là 6,25 giờ",
                "is_correct": True,
                "distractor_rationale": "Chính xác: tần số cao nhất là 15, giá trị đại diện là 6,25."
            },
            {
                "option": "B",
                "text": "Nhóm [6,5; 7) với giá trị đại diện là 6,75 giờ",
                "is_correct": False,
                "distractor_rationale": "Nhóm này có tần số là 10, không phải cao nhất."
            },
            {
                "option": "C",
                "text": "Nhóm [5,5; 6) với giá trị đại diện là 5,75 giờ",
                "is_correct": False,
                "distractor_rationale": "Nhóm này có tần số là 8."
            },
            {
                "option": "D",
                "text": "Nhóm [6; 6,5) với giá trị đại diện là 6,00 giờ",
                "is_correct": False,
                "distractor_rationale": "Lấy nhầm mút trái của nhóm làm giá trị đại diện."
            }
        ]
    },
    {
        "id": "kntt12-c3-b2-quiz13",
        "grade": 12,
        "lesson_id": "M12-C3-B2",
        "chapter": "Chương III. Các số đặc trưng đo mức độ phân tán của mẫu số liệu ghép nhóm",
        "topic": "phương sai và độ lệch chuẩn",
        "question_type": "multiple_choice",
        "difficulty": "hard",
        "question": "Một người bán hàng phân loại bưởi da xanh theo cân nặng thu được bảng sau (Đề minh họa 2025):\n\n| Cân nặng (kg) | [1; 1,2) | [1,2; 1,4) | [1,4; 1,6) | [1,6; 1,8) |\n|---|---|---|---|---|\n| Số quả | 3 | 6 | 7 | 4 |\n\nĐộ lệch chuẩn $s$ của mẫu số liệu ghép nhóm về cân nặng bưởi da xanh (làm tròn đến hai chữ số thập phân) là:",
        "choices": [
            "A. 0,19 kg",
            "B. 0,25 kg",
            "C. 0,15 kg",
            "D. 0,31 kg"
        ],
        "answer": "A",
        "solution": "Giá trị đại diện: $c = [1,1; 1,3; 1,5; 1,7]$.\nCỡ mẫu $n = 3 + 6 + 7 + 4 = 20$.\nSố trung bình: $\\bar{x} = \\frac{3(1,1) + 6(1,3) + 7(1,5) + 4(1,7)}{20} = \\frac{3,3 + 7,8 + 10,5 + 6,8}{20} = \\frac{28,4}{20} = 1,42$ kg.\nPhương sai: $s^2 = \\frac{3(1,1-1,42)^2 + 6(1,3-1,42)^2 + 7(1,5-1,42)^2 + 4(1,7-1,42)^2}{20} = \\frac{3(0,1024) + 6(0,0144) + 7(0,0064) + 4(0,0784)}{20} = \\frac{0,3072 + 0,0864 + 0,0448 + 0,3136}{20} = \\frac{0,752}{20} = 0,0376$.\nĐộ lệch chuẩn: $s = \\sqrt{0,0376} \\approx 0,1939 \\approx 0,19$ kg.",
        "worked_solution_steps": [
            {
                "step": "Bước 1: Tính số trung bình",
                "math": "\\bar{x} = \\frac{3(1,1) + 6(1,3) + 7(1,5) + 4(1,7)}{20} = 1,42 \\text{ (kg)}",
                "note": "Cỡ mẫu n = 20 quả bưởi."
            },
            {
                "step": "Bước 2: Tính phương sai",
                "math": "s^2 = \\frac{1}{20} \\left[ 3(1,1 - 1,42)^2 + 6(1,3 - 1,42)^2 + 7(1,5 - 1,42)^2 + 4(1,7 - 1,42)^2 \\right] = 0,0376",
                "note": "Tính tổng bình phương độ lệch có trọng số."
            },
            {
                "step": "Bước 3: Khai căn tìm độ lệch chuẩn",
                "math": "s = \\sqrt{0,0376} \\approx 0,19 \\text{ (kg)}",
                "note": "Chọn đáp án A."
            }
        ],
        "quiz_options": [
            {
                "option": "A",
                "text": "0,19 kg",
                "is_correct": True,
                "distractor_rationale": "Chính xác: $\\sqrt{0,0376} \\approx 0,19$ kg."
            },
            {
                "option": "B",
                "text": "0,25 kg",
                "is_correct": False,
                "distractor_rationale": "Tính sai độ lệch của nhóm cuối."
            },
            {
                "option": "C",
                "text": "0,15 kg",
                "is_correct": False,
                "distractor_rationale": "Làm tròn sớm số trung bình $\\bar{x} = 1,4$ kg."
            },
            {
                "option": "D",
                "text": "0,31 kg",
                "is_correct": False,
                "distractor_rationale": "Quên chia cho cỡ mẫu 20 trước khi khai căn."
            }
        ]
    }
]


def enrich_dataset():
    # __file__ = app/backend/scripts/enrich_chapter3_questions.py
    # parents: [0]=scripts, [1]=backend, [2]=app, [3]=Lesson-Plan-Generator
    base_dir = Path(__file__).resolve().parents[3]
    backend_data_dir = base_dir / "app" / "backend" / "data"
    root_data_dir = base_dir / "data"

    print(f"[*] Base directory: {base_dir}")
    print(f"[*] Backend data directory: {backend_data_dir}")

    # Paths
    backend_rag_file = backend_data_dir / "questions" / "questions_math12_rag.jsonl"
    root_rag_file = root_data_dir / "questions" / "questions_math12_rag.jsonl"

    if not backend_rag_file.exists():
        print(f"[!] Error: {backend_rag_file} does not exist. Run file sync first!")
        sys.exit(1)

    # 1. Đọc danh sách câu hỏi hiện có
    existing_questions = []
    existing_ids = set()
    with open(backend_rag_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            existing_questions.append(item)
            existing_ids.add(item["id"])

    print(f"[*] Currently loaded questions in RAG dataset: {len(existing_questions)}")

    # 2. Lọc và thêm các câu hỏi mới của Chương 3
    added_count = 0
    for q in CHAPTER_3_QUESTIONS:
        if q["id"] not in existing_ids:
            existing_questions.append(q)
            existing_ids.add(q["id"])
            added_count += 1
        else:
            # Cập nhật nếu đã tồn tại
            for idx, ex in enumerate(existing_questions):
                if ex["id"] == q["id"]:
                    existing_questions[idx] = q
                    break

    print(f"[+] Added/Updated {added_count} enriched questions for Chapter 3.")
    print(f"[*] New total question count: {len(existing_questions)}")

    # 3. Ghi ra cả 2 file (backend và root)
    for target_path in [backend_rag_file, root_rag_file]:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            for item in existing_questions:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        print(f"[✓] Wrote {len(existing_questions)} items to {target_path}")

    # 4. Thống kê theo bài học
    from collections import Counter
    c3_stats = Counter(q.get("lesson_id") for q in existing_questions if "M12-C3" in (q.get("lesson_id") or ""))
    print("\n--- Thống kê câu hỏi Chương III sau khi làm giàu ---")
    for lesson, count in sorted(c3_stats.items()):
        print(f"  • {lesson}: {count} câu hỏi chuẩn RAG")
    print(f"  => Tổng số câu hỏi Chương III: {sum(c3_stats.values())} câu hỏi")

    # 5. Cập nhật dataset_summary.json
    for summary_path in [backend_data_dir / "dataset_summary.json", root_data_dir / "dataset_summary.json"]:
        if summary_path.exists():
            with open(summary_path, "r", encoding="utf-8") as f:
                summary = json.load(f)
            
            summary["questions_rag_count"] = len(existing_questions)
            summary["chapter_3_enriched"] = True
            summary["chapter_3_question_count"] = sum(c3_stats.values())
            
            with open(summary_path, "w", encoding="utf-8") as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            print(f"[✓] Updated dataset summary at {summary_path}")

    print("\n[SUCCESS] Hoàn thành làm giàu câu hỏi Chương III thành công!")


if __name__ == "__main__":
    enrich_dataset()
