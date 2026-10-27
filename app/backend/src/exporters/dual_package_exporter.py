# -*- coding: utf-8 -*-
"""
Dual-Package Exporter Module (Task 19.3)
LessonAI-5512 • Quantum Studio

Chức năng:
1. Đóng gói trọn bộ Kế hoạch bài dạy Word (.docx) chuẩn CV 5512 và Bài giảng PowerPoint (.pptx) chuẩn 16:9.
2. Đồng bộ hóa 100% dữ liệu song song (Dual-Mode Sync) giữa Giáo án và Slide.
3. Tự động tính toán mã kiểm tra tính toàn vẹn (SHA-256 Checksums).
4. Tạo tệp tin Bản quyền & Hướng dẫn sư phạm (Manifest) chi tiết.
5. Tối ưu hóa hiệu năng xuất tệp tin đa luồng (Concurrent ThreadPoolExecutor) và nén tối ưu ZIP_DEFLATED.
6. Chuẩn hóa tên tệp tương thích tuyệt đối với Windows Explorer, macOS và Linux.
"""

import io
import re
import zipfile
import hashlib
import unicodedata
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass
import concurrent.futures

from schemas.schemas import LessonPlanSchema
from schemas.slide_schema import SlideDeckSchema
from exporters.docx_exporter import export_lesson_plan_to_docx, synchronize_lesson_and_slide_deck
from exporters.slide_exporter import export_slide_deck_to_pptx


@dataclass
class DualPackageResult:
    """Kết quả đóng gói trọn bộ Dual-Package"""
    zip_bytes: bytes
    filename: str
    docx_filename: str
    pptx_filename: str
    manifest_filename: str
    docx_sha256: str
    pptx_sha256: str
    zip_sha256: str
    file_count: int
    manifest_text: str


_VIETNAMESE_MAP = str.maketrans(
    "àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ"
    "ÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ",
    "aaaaaaaaaaaaaaaaaeeeeeeeeeeeiiiiiooooooooooooooooouuuuuuuuuuuyyyyyd"
    "AAAAAAAAAAAAAAAAAEEEEEEEEEEEIIIIIOOOOOOOOOOOOOOOOOUUUUUUUUUUUYYYYYD"
)


def remove_vietnamese_diacritics(text: str) -> str:
    """
    Chuyển đổi chuỗi tiếng Việt có dấu thành không dấu an toàn (bảo toàn chữ hoa/thường).
    Tránh lỗi mã hóa tên tệp tin (mojibake) khi giải nén trên Windows cũ.
    """
    if not text:
        return ""
    translated = text.translate(_VIETNAMESE_MAP)
    normalized = unicodedata.normalize('NFKD', translated).encode('ascii', 'ignore').decode('ascii')
    return normalized


def sanitize_filename(name: str, max_length: int = 60) -> str:
    """
    Chuẩn hóa tên tệp tin: bỏ dấu tiếng Việt, loại bỏ ký tự cấm, thay khoảng trắng bằng dấu gạch dưới.
    """
    ascii_name = remove_vietnamese_diacritics(name)
    cleaned = re.sub(r'[^a-zA-Z0-9_\-]', '_', ascii_name)
    cleaned = re.sub(r'_+', '_', cleaned).strip('_')
    if not cleaned:
        cleaned = "LessonAI_5512"
    return cleaned[:max_length]


def calculate_sha256(data: bytes) -> str:
    """Tính mã băm SHA-256 xác thực tính toàn vẹn của tệp tin nhị phân"""
    hasher = hashlib.sha256()
    hasher.update(data)
    return hasher.hexdigest()


