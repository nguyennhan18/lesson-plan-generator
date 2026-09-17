import os
import subprocess
from typing import Union, Dict, Any
from schemas.slide_schema import SlideDeckSchema, SlideSchema, SlideType

def convert_json_to_marp_markdown(data: Union[Dict[str, Any], SlideDeckSchema]) -> str:
    """
    Chuyển đổi dữ liệu SlideDeck (JSON/Dict hoặc Pydantic SlideDeckSchema) 
    sang nội dung Markdown chuẩn định dạng Marp.
    """
    if isinstance(data, SlideDeckSchema):
        deck_dict = data.model_dump()
    elif isinstance(data, dict):
        deck_dict = data
    else:
        raise ValueError("Dữ liệu vào phải là dict hoặc SlideDeckSchema")

    presentation_title = deck_dict.get("presentation_title", "Bài giảng")
    subject = deck_dict.get("subject", "")
    grade = deck_dict.get("grade", "")
    raw_theme = deck_dict.get("theme", "default")
    
    # Map theme tên tùy chỉnh sang Marp themes chuẩn (default, gaia, unwind)
    marp_theme_map = {
        "modern_blue": "default",
        "classic": "gaia",
        "minimal": "unwind"
    }
    theme = marp_theme_map.get(raw_theme, raw_theme if raw_theme in ["default", "gaia", "unwind"] else "default")

    md_lines = []

    # 1. Marp Header / Frontmatter
    md_lines.append("---")
    md_lines.append("marp: true")
    md_lines.append(f"theme: {theme}")
    md_lines.append("paginate: true")
    md_lines.append(f"header: 'Môn {subject} - Lớp {grade} | {presentation_title}'" if subject and grade else f"header: '{presentation_title}'")
    md_lines.append("footer: 'LessonAI-5512'")
    md_lines.append("style: |")
    md_lines.append("  section { font-family: 'Times New Roman', sans-serif; font-size: 24px; padding: 40px; }")
    md_lines.append("  h1 { color: #0056b3; }")
    md_lines.append("  h2 { color: #2c3e50; }")
    md_lines.append("  .highlight { background-color: #e6f2ff; padding: 15px; border-left: 5px solid #0056b3; border-radius: 4px; }")
    md_lines.append("  .teacher-note { font-size: 18px; color: #555; background: #fff3cd; padding: 10px; border-radius: 5px; }")
    md_lines.append("---\n")

    slides = deck_dict.get("slides", [])

    for idx, slide_data in enumerate(slides):
        slide_type = slide_data.get("type", "CONCEPT_SLIDE")
        title = slide_data.get("title", "")
        subtitle = slide_data.get("subtitle", "")
        bullet_points = slide_data.get("bullet_points", [])
        latex_formula = slide_data.get("main_definition_latex", "")
        teacher_note = slide_data.get("teacher_note", "")
        image_prompt = slide_data.get("image_prompt", "")
        layout = slide_data.get("layout", "SINGLE_COLUMN")

        # Thêm dấu ngắt slide cho từ slide thứ 2 trở đi
        if idx > 0:
            md_lines.append("\n---\n")

        # Slide Tiêu đề bài giảng
        if slide_type == SlideType.TITLE_SLIDE or slide_type == "TITLE_SLIDE":
            md_lines.append("<!-- _class: lead -->")
            md_lines.append("<!-- _header: '' -->") # Ẩn header ở slide đầu
            md_lines.append(f"# {title}")
            if subtitle:
                md_lines.append(f"### {subtitle}")
            if subject or grade:
                md_lines.append(f"\n**Môn:** {subject} | **Khối:** {grade}")

        # Slide Khởi động, Khái niệm, Bài tập, Tóm tắt,...
        else:
            # Type Badge / Tag
            type_labels = {
                "WARM_UP_SLIDE": "KHỞI ĐỘNG",
                "CONCEPT_SLIDE": "KHÁI NIỆM TRỌNG TÂM",
                "EXERCISE_SLIDE": "BÀI TẬP RÈN LUYỆN",
                "TEACHER_NOTE_SLIDE": "GHI CHÚ BÀI GIẢNG",
                "SUMMARY_SLIDE": "TÓM TẮT & DẶN DÒ"
            }
            badge = type_labels.get(slide_type, "")
            if badge:
                md_lines.append(f"#### {badge}")

            md_lines.append(f"# {title}")
            if subtitle:
                md_lines.append(f"*{subtitle}*\n")

            # Layout dạng 2 cột (Marp CSS grid)
            if layout == "TWO_COLUMN" and len(bullet_points) >= 2:
                mid = len(bullet_points) // 2
                col1 = bullet_points[:mid]
                col2 = bullet_points[mid:]

                md_lines.append('<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">')
                md_lines.append('<div>\n')
                for pt in col1:
                    md_lines.append(f"- {pt}")
                md_lines.append('\n</div>\n<div>\n')
                for pt in col2:
                    md_lines.append(f"- {pt}")
                md_lines.append('\n</div>\n</div>\n')
            else:
                # Layout mặc định (1 cột)
                for pt in bullet_points:
                    md_lines.append(f"- {pt}")
                md_lines.append("")

            # Chèn Công thức LaTeX (nếu có)
            if latex_formula:
                # Xử lý chuẩn hóa định dạng \( ... \) sang $ ... $ hoặc $$ ... $$ cho Marp (KaTeX)
                clean_latex = latex_formula.replace(r"\(", "").replace(r"\)", "").strip()
                if not (clean_latex.startswith("$") and clean_latex.endswith("$")):
                    formatted_latex = f"$$ {clean_latex} $$"
                else:
                    formatted_latex = clean_latex
                
                md_lines.append(f'<div class="highlight">\n\n**Công thức trọng tâm:**\n\n{formatted_latex}\n\n</div>\n')

            # Chèn Gợi ý hình ảnh (dạng comment hoặc placeholder)
            if image_prompt:
                md_lines.append(f"\n> 🖼️ *[Gợi ý minh họa AI]*: {image_prompt}\n")

        # Ghi chú dành cho Giáo viên (Presenter Notes trong Marp)
        if teacher_note:
            md_lines.append(f"\n<!-- Presenter Note: {teacher_note} -->")

    return "\n".join(md_lines)


