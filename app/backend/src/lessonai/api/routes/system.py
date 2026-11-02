import os
import json
from fastapi import HTTPException
from lessonai.utils.temp_file_cleaner import clean_expired_temp_files, get_temp_storage_stats, cleanup_memory_and_figures
from fastapi import APIRouter
from lessonai.core.config import TEST_CASES_PATH

router = APIRouter()

@router.get("/api/v1/health")
def health_check():
    """Kiểm tra trạng thái server và cấu hình API key"""
    return {
        "status": "online",
        "has_api_key": bool(os.getenv("GEMINI_API_KEY")),
        "version": "0.1.0"
    }


@router.get("/api/v1/test-cases")
def get_test_cases():
    """Trả về danh sách các ca kiểm thử mẫu để test nhanh trên giao diện"""
    test_file = TEST_CASES_PATH
    if os.path.exists(test_file):
        with open(test_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return [
        {"id": "tc-m12-01", "lesson_id": "M12-C1-B1", "topic": "Tính đơn điệu và cực trị của hàm số", "subject": "Toán học", "grade": 12},
        {"id": "tc-m12-03", "lesson_id": "M12-C1-B4", "topic": "Khảo sát sự biến thiên và vẽ đồ thị hàm số bậc ba", "subject": "Toán học", "grade": 12},
        {"id": "tc-m12-05", "lesson_id": "M12-C2-B2", "topic": "Hệ trục tọa độ trong không gian Oxyz", "subject": "Toán học", "grade": 12},
        {"id": "tc-m12-06", "lesson_id": "M12-C3-B1", "topic": "Khoảng biến thiên và khoảng tứ phân vị của mẫu số liệu ghép nhóm", "subject": "Toán học", "grade": 12},
        {"id": "tc-m12-07", "lesson_id": "M12-C3-B2", "topic": "Phương sai và độ lệch chuẩn của mẫu số liệu ghép nhóm", "subject": "Toán học", "grade": 12},
        {"id": "tc-m12-08", "lesson_id": "M12-C4-B2", "topic": "Tích phân và công thức Newton - Leibniz", "subject": "Toán học", "grade": 12},
        {"id": "tc-m12-09", "lesson_id": "M12-C5-B1", "topic": "Phương trình mặt phẳng trong không gian Oxyz", "subject": "Toán học", "grade": 12},
        {"id": "tc-m12-10", "lesson_id": "M12-C6-B2", "topic": "Công thức xác suất toàn phần và công thức Bayes", "subject": "Toán học", "grade": 12}
    ]


@router.post("/api/v1/system/clean-temp-files", tags=["System & Maintenance"])
def clean_temp_files_endpoint(
    max_age_seconds: int = 3600,
    force_all: bool = False,
    dry_run: bool = False
):
    """
    Task 19.4: Dọn dẹp các tệp tin tạm (Word, PPTX, ZIP, PNG đồ thị, cache) hết hạn lưu trữ
    trên máy chủ hoặc ép dọn sạch toàn bộ khi force_all=True.
    """
    try:
        report = clean_expired_temp_files(
            max_age_seconds=max_age_seconds,
            force_all=force_all,
            dry_run=dry_run
        )
        return report.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi dọn dẹp tệp tin tạm: {str(e)}")


@router.get("/api/v1/system/temp-stats", tags=["System & Maintenance"])
def get_temp_stats_endpoint():
    """
    Task 19.4: Tra cứu thống kê số lượng và dung lượng tệp tin tạm hiện có trên server.
    """
    try:
        stats = get_temp_storage_stats()
        return stats.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi truy vấn thống kê tệp tạm: {str(e)}")


@router.post("/api/v1/system/cleanup-memory", tags=["System & Maintenance"])
def cleanup_memory_endpoint():
    """
    Task 19.4: Giải phóng tài nguyên bộ nhớ rò rỉ (đóng toàn bộ figure Matplotlib & Garbage Collection).
    """
    try:
        return cleanup_memory_and_figures()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi giải phóng bộ nhớ: {str(e)}")

