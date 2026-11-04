import os
import json
from fastapi import HTTPException
from lessonai.utils.temp_file_cleaner import clean_expired_temp_files, get_temp_storage_stats, cleanup_memory_and_figures
from fastapi import APIRouter, Depends
from lessonai.core.ownership import require_owner
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


@router.post("/api/v1/system/clean-temp-files", tags=["System & Maintenance"])
def clean_temp_files_endpoint(
    max_age_seconds: int = 3600,
    force_all: bool = False,
    dry_run: bool = False,
    owner=Depends(require_owner)
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
def get_temp_stats_endpoint(owner=Depends(require_owner)):
    """
    Task 19.4: Tra cứu thống kê số lượng và dung lượng tệp tin tạm hiện có trên server.
    """
    try:
        stats = get_temp_storage_stats()
        return stats.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi truy vấn thống kê tệp tạm: {str(e)}")


@router.post("/api/v1/system/cleanup-memory", tags=["System & Maintenance"])
def cleanup_memory_endpoint(owner=Depends(require_owner)):
    """
    Task 19.4: Giải phóng tài nguyên bộ nhớ rò rỉ (đóng toàn bộ figure Matplotlib & Garbage Collection).
    """
    try:
        return cleanup_memory_and_figures()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi giải phóng bộ nhớ: {str(e)}")
