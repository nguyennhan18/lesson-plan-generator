import io
import math
import sys
from pathlib import Path
import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from openpyxl import Workbook

# 1. Nạp biến môi trường từ file .env trong thư mục backend
BACKEND_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BACKEND_DIR / "src"
ENV_PATH = BACKEND_DIR / ".env"

if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)

# 2. Thêm đường dẫn src vào sys.path để import các module hệ thống
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from services.grade_classifier import (
    StudentEvaluation,
    GradeStatistics,
    ClassProficiencyResult,
    _parse_score_value,
    _compute_percentile,
    _extract_scores_from_rows,
    _evaluate_individual_students,
    extract_scores,
    compute_grade_statistics,
    classify_class_proficiency,
    classify_grade_sheet,
)
from main import app

client = TestClient(app)


# ==============================================================================
# PHẦN 1: UNIT TEST CHO HÀM CHUẨN HÓA VÀ LỌC ĐIỂM SỐ (_parse_score_value)
# ==============================================================================

def test_parse_score_value_valid_numbers():
    """
    Kiểm tra _parse_score_value() với các số thực và số nguyên hợp lệ trong thang [0.0, 10.0].
    """
    assert _parse_score_value(8.5) == 8.5
    assert _parse_score_value(10.0) == 10.0
    assert _parse_score_value(0.0) == 0.0
    assert _parse_score_value(7) == 7.0
    assert _parse_score_value(7.256) == 7.26  # Đảm bảo làm tròn 2 chữ số thập phân


def test_parse_score_value_vietnamese_comma_strings():
    """
    Kiểm tra _parse_score_value() với định dạng chuỗi số dấu phẩy chuẩn Việt Nam ('7,5', '8,25').
    """
    assert _parse_score_value("7,5") == 7.5
    assert _parse_score_value("8,25") == 8.25
    assert _parse_score_value(" 9,0 ") == 9.0
    assert _parse_score_value("10,0") == 10.0
    assert _parse_score_value("0,0") == 0.0
    assert _parse_score_value("6.75") == 6.75


def test_parse_score_value_invalid_and_out_of_range():
    """
    Kiểm tra _parse_score_value() với các giá trị không hợp lệ (ngoài khoảng, chữ, boolean, None).
    """
    # Giá trị ngoài thang điểm [0, 10]
    assert _parse_score_value(-0.5) is None
    assert _parse_score_value(10.5) is None
    assert _parse_score_value("12") is None
    assert _parse_score_value("-1,5") is None

    # Kiểu boolean (Python True/False kế thừa từ int nhưng không phải điểm số)
    assert _parse_score_value(True) is None
    assert _parse_score_value(False) is None

    # Ô trống, ký tự ghi chú, vắng thi
    assert _parse_score_value(None) is None
    assert _parse_score_value("") is None
    assert _parse_score_value("   ") is None
    assert _parse_score_value("Vắng") is None
    assert _parse_score_value("Miễn") is None
    assert _parse_score_value("-") is None

    # Giá trị đặc biệt NaN, Infinity
    assert _parse_score_value(float("nan")) is None
    assert _parse_score_value(float("inf")) is None


# ==============================================================================
# PHẦN 2: UNIT TEST CHO HÀM TÍNH PHÂN VỊ NỘI SUY (_compute_percentile)
# ==============================================================================

def test_compute_percentile():
    """
    Kiểm tra _compute_percentile() tính phân vị tuyến tính:
    Dãy 5 phần tử: [2.0, 4.0, 6.0, 8.0, 10.0]
    - p=0.0 -> 2.0 (Min)
    - p=0.5 -> 6.0 (Median)
    - p=1.0 -> 10.0 (Max)
    - p=0.25 -> index = 0.25 * 4 = 1.0 -> 4.0 (Q1)
    - p=0.75 -> index = 0.75 * 4 = 3.0 -> 8.0 (Q3)
    """
    sample = [2.0, 4.0, 6.0, 8.0, 10.0]
    assert _compute_percentile(sample, 0.0) == 2.0
    assert _compute_percentile(sample, 0.5) == 6.0
    assert _compute_percentile(sample, 1.0) == 10.0
    assert _compute_percentile(sample, 0.25) == 4.0
    assert _compute_percentile(sample, 0.75) == 8.0

    # Danh sách rỗng trả về 0.0 an toàn
    assert _compute_percentile([], 0.5) == 0.0


# ==============================================================================
# PHẦN 3: UNIT TEST CHO HÀM TÍNH TOÁN THỐNG KÊ (compute_grade_statistics)
# ==============================================================================

