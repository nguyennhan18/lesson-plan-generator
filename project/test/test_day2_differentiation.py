import sys
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Nạp file .env từ thư mục project
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Thêm đường dẫn project/app vào sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent / "app"))

from schemas.slide_schema import ClassProficiency, SlideLayout
from services.ai_service import generate_slide_deck

def test_differentiation():
    print("==================================================")
    print("🚀 BẮT ĐẦU TEST TASK 2.3: SINH SLIDE PHÂN HÓA HỌC LỰC")
    print("🎯 BÀI HỌC: PHƯƠNG TRÌNH BẬC HAI MỘT ẨN")
    print("==================================================\n")

    topic = "Phương trình bậc hai một ẩn"
    subject = "Toán học"
    grade = 10

    # -------------------------------------------------------------
    # 1. TEST CASE 1: LỚP CƠ BẢN / YẾU (BASIC)
    # -------------------------------------------------------------
    print("⏳ [1/2] Đang gọi Gemini sinh slide cho Lớp Cơ bản (BASIC)...")
    deck_basic = generate_slide_deck(
        topic=topic,
        subject=subject,
        grade=grade,
        class_proficiency=ClassProficiency.BASIC,
        target_outcome="Học sinh xác định đúng hệ số a, b, c, tính chính xác biệt thức Delta và áp dụng công thức nghiệm cơ bản."
    )
    print(f"✅ Đã sinh thành công bộ slide BASIC: {len(deck_basic.slides)} slides.")
    
    # -------------------------------------------------------------
    # 2. TEST CASE 2: LỚP NÂNG CAO / CHUYÊN TOÁN (ADVANCED)
    # -------------------------------------------------------------
    print("\n⏳ [2/2] Đang gọi Gemini sinh slide cho Lớp Nâng cao (ADVANCED)...")
    deck_advanced = generate_slide_deck(
        topic=topic,
        subject=subject,
        grade=grade,
        class_proficiency=ClassProficiency.ADVANCED,
        target_outcome="Học sinh giải và biện luận phương trình chứa tham số m, kết hợp định lý Vi-ét xét dấu nghiệm và ứng dụng đồ thị Parabol."
    )
    print(f"✅ Đã sinh thành công bộ slide ADVANCED: {len(deck_advanced.slides)} slides.")

    # -------------------------------------------------------------
    # 3. ĐỐI CHIẾU VÀ ĐÁNH GIÁ TIÊU CHÍ DOD
    # -------------------------------------------------------------
    print("\n==================================================")
    print("📊 BÁO CÁO ĐỐI CHIẾU SỰ KHÁC BIỆT SƯ PHẠM (TASK 2.5 PREP):")
    print("==================================================")

    for name, deck in [("LỚP CƠ BẢN (BASIC)", deck_basic), ("LỚP NÂNG CAO (ADVANCED)", deck_advanced)]:
        quiz_slides = [s for s in deck.slides if s.layout == SlideLayout.QUIZ_OPTION or bool(s.quiz_options)]
        print(f"\n🔹 {name}:")
        print(f"   - Tổng số slide: {len(deck.slides)}")
        print(f"   - Số slide trắc nghiệm (QUIZ_OPTION): {len(quiz_slides)}")
        
        for q_idx, q in enumerate(quiz_slides, 1):
            print(f"     * Câu trắc nghiệm {q_idx}: '{q.title}'")
            for opt in q.quiz_options:
                status = "✅ ĐÚNG" if opt.is_correct else f"❌ SAI (Lỗi: {opt.distractor_rationale})"
                print(f"       [{opt.label}] {opt.text} -> {status}")

    print("\n🎉 HOÀN THÀNH TEST! Cả 2 bộ slide đều parse Pydantic hợp lệ 100%!")

if __name__ == "__main__":
    test_differentiation()
