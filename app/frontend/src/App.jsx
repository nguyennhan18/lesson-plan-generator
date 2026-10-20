import React, { useState, useEffect } from 'react';
import HeaderNav from './components/HeaderNav';
import PresentationStage from './components/PresentationStage';
import TeacherChatDock from './components/TeacherChatDock';
import RightToolsDock from './components/RightToolsDock';
import LessonPlanScreen from './components/LessonPlanScreen';
import SlideEditorScreen from './components/SlideEditorScreen';
import AnalyticsScreen from './components/AnalyticsScreen';
import {
  loadSlideDeckFromBrowserMemory,
  saveSlideDeckToBrowserMemory
} from './utils/slideDeckStorage';

// ==============================================================================
// 1. DỮ LIỆU BÀI MẪU CHUẨN MỰC: PHƯƠNG TRÌNH BẬC HAI (TOÁN 10)
// Tích hợp KaTeX, Đồ thị Parabol 2D, Tình huống bóng rổ thực tiễn & Bẫy sai lầm
// ==============================================================================
const SAMPLE_QUADRATIC_DECK = {
  presentation_title: "Phương Trình Bậc Hai Một Ẩn & Ứng Dụng Đồ Thị Parabol",
  subject: "Toán học",
  grade: 10,
  slides: [
    {
      slide_number: 1,
      title: "Khởi Động • Quỹ Đạo Ném Bóng Rổ Của Stephen Curry",
      activity_type: "KHỞI ĐỘNG & ĐẶT VẤN ĐỀ",
      layout: "IMAGE_TEXT",
      bullet_points: [
        "Quả bóng rổ được ném theo quỹ đạo Parabol có độ cao: $h(t) = -0.5t^2 + 2t + 2.5$ (mét).",
        "Khi quả bóng rơi xuống sàn ($h(t) = 0$), ta thu được phương trình: $-0.5t^2 + 2t + 2.5 = 0$.",
        "Câu hỏi khám phá: Sau bao nhiêu giây quả bóng chạm đất?",
        "Bản chất: Đây là bài toán tìm nghiệm của Phương trình bậc hai một ẩn $ax^2 + bx + c = 0$ ($a \\neq 0$)."
      ],
      main_definition_latex: "ax^2 + bx + c = 0 \\quad (a \\neq 0)",
      teacher_note: "Trình chiếu đồ thị Parabol, hướng dẫn học sinh nhận xét: Điểm bóng chạm đất chính là giao điểm của Parabol với trục hoành Ox.",
      chart_spec: {
        kind: "function_plot",
        expression: "-0.5*x**2 + 2*x + 2.5",
        chart_title: "Quỹ đạo ném bóng Parabol h(t)",
        pedagogical_purpose: "Minh họa quỹ đạo thực tiễn giúp học sinh thấy ý nghĩa của bài toán giải phương trình bậc hai."
      },
      has_3d: false
    },
    {
      slide_number: 2,
      title: "1. Bản Chất Hình Học Của Biệt Thức $\\Delta = b^2 - 4ac$",
      activity_type: "HÌNH THÀNH KIẾN THỨC",
      layout: "IMAGE_TEXT",
      bullet_points: [
        "Số nghiệm của phương trình $ax^2 + bx + c = 0$ bằng số giao điểm của Parabol $y = ax^2 + bx + c$ với trục $Ox$.",
        "Trường hợp $\\Delta > 0$: Parabol cắt trục hoành tại 2 điểm phân biệt $\\implies$ 2 nghiệm phân biệt $x_{1,2} = \\frac{-b \\pm \\sqrt{\\Delta}}{2a}$.",
        "Trường hợp $\\Delta = 0$: Đỉnh Parabol tiếp xúc trục hoành $\\implies$ Nghiệm kép $x_0 = -\\frac{b}{2a}$.",
        "Trường hợp $\\Delta < 0$: Parabol không cắt trục hoành $\\implies$ Phương trình vô nghiệm trên $\\mathbb{R}$."
      ],
      main_definition_latex: "\\Delta = b^2 - 4ac \\quad | \\quad x_{1,2} = \\frac{-b \\pm \\sqrt{\\Delta}}{2a}",
      teacher_note: "Nhấn mạnh liên hệ hình học: Biệt thức Delta đo khoảng cách từ đỉnh parabol tới trục hoành Ox.",
      chart_spec: {
        kind: "function_plot",
        expression: "x**2 - 4",
        chart_title: "Parabol y = x² - 4 (Δ = 16 > 0, cắt Ox tại x = ±2)",
        pedagogical_purpose: "Học sinh nhìn thấy tận mắt 2 nghiệm x1 = -2, x2 = 2 trên hệ trục Oxy."
      },
      has_3d: false
    },
    {
      slide_number: 3,
      title: "2. Quy Trình 4 Bước Giải Phương Trình Bậc Hai Chuẩn Mực",
      activity_type: "HÌNH THÀNH KỸ NĂNG",
      layout: "IMAGE_TEXT",
      bullet_points: [
        "Bước 1 (Xác định hệ số): Biến đổi về dạng chính tắc $ax^2 + bx + c = 0$, ghi rõ $a, b, c$ (Lưu ý dấu âm!).",
        "Bước 2 (Tính biệt thức): $\\Delta = b^2 - 4ac$. Chú ý $(-b)^2$ luôn dương, tránh tính nhầm $-b^2$.",
        "Bước 3 (Biện luận số nghiệm): So sánh $\\Delta$ với 0 để xác định số nghiệm.",
        "Bước 4 (Tính nghiệm & Kết luận): Sử dụng công thức nghiệm thu gọn hoặc tổng quát, kết luận tập nghiệm $S$."
      ],
      main_definition_latex: "S = \\left\\{ \\frac{-b - \\sqrt{\\Delta}}{2a}; \\frac{-b + \\sqrt{\\Delta}}{2a} \\right\\}",
      teacher_note: "Nhắc nhở học sinh bẫy sai lầm kinh điển: quên đổi dấu -b trong công thức nghiệm.",
      chart_spec: {
        kind: "function_plot",
        expression: "x**2 - 2*x - 3",
        chart_title: "Đồ thị Parabol y = x² - 2x - 3 (Nghiệm x = -1 và x = 3)",
        pedagogical_purpose: "Minh họa ví dụ giải phương trình cụ thể x² - 2x - 3 = 0."
      },
      has_3d: false
    },
    {
      slide_number: 4,
      title: "3. Định Lý Vi-ét & Kỹ Thuật Nhẩm Nhanh Nghiệm",
      activity_type: "LUYỆN TẬP & MỞ RỘNG",
      layout: "IMAGE_TEXT",
      bullet_points: [
        "Hệ thức Vi-ét: Tổng 2 nghiệm $S = x_1 + x_2 = -\\frac{b}{a}$, Tích 2 nghiệm $P = x_1 x_2 = \\frac{c}{a}$.",
        "Trường hợp đặc biệt 1: Nếu $a + b + c = 0 \\implies x_1 = 1, x_2 = \\frac{c}{a}$.",
        "Trường hợp đặc biệt 2: Nếu $a - b + c = 0 \\implies x_1 = -1, x_2 = -\\frac{c}{a}$.",
        "Phân tích đa thức thành nhân tử: $ax^2 + bx + c = a(x - x_1)(x - x_2)$."
      ],
      main_definition_latex: "x_1 + x_2 = -\\frac{b}{a} \\quad | \\quad x_1 x_2 = \\frac{c}{a}",
      teacher_note: "Tổ chức cho học sinh thi đua nhẩm nghiệm nhanh phương trình x² - 5x + 6 = 0 trong 10 giây.",
      chart_spec: {
        kind: "function_plot",
        expression: "x**2 - 5*x + 6",
        chart_title: "Đồ thị y = x² - 5x + 6 (Nhẩm nghiệm x = 2, x = 3)",
        pedagogical_purpose: "Trực quan hóa hai nghiệm x1 = 2 và x2 = 3 của định lý Vi-ét."
      },
      has_3d: false
    },
    {
      slide_number: 5,
      title: "4. Thử Thách Cả Lớp (Live Poll) • Phân Tích Bẫy Sai Lầm",
      activity_type: "VẬN DỤNG & QUIZ TRỰC TIẾP",
      layout: "QUIZ_OPTION",
      bullet_points: [
        "Cho phương trình $x^2 - 2(m-1)x + m^2 - 3 = 0$. Tìm điều kiện của tham số $m$ để phương trình có hai nghiệm phân biệt?"
      ],
      quiz_options: [
        { label: "A", text: "$m < 2$", is_correct: true, distractor_rationale: "Chính xác! $\\Delta' = (m-1)^2 - (m^2 - 3) = -2m + 4 > 0 \\iff m < 2$." },
        { label: "B", text: "$m > 2$", is_correct: false, distractor_rationale: "Sai. Quên đổi chiều bất đẳng thức khi chia hai vế cho số âm (-2)." },
        { label: "C", text: "$m \\leq 2$", is_correct: false, distractor_rationale: "Sai. Yêu cầu hai nghiệm phân biệt nên bắt buộc $\\Delta' > 0$ ngặt (không có dấu bằng)." },
        { label: "D", text: "$m < -2$", is_correct: false, distractor_rationale: "Sai. Nhầm dấu khi khai triển hằng đẳng thức $(m-1)^2$ thành $m^2 - 2m - 1$." }
      ],
      teacher_note: "Mở hộp giải thích bẫy sai lầm, phân tích lý do nhiều học sinh chọn phương án B và C.",
      has_3d: false
    }
  ]
};

