# -*- coding: utf-8 -*-
"""
Temp File Cleaner & Resource Leak Guard (Task 19.4)
LessonAI-5512 • Quantum Studio

Chức năng:
1. Quét và dọn dẹp các tệp tin tạm (temporary files) sinh ra trong quá trình xuất Word, PPTX, ZIP và render đồ thị.
2. Kiểm soát thời gian lưu trữ (retention policy) với ngưỡng `max_age_seconds` (mặc định 3600s = 1 giờ).
3. Hỗ trợ chế độ dọn sạch toàn bộ (`force_all=True`) và chế độ chạy thử (`dry_run=True`).
4. Giải phóng tài nguyên bộ nhớ (Memory Leak Guard): Đóng tất cả Matplotlib figure (`plt.close('all')`) và kích hoạt Python Garbage Collection (`gc.collect()`).
5. Cung cấp báo cáo thống kê dung lượng tệp tạm và kết quả thu hồi bộ nhớ chi tiết.
6. Hỗ trợ chạy dưới dạng module, API endpoint hoặc script dòng lệnh độc lập (CLI / Cronjob).
"""

import os
import sys
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib_cache")
import time
import gc
import logging
import argparse
import platform
import resource
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field, asdict

logger = logging.getLogger("temp_file_cleaner")

# Thư mục tạm mặc định của hệ thống LessonAI-5512
DEFAULT_TEMP_DIRS = [
    "/tmp/lessonai_5512_temp",
    "/tmp/matplotlib_cache",
]

# Phần mở rộng tệp tin tạm được phép dọn dẹp (bảo vệ tuyệt đối code nguồn .py, .json, .md)
ALLOWED_TEMP_EXTENSIONS: Set[str] = {
    ".tmp", ".temp", ".png", ".jpg", ".jpeg",
    ".docx", ".pptx", ".zip", ".log", ".cache"
}

# Tiền tố tệp tin tạm an toàn được dọn dẹp
ALLOWED_TEMP_PREFIXES: Set[str] = {
    "temp_", "tmp_", "chart_", "formula_", "export_",
    "slide_", "giao_an_", "tron_bo_", "lessonai_"
}


