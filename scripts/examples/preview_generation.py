"""Manual generation preview; may call configured AI providers."""
from pathlib import Path
from lessonai.core.config import OUTPUT_DIR
from lessonai.services.generation import generate_lesson_plan, generate_slide_deck
from lessonai.exporters.docx_exporter import export_lesson_plan_to_docx
from lessonai.exporters.slide_exporter import export_slide_deck_to_pptx_file as export_slide_to_pptx

def get_next_test_filepath(file_type: str) -> Path:
    """
    Tạo thư mục nếu chưa có và tìm đường dẫn file tiếp theo (vd: test/pptx/test_1.pptx).
    - file_type: 'pptx' hoặc 'word' (hoặc 'docx')
    """
    ext = "docx" if file_type in ["word", "docx"] else "pptx"
    folder_name = "word" if ext == "docx" else "pptx"

    # 1. Định vị thư mục lưu trữ: output/pptx/ hoặc output/word/
    base_dir = OUTPUT_DIR / folder_name
    base_dir.mkdir(parents=True, exist_ok=True)  # Tự động tạo thư mục nếu chưa tồn tại

    # 2. Quét các file hiện có để tìm index lớn nhất
    index = 1
    while (base_dir / f"test_{index}.{ext}").exists():
        index += 1

    return base_dir / f"test_{index}.{ext}"
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Sinh Kế hoạch bài dạy (5512) và Slide bài giảng bằng Gemini AI")
    parser.add_argument("--topic", type=str, help="Tên chủ đề / bài dạy (VD: Cấp số cộng, Đạo hàm...)")
    parser.add_argument("--subject", type=str, default="Toán học", help="Tên môn học (mặc định: Toán học)")
    parser.add_argument("--grade", type=int, default=12, help="Khối lớp (mặc định: 12)")
    args = parser.parse_args()

    topic = args.topic
    if not topic:
        try:
            topic = input("Nhập tên bài dạy / chủ đề cần sinh (VD: Cấp số cộng, Đạo hàm, Tích phân...): ").strip()
        except Exception:
            topic = ""
        if not topic:
            topic = "Cấp số cộng"

    subject = args.subject
    grade = args.grade

    print(f"\n Đang tiến hành tạo Giáo án & Slide cho bài: '{topic}', Môn {subject}, Lớp {grade}...")

    plan, val_result = generate_lesson_plan(
        topic=topic,
        subject=subject,
        grade=grade
    )
    docx_path = get_next_test_filepath("word")
    docx_stream = export_lesson_plan_to_docx(plan)
    with open(docx_path, "wb") as f:
        f.write(docx_stream.getbuffer())
    print(f"Đã xuất ra file Word: {docx_path}")

    # Xuất Slide dùng chính plan vừa sinh ra
    print("\nĐang sinh Slide bài giảng JSON từ AI...")
    try:
        slide_deck = generate_slide_deck(
            topic=topic,
            subject=subject,
            grade=grade,
            plan=plan  # Truyền plan vào để thông tin ăn khớp 100%
        )
        pptx_path = get_next_test_filepath("pptx")
        export_slide_to_pptx(slide_deck, str(pptx_path))
        print(f"Đã xuất thành công file PowerPoint: {pptx_path}")
    except Exception as e:
        print(f"Lỗi khi xuất PowerPoint: {e}")