const SAMPLE_QUADRATIC_PLAN = {
  lesson_title: "Phương trình bậc hai một ẩn và định lý Vi-ét",
  subject: "Toán học",
  grade: 10,
  duration_periods: 1,
  knowledge_goals: [
    "Hiểu bản chất hình học của biệt thức Delta (Δ = b² - 4ac) thông qua số giao điểm của Parabol y = ax² + bx + c với trục hoành Ox.",
    "Nắm vững và vận dụng thành thạo quy trình 4 bước giải phương trình bậc hai một ẩn cùng công thức nghiệm tổng quát.",
    "Hiểu và vận dụng hệ thức Vi-ét (S = -b/a, P = c/a) để nhẩm nghiệm nhanh và tính giá trị biểu thức đối xứng của nghiệm."
  ],
  competency_goals: [
    "Năng lực tư duy và lập luận toán học: Biện luận số nghiệm phương trình chứa tham số m.",
    "Năng lực mô hình hóa toán học: Thiết lập phương trình bậc hai từ bài toán quỹ đạo ném bóng Parabol thực tiễn."
  ],
  skills_goals: [
    "Biến đổi đại số chính xác, tránh bẫy sai dấu (-b) và khai triển hằng đẳng thức.",
    "Đọc và phân tích đồ thị hàm số bậc hai trên mặt phẳng tọa độ Oxy."
  ],
  character_goals: [
    "Rèn luyện tính cẩn thận, chính xác khi thực hiện biến đổi đại số; tinh thần trách nhiệm và hợp tác trong hoạt động nhóm."
  ],
  teaching_equipment: [
    "Giáo viên: Bộ Slide tương tác tích hợp đồ thị Parabol 2D trực quan, phiếu học tập nhóm.",
    "Học sinh: Sách giáo khoa Toán 10, máy tính cầm tay, bảng phụ nhóm."
  ],
  objectives: {
    knowledge: "Học sinh hiểu bản chất hình học của biệt thức Delta qua giao điểm của Parabol với trục Ox; thành thạo 4 bước giải và công thức nghiệm; vận dụng định lý Vi-ét tính tổng và tích nghiệm.",
    competencies: "Năng lực tư duy và lập luận toán học; năng lực mô hình hóa toán học qua bài toán quỹ đạo ném bóng Parabol; năng lực giải quyết vấn đề.",
    qualities: "Tính cẩn thận, chính xác khi thực hiện biến đổi đại số; tinh thần trung thực và trách nhiệm trong học tập."
  },
  activities: [
    {
      activity_number: 1,
      name: "Khởi động: Bài toán quỹ đạo ném bóng rổ Parabol",
      goal: "Mở đầu / Khởi động: Tạo hứng thú và nhận biết nhu cầu giải phương trình bậc hai qua bài toán quỹ đạo ném bóng rổ thực tế.",
      time_minutes: 7,
      objective: "Học sinh quan sát chuyển động ném bóng rổ thực tế, thiết lập phương trình độ cao -0.5t² + 2t + 2.5 = 0 và nhận biết nhu cầu giải phương trình bậc hai một ẩn.",
      expected_product: "Học sinh viết được phương trình -0.5t² + 2t + 2.5 = 0 và xác định được các hệ số a = -0.5, b = 2, c = 2.5.",
      execution: {
        step_1_assign: "GV chiếu mô phỏng quỹ đạo ném bóng rổ h(t) = -0.5t² + 2t + 2.5 và đặt câu hỏi: Khi bóng chạm sàn (h=0), làm thế nào tìm được thời điểm t?",
        step_2_excute: "HS thảo luận cặp đôi, thay h(t) = 0 để lập phương trình đại số và nhận xét bậc của ẩn t.",
        step_3_report: "Đại diện 2 nhóm trình bày phương trình thu được và chỉ ra vị trí bóng chạm đất trên đồ thị Parabol.",
        step_4_conclusion: "GV nhận xét, chốt định nghĩa phương trình bậc hai một ẩn ax² + bx + c = 0 (a ≠ 0) và dẫn dắt vào bài mới."
      }
    },
    {
      activity_number: 2,
      name: "Hình thành kiến thức: Biệt thức Delta và Ý nghĩa hình học",
      goal: "Hình thành kiến thức / Khám phá: Xây dựng công thức nghiệm tổng quát và liên hệ trực quan với đồ thị Parabol.",
      time_minutes: 18,
      objective: "Học sinh xây dựng công thức nghiệm qua phương pháp biến đổi bình phương; liên hệ trực quan số nghiệm với số giao điểm giữa Parabol y = ax² + bx + c và trục Ox.",
      expected_product: "Bảng tổng kết 3 trường hợp của Δ (Δ > 0, Δ = 0, Δ < 0) gắn liền với hình ảnh giao điểm Parabol và trục hoành Ox.",
      execution: {
        step_1_assign: "GV yêu cầu HS quan sát 3 đồ thị Parabol tương ứng Δ > 0, Δ = 0, Δ < 0 và hoàn thành bảng mối liên hệ giữa số giao điểm với trục Ox và số nghiệm.",
        step_2_excute: "HS thực hiện biến đổi đưa ax² + bx + c = 0 về dạng (x + b/2a)² = Δ / 4a² dưới sự hướng dẫn của GV.",
        step_3_report: "HS lên bảng trình bày công thức nghiệm trong 3 trường hợp của biệt thức Δ.",
        step_4_conclusion: "GV chốt công thức nghiệm tổng quát, nhấn mạnh ý nghĩa hình học của Δ và lưu ý bẫy sai dấu -b."
      }
    },
    {
      activity_number: 3,
      name: "Luyện tập: Quy trình 4 bước giải và Định lý Vi-ét",
      goal: "Luyện tập: Rèn luyện kỹ năng giải phương trình bậc hai theo 4 bước chuẩn mực và nhẩm nghiệm nhanh bằng hệ thức Vi-ét.",
      time_minutes: 12,
      objective: "Học sinh rèn luyện kỹ năng giải phương trình, tránh bẫy sai lầm dấu âm (-b), và thành thạo kỹ thuật nhẩm nghiệm nhanh a+b+c=0 và a-b+c=0.",
      expected_product: "Lời giải chi tiết các phương trình x² - 2x - 3 = 0, x² - 5x + 6 = 0 trên phiếu học tập.",
      execution: {
        step_1_assign: "GV giao 2 bài tập trên phiếu học tập: Bài 1 giải theo quy trình 4 bước; Bài 2 áp dụng định lý Vi-ét nhẩm nghiệm nhanh trong 15 giây.",
        step_2_excute: "HS làm việc cá nhân rồi trao đổi chéo kiểm tra bước xác định hệ số a, b, c và bước tính Δ.",
        step_3_report: "3 HS trình bày lời giải, cả lớp đối chiếu với giao điểm trên đồ thị Parabol 2D.",
        step_4_conclusion: "GV tổng kết các lỗi sai thường gặp (quên đổi dấu -b, tính nhầm -b²) và khen thưởng nhóm làm nhanh nhất."
      }
    },
    {
      activity_number: 4,
      name: "Vận dụng: Tìm tham số m và Giải quyết tình huống thực tế",
      goal: "Vận dụng: Giải quyết bài toán tìm tham số m để phương trình có hai nghiệm phân biệt qua Live Poll tương tác.",
      time_minutes: 8,
      objective: "Học sinh tham gia Live Poll tương tác, tìm điều kiện tham số m để phương trình có 2 nghiệm phân biệt và phân tích các bẫy sai lầm thường gặp.",
      expected_product: "Học sinh tìm đúng điều kiện m < 2 cho phương trình x² - 2(m-1)x + m² - 3 = 0 và giải thích được bẫy chia số âm.",
      execution: {
        step_1_assign: "GV mở câu hỏi trắc nghiệm Live Poll trên màn hình: Tìm m để x² - 2(m-1)x + m² - 3 = 0 có hai nghiệm phân biệt.",
        step_2_excute: "HS tính nhanh Δ' = (m-1)² - (m² - 3) = -2m + 4 > 0 và chọn đáp án A, B, C hoặc D.",
        step_3_report: "GV công bố tỷ lệ bình chọn và mời HS giải thích tại sao phương án B (m > 2) và C (m ≤ 2) là bẫy sai lầm.",
        step_4_conclusion: "GV chốt bài học, dặn dò bài tập về nhà và hướng dẫn chuẩn bị bài dấu của tam thức bậc hai."
      }
    }
  ]
};

