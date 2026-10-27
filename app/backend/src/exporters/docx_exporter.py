# -*- coding: utf-8 -*-
"""
Module Xuất Kế Hoạch Bài Dạy Chuẩn Công Văn 5512/BGDĐT-GDTrH Sang Microsoft Word (.docx)
Nâng cấp Ngày 19:
- Đồng bộ 100% nội dung với Slide bài giảng (SlideDeckSchema)
- Chuyển đổi công thức toán học LaTeX sang OMML Native Equation trong Word
- Nhúng hệ thống câu hỏi trắc nghiệm kèm phân tích bẫy sai lầm (Distractor Rationales)
- Nhúng các bước giải mẫu tự luận chuẩn mực SGK (worked_solution_steps)
- Quản lý kiểu dáng bảng biểu, căn chỉnh lề in ấn và chữ ký duyệt giáo án
"""

import io
import os
import re
import copy
from typing import Union, Optional, Dict, Any, List

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

import latex2mathml.converter
import mathml2omml

from schemas.schemas import LessonPlanSchema, LessonActivity, ExecutionSteps
from schemas.slide_schema import SlideDeckSchema, SlideSchema
from exporters.slide_exporter import latex_to_unicode_math, POLYHEDRON_LABELS


def clean_xml_string(s: str) -> str:
    """Lọc và xóa các ký tự rác / ký tự ẩn không hợp lệ trong văn bản tránh lỗi XML Word"""
    if not isinstance(s, str):
        s = str(s or "")
    return re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x84\x86-\x9F]', '', s)


def set_cell_background(cell, fill_hex: str):
    """Tô màu nền cho ô trong table Word"""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}" />')
    tcPr.append(shd)


def set_cell_margins(cell, top: int = 100, bottom: int = 100, left: int = 140, right: int = 140):
    """Thiết lập khoảng cách đệm lề trong của ô bảng (đơn vị dxa, 20 dxa = 1 pt)"""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'  <w:top w:w="{top}" w:type="dxa"/>'
        f'  <w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'  <w:left w:w="{left}" w:type="dxa"/>'
        f'  <w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)


_LATEX_REPAIR_RULES = [
    (re.compile(r'(?<![\\a-zA-Z])rac(?=\{)'), r'\\frac'),
    (re.compile(r'(?<![\\a-zA-Z])ext(?=\{)'), r'\\text'),
    (re.compile(r'(?<![\\a-zA-Z])qrt(?=\{)'), r'\\sqrt'),
    (re.compile(r'(?<![\\a-zA-Z])boxed(?=\{)'), r'\\boxed'),
    (re.compile(r'(?<![\\a-zA-Z])begin(?=\{)'), r'\\begin'),
    (re.compile(r'(?<![\\a-zA-Z])le(?=[\s\d_a-zA-Z\\])'), r'\\le'),
    (re.compile(r'(?<![\\a-zA-Z])ge(?=[\s\d_a-zA-Z\\])'), r'\\ge'),
]


def repair_latex_code(latex_code: str) -> str:
    """Tự động sửa chữa các lỗi cú pháp LaTeX phổ biến do mô hình sinh"""
    if not latex_code:
        return ""
    repaired = latex_code.strip()
    for pattern, replacement in _LATEX_REPAIR_RULES:
        repaired = pattern.sub(replacement, repaired)
    repaired = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F]', '', repaired)
    return repaired


def convert_latex_to_omml(latex_code: str):
    """
    Chuyển đổi chuỗi mã LaTeX sang đối tượng XML OMML (Công thức toán native trong Word).
    Nếu thành công: trả về parse_xml node để gắn trực tiếp vào w:p element.
    Nếu thất bại: trả về None để dùng cơ chế fallback Unicode Math.
    """
    if not latex_code or not latex_code.strip():
        return None
    try:
        repaired = repair_latex_code(latex_code)
        # 1. Chuyển LaTeX sang MathML
        mathml_code = latex2mathml.converter.convert(repaired)
        # 2. Chuyển MathML sang OMML XML
        omml_str = mathml2omml.convert(mathml_code)
        # 3. Thêm khai báo namespace nếu chưa có
        if '<m:oMath>' in omml_str and 'xmlns:m=' not in omml_str:
            omml_str = omml_str.replace('<m:oMath>', f'<m:oMath {nsdecls("m")}>')
        elif '<m:oMathPara>' in omml_str and 'xmlns:m=' not in omml_str:
            omml_str = omml_str.replace('<m:oMathPara>', f'<m:oMathPara {nsdecls("m")}>')
        # 4. Parse sang Element XML của docx
        return parse_xml(omml_str)
    except Exception:
        return None