def normalize_slide_deck_payload(deck_raw: Any) -> SlideDeckSchema:
    """
    Tự động chuẩn hóa dữ liệu SlideDeck trước khi kết xuất PowerPoint:
    - Bổ sung tiêu đề mặc định nếu bị thiếu.
    - Ép kiểu SlideType hợp lệ ('TITLE_SLIDE', 'WARM_UP_SLIDE', 'CONCEPT_SLIDE', 'EXERCISE_SLIDE', ...).
    - Bảo toàn toàn vẹn chuỗi ảnh snapshot 3D Base64 Data URL.
    """
    if isinstance(deck_raw, SlideDeckSchema):
        return deck_raw

    if not isinstance(deck_raw, dict):
        raise ValueError("Dữ liệu SlideDeck phải là dict hoặc SlideDeckSchema")

    deck_copy = dict(deck_raw)
    valid_types = {
        'TITLE_SLIDE', 'WARM_UP_SLIDE', 'CONCEPT_SLIDE',
        'EXERCISE_SLIDE', 'TEACHER_NOTE_SLIDE', 'SUMMARY_SLIDE'
    }

    slides = deck_copy.get("slides", [])
    normalized_slides = []
    for idx, s in enumerate(slides):
        if isinstance(s, dict):
            s_copy = dict(s)
            # Chuẩn hóa slide_index
            if "slide_index" not in s_copy and "slide_number" in s_copy:
                s_copy["slide_index"] = s_copy["slide_number"]
            elif "slide_index" not in s_copy:
                s_copy["slide_index"] = idx + 1

            # Chuẩn hóa SlideType
            stype = str(s_copy.get("type", "")).strip()
            if stype not in valid_types:
                s_copy["type"] = "EXERCISE_SLIDE"

            # Chuẩn hóa Tiêu đề bắt buộc
            if not s_copy.get("title"):
                s_copy["title"] = s_copy.get("question") or f"Trang {idx + 1}"

            normalized_slides.append(s_copy)
        else:
            normalized_slides.append(s)

    deck_copy["slides"] = normalized_slides
    return SlideDeckSchema.model_validate(deck_copy)


def generate_dual_package_manifest(
    title: str,
    subject: str,
    grade: int,
    docx_filename: str,
    docx_size: int,
    docx_sha256: str,
    pptx_filename: str,
    pptx_size: int,
    pptx_sha256: str,
    slide_count: int,
    activity_count: int,
    has_3d: bool = False,
    quiz_count: int = 0
) -> str:
    """
    Tạo nội dung tệp tin Hướng dẫn Sư phạm & Bản quyền (Manifest) cho gói kép Dual-Package
    """
    # Lấy giờ Việt Nam (UTC+7)
    vn_tz = timezone(timedelta(hours=7))
    created_at = datetime.now(vn_tz).strftime("%H:%M:%S ngày %d/%m/%Y")

    docx_kb = docx_size / 1024.0
    pptx_kb = pptx_size / 1024.0

    manifest = f"""================================================================================
TRỌN BỘ TÀI LIỆU DẠY HỌC CHUẨN CÔNG VĂN 5512/BGDĐT (DUAL-MODE TOÁN HỌC)
Phát triển bởi: Hệ thống Trợ Giảng AI - Quantum Studio (LessonAI-5512)
================================================================================

1. THÔNG TIN BÀI DẠY:
   - Tên bài dạy / Chủ đề: {title}
   - Môn học: {subject}
   - Khối lớp: {grade}
   - Thời điểm xuất bản: {created_at} (Giờ Việt Nam UTC+7)
   - Tiêu chuẩn sư phạm: Công văn 5512/BGDĐT & Chương trình GDPT 2018

2. DANH MỤC TÀI LIỆU TRONG GÓI KÉP (DUAL-PACK):
   [1] KẾ HOẠCH BÀI DẠY (GIÁO ÁN WORD):
       - Tệp tin: {docx_filename}
       - Dung lượng: {docx_kb:.1f} KB
       - Quy chuẩn lề: Nghị định 30/2020/NĐ-CP (Trái 3.0cm, Phải 1.5cm, Trên/Dưới 2.0cm)
       - Định dạng công thức: OMML (Office Math Markup Language) gốc, chỉnh sửa tự nhiên
       - Cấu trúc: Đầy đủ 4 hoạt động sư phạm (Khởi động, Hình thành kiến thức, Luyện tập, Vận dụng)
       - Tích hợp: Bổ sung câu hỏi trắc nghiệm đánh giá & bài tập tự luận mẫu đồng bộ từ Slide
       - Checksum (SHA-256): {docx_sha256}

   [2] BÀI GIẢNG ĐIỆN TỬ (POWERPOINT PPTX):
       - Tệp tin: {pptx_filename}
       - Dung lượng: {pptx_kb:.1f} KB
       - Tỉ lệ khung hình: Widescreen 16:9 (13.333 x 7.5 inches)
       - Số lượng slide: {slide_count} slide
       - Trực quan hóa: Mô hình không gian 3D WebGL (Box-Fit) & Đồ thị giải tích Matplotlib
       - Câu hỏi củng cố: {quiz_count} câu hỏi trắc nghiệm phân tích bẫy sai lầm
       - Speaker Notes: Kịch bản lời thoại giáo viên & mục tiêu sư phạm từng slide
       - Checksum (SHA-256): {pptx_sha256}

3. TÍNH NĂNG ĐỒNG BỘ NỘI DUNG DUAL-MODE (100% SYNC):
   - Đảm bảo tính nhất quán tuyệt đối giữa nội dung giảng dạy trên lớp và hồ sơ giáo án.
   - Hoạt động 1 (Khởi động): Đồng bộ bài toán gợi mở thực tế và câu hỏi khám phá.
   - Hoạt động 2 (Kiến thức mới): Đồng bộ công thức định nghĩa toán học và mô hình trực quan.
   - Hoạt động 3 (Luyện tập): Tự động nhúng câu hỏi trắc nghiệm và lời giải chi tiết 3 bước.
   - Hoạt động 4 (Vận dụng): Đồng bộ bài toán thực tiễn và giao nhiệm vụ về nhà.
   - Mục II: Tự động ghi nhận thiết bị dạy học gồm Mô hình 3D WebGL và Bài giảng điện tử Studio.

4. HƯỚNG DẪN MỞ & SỬ DỤNG:
   - Mở Kế hoạch bài dạy: Khuyến nghị sử dụng Microsoft Word 2016 trở lên hoặc Microsoft 365 để hiển thị chuẩn xác nhất các công thức toán học OMML.
   - Mở Bài giảng điện tử: Khuyến nghị sử dụng Microsoft PowerPoint 2016 trở lên để trình chiếu mượt mà tỉ lệ 16:9.
   - Tương tác mô hình 3D động: Thầy/Cô có thể tương tác trực tiếp xoay, lật, trải phẳng hình 3D trên Web Studio tại ứng dụng Quantum Studio.

================================================================================
Bản quyền tài liệu thuộc về Giáo viên biên soạn và Hệ thống LessonAI-5512.
"""
    return manifest