// ==============================================================================
// 2. DỮ LIỆU BÀI MẪU: HÌNH LẬP PHƯƠNG (TOÁN 11)
// ==============================================================================
const SAMPLE_CUBE_DECK = {
  presentation_title: "Hình Lập Phương & Quan Hệ Vuông Góc Trong Không Gian",
  subject: "Toán học",
  grade: 11,
  slides: [
    {
      slide_number: 1,
      title: "Hình Lập Phương ABCD.A'B'C'D' • Khối Đa Diện Đều",
      activity_type: "KHỞI ĐỘNG & ĐẶT VẤN ĐỀ",
      layout: "IMAGE_TEXT",
      bullet_points: [
        "Cho hình lập phương ABCD.A'B'C'D' có tất cả các cạnh bằng $a$.",
        "Đáy dưới $ABCD$ và đáy trên $A'B'C'D'$ là hai hình vuông bằng nhau.",
        "Các cạnh bên $AA', BB', CC', DD'$ vuông góc với hai mặt phẳng đáy.",
        "Hình gồm 8 đỉnh, 12 cạnh bằng nhau và 6 mặt hình vuông đối xứng."
      ],
      main_definition_latex: "V = a^3 \\quad | \\quad S_{tp} = 6a^2",
      teacher_note: "Chiếu mô hình 3D, yêu cầu học sinh quan sát các mặt phẳng song song và vuông góc.",
      has_3d: true
    },
    {
      slide_number: 2,
      title: "1. Đường Chéo AC' & Góc Giữa Đường Thẳng Với Mặt Phẳng",
      activity_type: "HÌNH THÀNH KIẾN THỨC",
      layout: "IMAGE_TEXT",
      bullet_points: [
        "Bước 1: Trong mặt phẳng đáy $(ABCD)$, $AC = \\sqrt{AB^2 + BC^2} = a\\sqrt{2}$.",
        "Bước 2: Vì $CC' \\perp (ABCD)$ nên tam giác $ACC'$ vuông tại $C$.",
        "Bước 3: Áp dụng định lý Pytago trong tam giác $ACC'$: $AC' = a\\sqrt{3}$."
      ],
      main_definition_latex: "AC' = \\sqrt{(a\\sqrt{2})^2 + a^2} = a\\sqrt{3}",
      teacher_note: "Nhắc học sinh không nhầm giữa đường chéo sàn a√2 và đường chéo không gian a√3.",
      has_3d: true
    },
    {
      slide_number: 3,
      title: "2. Đoạn Vuông Góc Chung AH ⊥ B'D' & Khoảng Cách",
      activity_type: "HÌNH THÀNH KIẾN THỨC",
      layout: "IMAGE_TEXT",
      bullet_points: [
        "Xét tam giác $AB'D'$ cân tại $A$ có $B'D' = a\\sqrt{2}$.",
        "Kẻ $AH \\perp B'D'$ tại trung điểm $H$ của đoạn $B'D'$.",
        "Độ dài khoảng cách: $AH = \\sqrt{AB'^2 - B'H^2} = a\\sqrt{3/2}$."
      ],
      main_definition_latex: "AH = \\frac{a\\sqrt{6}}{2} \\approx 1.22a",
      teacher_note: "Xoay mô hình sang góc nhìn trực diện để học sinh thấy rõ đoạn vuông góc đỏ AH.",
      has_3d: true
    },
    {
      slide_number: 4,
      title: "3. Thiết Diện Mặt Phẳng (A'BD) & Diện Tích",
      activity_type: "LUYỆN TẬP & CỦNG CỐ",
      layout: "IMAGE_TEXT",
      bullet_points: [
        "Ba đoạn thẳng nối các đỉnh: $A'B = BD = DA' = a\\sqrt{2}$.",
        "Thiết diện tạo bởi mặt phẳng $(A'BD)$ cắt hình lập phương là tam giác đều.",
        "Diện tích thiết diện: $S = \\frac{(\\text{cạnh})^2 \\sqrt{3}}{4}$."
      ],
      main_definition_latex: "S_{A'BD} = \\frac{(a\\sqrt{2})^2 \\sqrt{3}}{4} = \\frac{a^2\\sqrt{3}}{2}",
      teacher_note: "Bật chế độ mặt phẳng cắt màu lam trong suốt để học sinh quan sát thiết diện.",
      has_3d: true
    },
    {
      slide_number: 5,
      title: "4. Khảo Sát Nhanh Cả Lớp (Live Poll) • Góc Giữa AC & A'D",
      activity_type: "VẬN DỤNG & QUIZ TRỰC TIẾP",
      layout: "QUIZ_OPTION",
      bullet_points: [
        "Trong hình lập phương $ABCD.A'B'C'D'$, góc giữa $AC$ và $A'D$ bằng bao nhiêu độ?"
      ],
      quiz_options: [
        { label: "A", text: "$60^\\circ$", is_correct: true, distractor_rationale: "Chính xác! Do AC // A'C' nên góc(AC, A'D) = góc(A'C', A'D) = 60° (tam giác A'C'D đều)." },
        { label: "B", text: "$90^\\circ$", is_correct: false, distractor_rationale: "Sai. Học sinh nhầm lẫn giữa hai đường chéo của cùng một mặt vuông." },
        { label: "C", text: "$45^\\circ$", is_correct: false, distractor_rationale: "Sai. 45° là góc giữa đường chéo đáy và một cạnh đáy kề." },
        { label: "D", text: "$120^\\circ$", is_correct: false, distractor_rationale: "Sai. Góc giữa hai đường thẳng trong không gian quy ước không vượt quá 90°." }
      ],
      teacher_note: "Bấm nút bình chọn và mở phần giải thích bẫy sai lầm cho học sinh.",
      has_3d: false
    }
  ]
};