def add_text_with_latex(
    paragraph,
    text: str,
    prefix: str = "",
    font_name: str = "Times New Roman",
    font_size: float = 13.0,
    bold_prefix: bool = True,
    italic: bool = False
):
    r"""
    Phân tích văn bản và chèn vào paragraph Word.
    Tự động nhận diện các đoạn mã LaTeX dạng \(...\), \[...\], $...$, $$...$$
    và chuyển thành Công thức toán chuẩn của Word (OMML Native Equation).
    Nếu công thức phức tạp không thể parse sang OMML, áp dụng Fallback thông minh:
    Chuyển sang Unicode Math và gán font Cambria Math nghiêng chuẩn mực.
    """
    cleaned_text = clean_xml_string(text)

    if prefix:
        r_pre = paragraph.add_run(prefix)
        r_pre.font.name = font_name
        r_pre.font.size = Pt(font_size)
        if bold_prefix:
            r_pre.font.bold = True

    if not cleaned_text:
        return

    # Regex bóc tách các thẻ công thức LaTeX: \(...\), \[...\], $...$, $$...$$
    pattern = r'(\\\(.*?\x5c\)|\\\[.*?\\\]|(?:\$\$[^$]+\$\$)|(?:\$[^$]+\$))'
    parts = re.split(pattern, cleaned_text)

    for part in parts:
        if not part:
            continue

        is_latex = False
        latex_code = ""
        if (part.startswith(r"\(") and part.endswith(r"\)")) or (part.startswith(r"\[") and part.endswith(r"\]")):
            is_latex = True
            latex_code = part[2:-2].strip()
        elif part.startswith("$$") and part.endswith("$$"):
            is_latex = True
            latex_code = part[2:-2].strip()
        elif part.startswith("$") and part.endswith("$"):
            is_latex = True
            latex_code = part[1:-1].strip()

        if is_latex and latex_code:
            omml_node = convert_latex_to_omml(latex_code)
            if omml_node is not None:
                paragraph._p.append(omml_node)
            else:
                # Fallback thông minh: Chuyển sang ký tự toán học Unicode và font Cambria Math
                unicode_math = latex_to_unicode_math(latex_code)
                run = paragraph.add_run(f" {unicode_math} ")
                run.font.name = 'Cambria Math'
                run.font.size = Pt(font_size)
                run.font.italic = True
        else:
            run = paragraph.add_run(part)
            run.font.name = font_name
            run.font.size = Pt(font_size)
            if italic:
                run.font.italic = True


def _extract_slide_deck_elements(slide_deck: Optional[Union[SlideDeckSchema, dict, list]]) -> dict:
    """
    Trích xuất toàn diện các thành phần nội dung từ SlideDeck:
    - Câu hỏi trắc nghiệm (quiz_items)
    - Các bước giải tự luận mẫu (worked_examples)
    - Công thức toán trọng tâm (concept_formulas)
    - Mô hình hình học trực quan 3D và đồ thị (visual_models)
    """
    result = {
        "presentation_title": "",
        "subject": "",
        "grade": None,
        "quiz_items": [],
        "worked_examples": [],
        "concept_formulas": [],
        "visual_models": [],
        "warm_ups": [],
        "summaries": [],
    }
    if not slide_deck:
        return result

    raw_slides = []
    if isinstance(slide_deck, SlideDeckSchema):
        result["presentation_title"] = slide_deck.presentation_title or ""
        result["subject"] = slide_deck.subject or ""
        result["grade"] = slide_deck.grade
        raw_slides = [s.model_dump() for s in slide_deck.slides]
    elif isinstance(slide_deck, dict):
        result["presentation_title"] = slide_deck.get("presentation_title") or ""
        result["subject"] = slide_deck.get("subject") or ""
        result["grade"] = slide_deck.get("grade")
        raw_slides = slide_deck.get("slides") or []
    elif isinstance(slide_deck, list):
        raw_slides = slide_deck

    for idx, s in enumerate(raw_slides):
        if not isinstance(s, dict):
            continue

        slide_type = str(s.get("type") or "").upper()
        layout = str(s.get("layout") or "").upper()
        title = s.get("title") or ""

        # 1. Slide Khởi động
        if slide_type == "WARM_UP_SLIDE" or "khởi động" in title.lower():
            result["warm_ups"].append(s)

        # 2. Câu hỏi trắc nghiệm
        quiz_options = s.get("quiz_options") or []
        is_quiz = (slide_type == "QUIZ_SLIDE" or layout == "QUIZ_OPTION" or bool(quiz_options))
        if is_quiz and quiz_options:
            q_text = s.get("question") or title or f"Câu hỏi trắc nghiệm {len(result['quiz_items']) + 1}"
            result["quiz_items"].append({
                "slide_index": s.get("slide_index") or (idx + 1),
                "title": title,
                "question": q_text,
                "quiz_options": quiz_options,
                "teacher_note": s.get("teacher_note") or "",
                "activity_type": s.get("activity_type") or "Luyện tập trắc nghiệm",
            })

        # 3. Lời giải mẫu tự luận từng bước
        sol_steps = s.get("worked_solution_steps") or []
        if sol_steps:
            result["worked_examples"].append({
                "slide_index": s.get("slide_index") or (idx + 1),
                "title": title or f"Ví dụ áp dụng {len(result['worked_examples']) + 1}",
                "steps": sol_steps,
                "teacher_note": s.get("teacher_note") or "",
            })

        # 4. Công thức toán học trọng tâm
        formula = s.get("main_definition_latex")
        if formula and formula.strip():
            result["concept_formulas"].append({
                "slide_index": s.get("slide_index") or (idx + 1),
                "title": title,
                "formula": formula.strip(),
                "bullets": s.get("bullet_points") or [],
            })

        # 5. Mô hình trực quan 3D WebGL / Đồ thị
        poly_type = s.get("polyhedron_type")
        has_3d = bool(s.get("has_3d")) or bool(poly_type)
        chart_spec = s.get("chart_spec")
        if has_3d or chart_spec:
            poly_label = POLYHEDRON_LABELS.get(str(poly_type).lower(), "Mô hình Hình học không gian 3D WebGL (SGK)")
            result["visual_models"].append({
                "slide_index": s.get("slide_index") or (idx + 1),
                "title": title,
                "has_3d": has_3d,
                "polyhedron_type": poly_type,
                "polyhedron_label": poly_label,
                "has_chart": bool(chart_spec),
            })

        # 6. Slide Tóm tắt / Vận dụng cuối bài
        if slide_type == "SUMMARY_SLIDE" or "vận dụng" in title.lower() or "tóm tắt" in title.lower():
            result["summaries"].append(s)

    return result