def export_to_marp_md_file(data: Union[Dict[str, Any], SlideDeckSchema], output_filepath: str) -> str:
    """
    Xuất dữ liệu SlideDeck ra file Markdown (.md) chuẩn Marp.
    """
    md_content = convert_json_to_marp_markdown(data)
    
    # Tạo thư mục chứa nếu chưa tồn tại
    os.makedirs(os.path.dirname(os.path.abspath(output_filepath)), exist_ok=True)
    
    with open(output_filepath, "w", encoding="utf-8") as f:
        f.write(md_content)
    
    print(f"✅ Đã xuất thành công file Marp Markdown: {output_filepath}")
    return output_filepath


def compile_marp_to_pptx(md_filepath: str, output_pptx_path: str) -> bool:
    """
    Gọi Marp CLI (nếu hệ thống đã cài marp CLI via npm/npx) để render file .md thành file PowerPoint (.pptx).
    Yêu cầu: Đã cài Node.js / @marp-team/marp-cli
    """
    try:
        command = f"npx @marp-team/marp-cli '{md_filepath}' --pptx -o '{output_pptx_path}'"
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"🎉 Đã biên dịch file PPTX bằng Marp CLI thành công: {output_pptx_path}")
            return True
        else:
            print(f"⚠️ Lỗi Marp CLI: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Không thể thực thi Marp CLI: {e}")
        return False


if __name__ == "__main__":
    # Test chạy thử nghiệm converter với dữ liệu mẫu
    sample_slide_deck = {
        "presentation_title": "Bài 3: Cấp số cộng",
        "subject": "Toán học",
        "grade": 11,
        "theme": "modern_blue",
        "slides": [
            {
                "slide_index": 1,
                "type": "TITLE_SLIDE",
                "title": "BÀI 3: CẤP SỐ CỘNG",
                "subtitle": "Chương IV: Dãy số - Cấp số cộng và Cấp số nhân",
                "teacher_note": "GV giới thiệu tổng quan bài học trong 2 phút."
            },
            {
                "slide_index": 2,
                "type": "WARM_UP_SLIDE",
                "title": "Hoạt động Khởi động",
                "bullet_points": [
                    "Quan sát dãy số tiền tiết kiệm hàng tháng: 100k, 150k, 200k, 250k...",
                    "Em có nhận xét gì về sự chênh lệch giữa 2 tháng liên tiếp?",
                    "Quy luật tăng trưởng ở đây là gì?"
                ],
                "teacher_note": "GV gọi 1-2 học sinh trả lời nhận xét quy luật cộng thêm 50k."
            },
            {
                "slide_index": 3,
                "type": "CONCEPT_SLIDE",
                "title": "1. Định nghĩa Cấp số cộng",
                "bullet_points": [
                    "Cấp số cộng là một dãy số (hữu hạn hoặc vô hạn).",
                    "Kể từ số hạng thứ hai, mỗi số hạng đều bằng số hạng đứng ngay trước nó cộng với một số không đổi d.",
                    "Số d được gọi là công sai của cấp số cộng."
                ],
                "main_definition_latex": r"\( u_{n+1} = u_n + d, \quad \forall n \in \mathbb{N}^* \)",
                "image_prompt": "Hình ảnh minh họa các bậc thang tăng đều chiều cao",
                "teacher_note": "GV nhấn mạnh công sai d có thể âm, dương hoặc bằng 0."
            }
        ]
    }

    # 1. Xuất file .md
    output_md = "sample_presentation.md"
    export_to_marp_md_file(sample_slide_deck, output_md)

    # 2. Thử biên dịch sang PPTX bằng Marp CLI (nếu có)
    # compile_marp_to_pptx(output_md, "sample_presentation.pptx")