@dataclass
class CleaningReport:
    """Báo cáo kết quả dọn dẹp tệp tin tạm và giải phóng bộ nhớ"""
    scanned_files: int = 0
    deleted_files: int = 0
    bytes_reclaimed: int = 0
    reclaimed_mb: float = 0.0
    errors: List[str] = field(default_factory=list)
    directories_scanned: List[str] = field(default_factory=list)
    execution_time_ms: float = 0.0
    freed_memory_mb: float = 0.0
    gc_objects_collected: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TempStatsReport:
    """Báo cáo hiện trạng các thư mục tệp tin tạm"""
    total_files: int = 0
    total_bytes: int = 0
    total_mb: float = 0.0
    directories: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    oldest_file_age_seconds: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TempFileCleaner:
    """
    Bộ dọn dẹp tệp tin tạm và quản lý tài nguyên hệ thống
    """
    def __init__(
        self,
        target_dirs: Optional[List[str]] = None,
        allowed_extensions: Optional[Set[str]] = None,
        allowed_prefixes: Optional[Set[str]] = None
    ):
        self.target_dirs = target_dirs or list(DEFAULT_TEMP_DIRS)
        self.allowed_extensions = allowed_extensions or set(ALLOWED_TEMP_EXTENSIONS)
        self.allowed_prefixes = allowed_prefixes or set(ALLOWED_TEMP_PREFIXES)

    def is_safe_to_delete(self, file_path: Path) -> bool:
        """
        Kiểm tra xem một tệp tin có thỏa mãn điều kiện tệp tạm an toàn hay không:
        1. Phải là file (không xóa thư mục nguồn).
        2. Phần mở rộng phải nằm trong ALLOWED_TEMP_EXTENSIONS HOẶC tiền tố nằm trong ALLOWED_TEMP_PREFIXES.
        3. TUYỆT ĐỐI KHÔNG xóa file code nguồn (.py, .js, .jsx, .html, .css, .json, .md, .git).
        """
        if not file_path.is_file():
            return False

        ext = file_path.suffix.lower()
        if ext in {".py", ".pyc", ".js", ".jsx", ".ts", ".tsx", ".html", ".css", ".json", ".md", ".sh", ".env"}:
            return False

        # Kiểm tra phần mở rộng
        if ext in self.allowed_extensions:
            return True

        # Kiểm tra tiền tố tên tệp
        stem = file_path.stem.lower()
        for prefix in self.allowed_prefixes:
            if stem.startswith(prefix):
                return True

        return False

    def scan_stats(self, directories: Optional[List[str]] = None) -> TempStatsReport:
        """
        Quét thống kê số lượng và dung lượng tệp tin tạm hiện có trong các thư mục mục tiêu
        """
        dirs_to_scan = directories or self.target_dirs
        total_files = 0
        total_bytes = 0
        now = time.time()
        oldest_age: Optional[float] = None
        dir_breakdown: Dict[str, Dict[str, Any]] = {}

        for d_str in dirs_to_scan:
            d_path = Path(d_str)
            if not d_path.exists():
                dir_breakdown[d_str] = {"exists": False, "files": 0, "bytes": 0, "size_mb": 0.0}
                continue

            d_files = 0
            d_bytes = 0

            try:
                for root, _, files in os.walk(d_path):
                    for fname in files:
                        fpath = Path(root) / fname
                        if self.is_safe_to_delete(fpath):
                            try:
                                stat = fpath.stat()
                                f_size = stat.st_size
                                f_age = max(0.0, now - stat.st_mtime)

                                d_files += 1
                                d_bytes += f_size
                                total_files += 1
                                total_bytes += f_size

                                if oldest_age is None or f_age > oldest_age:
                                    oldest_age = f_age
                            except (OSError, PermissionError):
                                pass

                dir_breakdown[d_str] = {
                    "exists": True,
                    "files": d_files,
                    "bytes": d_bytes,
                    "size_mb": round(d_bytes / (1024.0 * 1024.0), 3)
                }
            except Exception as e:
                dir_breakdown[d_str] = {"exists": True, "error": str(e), "files": d_files, "bytes": d_bytes}

        return TempStatsReport(
            total_files=total_files,
            total_bytes=total_bytes,
            total_mb=round(total_bytes / (1024.0 * 1024.0), 3),
            directories=dir_breakdown,
            oldest_file_age_seconds=round(oldest_age, 1) if oldest_age is not None else None
        )

    def clean(
        self,
        directories: Optional[List[str]] = None,
        max_age_seconds: int = 3600,
        force_all: bool = False,
        dry_run: bool = False,
        clean_memory: bool = True
    ) -> CleaningReport:
        """
        Dọn dẹp các tệp tin tạm hết hạn hoặc dọn toàn bộ khi force_all=True:
        - `max_age_seconds`: Ngưỡng tuổi tệp tin (giây). Mặc định 3600s = 1 giờ.
        - `force_all`: Nếu True, bỏ qua kiểm tra tuổi tệp tin, dọn sạch tất cả tệp tạm.
        - `dry_run`: Nếu True, chỉ tính toán thống kê mà không thực sự xóa tệp.
        - `clean_memory`: Nếu True, kích hoạt giải phóng Matplotlib & Garbage Collection.
        """
        start_time = time.perf_counter()
        dirs_to_clean = directories or self.target_dirs

        report = CleaningReport()
        report.directories_scanned = list(dirs_to_clean)
        now = time.time()

        # Đo bộ nhớ trước khi dọn
        mem_before = self._get_memory_usage_mb()

        for d_str in dirs_to_clean:
            d_path = Path(d_str)
            if not d_path.exists():
                continue

            try:
                # Quét đệ quy thư mục
                for root, dirs, files in os.walk(d_path, topdown=False):
                    for fname in files:
                        fpath = Path(root) / fname
                        report.scanned_files += 1

                        if not self.is_safe_to_delete(fpath):
                            continue

                        try:
                            stat = fpath.stat()
                            age = now - stat.st_mtime

                            # Kiểm tra thời gian hết hạn hoặc cờ force_all
                            if force_all or age >= max_age_seconds:
                                f_size = stat.st_size
                                if not dry_run:
                                    try:
                                        fpath.unlink(missing_ok=True)
                                    except Exception as del_err:
                                        report.errors.append(f"Không thể xóa {fpath}: {str(del_err)}")
                                        continue

                                report.deleted_files += 1
                                report.bytes_reclaimed += f_size
                        except (FileNotFoundError, OSError) as stat_err:
                            report.errors.append(f"Lỗi truy cập {fpath}: {str(stat_err)}")

                    # Dọn các thư mục con rỗng bên trong thư mục tạm
                    if not dry_run and root != str(d_path):
                        try:
                            sub_dir = Path(root)
                            if sub_dir.exists() and not any(sub_dir.iterdir()):
                                sub_dir.rmdir()
                        except Exception:
                            pass

            except Exception as walk_err:
                report.errors.append(f"Lỗi khi duyệt thư mục {d_str}: {str(walk_err)}")

        # Giải phóng tài nguyên bộ nhớ nếu được yêu cầu
        if clean_memory:
            gc_res = self.clean_memory_and_figures()
            report.gc_objects_collected = gc_res.get("collected_objects", 0)

        mem_after = self._get_memory_usage_mb()
        report.freed_memory_mb = round(max(0.0, mem_before - mem_after), 2)
        report.reclaimed_mb = round(report.bytes_reclaimed / (1024.0 * 1024.0), 3)
        report.execution_time_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        return report

    def clean_memory_and_figures(self) -> Dict[str, Any]:
        """
        Dọn dẹp các đối tượng bộ nhớ rò rỉ:
        - Đóng tất cả Matplotlib Figures (plt.close('all'))
        - Xóa sạch pyplot figure canvas
        - Ép kích hoạt gc.collect()
        """
        figures_closed = 0
        try:
            import matplotlib.pyplot as plt
            fig_nums = plt.get_fignums()
            figures_closed = len(fig_nums)
            plt.close('all')
        except Exception as e:
            logger.debug(f"Matplotlib cleanup notice: {e}")

        # Thu gom rác cấp tiến trình Python
        collected = gc.collect()

        return {
            "figures_closed": figures_closed,
            "collected_objects": collected,
            "current_memory_mb": round(self._get_memory_usage_mb(), 2)
        }

    @staticmethod
    def _get_memory_usage_mb() -> float:
        """Đo dung lượng bộ nhớ Resident Set Size (RSS) hiện tại của tiến trình (MB)"""
        try:
            usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            # Trên macOS, ru_maxrss tính bằng bytes; trên Linux tính bằng kilobytes
            if platform.system() == "Darwin":
                return usage / (1024.0 * 1024.0)
            else:
                return usage / 1024.0
        except Exception:
            return 0.0


