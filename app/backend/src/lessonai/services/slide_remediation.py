"""
Làm sạch cấu trúc các slide trích xuất từ luồng `pdf2xml` (Toán 12 KNTT - CT 2018)
theo Phụ lục A (`plan_v3.md`), bảo toàn trung thực các cảnh báo nội dung
(`missing_visual`, `truncated_solution`) để giáo viên đối chiếu và duyệt.
"""
from __future__ import annotations

import copy
import re
from typing import Any, Dict, List

from lessonai.services.deck_lint import (
    DIVIDER_TOKEN_RE,
    WARMUP_FORBIDDEN_TITLE_RE,
    is_divider_slide,
    is_fragment_line,
)

PRIVATE_USE_AND_BULLET_GLYPHS_RE = re.compile(r"[\uf000-\uf8ff\u0de3❑✓]")
VECTOR_ARROW_AFTER_TOKEN_RE = re.compile(r"\b([A-Z]{1,2}|[a-z])\s*\u0526")
STRAY_VECTOR_ARROW_RE = re.compile(r"\s*\u0526\s*")
ATTACH_NO_SPACE_TOKENS = {")", ".", ",", ";", ":", "?", "!"}


def _clean_line_glyphs(text: str) -> str:
    """Loại bỏ ký tự Wingdings/Private Use và chuẩn hóa mũi tên vectơ rời (\\u0526)."""
    if not text:
        return ""
    cleaned = PRIVATE_USE_AND_BULLET_GLYPHS_RE.sub("", str(text))
    cleaned = VECTOR_ARROW_AFTER_TOKEN_RE.sub(r"$\\vec{\1}$", cleaned)
    cleaned = STRAY_VECTOR_ARROW_RE.sub("", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def remediate_pdf2xml_slide(raw_slide: Dict[str, Any]) -> Dict[str, Any]:
    """
    Hàn gắn các dòng mảnh vỡ (`fragment_line`), số mũ/token chuyển mục rời (`divider_token`),
    và sửa phân loại nhầm Khởi động (`misclassified_warmup`) do quá trình tách block `pdf2xml`.

    Tuyệt đối KHÔNG tự thêm hình giả (`has_image=True`) hay tự điền lời giải cho các slide
    bị cắt cụt (`truncated_solution`), nhằm giữ nguyên cảnh báo thật cho giáo viên duyệt.
    """
    slide = copy.deepcopy(raw_slide)
    title = _clean_line_glyphs(slide.get("title") or "")
    raw_bullets = [
        _clean_line_glyphs(str(b))
        for b in (slide.get("bullet_points") or [])
        if str(b).strip()
    ]

    # 1. Xử lý các token chuyển mục hoặc số mũ 1-2 chữ số bị tách thành dòng riêng
    filtered_bullets: List[str] = []
    for line in raw_bullets:
        if not line:
            continue
        if DIVIDER_TOKEN_RE.match(line):
            if (
                filtered_bullets
                and re.fullmatch(r"\d{1,2}", line)
                and re.search(r"[xytabnmkf)|]$", filtered_bullets[-1])
            ):
                filtered_bullets[-1] = f"{filtered_bullets[-1]}^{line}"
            continue
        filtered_bullets.append(line)

    # 2. Hàn gắn lặp lại các dòng mảnh vỡ (< 3 từ và không phải công thức/nhãn mục) vào dòng liền kề
    final_bullets: List[str] = list(filtered_bullets)
    for _ in range(4):
        if not any(is_fragment_line(b) for b in final_bullets):
            break
        next_pass: List[str] = []
        for line in final_bullets:
            if is_fragment_line(line):
                sep = "" if line in ATTACH_NO_SPACE_TOKENS else " "
                if next_pass:
                    next_pass[-1] = f"{next_pass[-1]}{sep}{line}".strip()
                else:
                    title = f"{title}{sep}{line}".strip()
            else:
                next_pass.append(line)
        final_bullets = next_pass

    # Nếu tiêu đề rỗng hoặc vẫn là token chuyển mục đơn lẻ, ghép với dòng đầu tiên
    if (not title or DIVIDER_TOKEN_RE.match(title)) and final_bullets:
        first = final_bullets.pop(0)
        title = f"{title} - {first}".strip(" -") if title else first

    # 3. Sửa phân loại nhầm Khởi động khi tiêu đề thực chất là Vận dụng / Luyện tập / Bài tập
    if slide.get("activity_type") == "khoi_dong" and WARMUP_FORBIDDEN_TITLE_RE.search(title):
        slide["activity_type"] = "van_dung" if "vận dụng" in title.lower() else "luyen_tap"

    slide["title"] = title
    slide["bullet_points"] = final_bullets

    # 4. Đánh dấu đúng layout_hint="TITLE_ONLY" cho các slide bìa/chuyển mục thuần túy
    if is_divider_slide(slide) or DIVIDER_TOKEN_RE.match(slide["title"]):
        slide["layout_hint"] = "TITLE_ONLY"
        slide["slide_role"] = "section_header"

    slide["full_text"] = "\n".join([slide["title"], *slide["bullet_points"]]).strip()
    return slide