def test_compute_grade_statistics_exact_math():
    """
    Kiểm tra compute_grade_statistics() với các công thức xác suất thống kê thuần túy:
    Dãy điểm: [4.0, 5.0, 6.0, 7.0, 8.0]
    - N = 5
    - Kỳ vọng mẫu (Mean mu): (4 + 5 + 6 + 7 + 8)/5 = 6.0
    - Phương sai mẫu (Variance sigma^2): [(-2)^2 + (-1)^2 + 0^2 + 1^2 + 2^2] / 5 = 10 / 5 = 2.0
    - Độ lệch chuẩn (Std Dev sigma): sqrt(2.0) = 1.41421... -> round(1.41)
    - Hệ số biến thiên (CV): 1.41421... / 6.0 = 0.2357... -> round(0.2357)
    - P(X < 5.0): điểm 4.0 (1/5) = 0.20
    - P(X >= 8.0): điểm 8.0 (1/5) = 0.20
    """
    scores = [4.0, 5.0, 6.0, 7.0, 8.0]
    stats = compute_grade_statistics(scores)

    assert stats.total_students == 5
    assert stats.mean == 6.0
    assert stats.variance == 2.0
    assert stats.std_dev == 1.41
    assert stats.cv == 0.2357
    assert stats.min_score == 4.0
    assert stats.max_score == 8.0
    assert stats.median == 6.0
    assert stats.rate_below_5 == 0.20
    assert stats.rate_above_8 == 0.20


def test_compute_grade_statistics_empty_list_raises_error():
    """
    Kiểm tra compute_grade_statistics() ném ngoại lệ ValueError khi nhận danh sách điểm rỗng.
    """
    with pytest.raises(ValueError, match="Danh sách điểm trống"):
        compute_grade_statistics([])


# ==============================================================================
# PHẦN 4: UNIT TEST CHO HÀM ĐÁNH GIÁ CÁ NHÂN HÓA HỌC SINH (_evaluate_individual_students)
# ==============================================================================

def test_evaluate_individual_students_z_and_t_scores():
    """
    Kiểm tra _evaluate_individual_students() tính đúng Z-score, T-score (T = 50 + 10*Z)
    và xếp loại học sinh theo ngưỡng quy định.
    """
    scores = [4.0, 7.0, 9.0]
    mean = 7.0
    std_dev = 2.0

    evals = _evaluate_individual_students(scores, mean, std_dev)
    assert len(evals) == 3

    # Học sinh 1: score = 4.0 -> Z = (4 - 7)/2 = -1.5, T = 50 + 10*(-1.5) = 35.0
    s1 = evals[0]
    assert s1.score == 4.0
    assert s1.z_score == -1.5
    assert s1.t_score == 35.0
    assert s1.student_label == "Yếu"

    # Học sinh 2: score = 7.0 -> Z = 0.0, T = 50.0
    s2 = evals[1]
    assert s2.score == 7.0
    assert s2.z_score == 0.0
    assert s2.t_score == 50.0
    assert s2.student_label == "Khá"

    # Học sinh 3: score = 9.0 -> Z = (9 - 7)/2 = 1.0, T = 60.0
    s3 = evals[2]
    assert s3.score == 9.0
    assert s3.z_score == 1.0
    assert s3.t_score == 60.0
    assert s3.student_label == "Giỏi"


def test_evaluate_individual_students_zero_variance():
    """
    Kiểm tra trường hợp đặc biệt: cả lớp cùng đạt một mức điểm (độ lệch chuẩn std_dev = 0).
    Z-score phải bằng 0.0 và T-score phải bằng 50.0 (tránh lỗi ZeroDivisionError).
    """
    scores = [8.0, 8.0, 8.0]
    evals = _evaluate_individual_students(scores, mean=8.0, std_dev=0.0)
    for s in evals:
        assert s.z_score == 0.0
        assert s.t_score == 50.0
        assert s.student_label == "Giỏi"


# ==============================================================================
# PHẦN 5: UNIT TEST CHO QUY TẮC PHÂN LOẠI HỌC LỰC CẢ LỚP (classify_class_proficiency)
# ==============================================================================

def test_classify_class_proficiency_basic():
    """
    Kiểm tra phân loại lớp 'basic': Khi điểm TB < 6.0 hoặc tỉ lệ dưới trung bình >= 30%.
    """
    # Lớp yếu: nhiều điểm dưới trung bình
    scores = [3.0, 4.0, 4.5, 5.0, 5.5, 6.0]
    stats = compute_grade_statistics(scores)
    result = classify_class_proficiency(stats, scores)

    assert result.class_label == "basic"
    assert "Lớp cơ bản" in result.target_outcome
    assert len(result.student_evaluations) == 6


