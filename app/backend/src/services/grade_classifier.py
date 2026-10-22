import csv
import math
import os
from dataclasses import dataclass, field
from io import StringIO, BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, BinaryIO, TypeAlias

from openpyxl import load_workbook

# Định nghĩa bí danh kiểu dữ liệu đầu vào cho file bảng điểm (PEP 613 TypeAlias)
Source: TypeAlias = Union[str, Path, bytes, BinaryIO, BytesIO]

try:
    from parsers.common import read_source
    from schemas.slide_schema import ClassProficiency
except ImportError:
    from ..parsers.common import read_source
    from ..schemas.slide_schema import ClassProficiency


@dataclass
class StudentEvaluation:
    """
    Đánh giá năng lực và vị trí phân hóa của học sinh cá nhân trong lớp học.

    Attributes:
        score: Điểm tổng kết thực tế của học sinh theo thang điểm chuẩn [0, 10].
        z_score: Độ lệch chuẩn hóa so với trung bình lớp Z = (X - mu) / sigma.
        t_score: Điểm quy đổi McCall T = 50 + 10*Z, đưa về phân phối chuẩn loại bỏ số âm
                 để thuận tiện giải thích sư phạm cho học sinh và phụ huynh.
        student_label: Xếp loại học lực theo quy chế khảo thí ('Giỏi', 'Khá', 'Trung bình', 'Yếu').
        recommendation: Định hướng học tập cá nhân hóa phù hợp với năng lực hiện tại.
    """
    score: float
    z_score: float
    t_score: float
    student_label: str
    recommendation: str


@dataclass
class GradeStatistics:
    """
    Tập hợp các đại lượng thống kê mô tả đặc trưng cho phân phối điểm của lớp học.

    Attributes:
        total_students: Tổng số học sinh tham gia khảo sát (cỡ mẫu N).
        mean: Điểm trung bình cộng (kỳ vọng mẫu mu) đại diện cho mặt bằng học lực chung.
        variance: Phương sai mẫu (sigma^2) đo mức độ biến thiên phân tán bình phương quanh mu.
        std_dev: Độ lệch chuẩn (sigma) phản ánh khoảng chênh lệch điểm thực tế so với mu.
        cv: Hệ số biến thiên (sigma / mu) đo mức độ phân hóa tương đối của lớp,
            cho phép so sánh khách quan giữa các lớp mà không phụ thuộc vào độ khó đề thi.
        min_score: Điểm số thấp nhất trong lớp.
        max_score: Điểm số cao nhất trong lớp.
        median: Điểm trung vị chia đôi danh sách học sinh theo tần suất tích lũy 50%.
        q1: Tứ phân vị thứ nhất, điểm chặn trên của 25% học sinh thấp điểm nhất.
        q3: Tứ phân vị thứ ba, điểm chặn dưới của 25% học sinh cao điểm nhất.
        rate_below_5: Tần suất thực nghiệm học sinh dưới trung bình P(X < 5.0).
        rate_above_8: Tần suất thực nghiệm học sinh khá giỏi P(X >= 8.0).
    """
    total_students: int
    mean: float
    variance: float
    std_dev: float
    cv: float
    min_score: float
    max_score: float
    median: float
    q1: float
    q3: float
    rate_below_5: float
    rate_above_8: float