const SAMPLE_CUBE_PLAN = {
  lesson_title: "Hình lập phương & Quan hệ vuông góc trong không gian",
  subject: "Toán học",
  grade: 11,
  duration_periods: 1,
  knowledge_goals: [
    "Xác định được góc giữa đường thẳng và mặt phẳng trong hình lập phương.",
    "Tính được độ dài đường chéo không gian AC' = a√3 và diện tích thiết diện (A'BD)."
  ],
  competency_goals: [
    "Năng lực tưởng tượng không gian 3D và mô hình hóa hình học."
  ],
  skills_goals: [
    "Vẽ hình biểu diễn và xác định hình chiếu vuông góc trên mặt phẳng đáy."
  ],
  character_goals: [
    "Chăm chỉ, tư duy trực quan hình học khoa học."
  ],
  teaching_equipment: [
    "Mô hình 3D WebGL hình lập phương ABCD.A'B'C'D' tương tác trực tiếp."
  ],
  objectives: {
    knowledge: "Học sinh xác định được góc giữa đường thẳng và mặt phẳng, tính độ dài đường chéo AC' = a√3 và dựng được thiết diện mặt phẳng (A'BD).",
    competencies: "Năng lực tưởng tượng không gian 3D, năng lực tính toán hình học không gian.",
    qualities: "Chăm chỉ, tư duy trực quan hình học khoa học."
  },
  activities: [
    {
      activity_number: 1,
      name: "Khởi động: Nhận diện hình lập phương trong thực tế",
      goal: "Mở đầu / Khởi động: Nhận diện các tính chất đối xứng và vuông góc của hình lập phương.",
      time_minutes: 5,
      objective: "Học sinh quan sát khối rubik, hộp quà và mô hình 3D hình lập phương.",
      expected_product: "Học sinh nêu được 8 đỉnh, 12 cạnh bằng nhau và 6 mặt hình vuông.",
      execution: {
        step_1_assign: "GV chiếu mô hình 3D hình lập phương và yêu cầu HS chỉ ra các cạnh bên vuông góc với mặt đáy.",
        step_2_excute: "HS quan sát mô hình xoay 360 độ và liệt kê các cặp đường thẳng vuông góc.",
        step_3_report: "Đại diện HS trả lời nhanh tại chỗ.",
        step_4_conclusion: "GV chốt lại tính chất AA', BB', CC', DD' cùng vuông góc với hai đáy."
      }
    },
    {
      activity_number: 2,
      name: "Hình thành kiến thức: Đường chéo AC' và góc đường - mặt",
      goal: "Hình thành kiến thức / Khám phá: Chứng minh công thức đường chéo AC' = a√3.",
      time_minutes: 20,
      objective: "Chứng minh CC' vuông góc đáy và tính độ dài AC' = a√3 qua định lý Pytago.",
      expected_product: "Chứng minh tam giác ACC' vuông tại C và tính đúng AC' = a√3.",
      execution: {
        step_1_assign: "GV yêu cầu HS xác định hình chiếu của AC' lên mặt phẳng (ABCD) và tính AC'.",
        step_2_excute: "HS áp dụng định lý Pytago trong tam giác ABC và tam giác ACC'.",
        step_3_report: "HS lên bảng trình bày các bước tính toán.",
        step_4_conclusion: "GV tổng quát hóa công thức đường chéo hình lập phương cạnh a là a√3."
      }
    },
    {
      activity_number: 3,
      name: "Luyện tập: Dựng thiết diện (A'BD)",
      goal: "Luyện tập: Xác định thiết diện tạo bởi mặt phẳng (A'BD) và tính diện tích.",
      time_minutes: 12,
      objective: "Chứng minh thiết diện là tam giác đều cạnh a√2 và tính diện tích.",
      expected_product: "Tính đúng diện tích S = (a²√3)/2.",
      execution: {
        step_1_assign: "GV bật mặt phẳng cắt (A'BD) trên mô hình 3D và yêu cầu HS nhận xét tam giác A'BD.",
        step_2_excute: "HS tính độ dài 3 cạnh A'B, BD, DA' và áp dụng công thức diện tích tam giác đều.",
        step_3_report: "Đại diện nhóm báo cáo kết quả.",
        step_4_conclusion: "GV nhận xét và chốt phương pháp dựng thiết diện."
      }
    },
    {
      activity_number: 4,
      name: "Vận dụng: Live Poll góc giữa hai đường chéo",
      goal: "Vận dụng: Xác định góc giữa hai đường thẳng chéo nhau AC và A'D trong không gian.",
      time_minutes: 8,
      objective: "Xác định góc 60 độ giữa AC và A'D qua quan hệ song song.",
      expected_product: "HS chọn đúng đáp án 60 độ và giải thích được vì sao tam giác A'C'D đều.",
      execution: {
        step_1_assign: "GV mở câu hỏi Live Poll: Góc giữa AC và A'D bằng bao nhiêu độ?",
        step_2_excute: "HS kẻ đường thẳng song song AC là A'C' và xét tam giác A'C'D.",
        step_3_report: "HS giải thích lý do chọn đáp án A (60°).",
        step_4_conclusion: "GV tổng kết bài học và giao nhiệm vụ về nhà."
      }
    }
  ]
};