def synchronize_lesson_and_slide_deck(
    plan_input: Union[LessonPlanSchema, dict],
    slide_deck: Optional[Union[SlideDeckSchema, dict, list]] = None
) -> LessonPlanSchema:
    """
    Task 19.1: Thuật toán Đồng bộ Song hướng (Bi-directional Content Synchronization).
    Đảm bảo 100% nội dung bài dạy khớp nối hoàn hảo giữa Kế hoạch bài dạy Word (CV 5512)
    và Slide bài giảng PowerPoint:
    - Đồng bộ Tiêu đề, Môn học, Khối lớp
    - Bổ sung thiết bị dạy học trực quan 3D / Đồ thị
    - Cập nhật công thức toán học trọng tâm vào Hoạt động 2
    - Tích hợp toàn bộ câu hỏi trắc nghiệm, bẫy sai lầm và lời giải tự luận vào Hoạt động 3
    """
    # 1. Trích xuất hoặc khởi tạo plan
    plan_dict = {}
    if isinstance(plan_input, LessonPlanSchema):
        plan_dict = plan_input.model_dump()
    elif isinstance(plan_input, dict):
        if "plan" in plan_input and isinstance(plan_input["plan"], (dict, LessonPlanSchema)):
            sub_plan = plan_input["plan"]
            plan_dict = sub_plan.model_dump() if isinstance(sub_plan, LessonPlanSchema) else dict(sub_plan)
            if not slide_deck and "slide_deck" in plan_input:
                slide_deck = plan_input["slide_deck"]
        else:
            plan_dict = dict(plan_input)
    else:
        plan_dict = {}

    # Trích xuất slide deck elements
    if not slide_deck:
        if "slide_deck" in plan_dict:
            slide_deck = plan_dict.pop("slide_deck")
        elif "slides" in plan_dict:
            slide_deck = {"slides": plan_dict.get("slides")}

    deck_info = _extract_slide_deck_elements(slide_deck)

    # 2. Đồng bộ Tiêu đề, Môn, Lớp
    if not plan_dict.get("lesson_title") or plan_dict["lesson_title"] == "Kế hoạch bài dạy":
        plan_dict["lesson_title"] = deck_info["presentation_title"] or "KẾ HOẠCH BÀI DẠY TOÁN HỌC"
    if not plan_dict.get("subject"):
        plan_dict["subject"] = deck_info["subject"] or "Toán học"
    if not plan_dict.get("grade"):
        plan_dict["grade"] = deck_info["grade"] or 11

    # 3. Đồng bộ Thiết bị dạy học và học liệu (Phần II)
    equipment = list(plan_dict.get("teaching_equipment") or [])
    if deck_info["visual_models"]:
        has_3d_any = any(vm["has_3d"] for vm in deck_info["visual_models"])
        if has_3d_any:
            eq_3d_text = "Mô hình Hình học không gian 3D tương tác WebGL (Three.js chuẩn SGK)"
            if not any(eq_3d_text in e for e in equipment):
                equipment.append(eq_3d_text)
        has_chart_any = any(vm["has_chart"] for vm in deck_info["visual_models"])
        if has_chart_any:
            eq_chart_text = "Phần mềm đồ họa trực quan hóa đồ thị toán học (Matplotlib Native)"
            if not any(eq_chart_text in e for e in equipment):
                equipment.append(eq_chart_text)

    eq_studio_text = "Bài giảng điện tử tương tác chuẩn Web Studio & Slide PowerPoint (LessonAI-5512)"
    if not any(eq_studio_text in e for e in equipment):
        equipment.append(eq_studio_text)
    plan_dict["teaching_equipment"] = equipment

    # 4. Kiểm tra và bổ sung danh sách 4 Hoạt động chuẩn CV 5512 nếu chưa có
    activities = plan_dict.get("activities") or []
    if len(activities) < 4:
        default_acts = [
            {
                "activity_number": 1,
                "time_minutes": 5,
                "goal": "Tạo hứng thú, kích hoạt kiến thức nền tảng và dẫn dắt học sinh vào bài học mới.",
                "expected_product": "Câu trả lời của học sinh cho bài toán khởi động và sự sẵn sàng tiếp thu bài học.",
                "execution": {
                    "step_1_assign": "GV trình chiếu slide khởi động, giao tình huống thực tế hoặc câu hỏi gợi mở cho HS.",
                    "step_2_excute": "HS quan sát slide, suy nghĩ độc lập hoặc trao đổi nhanh theo bàn.",
                    "step_3_report": "Đại diện 1-2 HS phát biểu câu trả lời; các HS khác nhận xét, bổ sung.",
                    "step_4_conclusion": "GV nhận xét câu trả lời, dẫn dắt và công bố mục tiêu của bài học mới."
                }
            },
            {
                "activity_number": 2,
                "time_minutes": 20,
                "goal": "Hình thành định nghĩa, tính chất, định lý và công thức toán học trọng tâm của bài học.",
                "expected_product": "Học sinh hiểu và ghi chép đầy đủ định nghĩa, công thức toán học trọng tâm vào vở.",
                "execution": {
                    "step_1_assign": "GV trình chiếu slide lý thuyết, hướng dẫn HS quan sát mô hình trực quan và đọc SGK.",
                    "step_2_excute": "HS thảo luận nhóm, thực hiện các yêu cầu khám phá, rút ra nhận xét toán học.",
                    "step_3_report": "Đại diện nhóm báo cáo kết quả phát hiện tính chất; các nhóm khác phản biện.",
                    "step_4_conclusion": "GV chuẩn hóa kiến thức, chốt công thức toán trọng tâm và hướng dẫn ghi nhớ."
                }
            },
            {
                "activity_number": 3,
                "time_minutes": 15,
                "goal": "Vận dụng kiến thức vừa học giải quyết hệ thống câu hỏi trắc nghiệm rèn luyện và ví dụ tự luận chuẩn mực SGK.",
                "expected_product": "Đáp án các câu hỏi trắc nghiệm rèn luyện và lời giải chi tiết từng bước của bài tập tự luận.",
                "execution": {
                    "step_1_assign": "GV trình chiếu các câu hỏi trắc nghiệm và bài tập ví dụ từ Slide Studio, yêu cầu HS làm bài.",
                    "step_2_excute": "HS làm việc cá nhân, tính toán cẩn thận và ghi các bước giải vào vở bài tập.",
                    "step_3_report": "HS xung phong trả lời phương án trắc nghiệm hoặc lên bảng trình bày bài giải tự luận.",
                    "step_4_conclusion": "GV phân tích bẫy sai lầm của các phương án nhiễu, chốt đáp án đúng và các bước giải tự luận chuẩn mực."
                }
            },
            {
                "activity_number": 4,
                "time_minutes": 5,
                "goal": "Vận dụng kiến thức bài học để giải quyết bài toán thực tế liên môn và giao nhiệm vụ tự học.",
                "expected_product": "Ý tưởng giải quyết bài toán thực tế và kế hoạch tự học, chuẩn bị bài mới ở nhà.",
                "execution": {
                    "step_1_assign": "GV giao nhiệm vụ vận dụng thực tế trên slide dặn dò, hướng dẫn cách thực hiện tại nhà.",
                    "step_2_excute": "HS lắng nghe, ghi chép nhiệm vụ và thắc mắc (nếu có) để GV giải đáp.",
                    "step_3_report": "Báo cáo sản phẩm vận dụng vào tiết học tiếp theo hoặc nộp qua hệ thống học tập.",
                    "step_4_conclusion": "GV đánh giá tinh thần học tập trong tiết học, dặn dò ôn tập và kết thúc bài học."
                }
            }
        ]
        # Bổ sung các hoạt động còn thiếu
        for i in range(len(activities), 4):
            activities.append(default_acts[i])
        plan_dict["activities"] = activities

    # 5. Đồng bộ Hoạt động 2 với Công thức Toán trọng tâm
    if deck_info["concept_formulas"] and len(plan_dict["activities"]) >= 2:
        act2 = plan_dict["activities"][1]
        formula_strs = [cf["formula"] for cf in deck_info["concept_formulas"] if cf.get("formula")]
        if formula_strs:
            f_summary = " • Công thức trọng tâm: " + "; ".join(f"${f}$" for f in formula_strs)
            if f_summary not in str(act2.get("expected_product", "")):
                act2["expected_product"] = (str(act2.get("expected_product", "")) + "\n" + f_summary).strip()

    # 6. Đồng bộ Hoạt động 3 với Câu hỏi Trắc nghiệm & Lời giải Tự luận
    if len(plan_dict["activities"]) >= 3:
        act3 = plan_dict["activities"][2]
        sync_notes = []
        if deck_info["quiz_items"]:
            q_count = len(deck_info["quiz_items"])
            sync_notes.append(f"- Hệ thống {q_count} câu hỏi trắc nghiệm rèn luyện (A, B, C, D) đồng bộ chuẩn Slide Studio.")
        if deck_info["worked_examples"]:
            ex_count = len(deck_info["worked_examples"])
            sync_notes.append(f"- Hướng dẫn giải chi tiết {ex_count} bài tập tự luận mẫu chuẩn mực SGK.")
        if sync_notes:
            act3["goal"] = (str(act3.get("goal", "")) + " (" + "; ".join(sync_notes) + ")").strip()

    # Bổ sung các trường bắt buộc của LessonPlanSchema nếu bị thiếu
    if "knowledge_goals" not in plan_dict or not plan_dict["knowledge_goals"]:
        plan_dict["knowledge_goals"] = ["Nắm vững các khái niệm, tính chất và công thức trọng tâm của bài học."]
    if "competency_goals" not in plan_dict:
        plan_dict["competency_goals"] = []
    if "skills_goals" not in plan_dict:
        plan_dict["skills_goals"] = []
    if "character_goals" not in plan_dict:
        plan_dict["character_goals"] = []

    try:
        plan_obj = LessonPlanSchema.model_validate(plan_dict)
    except Exception:
        from services.fallback_service import get_curated_lesson_plan
        plan_obj = get_curated_lesson_plan(
            topic=plan_dict.get("lesson_title"),
            subject=plan_dict.get("subject", "Toán học"),
            grade=int(plan_dict.get("grade") or 10)
        )
    return plan_obj, deck_info