def test_classify_class_proficiency_advanced():
    """
    Kiểm tra phân loại lớp 'advanced': Khi điểm TB >= 7.8, tỉ lệ giỏi >= 50% và tỉ lệ dưới 5 < 5%.
    """
    # Lớp chuyên/chọn: điểm đồng đều từ 8.0 trở lên
    scores = [8.0, 8.5, 9.0, 9.0, 9.5, 8.5, 8.0, 9.5]
    stats = compute_grade_statistics(scores)
    result = classify_class_proficiency(stats, scores)

    assert result.class_label == "advanced"
    assert "Lớp nâng cao" in result.target_outcome


def test_classify_class_proficiency_standard():
    """
    Kiểm tra phân loại lớp 'standard': Điểm trung bình nằm ở mức chuẩn (~6.5 - 7.5).
    """
    scores = [6.0, 6.5, 7.0, 7.0, 7.5, 7.0]
    stats = compute_grade_statistics(scores)
    result = classify_class_proficiency(stats, scores)

    assert result.class_label == "standard"
    assert "Lớp chuẩn" in result.target_outcome


def test_classify_class_proficiency_high_variation_warning():
    """
    Kiểm tra cảnh báo phân hóa học lực cao: Khi CV >= 28% hoặc sigma >= 2.0.
    """
    # Lớp có sự phân hóa cực đoan: gồm các bạn rất yếu (2.0, 3.0) và các bạn rất giỏi (9.0, 10.0)
    scores = [2.0, 3.0, 9.0, 10.0]
    stats = compute_grade_statistics(scores)
    result = classify_class_proficiency(stats, scores)

    assert len(result.warning_notes) > 0
    assert "phân hóa học lực cao" in result.warning_notes[0]
    assert "phân hóa học lực cao" in result.target_outcome


# ==============================================================================
# PHẦN 6: UNIT TEST TRÍCH XUẤT ĐIỂM TỪ CSV VÀ EXCEL (extract_scores)
# ==============================================================================

def test_extract_scores_from_csv_standard():
    """
    Kiểm tra bóc tách điểm từ chuỗi CSV chuẩn quốc tế (dấu phẩy phân cách, số thập phân dấu chấm).
    """
    csv_content = (
        "STT,Họ và tên,Điểm TB\n"
        "1,Nguyễn Văn An,8.5\n"
        "2,Trần Thị Bình,6.0\n"
        "3,Lê Văn Cường,4.5\n"
    ).encode("utf-8")

    scores = extract_scores(csv_content, filename="bang_diem.csv")
    assert scores == [8.5, 6.0, 4.5]


def test_extract_scores_from_csv_vietnamese_semicolon():
    """
    Kiểm tra bóc tách điểm từ CSV xuất khẩu từ Excel tiếng Việt (dấu chấm phẩy phân cách, số thập phân dấu phẩy).
    """
    csv_content = (
        "STT;Họ và tên;ĐTB\n"
        "1;Nguyễn Văn An;8,5\n"
        "2;Trần Thị Bình;6,0\n"
        "3;Lê Văn Cường;4,5\n"
    ).encode("utf-8-sig")

    scores = extract_scores(csv_content, filename="bang_diem_vn.csv")
    assert scores == [8.5, 6.0, 4.5]