export default function App() {
  const [activeScreen, setActiveScreen] = useState('presentation'); // 'presentation' | 'lesson-plan' | 'slide-editor' | 'analytics'
  const [currentSlide, setCurrentSlide] = useState(0);

  // Cockpit Dock States
  const [isLeftOpen, setIsLeftOpen] = useState(true);
  const [isRightOpen, setIsRightOpen] = useState(false);

  // 3D Geometry Shared Parameters
  const [polyhedronType, setPolyhedronType] = useState('cube');
  const [edgeLength, setEdgeLength] = useState(4.0);
  const [showHiddenLines, setShowHiddenLines] = useState(true);
  const [showVertexLabels, setShowVertexLabels] = useState(true);
  const [showAxes, setShowAxes] = useState(false);
  const [cameraPreset, setCameraPreset] = useState('iso');

  // ================= CENTRAL STATE (ĐỒNG BỘ 2 CHIỀU VỚI BỘ NHỚ TRÌNH DUYỆT - TASK 9.2) =================
  const [slideDeck, setSlideDeck] = useState(() =>
    loadSlideDeckFromBrowserMemory(SAMPLE_QUADRATIC_DECK)
  );
  const [lessonPlan, setLessonPlan] = useState(SAMPLE_QUADRATIC_PLAN);

  // Task 9.2: Tự động đồng bộ cấu trúc Slide JSON vào bộ nhớ trình duyệt (sessionStorage) mỗi khi cập nhật
  useEffect(() => {
    saveSlideDeckToBrowserMemory(slideDeck);
  }, [slideDeck]);

  // State đồng bộ Phân tích Bảng điểm Z-Score -> Soạn Giáo Án 5512
  const [analyticsData, setAnalyticsData] = useState(null);
  const [classProficiency, setClassProficiency] = useState('standard');
  const [recommendedOutcome, setRecommendedOutcome] = useState('');

  // 3. Trạng thái Loading khi gọi Gemini AI
  const [isAiGenerating, setIsAiGenerating] = useState(false);
  const [generationStep, setGenerationStep] = useState('');

  const handleClassificationSuccess = (result) => {
    setAnalyticsData(result);
    if (result?.class_label) {
      setClassProficiency(result.class_label);
    }
    if (result?.target_outcome) {
      setRecommendedOutcome(result.target_outcome);
    }
  };

  const handleApplyAnalyticsToLessonPlan = (proficiencyLabel, outcomeText) => {
    if (proficiencyLabel) setClassProficiency(proficiencyLabel);
    if (outcomeText) setRecommendedOutcome(outcomeText);
    setActiveScreen('lesson-plan');
  };

  // Hàm chuyển đổi nhanh giữa các bài mẫu (Quick Topic Switcher)
  const handleSwitchSample = (type) => {
    if (type === 'quadratic') {
      setSlideDeck(SAMPLE_QUADRATIC_DECK);
      setLessonPlan(SAMPLE_QUADRATIC_PLAN);
      setCurrentSlide(0);
    } else {
      setSlideDeck(SAMPLE_CUBE_DECK);
      setLessonPlan(SAMPLE_CUBE_PLAN);
      setPolyhedronType('cube');
      setCurrentSlide(0);
    }
  };

  // Keyboard Shortcuts Handler
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (['INPUT', 'TEXTAREA', 'SELECT', 'MATH-FIELD'].includes(e.target.tagName)) return;

      if (e.key === 'c' || e.key === 'C') {
        setIsLeftOpen((prev) => !prev);
      } else if (e.key === 't' || e.key === 'T') {
        setIsRightOpen((prev) => !prev);
      } else if (e.key === 'ArrowLeft') {
        setCurrentSlide((prev) => Math.max(0, prev - 1));
      } else if (e.key === 'ArrowRight') {
        const maxIdx = (slideDeck.slides?.length || 1) - 1;
        setCurrentSlide((prev) => Math.min(maxIdx, prev + 1));
      } else if (e.key === 'f' || e.key === 'F' || e.key === 'F5') {
        e.preventDefault();
        toggleFullscreen();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [slideDeck]);

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {});
    } else {
      document.exitFullscreen().catch(() => {});
    }
  };

  // ================= HÀM GỌI AI SINH THẬT TOÀN BỘ BÀI DẠY =================
  const handleGenerateFromAi = async (params) => {
    setIsAiGenerating(true);
    setGenerationStep('Đang gửi yêu cầu và kết nối Gemini AI...');

    try {
      // 1. Gọi API sinh Kế hoạch bài dạy 5512 thật
      setGenerationStep('Gemini đang phân tích sư phạm và soạn Kế hoạch 5512...');
      const planRes = await fetch('/api/v1/lesson-plan/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic: params.topic,
          subject: params.subject,
          grade: parseInt(params.grade, 10),
          class_proficiency: params.proficiency || 'standard',
          target_outcome: params.outcome || ''
        })
      });

      if (!planRes.ok) throw new Error(`Lỗi sinh giáo án: HTTP ${planRes.status}`);
      const planData = await planRes.json();
      setLessonPlan(planData.plan);

      // 2. Gọi API sinh SlideDeck đồng bộ với Kế hoạch vừa sinh
      setGenerationStep('Gemini đang thiết kế bộ Slide bài giảng tương ứng...');
      const slideRes = await fetch('/api/v1/slide/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic: params.topic,
          subject: params.subject,
          grade: parseInt(params.grade, 10),
          class_proficiency: params.proficiency || 'standard',
          target_outcome: params.outcome || '',
          plan: planData.plan
        })
      });

      if (!slideRes.ok) throw new Error(`Lỗi sinh slide: HTTP ${slideRes.status}`);
      const slideData = await slideRes.json();
      setSlideDeck(slideData);
      setCurrentSlide(0);

      // Tự động nhận diện mô hình 3D nếu chủ đề là Hình học không gian
      const lowerTopic = params.topic.toLowerCase();
      if (lowerTopic.includes('lập phương')) setPolyhedronType('cube');
      else if (lowerTopic.includes('chóp tam giác')) setPolyhedronType('triangular_pyramid');
      else if (lowerTopic.includes('chóp tứ giác') || lowerTopic.includes('s.abcd')) setPolyhedronType('rectangular_pyramid');

      // Chuyển thẳng về Màn hình Trình Chiếu để giáo viên bắt đầu tiết học
      setActiveScreen('presentation');
      alert(`Đã gọi Gemini AI sinh thành công Kế hoạch bài dạy và ${slideData.slides?.length || 0} slide cho chủ đề: "${params.topic}"!`);
    } catch (err) {
      console.error(err);
      alert(`Không thể sinh bài từ AI: ${err.message}. Vui lòng kiểm tra server FastAPI và GEMINI_API_KEY.`);
    } finally {
      setIsAiGenerating(false);
      setGenerationStep('');
    }
  };

  // ================= HÀM XUẤT FILE THẬT QUA FASTAPI =================
  const handleExportDocx = async () => {
    if (!lessonPlan) {
      alert("Chưa có dữ liệu Kế hoạch bài dạy để xuất Word. Hãy bấm 'Sinh Giáo Án Bằng AI' trước!");
      return;
    }
    try {
      const res = await fetch('/api/v1/lesson-plan/export-docx', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(lessonPlan)
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Giao_An_5512_${lessonPlan.lesson_title || 'Toan'}.docx`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      alert("Lỗi khi tải file Word: " + e.message);
    }
  };

  const handleExportPptx = async () => {
    if (!slideDeck || !slideDeck.slides?.length) {
      alert("Chưa có dữ liệu Slide để xuất PowerPoint!");
      return;
    }
    try {
      const res = await fetch('/api/v1/lesson-plan/export-slide', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(slideDeck)
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Slide_${slideDeck.presentation_title || 'BaiGiang'}.pptx`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      alert("Lỗi khi tải file PowerPoint: " + e.message);
    }
  };

  // Áp dụng Live Patch từ Trợ giảng AI vào Slide hiện tại (Hỗ trợ cả chuẩn SlidePatchProposal của Backend & mẫu cũ)
  const handleApplySlidePatch = (patch) => {
    if (!patch) return false;
    const targetIdx =
      patch.target_slide_index !== undefined && patch.target_slide_index !== null
        ? patch.target_slide_index
        : currentSlide;
    const updatedSlides = [...(slideDeck.slides || [])];

    if (updatedSlides[targetIdx]) {
      const target = { ...updatedSlides[targetIdx] };

      const newTitle = patch.title || patch.updated_title;
      if (newTitle) target.title = newTitle;

      const newBullets = patch.bullet_points || patch.updated_bullet_points;
      if (Array.isArray(newBullets) && newBullets.length > 0) {
        target.bullet_points = newBullets;
      }

      const newLatex = patch.main_definition_latex || patch.updated_latex;
      if (newLatex) target.main_definition_latex = newLatex;

      const newTeacherNote = patch.teacher_note || patch.updated_teacher_note;
      if (newTeacherNote) target.teacher_note = newTeacherNote;

      // Xử lý khi bản vá bổ sung Câu hỏi Trắc nghiệm (QuizData từ Backend)
      if (patch.quiz) {
        target.layout = 'QUIZ_OPTION';
        if (patch.quiz.question) {
          target.bullet_points = [patch.quiz.question];
        }
        if (Array.isArray(patch.quiz.options) && patch.quiz.options.length > 0) {
          const correctLetter = String(patch.quiz.correct_answer || 'A').trim().toUpperCase();
          target.quiz_options = patch.quiz.options.map((optStr, idx) => {
            const labels = ['A', 'B', 'C', 'D'];
            const label = labels[idx] || String(idx + 1);
            const cleanText = String(optStr).replace(/^[A-D]\.\s*/, '');
            const isCorrect = label === correctLetter;
            return {
              label,
              text: cleanText,
              is_correct: isCorrect,
              distractor_rationale: isCorrect
                ? (patch.quiz.explanation || 'Đáp án chính xác.')
                : 'Phương án gây nhiễu, học sinh cần kiểm tra lại công thức.'
            };
          });
        }
      } else if (patch.new_quiz_option) {
        target.quiz_options = [...(target.quiz_options || []), patch.new_quiz_option];
      }

      updatedSlides[targetIdx] = target;
      setSlideDeck({ ...slideDeck, slides: updatedSlides });
      setCurrentSlide(targetIdx);
      return true;
    }
    return false;
  };

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-[#050811] text-slate-100 select-none">
      {/* 1. Header Navigation */}
      <HeaderNav
        activeScreen={activeScreen}
        setActiveScreen={setActiveScreen}
        currentSlide={currentSlide}
        totalSlides={slideDeck.slides?.length || 1}
        presentationTitle={slideDeck.presentation_title}
        onExportDocx={handleExportDocx}
        onExportPptx={handleExportPptx}
        isAiGenerating={isAiGenerating}
        generationStep={generationStep}
      />

      {/* Thông báo trạng thái đang gọi AI toàn màn hình */}
      {isAiGenerating && (
        <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-md z-50 flex flex-col items-center justify-center gap-4">
          <div className="w-14 h-14 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin"></div>
          <div className="text-center space-y-1">
            <h3 className="text-lg font-bold text-white">Gemini AI Đang Xử Lý Sư Phạm Chuyên Sâu</h3>
            <p className="text-sm text-cyan-400 font-mono animate-pulse">{generationStep}</p>
            <p className="text-xs text-slate-500">Đang tạo Kế hoạch 5512, đồng bộ SlideDeck và kết xuất Đồ thị Matplotlib...</p>
          </div>
        </div>
      )}

      {/* 2. Main Content Screens */}
      <main className="flex-1 flex overflow-hidden relative">
        {/* MÀN HÌNH 1: SÂN KHẤU TRÌNH CHIẾU GIẢNG DẠY (Ưu tiên số 1) */}
        {activeScreen === 'presentation' && (
          <div className="w-full h-full flex overflow-hidden">
            <TeacherChatDock
              isOpen={isLeftOpen}
              onToggle={() => setIsLeftOpen(false)}
              currentSlide={currentSlide}
              slideDeck={slideDeck}
              onApplyPatch={handleApplySlidePatch}
            />

            <PresentationStage
              slideDeck={slideDeck}
              setSlideDeck={setSlideDeck}
              currentSlide={currentSlide}
              setCurrentSlide={setCurrentSlide}
              isLeftOpen={isLeftOpen}
              isRightOpen={isRightOpen}
              onToggleLeft={() => setIsLeftOpen(true)}
              onToggleRight={() => setIsRightOpen(true)}
              polyhedronType={polyhedronType}
              edgeLength={edgeLength}
              showHiddenLines={showHiddenLines}
              showVertexLabels={showVertexLabels}
              showAxes={showAxes}
              cameraPreset={cameraPreset}
              onSwitchSample={handleSwitchSample}
            />

            <RightToolsDock
              isOpen={isRightOpen}
              onToggle={() => setIsRightOpen(false)}
              polyhedronType={polyhedronType}
              setPolyhedronType={setPolyhedronType}
              edgeLength={edgeLength}
              setEdgeLength={setEdgeLength}
              showHiddenLines={showHiddenLines}
              setShowHiddenLines={setShowHiddenLines}
              showVertexLabels={showVertexLabels}
              setShowVertexLabels={setShowVertexLabels}
              showAxes={showAxes}
              setShowAxes={setShowAxes}
              onCameraPreset={setCameraPreset}
            />
          </div>
        )}

        {/* MÀN HÌNH 2: SOẠN KẾ HOẠCH BÀI DẠY 5512 (Kèm Danh mục Bài SGK & Nút Gọi AI Thật) */}
        {activeScreen === 'lesson-plan' && (
          <LessonPlanScreen
            lessonPlan={lessonPlan}
            isGenerating={isAiGenerating}
            onGenerateFromAi={handleGenerateFromAi}
            onExportDocx={handleExportDocx}
            externalProficiency={classProficiency}
            externalOutcome={recommendedOutcome}
          />
        )}

        {/* MÀN HÌNH 3: XƯỞNG BIÊN TẬP SLIDE (Kết nối SlideDeck thật & Xuất PPTX thật) */}
        {activeScreen === 'slide-editor' && (
          <SlideEditorScreen
            slideDeck={slideDeck}
            setSlideDeck={setSlideDeck}
            onExportPptx={handleExportPptx}
          />
        )}

        {/* MÀN HÌNH 4: PHÂN TÍCH LỚP HỌC (Z-Score & Bảng điểm thực) */}
        {activeScreen === 'analytics' && (
          <AnalyticsScreen
            analyticsData={analyticsData}
            onClassificationSuccess={handleClassificationSuccess}
            onApplyToLessonPlan={handleApplyAnalyticsToLessonPlan}
          />
        )}
      </main>
    </div>
  );
}