def export_lesson_plan_to_docx(
    plan: Union[LessonPlanSchema, dict],
    slide_deck: Optional[Union[SlideDeckSchema, dict, list]] = None
) -> io.BytesIO:
    """
    Chuyển đổi Kế hoạch bài dạy chuẩn Công văn 5512/BGDĐT thành file Word (.docx) chuyên nghiệp:
    - Tự động đồng bộ 100% nội dung với Slide bài giảng (Task 19.1)
    - Tự động chuyển đổi công thức Toán học sang OMML Native Equation
    - Thiết kế bảng 4 bước tổ chức hoạt động trang nhã, viền và màu nền chuẩn mực
    - Nhúng phụ lục câu hỏi trắc nghiệm kèm phân tích bẫy sai lầm
    - Nhúng ví dụ tự luận từng bước chuẩn mực SGK
    """
    # 1. Đồng bộ dữ liệu Kế hoạch bài dạy với SlideDeck
    plan_synced, deck_info = synchronize_lesson_and_slide_deck(plan, slide_deck)

    doc = Document()

    # 2. Căn chỉnh lề theo quy chuẩn văn bản hành chính Việt Nam (Nghị định 30/2020/NĐ-CP - Khổ giấy A4 210x297mm)
    for section in doc.sections:
        section.page_width = Inches(8.27)     # 21.0 cm (Khổ A4 chuẩn)
        section.page_height = Inches(11.69)   # 29.7 cm (Khổ A4 chuẩn)
        section.top_margin = Inches(0.79)     # 2.0 cm
        section.bottom_margin = Inches(0.79)  # 2.0 cm
        section.left_margin = Inches(1.18)    # 3.0 cm (đóng gáy hồ sơ)
        section.right_margin = Inches(0.59)   # 1.5 cm

    # 3. Định dạng Style Normal (Times New Roman, 13 pt, màu đen)
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(13)
    font.color.rgb = RGBColor(0x00, 0x00, 0x00)
    doc.styles['Normal'].paragraph_format.line_spacing = 1.15
    doc.styles['Normal'].paragraph_format.space_after = Pt(4)

    # 4. Phần Đầu Trang: Thông tin cơ quan & Chữ ký tiêu đề
    p_inst = doc.add_paragraph()
    r_inst1 = p_inst.add_run("TRƯỜNG THPT: .......................................\t\tTỔ CHUYÊN MÔN: TOÁN - TIN\n")
    r_inst1.font.bold = True
    r_inst1.font.size = Pt(11)
    r_inst2 = p_inst.add_run("HỌ VÀ TÊN GIÁO VIÊN: ..........................\n")
    r_inst2.font.bold = True
    r_inst2.font.size = Pt(11)

    p_header = doc.add_paragraph()
    p_header.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_h = p_header.add_run("KẾ HOẠCH BÀI DẠY (GIÁO ÁN)\n")
    r_h.font.bold = True
    r_h.font.size = Pt(14)
    r_h.font.color.rgb = RGBColor(0x1e, 0x3a, 0x8a)  # Academic Navy

    r_sub = p_header.add_run(f"MÔN: {clean_xml_string(plan_synced.subject).upper()} - LỚP {plan_synced.grade}\n")
    r_sub.font.bold = True
    r_sub.font.size = Pt(13)

    r_title = p_header.add_run(f"BÀI HỌC: {clean_xml_string(plan_synced.lesson_title).upper()}\n")
    r_title.font.bold = True
    r_title.font.size = Pt(15)
    r_title.font.color.rgb = RGBColor(0x1e, 0x3a, 0x8a)

    p_std = doc.add_paragraph()
    p_std.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_std = p_std.add_run("(Chuẩn cấu trúc Công văn số 5512/BGDĐT-GDTrH • Tích hợp Slide Studio LessonAI-5512)\n")
    r_std.font.italic = True
    r_std.font.size = Pt(10.5)
    r_std.font.color.rgb = RGBColor(0x64, 0x74, 0x8b)

    # 5. Phần I: MỤC TIÊU BÀI HỌC
    h1 = doc.add_paragraph()
    r1 = h1.add_run("I. MỤC TIÊU BÀI HỌC")
    r1.font.bold = True
    r1.font.size = Pt(13.5)
    r1.font.color.rgb = RGBColor(0x1e, 0x3a, 0x8a)

    # 1. Kiến thức
    p_k = doc.add_paragraph()
    r_k = p_k.add_run("1. Về kiến thức: ")
    r_k.font.bold = True
    if plan_synced.knowledge_goals:
        for k in plan_synced.knowledge_goals:
            p_item = doc.add_paragraph()
            add_text_with_latex(p_item, k, prefix="  - ")
    else:
        p_item = doc.add_paragraph()
        p_item.add_run("  - Nắm vững các khái niệm, tính chất và công thức trọng tâm của bài học theo chuẩn SGK GDPT 2018.")

    # 2. Năng lực
    competencies = plan_synced.competency_goals or plan_synced.skills_goals
    p_sk = doc.add_paragraph()
    r_sk = p_sk.add_run("2. Về năng lực: ")
    r_sk.font.bold = True
    if competencies:
        for s in competencies:
            p_item = doc.add_paragraph()
            add_text_with_latex(p_item, s, prefix="  - ")
    else:
        for default_comp in [
            "Năng lực tư duy và lập luận toán học: Phát hiện tính chất và biến đổi công thức chuẩn xác.",
            "Năng lực mô hình hóa toán học: Vận dụng mô hình hình học 3D và đồ thị giải quyết bài toán thực tiễn.",
            "Năng lực giải quyết vấn đề toán học: Tự tin vượt qua các bẫy sai lầm trong câu hỏi trắc nghiệm."
        ]:
            p_item = doc.add_paragraph()
            p_item.add_run(f"  - {default_comp}")

    # 3. Phẩm chất
    p_ch = doc.add_paragraph()
    r_ch = p_ch.add_run("3. Về phẩm chất: ")
    r_ch.font.bold = True
    if plan_synced.character_goals:
        for c in plan_synced.character_goals:
            p_item = doc.add_paragraph()
            add_text_with_latex(p_item, c, prefix="  - ")
    else:
        for default_char in [
            "Chăm chỉ: Tích cực phát biểu xây dựng bài, kiên trì hoàn thành các bài tập rèn luyện.",
            "Trung thực: Nghiêm túc làm bài tập cá nhân, không gian lận trong giờ kiểm tra.",
            "Trách nhiệm: Hợp tác tích cực trong các hoạt động thảo luận nhóm và báo cáo kết quả."
        ]:
            p_item = doc.add_paragraph()
            p_item.add_run(f"  - {default_char}")

    # 6. Phần II: THIẾT BỊ DẠY HỌC VÀ HỌC LIỆU
    h2 = doc.add_paragraph()
    r2 = h2.add_run("\nII. THIẾT BỊ DẠY HỌC VÀ HỌC LIỆU")
    r2.font.bold = True
    r2.font.size = Pt(13.5)
    r2.font.color.rgb = RGBColor(0x1e, 0x3a, 0x8a)

    p_eq_gv = doc.add_paragraph()
    r_eq_gv = p_eq_gv.add_run("1. Giáo viên: ")
    r_eq_gv.font.bold = True
    for eq in plan_synced.teaching_equipment:
        p_eq_item = doc.add_paragraph()
        add_text_with_latex(p_eq_item, eq, prefix="  - ")

    p_eq_hs = doc.add_paragraph()
    r_eq_hs = p_eq_hs.add_run("2. Học sinh: ")
    r_eq_hs.font.bold = True
    for eq_hs in [
        "Sách giáo khoa, vở ghi bài, đồ dùng học tập (thước kẻ, compa, bút màu).",
        "Máy tính cầm tay bỏ túi phục vụ bấm máy kiểm tra kết quả tính toán."
    ]:
        p_eq_hs_item = doc.add_paragraph()
        p_eq_hs_item.add_run(f"  - {eq_hs}")

    # 7. Phần III: TIẾN TRÌNH DẠY HỌC
    h3 = doc.add_paragraph()
    r3 = h3.add_run("\nIII. TIẾN TRÌNH DẠY HỌC (TỔ CHỨC CÁC HOẠT ĐỘNG DẠY HỌC)")
    r3.font.bold = True
    r3.font.size = Pt(13.5)
    r3.font.color.rgb = RGBColor(0x1e, 0x3a, 0x8a)

    for act in plan_synced.activities:
        act_num = act.activity_number
        act_goal = getattr(act, "goal", f"Hoạt động {act_num}")
        act_time = getattr(act, "time_minutes", 10)

        # Tiêu đề Hoạt động
        p_act = doc.add_paragraph()
        r_act_title = p_act.add_run(f"\n1. HOẠT ĐỘNG {act_num}: {clean_xml_string(act_goal).upper()} ({act_time} phút)\n")
        r_act_title.font.bold = True
        r_act_title.font.size = Pt(13)
        r_act_title.font.color.rgb = RGBColor(0x0f, 0x17, 0x2a)

        # a) Mục tiêu
        p_goal = doc.add_paragraph()
        add_text_with_latex(p_goal, act_goal, prefix="a) Mục tiêu: ")

        # b) Sản phẩm dự kiến
        p_prod = doc.add_paragraph()
        add_text_with_latex(p_prod, act.expected_product, prefix="b) Sản phẩm dự kiến: ")

        # c) Tổ chức thực hiện (Bảng 4 bước CV 5512)
        p_exec = doc.add_paragraph()
        r_exec = p_exec.add_run("c) Tổ chức thực hiện:")
        r_exec.font.bold = True

        table = doc.add_table(rows=5, cols=2)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False

        # Thiết lập độ rộng cột chuẩn mực
        COL_WIDTH_STEP = Inches(1.85)
        COL_WIDTH_CONTENT = Inches(4.70)
        for row in table.rows:
            row.cells[0].width = COL_WIDTH_STEP
            row.cells[1].width = COL_WIDTH_CONTENT

        # Header Bảng
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = "Các bước tổ chức"
        hdr_cells[1].text = "Nội dung chi tiết hoạt động của Thầy và Trò"
        set_cell_background(hdr_cells[0], "E2E8F0")  # Slate Gray
        set_cell_background(hdr_cells[1], "E2E8F0")
        set_cell_margins(hdr_cells[0], top=120, bottom=120, left=150, right=150)
        set_cell_margins(hdr_cells[1], top=120, bottom=120, left=150, right=150)
        for c in hdr_cells:
            for p in c.paragraphs:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for r in p.runs:
                    r.font.bold = True
                    r.font.size = Pt(12)
                    r.font.color.rgb = RGBColor(0x1e, 0x3a, 0x8a)

        steps_data = [
            ("Bước 1: Chuyển giao nhiệm vụ", act.execution.step_1_assign),
            ("Bước 2: Thực hiện nhiệm vụ", act.execution.step_2_excute),
            ("Bước 3: Báo cáo, thảo luận", act.execution.step_3_report),
            ("Bước 4: Kết luận & nhận định", act.execution.step_4_conclusion),
        ]

        for idx, (step_name, step_content) in enumerate(steps_data, start=1):
            row_cells = table.rows[idx].cells
            row_cells[0].text = step_name
            set_cell_margins(row_cells[0], top=100, bottom=100, left=150, right=150)
            set_cell_margins(row_cells[1], top=100, bottom=100, left=150, right=150)

            # Highlight nhẹ bước 1 và 4
            if idx in (1, 4):
                set_cell_background(row_cells[0], "F8FAFC")
            if row_cells[0].paragraphs[0].runs:
                row_cells[0].paragraphs[0].runs[0].font.bold = True
                row_cells[0].paragraphs[0].runs[0].font.size = Pt(12)

            p_content = row_cells[1].paragraphs[0]
            p_content.text = ""  # Xóa text rỗng mặc định
            add_text_with_latex(p_content, step_content, font_size=12.0)

        # ======================================================================
        # NÂNG CẤP TASK 19.1: ĐỒNG BỘ TRẮC NGHIỆM & LỜI GIẢI MẪU VÀO HOẠT ĐỘNG 3
        # ======================================================================
        if act_num == 3:
            # 1. Nhúng Hệ Thống Câu Hỏi Trắc Nghiệm Đồng Bộ Từ Slide
            quiz_items = deck_info.get("quiz_items") or []
            if quiz_items:
                p_q_head = doc.add_paragraph()
                r_qh = p_q_head.add_run("\n❖ HỆ THỐNG CÂU HỎI TRẮC NGHIỆM ĐÁNH GIÁ ĐỊNH DẠNG BGD&ĐT (ĐỒNG BỘ SLIDE):")
                r_qh.font.bold = True
                r_qh.font.size = Pt(12.5)
                r_qh.font.color.rgb = RGBColor(0x1e, 0x40, 0xaf)  # Royal Blue

                for q_idx, q_item in enumerate(quiz_items):
                    q_num = q_idx + 1
                    q_title = q_item.get("question") or f"Câu hỏi rèn luyện {q_num}"

                    p_q = doc.add_paragraph()
                    r_q_num = p_q.add_run(f"Câu {q_num}: ")
                    r_q_num.font.bold = True
                    add_text_with_latex(p_q, q_title)

                    # 4 Phương án A, B, C, D
                    options = q_item.get("quiz_options") or []
                    correct_opt = None
                    distractors = []

                    for opt in options:
                        if not isinstance(opt, dict):
                            continue
                        lbl = str(opt.get("label") or "A").strip()
                        txt = str(opt.get("text") or "").strip()
                        is_c = bool(opt.get("is_correct", False))

                        p_opt = doc.add_paragraph()
                        r_lbl = p_opt.add_run(f"  [{lbl}]. ")
                        r_lbl.font.bold = True
                        if is_c:
                            correct_opt = (lbl, txt)
                            r_lbl.font.color.rgb = RGBColor(0x05, 0x96, 0x69)  # Green
                        add_text_with_latex(p_opt, txt)

                        if not is_c:
                            distractors.append((lbl, opt.get("distractor_rationale") or ""))

                    # Đáp án đúng & Bẫy sai lầm
                    p_ans = doc.add_paragraph()
                    if correct_opt:
                        r_ans_lbl = p_ans.add_run(f"  ➜ [Đáp án đúng chuẩn SGK]: Phương án {correct_opt[0]}\n")
                        r_ans_lbl.font.bold = True
                        r_ans_lbl.font.color.rgb = RGBColor(0x05, 0x96, 0x69)

                    if distractors:
                        r_dis_head = p_ans.add_run("  💡 [Phân tích bẫy sai lầm học sinh dễ mắc phải]:\n")
                        r_dis_head.font.bold = True
                        r_dis_head.font.italic = True
                        for d_lbl, d_rat in distractors:
                            if d_rat:
                                p_d = doc.add_paragraph()
                                r_dl = p_d.add_run(f"    • Phương án {d_lbl}: ")
                                r_dl.font.bold = True
                                r_dl.font.italic = True
                                add_text_with_latex(p_d, d_rat, italic=True)

            # 2. Nhúng Các Bước Giải Mẫu Tự Luận Chuẩn Mực SGK
            worked_examples = deck_info.get("worked_examples") or []
            if worked_examples:
                p_we_head = doc.add_paragraph()
                r_weh = p_we_head.add_run("\n❖ HƯỚNG DẪN GIẢI MẪU TỰ LUẬN TỪNG BƯỚC CHUẨN MỰC SGK:")
                r_weh.font.bold = True
                r_weh.font.size = Pt(12.5)
                r_weh.font.color.rgb = RGBColor(0x7c, 0x2d, 0x12)  # Amber-Red

                for we_idx, we_item in enumerate(worked_examples):
                    we_num = we_idx + 1
                    we_title = we_item.get("title") or f"Ví dụ áp dụng {we_num}"

                    p_we = doc.add_paragraph()
                    r_we_num = p_we.add_run(f"Ví dụ {we_num}: ")
                    r_we_num.font.bold = True
                    add_text_with_latex(p_we, we_title)

                    steps = we_item.get("steps") or []
                    for s_idx, step_text in enumerate(steps):
                        p_step = doc.add_paragraph()
                        r_s_idx = p_step.add_run(f"  • Bước {s_idx + 1}: ")
                        r_s_idx.font.bold = True
                        add_text_with_latex(p_step, step_text)

    # 8. Phần Cuối Trang: Khung Ký Duyệt Giáo Án
    p_sign = doc.add_paragraph()
    p_sign.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r_date = p_sign.add_run("\n\nNgày ..... tháng ..... năm 2026\n")
    r_date.font.italic = True

    table_sign = doc.add_table(rows=1, cols=2)
    table_sign.alignment = WD_TABLE_ALIGNMENT.CENTER
    c_sign1, c_sign2 = table_sign.rows[0].cells
    c_sign1.width = Inches(3.2)
    c_sign2.width = Inches(3.3)

    p_s1 = c_sign1.paragraphs[0]
    p_s1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_s1 = p_s1.add_run("TỔ TRƯỞNG CHUYÊN MÔN DUYỆT\n")
    r_s1.font.bold = True
    r_s1_sub = p_s1.add_run("(Ký và ghi rõ họ tên)")
    r_s1_sub.font.italic = True

    p_s2 = c_sign2.paragraphs[0]
    p_s2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_s2 = p_s2.add_run("GIÁO VIÊN SOẠN BÀI\n")
    r_s2.font.bold = True
    r_s2_sub = p_s2.add_run("(Ký và ghi rõ họ tên)")
    r_s2_sub.font.italic = True

    # 9. Xuất byte stream
    target_stream = io.BytesIO()
    doc.save(target_stream)
    target_stream.seek(0)
    return target_stream


def export_lesson_plan_to_docx_file(
    plan: Union[LessonPlanSchema, dict],
    output_filepath: str,
    slide_deck: Optional[Union[SlideDeckSchema, dict, list]] = None
) -> str:
    """Xuất Kế hoạch bài dạy ra file Word .docx trên đĩa cứng"""
    docx_stream = export_lesson_plan_to_docx(plan, slide_deck=slide_deck)
    os.makedirs(os.path.dirname(os.path.abspath(output_filepath)), exist_ok=True)
    with open(output_filepath, "wb") as f:
        f.write(docx_stream.getbuffer())
    print(f"Đã xuất thành công file Word Kế hoạch bài dạy chuẩn CV 5512: {output_filepath}")
    return output_filepath