@dataclass
class ClassProficiencyResult:
    """
    Hồ sơ phân loại học lực tổng thể và chuẩn đầu ra sư phạm được định hình cho lớp học.

    Attributes:
        total_students: Tổng số học sinh trong lớp.
        mean: Điểm trung bình cả lớp.
        std_dev: Độ lệch chuẩn điểm số.
        cv: Hệ số biến thiên của phổ điểm.
        min_score: Điểm số thấp nhất.
        max_score: Điểm số cao nhất.
        q1: Điểm tứ phân vị thứ nhất (25%).
        median: Điểm trung vị của lớp (50%).
        q3: Điểm tứ phân vị thứ ba (75%).
        rate_below_5: Tỷ lệ học sinh dưới trung bình.
        rate_above_8: Tỷ lệ học sinh đạt điểm giỏi.
        class_label: Nhãn học lực cả lớp ('basic' | 'standard' | 'advanced').
        target_outcome: Mục tiêu sư phạm chuẩn đầu ra cung cấp cho AI sinh bài giảng.
        warning_notes: Cảnh báo sư phạm khi lớp có độ phân hóa bất thường (CV >= 28%).
        student_evaluations: Đánh giá Z-score và T-score chi tiết cho từng học sinh.
    """
    total_students: int
    mean: float
    std_dev: float
    cv: float
    min_score: float
    max_score: float
    q1: float
    median: float
    q3: float
    rate_below_5: float
    rate_above_8: float
    class_label: str
    target_outcome: str
    warning_notes: List[str] = field(default_factory=list)
    student_evaluations: List[StudentEvaluation] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Chuyển đổi đối tượng kết quả thành Dictionary phục vụ trả lời API JSON."""
        return {
            "total_students": self.total_students,
            "mean": self.mean,
            "std_dev": self.std_dev,
            "cv": self.cv,
            "min_score": self.min_score,
            "max_score": self.max_score,
            "q1": self.q1,
            "median": self.median,
            "q3": self.q3,
            "rate_below_5": self.rate_below_5,
            "rate_above_8": self.rate_above_8,
            "class_label": self.class_label,
            "target_outcome": self.target_outcome,
            "warning_notes": self.warning_notes,
            "student_evaluations": [
                {
                    "score": s.score,
                    "z_score": s.z_score,
                    "t_score": s.t_score,
                    "student_label": s.student_label,
                    "recommendation": s.recommendation,
                }
                for s in self.student_evaluations
            ],
        }


def _parse_score_value(val: Any) -> Optional[float]:
    """
    Chuyển đổi giá trị ô bảng điểm về số thực hợp lệ trong thang điểm chuẩn [0.0, 10.0].

    Lý do thiết kế (Why):
    - isinstance(val, bool) phải được loại bỏ đầu tiên vì trong Python kiểu bool kế thừa
      từ int (True == 1), nếu ép kiểu thẳng sẽ ngộ nhận giá trị boolean thành điểm 1.0.
    - Chuỗi ký tự cần thay thế dấu phẩy ',' thành dấu chấm '.' để tương thích với quy ước
      số thập phân trong các file Excel xuất từ máy tính cài đặt vùng Việt Nam (ví dụ: '7,5').
    - Lọc bỏ NaN, Infinity và các điểm ngoài khoảng [0, 10] để bảo toàn tính toàn vẹn
      cho các phép tính thống kê tiếp theo.
    """
    if val is None or isinstance(val, bool):
        return None

    if isinstance(val, (int, float)):
        num = float(val)
    elif isinstance(val, str):
        cleaned = val.strip().replace(",", ".")
        if not cleaned:
            return None
        try:
            num = float(cleaned)
        except ValueError:
            return None
    else:
        return None

    if math.isnan(num) or math.isinf(num):
        return None

    if 0.0 <= num <= 10.0:
        return round(num, 2)

    return None


def _extract_scores_from_rows(rows: List[List[Any]]) -> List[float]:
    """
    Tự động dò tìm đúng cột điểm tổng kết trong bảng 2 chiều không cố định cấu trúc.

    Lý do thiết kế (Why):
    - Giai đoạn 1 (Ưu tiên Header): Quét 15 hàng đầu tiên tìm từ khóa tổng kết ('TBM', 'ĐTB'...)
      đồng thời chủ động loại trừ các cột hành chính ('STT', 'Mã số', 'Năm sinh') để không
      bắt nhầm cột số thứ tự 1, 2, 3... làm điểm số.
    - Giai đoạn 2 (Fallback): Khi file không có dòng tiêu đề, thuật toán chọn cột có mật độ điểm
      hợp lệ cao nhất nhưng kiểm tra và loại trừ cột có dãy số nguyên tăng liên tiếp (1, 2, 3, 4, 5).
    """
    if not rows:
        return []

    priority_keywords = (
        "tbm",
        "dtb",
        "đtb",
        "trung bình",
        "tổng kết",
        "cuối kỳ",
        "ck",
        "thi",
        "điểm",
        "score",
        "grade",
    )
    excluded_keywords = (
        "stt",
        "số tt",
        "số thứ tự",
        "mã",
        "id",
        "họ",
        "tên",
        "lớp",
        "năm",
        "ngày",
        "sinh",
        "phái",
    )

    target_col_idx: Optional[int] = None
    data_start_row = 0

    for row_idx, row in enumerate(rows[:15]):
        str_cells = [str(c).strip().lower() if c is not None else "" for c in row]

        matched_cols: List[Tuple[int, str]] = []
        for col_idx, cell_text in enumerate(str_cells):
            if not cell_text:
                continue
            if any(ex in cell_text for ex in excluded_keywords):
                continue
            for kw in priority_keywords:
                if kw in cell_text:
                    matched_cols.append((col_idx, kw))
                    break

        if matched_cols:
            tbm_cols = [
                c[0]
                for c in matched_cols
                if c[1] in ("tbm", "dtb", "đtb", "trung bình", "tổng kết")
            ]
            target_col_idx = tbm_cols[-1] if tbm_cols else matched_cols[-1][0]
            data_start_row = row_idx + 1
            break

    if target_col_idx is None:
        max_cols = max(len(r) for r in rows)
        candidates: List[Tuple[int, int]] = []

        for col_idx in range(max_cols):
            col_scores = []
            for row in rows:
                if col_idx < len(row):
                    parsed = _parse_score_value(row[col_idx])
                    if parsed is not None:
                        col_scores.append(parsed)

            if len(col_scores) >= 3:
                is_stt = col_scores[:5] == [1.0, 2.0, 3.0, 4.0, 5.0][: len(col_scores[:5])]
                if not is_stt:
                    candidates.append((len(col_scores), col_idx))

        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            target_col_idx = candidates[0][1]
            data_start_row = 0

    if target_col_idx is None:
        return []

    scores: List[float] = []
    for row in rows[data_start_row:]:
        if target_col_idx < len(row):
            score = _parse_score_value(row[target_col_idx])
            if score is not None:
                scores.append(score)

    return scores


def extract_scores(source: Source, filename: str = "") -> List[float]:
    """
    Trích xuất danh sách điểm số từ file Excel (.xlsx) hoặc CSV (.csv).

    Lý do thiết kế (Why):
    - Với file Excel: Bắt buộc dùng `data_only=True` để openpyxl đọc kết quả số học đã được tính
      sẵn trong cache XML thay vì lấy chuỗi công thức thô (ví dụ: '=AVERAGE(D4:F4)');
      dùng `read_only=True` để tối ưu bộ nhớ RAM khi mở file lớn.
    - Với file CSV: Ưu tiên decode bảng mã 'utf-8-sig' vì Excel trên Windows thường xuất CSV
      kèm ký tự BOM đầu file; tự động nhận diện dấu phân cách ';' hay ',' dựa trên số lượng
      xuất hiện ở dòng đầu tiên để thích ứng với quy ước vùng của hệ điều hành.
    """
    fname = str(filename or "")
    if not fname and isinstance(source, (str, Path)):
        fname = Path(source).name

    ext = Path(fname).suffix.lower() if fname else ".xlsx"
    stream = read_source(source)
    rows: List[List[Any]] = []

    if ext in (".xlsx", ".xlsm"):
        wb = load_workbook(filename=stream, data_only=True, read_only=True)
        ws = wb.active
        for row in ws.iter_rows(values_only=True):
            rows.append(list(row))
        wb.close()

    elif ext == ".csv":
        raw_bytes = stream.getvalue()
        try:
            csv_text = raw_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            try:
                csv_text = raw_bytes.decode("utf-8")
            except UnicodeDecodeError:
                csv_text = raw_bytes.decode("latin-1")

        first_line = csv_text.split("\n")[0] if csv_text else ""
        delimiter = ";" if first_line.count(";") > first_line.count(",") else ","

        reader = csv.reader(StringIO(csv_text), delimiter=delimiter)
        for row in reader:
            rows.append(row)

    else:
        raise ValueError(
            f"Định dạng file '{ext}' không được hỗ trợ. Chỉ chấp nhận .xlsx hoặc .csv."
        )

    scores = _extract_scores_from_rows(rows)
    if not scores:
        raise ValueError(
            f"Không tìm thấy cột điểm hợp lệ trong file '{fname or 'bảng điểm'}'. "
            "Vui lòng đảm bảo bảng điểm có cột điểm trong thang điểm [0, 10]."
        )

    return scores


def _compute_percentile(sorted_list: List[float], p: float) -> float:
    """
    Tính phân vị mẫu p bằng phương pháp nội suy tuyến tính (Linear Interpolation).

    Lý do thiết kế (Why):
    - Khi cỡ mẫu N nhỏ, việc lấy tròn chỉ số nguyên thô (Nearest Rank) sẽ tạo ra bước nhảy
      gián đoạn không phản ánh đúng phổ điểm liên tục.
    - Phương pháp nội suy tuyến tính tính tọa độ thực idx = p * (N - 1) và bù trừ trọng số
      thập phân giữa 2 mốc lân cận (floor và ceil) đảm bảo phân vị biến thiên mượt mà.
    """
    if not sorted_list:
        return 0.0
    n = len(sorted_list)
    idx = p * (n - 1)
    low = int(math.floor(idx))
    high = int(math.ceil(idx))
    weight = idx - low
    return round(sorted_list[low] * (1.0 - weight) + sorted_list[high] * weight, 2)


def compute_grade_statistics(scores: List[float]) -> GradeStatistics:
    """
    Tính toán các chỉ số xác suất thống kê mô tả đặc trưng cho phổ điểm lớp học.

    Lý do nghiệp vụ (Why):
    - Điểm trung bình (mu = sum(x) / N) và Độ lệch chuẩn (sigma = sqrt(E[(x-mu)^2]))
      xác định tâm phân phối và mức độ phân tán quanh tâm.
    - Hệ số biến thiên (CV = sigma / mu) chuẩn hóa độ phân tán theo kỳ vọng,
      giúp phát hiện chính xác các lớp phân hóa cực đoan mà không bị phụ thuộc vào độ khó đề thi.
    - Phân vị Q1, Q3 đo đạc biên dưới của nhóm 25% yếu nhất và biên trên của 25% giỏi nhất.
    - Trung vị (median) được tính theo phương pháp chỉ số điểm giữa chia trường hợp chẵn/lẻ
      theo chuẩn mực giảng dạy SGK Toán THPT để giáo viên dễ đối chiếu kiểm tra thủ công.
    - Tần suất thực nghiệm P(X < 5) và P(X >= 8) cung cấp trực quan tỷ lệ cần phụ đạo và bồi dưỡng.
    """
    n = len(scores)
    if n == 0:
        raise ValueError("Danh sách điểm trống, không thể tính toán thống kê.")

    # 1. Điểm trung bình cộng (Kỳ vọng mẫu)
    mean_val = sum(scores) / n

    # 2. Phương sai và Độ lệch chuẩn
    variance_val = sum((x - mean_val) ** 2 for x in scores) / n
    std_dev_val = math.sqrt(variance_val)

    # 3. Hệ số biến thiên (CV đo độ phân hóa tương đối)
    cv_val = (std_dev_val / mean_val) if mean_val > 0 else 0.0

    # 4. Phân vị tứ phân theo nội suy liên tục
    sorted_scores = sorted(scores)
    q1_val = _compute_percentile(sorted_scores, 0.25)
    q3_val = _compute_percentile(sorted_scores, 0.75)

    # 5. Tần suất xác suất thực nghiệm
    count_below_5 = sum(1 for x in scores if x < 5.0)
    count_above_8 = sum(1 for x in scores if x >= 8.0)
    rate_below_5 = count_below_5 / n
    rate_above_8 = count_above_8 / n

    # 6. Điểm cực trị & trung vị (Quy tắc chia chẵn lẻ truyền thống SGK Toán)
    scores_sort = sorted(scores)
    min_score = scores_sort[0]
    max_score = scores_sort[-1]
    mid_point = n // 2
    if n % 2 == 1:
        median_val = scores_sort[mid_point]
    else:
        median_val = (scores_sort[mid_point - 1] + scores_sort[mid_point]) / 2

    return GradeStatistics(
        total_students=n,
        mean=round(mean_val, 2),
        variance=round(variance_val, 4),
        std_dev=round(std_dev_val, 2),
        cv=round(cv_val, 4),
        min_score=min_score,
        max_score=max_score,
        median=median_val,
        q1=q1_val,
        q3=q3_val,
        rate_below_5=round(rate_below_5, 4),
        rate_above_8=round(rate_above_8, 4),
    )


def _evaluate_individual_students(
    scores: List[float], mean: float, std_dev: float
) -> List[StudentEvaluation]:
    """
    Chuẩn hóa điểm số Z-score và chuyển đổi sang thang điểm khảo thí McCall T-score.

    Lý do thiết kế (Why):
    - Z-Score Z = (X - mu) / sigma cho biết vị trí tương đối của học sinh theo đơn vị độ lệch chuẩn.
      Tuy nhiên, Z-score có giá trị âm và chữ số thập phân nhỏ, khó giao tiếp sư phạm với học sinh.
    - Điểm McCall's T-Score T = 50 + 10*Z đưa về phân phối chuẩn hóa có trung bình 50 và độ lệch chuẩn 10,
      loại bỏ hoàn toàn số âm giúp định vị năng lực một cách tích cực, mang tính khích lệ học tập.
    - Khi cả lớp có cùng một mức điểm (sigma == 0), Z được gán an toàn bằng 0.0 và T bằng 50.0
      để triệt tiêu lỗi chia cho 0 (ZeroDivisionError).
    """
    evaluations: List[StudentEvaluation] = []
    for score in scores:
        z = (score - mean) / std_dev if std_dev > 0 else 0.0
        t = 50.0 + 10.0 * z

        if score >= 8.0:
            label = "Giỏi"
            rec = "Khuyến khích rèn luyện thêm các bài toán vận dụng cao."
        elif score >= 6.5:
            label = "Khá"
            rec = "Nắm chắc kiến thức, củng cố thêm bài tập vận dụng."
        elif score >= 5.0:
            label = "Trung bình"
            rec = "Cần rèn luyện bài tập cơ bản để tránh mất điểm đáng tiếc."
        else:
            label = "Yếu"
            rec = "Cần phụ đạo kiến thức nền tảng và kèm cặp thêm."

        evaluations.append(
            StudentEvaluation(
                score=score,
                z_score=round(z, 2),
                t_score=round(t, 2),
                student_label=label,
                recommendation=rec,
            )
        )
    return evaluations


def classify_class_proficiency(
    stats: GradeStatistics, scores: Optional[List[float]] = None
) -> ClassProficiencyResult:
    """
    Phân loại học lực cả lớp và định hình mục tiêu chuẩn đầu ra (target_outcome) cho AI.

    Lý do thiết kế các ngưỡng quy tắc nghiệp vụ (Why):
    - Cảnh báo phân hóa (CV >= 28% hoặc sigma >= 2.0): Độ phân tán 28% là mốc ranh giới
      trong trắc lượng giáo dục cho thấy phổ điểm có độ lệch cực lớn (xuất hiện cả học sinh
      rất yếu lẫn rất giỏi), cần kích hoạt phương pháp dạy phân tầng theo nhóm.
    - Lớp cơ bản ('basic'): Khi điểm TB < 6.0 hoặc tỷ lệ dưới trung bình >= 30%
      -> Hướng dẫn AI tập trung củng cố kiến thức gốc, công thức nền tảng, giải chi tiết từng bước.
    - Lớp nâng cao ('advanced'): Khi điểm TB >= 7.8, tỷ lệ giỏi >= 50% và tỷ lệ dưới 5 < 5%
      -> Hướng dẫn AI đi nhanh lý thuyết, tập trung vào bản chất toán học mở rộng và bài toán chứa tham số.
    - Lớp chuẩn ('standard'): Phổ điểm phân bố cân bằng theo chuẩn kiến thức kỹ năng SGK GDPT 2018.
    """
    warnings: List[str] = []

    if stats.std_dev >= 2.0 or stats.cv >= 0.28:
        warnings.append(
            f"Lớp có độ phân hóa học lực cao (Độ lệch chuẩn sigma = {stats.std_dev:.2f}, "
            f"Hệ số biến thiên CV = {stats.cv*100:.1f}%). Cần thiết kế bài tập phân tầng từ dễ đến khó."
        )

    if stats.mean < 6.0 or stats.rate_below_5 >= 0.30:
        class_label = "basic"
        target_outcome = (
            f"Lớp cơ bản (Điểm TB: {stats.mean:.1f}, tỉ lệ dưới trung bình: {stats.rate_below_5*100:.1f}%). "
            "Tập trung củng cố kiến thức nền tảng, công thức gốc, hướng dẫn giải chi tiết từng bước, "
            "tránh bài toán biến đổi phức tạp."
        )
    elif stats.mean >= 7.8 and stats.rate_above_8 >= 0.50 and stats.rate_below_5 < 0.05:
        class_label = "advanced"
        target_outcome = (
            f"Lớp nâng cao (Điểm TB: {stats.mean:.1f}, tỉ lệ giỏi: {stats.rate_above_8*100:.1f}%). "
            "Lướt nhanh lý thuyết cơ bản, tập trung vào bản chất toán học mở rộng, bài toán chứa tham số, "
            "điều kiện biên và câu hỏi vận dụng cao."
        )
    else:
        class_label = "standard"
        target_outcome = (
            f"Lớp chuẩn (Điểm TB: {stats.mean:.1f}, mặt bằng chung ổn định). "
            "Bám sát chuẩn kiến thức kỹ năng SGK GDPT 2018, cân bằng đều giữa lý thuyết "
            "và bài tập thông hiểu - vận dụng."
        )

    if warnings:
        target_outcome += f" [{warnings[0]}]"

    student_evals: List[StudentEvaluation] = []
    if scores:
        student_evals = _evaluate_individual_students(scores, stats.mean, stats.std_dev)

    return ClassProficiencyResult(
        total_students=stats.total_students,
        mean=stats.mean,
        std_dev=stats.std_dev,
        cv=stats.cv,
        min_score=stats.min_score,
        max_score=stats.max_score,
        q1=stats.q1,
        median=stats.median,
        q3=stats.q3,
        rate_below_5=stats.rate_below_5,
        rate_above_8=stats.rate_above_8,
        class_label=class_label,
        target_outcome=target_outcome,
        warning_notes=warnings,
        student_evaluations=student_evals,
    )


def classify_grade_sheet(source: Source, filename: str = "") -> ClassProficiencyResult:
    """
    Hàm nhạc trưởng điều phối toàn bộ quá trình:
    1. Đọc file Excel/CSV bóc tách điểm.
    2. Tính toán thống kê giải tích.
    3. Phân loại trình độ lớp và định hình mục tiêu sư phạm chuẩn đầu ra.
    """
    scores = extract_scores(source, filename)
    stats = compute_grade_statistics(scores)
    return classify_class_proficiency(stats, scores)