def test_extract_scores_from_excel_openpyxl():
    """
    Kiểm tra bóc tách điểm từ file Excel .xlsx được sinh động bằng thư viện openpyxl.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Bảng Điểm Lớp 10A1"

    # Thêm tiêu đề bảng
    ws.append(["Trường THPT Chuyên - Năm học 2023-2024"])
    ws.append(["STT", "Họ và tên", "Năm sinh", "Điểm Tổng Kết"])
    ws.append([1, "Học sinh A", 2008, 9.25])
    ws.append([2, "Học sinh B", 2008, 7.5])
    ws.append([3, "Học sinh C", 2008, 5.0])
    ws.append([4, "Học sinh D", 2008, "Vắng"])  # Kiểm tra ô chữ được bỏ qua an toàn

    excel_stream = io.BytesIO()
    wb.save(excel_stream)
    excel_bytes = excel_stream.getvalue()

    scores = extract_scores(excel_bytes, filename="diem_10A1.xlsx")
    assert scores == [9.25, 7.5, 5.0]


def test_extract_scores_unsupported_extension():
    """
    Kiểm tra ném ngoại lệ ValueError khi tải lên định dạng file không hỗ trợ (.txt, .pdf).
    """
    with pytest.raises(ValueError, match="không được hỗ trợ"):
        extract_scores(b"sample text", filename="grades.pdf")


def test_extract_scores_no_valid_scores_raises():
    """
    Kiểm tra ném ngoại lệ ValueError khi file CSV hợp lệ nhưng không chứa bất kỳ cột điểm nào.
    """
    csv_content = (
        "STT,Họ và tên,Lớp\n"
        "1,Nguyễn Văn An,10A1\n"
        "2,Trần Thị Bình,10A1\n"
    ).encode("utf-8")

    with pytest.raises(ValueError, match="Không tìm thấy cột điểm hợp lệ"):
        extract_scores(csv_content, filename="khong_co_diem.csv")


# ==============================================================================
# PHẦN 7: INTEGRATION TEST TOÀN TRÌNH classify_grade_sheet()
# ==============================================================================

def test_classify_grade_sheet_end_to_end():
    """
    Kiểm tra hàm điều phối toàn trình classify_grade_sheet() và định dạng đầu ra to_dict().
    """
    csv_data = (
        "STT,Họ và tên,Điểm TB\n"
        "1,Em 1,8.5\n"
        "2,Em 2,9.0\n"
        "3,Em 3,8.0\n"
        "4,Em 4,8.5\n"
    ).encode("utf-8")

    result = classify_grade_sheet(csv_data, filename="lop_nang_cao.csv")
    assert isinstance(result, ClassProficiencyResult)
    assert result.total_students == 4
    assert result.class_label == "advanced"

    d = result.to_dict()
    assert d["total_students"] == 4
    assert d["class_label"] == "advanced"
    assert len(d["student_evaluations"]) == 4
    assert "mean" in d and "std_dev" in d and "target_outcome" in d


# ==============================================================================
# PHẦN 8: API ENDPOINT TEST (POST /api/v1/ingest/classify-grades)
# ==============================================================================

def test_api_classify_grades_csv_success():
    """
    Kiểm tra gọi API POST /api/v1/ingest/classify-grades với file CSV hợp lệ.
    """
    csv_bytes = (
        "STT,Họ và tên,Điểm TB\n"
        "1,Nguyễn Văn A,8.5\n"
        "2,Trần Thị B,7.0\n"
        "3,Lê Văn C,6.5\n"
        "4,Phạm Văn D,4.0\n"
    ).encode("utf-8")

    response = client.post(
        "/api/v1/ingest/classify-grades",
        files={"file": ("grades.csv", csv_bytes, "text/csv")}
    )

    assert response.status_code == 200
    json_data = response.json()
    assert json_data["filename"] == "grades.csv"
    assert json_data["total_students"] == 4
    assert json_data["class_label"] in ("basic", "standard", "advanced")
    assert "mean" in json_data
    assert "target_outcome" in json_data
    assert len(json_data["student_evaluations"]) == 4


def test_api_classify_grades_excel_success():
    """
    Kiểm tra gọi API POST /api/v1/ingest/classify-grades với file Excel .xlsx hợp lệ.
    """
    wb = Workbook()
    ws = wb.active
    ws.append(["STT", "Họ và tên", "Điểm TB"])
    ws.append([1, "Học sinh 1", 9.0])
    ws.append([2, "Học sinh 2", 8.5])
    ws.append([3, "Học sinh 3", 8.0])

    excel_buf = io.BytesIO()
    wb.save(excel_buf)
    excel_bytes = excel_buf.getvalue()

    response = client.post(
        "/api/v1/ingest/classify-grades",
        files={"file": ("grades.xlsx", excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    )

    assert response.status_code == 200
    json_data = response.json()
    assert json_data["filename"] == "grades.xlsx"
    assert json_data["total_students"] == 3
    assert json_data["class_label"] == "advanced"


def test_api_classify_grades_unsupported_file_type():
    """
    Kiểm tra API trả về mã lỗi HTTP 400 khi upload định dạng không hỗ trợ (.txt).
    """
    response = client.post(
        "/api/v1/ingest/classify-grades",
        files={"file": ("grades.txt", b"plain text content", "text/plain")}
    )
    assert response.status_code == 400
    assert "không được hỗ trợ" in response.json()["detail"]


def test_api_classify_grades_empty_file():
    """
    Kiểm tra API trả về mã lỗi HTTP 400 khi upload file rỗng (0 bytes).
    """
    response = client.post(
        "/api/v1/ingest/classify-grades",
        files={"file": ("grades.csv", b"", "text/csv")}
    )
    assert response.status_code == 400
    assert "bị rỗng" in response.json()["detail"]


def test_api_classify_grades_no_score_column():
    """
    Kiểm tra API trả về mã lỗi HTTP 400 khi file không chứa cột điểm hợp lệ.
    """
    csv_bytes = "STT,Họ và tên,Lớp\n1,An,10A1\n".encode("utf-8")
    response = client.post(
        "/api/v1/ingest/classify-grades",
        files={"file": ("invalid_grades.csv", csv_bytes, "text/csv")}
    )
    assert response.status_code == 400
    assert "Không tìm thấy cột điểm hợp lệ" in response.json()["detail"]


if __name__ == "__main__":
    pytest.main(["-v", str(Path(__file__))])
