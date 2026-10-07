import os
import sys
import json
from pathlib import Path

# Thêm đường dẫn app vào sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.ai_service import generate_lesson_plan, generate_slide_deck, export_slide_to_pptx
from exporters.docx_exporter import export_lesson_plan_to_docx

# Danh sách bộ test đa dạng môn học & khối lớp để đánh giá AI
DEFAULT_TEST_CASES = [
    {"topic": "Cấp số cộng", "subject": "Toán học", "grade": 11},
    {"topic": "Đạo hàm và ứng dụng", "subject": "Toán học", "grade": 11},
    {"topic": "Phương trình bậc hai một ẩn", "subject": "Toán học", "grade": 9},
    {"topic": "Sóng cơ và sự truyền sóng cơ", "subject": "Vật lý", "grade": 12},
    {"topic": "Khảo sát và vẽ đồ thị hàm số", "subject": "Toán học", "grade": 12}
]

def run_batch():
    test_file = Path(__file__).parent / "test_cases.json"
    if test_file.exists():
        with open(test_file, "r", encoding="utf-8") as f:
            test_cases = json.load(f)
        print(f"📂 Đã nạp {len(test_cases)} bài test từ {test_file.name}")
    else:
        test_cases = DEFAULT_TEST_CASES
        with open(test_file, "w", encoding="utf-8") as f:
            json.dump(test_cases, f, ensure_ascii=False, indent=2)
        print(f"📝 Đã tạo file mẫu {test_file.name} chứa {len(test_cases)} bài test.")

    out_word_dir = Path(__file__).resolve().parent.parent / "test" / "word"
    out_pptx_dir = Path(__file__).resolve().parent.parent / "test" / "pptx"
    out_word_dir.mkdir(parents=True, exist_ok=True)
    out_pptx_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n==================================================")
    print(f"🚀 BẮT ĐẦU CHẠY BATCH TEST DÀNH CHO {len(test_cases)} BÀI HỌC DỰ ÁN")
    print(f"==================================================\n")

    for idx, tc in enumerate(test_cases, start=1):
        topic = tc.get("topic", "Bài dạy")
        subject = tc.get("subject", "Toán học")
        grade = tc.get("grade", 12)

        safe_name = re_safe_filename(topic)
        print(f"[{idx}/{len(test_cases)}] 🎯 Đang sinh: '{topic}' - Môn {subject} - Lớp {grade}...")

        try:
            # 1. Sinh Giáo án
            plan, val_result = generate_lesson_plan(topic=topic, subject=subject, grade=grade)
            docx_path = out_word_dir / f"GA_{safe_name}_Lop{grade}.docx"
            docx_stream = export_lesson_plan_to_docx(plan)
            with open(docx_path, "wb") as f:
                f.write(docx_stream.getbuffer())
            print(f"   ✅ Word: {docx_path.name}")

            # 2. Sinh Slide
            slide_deck = generate_slide_deck(topic=topic, subject=subject, grade=grade, plan=plan)
            pptx_path = out_pptx_dir / f"Slide_{safe_name}_Lop{grade}.pptx"
            export_slide_to_pptx(slide_deck, str(pptx_path))
            print(f"   🎉 Slide PPTX: {pptx_path.name}\n")

        except Exception as e:
            print(f"   ❌ Lỗi khi xử lý bài '{topic}': {e}\n")

def re_safe_filename(name: str) -> str:
    import re
    return re.sub(r'[^\w\s-]', '', name).strip().replace(' ', '_')

if __name__ == "__main__":
    run_batch()