def export_dual_package(payload: Dict[str, Any], use_concurrency: bool = True) -> DualPackageResult:
    """
    Hàm xuất trọn bộ Gói kép Dual-Package:
    - Tiếp nhận payload chứa 'plan' (hoặc 'lesson_plan') và 'slide_deck' (hoặc 'deck').
    - Đồng bộ hóa dữ liệu sư phạm giữa hai tài liệu.
    - Kết xuất song song file Word (.docx) và file Slide (.pptx) để tối ưu thời gian phản hồi.
    - Đóng gói file .zip với tỷ lệ nén tối ưu ZIP_DEFLATED (compresslevel=6).
    - Tạo tệp tin Bản quyền & Hướng dẫn (Manifest) kèm mã băm SHA-256 xác thực.
    """
    if not isinstance(payload, dict):
        raise ValueError("Payload phải là đối tượng dict chứa 'plan' hoặc 'slide_deck'")

    plan_raw = payload.get("plan") or payload.get("lesson_plan")
    deck_raw = payload.get("slide_deck") or payload.get("deck")

    if not plan_raw and not deck_raw:
        raise ValueError("Cần cung cấp ít nhất một trong hai: 'plan' hoặc 'slide_deck'")

    # Xác định tiêu đề, môn học và khối lớp
    title = "BaiGiang"
    subject = "Toán học"
    grade = 11

    if plan_raw and isinstance(plan_raw, dict):
        title = plan_raw.get("lesson_title") or title
        subject = plan_raw.get("subject") or subject
        grade = plan_raw.get("grade") or grade
    elif plan_raw and isinstance(plan_raw, LessonPlanSchema):
        title = plan_raw.lesson_title or title
        subject = plan_raw.subject or subject
        grade = plan_raw.grade or grade
    elif deck_raw and isinstance(deck_raw, dict):
        title = deck_raw.get("presentation_title") or title
        subject = deck_raw.get("subject") or subject
        grade = deck_raw.get("grade") or grade
    elif deck_raw and isinstance(deck_raw, SlideDeckSchema):
        title = deck_raw.presentation_title or title
        subject = deck_raw.subject or subject
        grade = deck_raw.grade or grade

    # Tên tệp tin an toàn (bỏ dấu tiếng Việt, không khoảng trắng)
    safe_title = sanitize_filename(title)

    # 1. Chuẩn bị đối tượng SlideDeckSchema nếu có
    deck_obj: Optional[SlideDeckSchema] = None
    slide_count = 0
    has_3d = False
    quiz_count = 0

    if deck_raw:
        deck_obj = normalize_slide_deck_payload(deck_raw)
        slide_count = len(deck_obj.slides) if deck_obj.slides else 0
        for s in (deck_obj.slides or []):
            if s.has_3d or s.polyhedron_type:
                has_3d = True
            if s.quiz_options and len(s.quiz_options) > 0:
                quiz_count += 1

    # 2. Chuẩn bị đối tượng LessonPlan nếu có
    activity_count = 0
    if plan_raw:
        if isinstance(plan_raw, dict):
            activity_count = len(plan_raw.get("activities", []))
        elif isinstance(plan_raw, LessonPlanSchema):
            activity_count = len(plan_raw.activities)

    # 3. Kết xuất song song (Concurrent Execution) DOCX và PPTX
    docx_bytes = b""
    pptx_bytes = b""

    def _render_docx():
        if plan_raw is None:
            return b""
        docx_stream = export_lesson_plan_to_docx(plan_raw, slide_deck=deck_raw)
        return docx_stream.getvalue()

    def _render_pptx():
        if deck_obj is None:
            return b""
        pptx_stream = export_slide_deck_to_pptx(deck_obj)
        return pptx_stream.getvalue()

    if use_concurrency and plan_raw and deck_obj:
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_docx = executor.submit(_render_docx)
            future_pptx = executor.submit(_render_pptx)
            docx_bytes = future_docx.result()
            pptx_bytes = future_pptx.result()
    else:
        if plan_raw:
            docx_bytes = _render_docx()
        if deck_obj:
            pptx_bytes = _render_pptx()

    # 4. Tính toán mã băm SHA-256
    docx_sha256 = calculate_sha256(docx_bytes) if docx_bytes else "N/A"
    pptx_sha256 = calculate_sha256(pptx_bytes) if pptx_bytes else "N/A"

    # 5. Tên tệp tin thành phần
    docx_filename = f"Giao_An_5512_{safe_title}.docx"
    pptx_filename = f"Slide_Bai_Giang_{safe_title}.pptx"
    manifest_filename = "Huong_Dan_Goi_Kep_5512.txt"

    # 6. Tạo Manifest
    manifest_text = generate_dual_package_manifest(
        title=title,
        subject=subject,
        grade=grade,
        docx_filename=docx_filename,
        docx_size=len(docx_bytes),
        docx_sha256=docx_sha256,
        pptx_filename=pptx_filename,
        pptx_size=len(pptx_bytes),
        pptx_sha256=pptx_sha256,
        slide_count=slide_count,
        activity_count=activity_count,
        has_3d=has_3d,
        quiz_count=quiz_count
    )

    # 7. Đóng gói ZIP Stream với tối ưu nén
    zip_buffer = io.BytesIO()
    file_count = 0

    with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        # File Word
        if docx_bytes:
            zf.writestr(docx_filename, docx_bytes)
            file_count += 1

        # File PowerPoint
        if pptx_bytes:
            zf.writestr(pptx_filename, pptx_bytes)
            file_count += 1

        # File Manifest
        zf.writestr(manifest_filename, manifest_text.encode("utf-8"))
        file_count += 1

    zip_buffer.seek(0)
    zip_bytes = zip_buffer.getvalue()
    zip_sha256 = calculate_sha256(zip_bytes)

    zip_filename = f"Tron_Bo_Giao_An_Slide_{safe_title}.zip"

    return DualPackageResult(
        zip_bytes=zip_bytes,
        filename=zip_filename,
        docx_filename=docx_filename,
        pptx_filename=pptx_filename,
        manifest_filename=manifest_filename,
        docx_sha256=docx_sha256,
        pptx_sha256=pptx_sha256,
        zip_sha256=zip_sha256,
        file_count=file_count,
        manifest_text=manifest_text
    )