# Khởi tạo instance tiện ích mặc định
_default_cleaner = TempFileCleaner()


def clean_expired_temp_files(
    directories: Optional[List[str]] = None,
    max_age_seconds: int = 3600,
    force_all: bool = False,
    dry_run: bool = False
) -> CleaningReport:
    """Hàm tiện ích dọn dẹp các tệp tin tạm hết hạn"""
    return _default_cleaner.clean(
        directories=directories,
        max_age_seconds=max_age_seconds,
        force_all=force_all,
        dry_run=dry_run
    )


def cleanup_memory_and_figures() -> Dict[str, Any]:
    """Hàm tiện ích giải phóng bộ nhớ và đóng tất cả figure Matplotlib"""
    return _default_cleaner.clean_memory_and_figures()


def get_temp_storage_stats(directories: Optional[List[str]] = None) -> TempStatsReport:
    """Hàm tiện ích tra cứu thống kê dung lượng tệp tin tạm"""
    return _default_cleaner.scan_stats(directories=directories)


# ==============================================================================
# CLI EXECUTION (Dành cho việc lập lịch Cronjob hoặc chạy trực tiếp qua Terminal)
# ==============================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script dọn dẹp file tạm trên server (LessonAI-5512 Temp File Cleaner)"
    )
    parser.add_argument(
        "--max-age",
        type=int,
        default=3600,
        help="Tuổi tối đa của tệp tin trước khi bị xóa (giây, mặc định: 3600 = 1 giờ)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Xóa toàn bộ tệp tạm không kể tuổi tệp tin"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Chỉ thống kê các tệp sẽ bị xóa mà không thực hiện xóa thật"
    )
    parser.add_argument(
        "--dir",
        action="append",
        dest="custom_dirs",
        help="Thư mục tùy chỉnh bổ sung cần quét dọn"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Chỉ hiển thị thống kê dung lượng tệp tạm hiện thời"
    )

    args = parser.parse_args()
    cleaner = TempFileCleaner(target_dirs=args.custom_dirs if args.custom_dirs else None)

    if args.stats:
        stats = cleaner.scan_stats()
        print(f"\n[THỐNG KÊ TỆP TIN TẠM]:")
        print(f"- Tổng số tệp tin: {stats.total_files}")
        print(f"- Tổng dung lượng: {stats.total_mb:.3f} MB ({stats.total_bytes} bytes)")
        if stats.oldest_file_age_seconds is not None:
            print(f"- Tệp tin cũ nhất: {stats.oldest_file_age_seconds / 60.0:.1f} phút trước")
        print("- Chi tiết từng thư mục:")
        for d, info in stats.directories.items():
            print(f"  + {d}: {info.get('files', 0)} files, {info.get('size_mb', 0.0)} MB")
        sys.exit(0)

    print(f"\n[TIẾN HÀNH DỌN DẸP]: max_age={args.max_age}s, force={args.force}, dry_run={args.dry_run}")
    report = cleaner.clean(
        max_age_seconds=args.max_age,
        force_all=args.force,
        dry_run=args.dry_run
    )

    print(f"- Đã quét: {report.scanned_files} tệp")
    print(f"- Đã xóa: {report.deleted_files} tệp")
    print(f"- Dung lượng thu hồi: {report.reclaimed_mb} MB ({report.bytes_reclaimed} bytes)")
    print(f"- Đối tượng GC thu gom: {report.gc_objects_collected}")
    print(f"- Thời gian thực thi: {report.execution_time_ms:.2f} ms")
    if report.errors:
        print(f"- Gặp {len(report.errors)} lỗi:")
        for err in report.errors:
            print(f"  ! {err}")
    print("[HOÀN TẤT DỌN DẸP AN TOÀN]\n")
