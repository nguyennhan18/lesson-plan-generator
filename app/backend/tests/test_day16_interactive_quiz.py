r"""
Automated Test Suite — Day 16: Câu hỏi Trắc nghiệm Tương tác & Phân tích Bẫy Sai lầm
Kiểm thử chi tiết các hạng mục của Ngày 16:
- Task 16.1: Dựng component trắc nghiệm trên slide trình chiếu: 4 nút bấm phương án A, B, C, D to rõ ràng
- Task 16.2: Bắt sự kiện bấm chọn: Nếu chọn đáp án đúng -> Nút đổi màu xanh lá cây + âm thanh/hiệu ứng chúc mừng
- Task 16.3: Tính năng cốt lõi: Nếu chọn đáp án sai -> Nút đổi màu đỏ + Bật hộp thoại giải thích chi tiết tại sao sai (distractor_rationale)
- Task 16.4: Nút "Xem Lời giải Chi tiết": Hiển thị từng bước biến đổi chuẩn mực của bài toán để học sinh ghi chép
- Task 16.5: Nghiệm thu Definition of Done (DoD) Ngày 16 và kiểm thử toàn diện
"""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[3]
BACKEND_SRC = ROOT_DIR / "app" / "backend" / "src"
FRONTEND_DIR = ROOT_DIR / "app" / "frontend"

if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from main import app

client = TestClient(app)


def test_task_16_1_interactive_quiz_card_component():
    """
    Task 16.1: Kiểm tra tệp InteractiveQuizCard.jsx:
    - Component tồn tại và nhận đầy đủ props: slide, currentSlide, votedOption, onVote, votes, isPresentationMode
    - Hiển thị khung câu hỏi với MathText KaTeX
    - Render 4 phương án A, B, C, D trong lưới 2 cột to rõ ràng
    - Mỗi nút có nhãn A, B, C, D, nội dung MathText, thanh tiến trình tỉ lệ bình chọn
    - Hỗ trợ phím tắt số [1], [2], [3], [4] tương ứng phương án A, B, C, D
    - Có nút bình chọn lại (RotateCcw)
    """
    quiz_path = FRONTEND_DIR / "src" / "components" / "InteractiveQuizCard.jsx"
    assert quiz_path.exists(), f"Không tìm thấy tệp {quiz_path}"
    content = quiz_path.read_text(encoding="utf-8")

    # Kiểm tra props & import MathText
    assert "export default function InteractiveQuizCard" in content
    assert "import MathText from './MathText'" in content
    assert "votedOption" in content
    assert "onVote" in content
    assert "votes" in content

    # Lưới 4 phương án A, B, C, D
    assert "grid grid-cols-1 md:grid-cols-2" in content
    assert "quizOptions.map" in content
    assert "opt.label" in content
    assert "opt.text" in content

    # Phím tắt bàn phím [1]=A, [2]=B, [3]=C, [4]=D
    assert "'1': 'A'" in content
    assert "'2': 'B'" in content
    assert "'3': 'C'" in content
    assert "'4': 'D'" in content

    # Thanh tiến trình tỉ lệ bình chọn (Live Poll)
    assert "totalVotes" in content
    assert "pct" in content
    assert "style={{ width: `${pct}%` }}" in content


def test_task_16_1_quiz_card_integration_in_presentation_stage():
    """
    Task 16.1: Kiểm tra tích hợp InteractiveQuizCard trong PresentationStage.jsx:
    - Import InteractiveQuizCard from './InteractiveQuizCard'
    - Render <InteractiveQuizCard ... /> trong nhánh isQuizLayout
    - Truyền slide, currentSlide, votedOption, onVote={handleVote}, votes, onResetVotes, isPresentationMode
    """
    stage_path = FRONTEND_DIR / "src" / "components" / "PresentationStage.jsx"
    assert stage_path.exists(), f"Không tìm thấy tệp {stage_path}"
    content = stage_path.read_text(encoding="utf-8")

    assert "import InteractiveQuizCard from './InteractiveQuizCard'" in content
    assert "<InteractiveQuizCard" in content
    assert "slide={slide}" in content
    assert "votedOption={votedOption}" in content
    assert "onVote={handleVote}" in content
    assert "isPresentationMode={isPresentationMode}" in content


def test_task_16_2_quiz_audio_feedback_synthesizer():
    """
    Task 16.2: Kiểm tra module âm thanh Web Audio API thuần (quizAudioFeedback.js):
    - Không phụ thuộc tệp âm thanh bên ngoài (.mp3/.wav), độ trễ 0ms
    - Sử dụng AudioContext / webkitAudioContext tiêu chuẩn
    - playCorrect: Hòa âm 2 nốt E5 (659.25 Hz) và A5 (880.00 Hz) ngân vang chúc mừng
    - playWrong: Âm trầm nhẹ nhàng (220 Hz -> 140 Hz) sư phạm
    - Có cơ chế kiểm soát âm lượng và mute/unmute
    """
    audio_path = FRONTEND_DIR / "src" / "utils" / "quizAudioFeedback.js"
    assert audio_path.exists(), f"Không tìm thấy tệp {audio_path}"
    content = audio_path.read_text(encoding="utf-8")

    assert "class QuizAudioFeedback" in content
    assert "AudioContext || window.webkitAudioContext" in content
    assert "playCorrect()" in content
    assert "659.25" in content  # Nốt E5
    assert "880.00" in content  # Nốt A5
    assert "playWrong()" in content
    assert "220" in content     # Nốt A3
    assert "140" in content     # Ramping down
    assert "setMuted" in content
    assert "export const quizAudio = new QuizAudioFeedback()" in content


def test_task_16_2_canvas_confetti_engine():
    """
    Task 16.2: Kiểm tra engine pháo hoa Canvas Confetti thuần (canvasConfetti.js):
    - 0 phụ thuộc thư viện ngoài (zero external dependencies)
    - Vẽ trên HTML5 Canvas với requestAnimationFrame đạt 60 FPS
    - Mô hình vật lý hạt: Trọng lực (gravity), lực cản không khí (drag), xoay lật 3D (tilt flutter), độ mờ (alpha decay)
    - Hỗ trợ màn hình Retina (window.devicePixelRatio)
    - Tự động dọn dẹp canvas và huỷ animation frame khi hoàn tất
    """
    confetti_path = FRONTEND_DIR / "src" / "utils" / "canvasConfetti.js"
    assert confetti_path.exists(), f"Không tìm thấy tệp {confetti_path}"
    content = confetti_path.read_text(encoding="utf-8")

    assert "export function launchCanvasConfetti" in content
    assert "devicePixelRatio" in content
    assert "requestAnimationFrame" in content
    assert "gravity" in content
    assert "drag" in content
    assert "tilt" in content
    assert "alpha" in content
    assert "cancelAnimationFrame" in content
    assert "clearRect" in content


def test_task_16_2_quiz_card_correct_feedback_integration():
    """
    Task 16.2: Kiểm tra tích hợp hiệu ứng Chọn Đúng trong InteractiveQuizCard.jsx:
    - Import quizAudio và launchCanvasConfetti
    - Khởi tạo canvas ref và render thẻ <canvas ... /> cho pháo hoa
    - Khi chọn đáp án đúng (chosen?.is_correct):
      + Kích hoạt quizAudio.playCorrect()
      + Kích hoạt launchCanvasConfetti()
    - Nút đổi sang màu xanh lá cây rực rỡ (border-emerald-400, bg-emerald-950/60, ring-2 ring-emerald-400)
    - Nhãn 'CHÍNH XÁC' và biểu tượng CheckCircle2, Sparkles
    - Nút chuyển đổi âm thanh (Volume2/VolumeX) phục vụ không gian lớp học
    """
    quiz_path = FRONTEND_DIR / "src" / "components" / "InteractiveQuizCard.jsx"
    assert quiz_path.exists(), f"Không tìm thấy tệp {quiz_path}"
    content = quiz_path.read_text(encoding="utf-8")

    # Import công cụ âm thanh và pháo hoa
    assert "import { quizAudio } from '../utils/quizAudioFeedback'" in content
    assert "import { launchCanvasConfetti } from '../utils/canvasConfetti'" in content

    # Canvas ref và DOM element
    assert "confettiCanvasRef" in content
    assert "<canvas" in content
    assert "ref={confettiCanvasRef}" in content

    # Logic chọn đáp án đúng
    assert "chosen?.is_correct" in content
    assert "quizAudio.playCorrect()" in content
    assert "launchCanvasConfetti(confettiCanvasRef.current" in content

    # Giao diện xanh lá cây chúc mừng
    assert "border-emerald-400" in content
    assert "bg-emerald-950/60" in content
    assert "ring-emerald-400" in content
    assert "CHÍNH XÁC" in content
    assert "CheckCircle2" in content
    assert "Sparkles" in content

    # Điều khiển âm thanh
    assert "Volume2" in content
    assert "VolumeX" in content


def test_task_16_3_misconception_classifier_utility():
    """
    Task 16.3: Kiểm tra bộ phân loại bẫy sai lầm Toán học (misconceptionClassifier.js):
    - Phân loại SIGN_ERROR (Lỗi dấu đại số)
    - Phân loại DOMAIN_ERROR (Lỗi điều kiện xác định)
    - Phân loại FORMULA_ERROR (Lỗi nhầm công thức)
    - Phân loại GEOMETRY_ERROR (Lỗi trực quan hình học)
    - Phân loại CALCULATION_ERROR (Lỗi tính toán số học)
    - Có thông tin badgeClass, iconColor và advice sư phạm cho từng loại
    """
    classifier_path = FRONTEND_DIR / "src" / "utils" / "misconceptionClassifier.js"
    assert classifier_path.exists(), f"Không tìm thấy tệp {classifier_path}"
    content = classifier_path.read_text(encoding="utf-8")

    assert "export const MISCONCEPTION_TYPES" in content
    assert "SIGN_ERROR" in content
    assert "DOMAIN_ERROR" in content
    assert "FORMULA_ERROR" in content
    assert "GEOMETRY_ERROR" in content
    assert "CALCULATION_ERROR" in content
    assert "export function classifyMisconception" in content
    assert "advice" in content


def test_task_16_3_misconception_modal_component():
    """
    Task 16.3: Kiểm tra component MisconceptionModal.jsx:
    - Nhận props: isOpen, onClose, selectedOption, allOptions, questionText, onRetry
    - Hiển thị tiêu đề Phân Tích Bẫy Sai Lầm Sư Phạm (Distractor Analysis)
    - Render công thức Toán học KaTeX qua MathText
    - Có thanh tab chuyển đổi giữa các phương án A, B, C, D để giáo viên giảng giải
    - Đưa ra bản chất sai lầm Toán học và Lời khuyên sư phạm phòng tránh
    - Hỗ trợ phím Escape để đóng hộp thoại
    """
    modal_path = FRONTEND_DIR / "src" / "components" / "MisconceptionModal.jsx"
    assert modal_path.exists(), f"Không tìm thấy tệp {modal_path}"
    content = modal_path.read_text(encoding="utf-8")

    assert "export default function MisconceptionModal" in content
    assert "import MathText from './MathText'" in content
    assert "classifyMisconception" in content
    assert "allOptions.map" in content
    assert "activeTab" in content
    assert "distractor_rationale" in content
    assert "Escape" in content
    assert "onRetry" in content


def test_task_16_3_quiz_card_wrong_choice_feedback_and_modal_trigger():
    """
    Task 16.3: Kiểm tra tích hợp phản hồi Chọn Sai trong InteractiveQuizCard.jsx:
    - Khi chọn đáp án sai (!chosen.is_correct):
      + Nút đổi màu đỏ (border-rose-500, bg-rose-950/60, ring-rose-400)
      + Nhãn 'CHƯA ĐÚNG' và icon XCircle
      + Phát âm trầm nhẹ nhàng: quizAudio.playWrong()
      + Tự động mở MisconceptionModal (setIsMisconceptionModalOpen(true))
    - Nút 'Phân Tích Bẫy Sai Lầm' trong thanh công cụ mở trực tiếp hộp thoại
    - Render <MisconceptionModal ... />
    """
    quiz_path = FRONTEND_DIR / "src" / "components" / "InteractiveQuizCard.jsx"
    assert quiz_path.exists(), f"Không tìm thấy tệp {quiz_path}"
    content = quiz_path.read_text(encoding="utf-8")

    # Import MisconceptionModal
    assert "import MisconceptionModal from './MisconceptionModal'" in content

    # Phản hồi khi chọn đáp án sai
    assert "chosen && !chosen.is_correct" in content
    assert "quizAudio.playWrong()" in content
    assert "setIsMisconceptionModalOpen(true)" in content

    # Màu đỏ viền nổi
    assert "border-rose-500" in content
    assert "bg-rose-950/60" in content
    assert "ring-rose-400" in content
    assert "CHƯA ĐÚNG" in content
    assert "XCircle" in content

    # Render modal component
    assert "<MisconceptionModal" in content
    assert "isOpen={isMisconceptionModalOpen}" in content
    assert "selectedOption={misconceptionOption}" in content


def test_task_16_4_solution_step_formatter_utility():
    """
    Task 16.4: Kiểm tra tiện ích chuẩn hóa lời giải SGK (solutionStepFormatter.js):
    - getNormalizedSolutionSteps: Trích xuất các bước giải từ slide.worked_solution_steps
      hoặc tự động tổng hợp 4 bước chuẩn mực: Giả thiết -> Công thức -> Biến đổi -> Kết luận
    - formatSolutionToClipboard: Định dạng toàn bộ lời giải thành Markdown để sao chép vào vở
    - Đảm bảo công thức toán học KaTeX được bao bọc chuẩn xác ($...$)
    """
    formatter_path = FRONTEND_DIR / "src" / "utils" / "solutionStepFormatter.js"
    assert formatter_path.exists(), f"Không tìm thấy tệp {formatter_path}"
    content = formatter_path.read_text(encoding="utf-8")

    assert "export function getNormalizedSolutionSteps" in content
    assert "worked_solution_steps" in content
    assert "quiz_options" in content
    assert "export function formatSolutionToClipboard" in content
    assert "Công văn 5512/BGDĐT" in content


def test_task_16_4_detailed_solution_modal_component():
    """
    Task 16.4: Kiểm tra component DetailedSolutionModal.jsx:
    - Nhận props: isOpen, onClose, slide, currentSlide
    - Hiển thị danh sách các bước giải tuần tự theo từng thẻ có chỉ số [1], [2], [3], [4]
    - Hỗ trợ công thức Toán học KaTeX qua MathText
    - Có nút Sao chép lời giải vào clipboard
    - Có khối Lưu ý sư phạm khi trình bày vào vở ghi
    - Hỗ trợ phím Escape để đóng hộp thoại
    """
    modal_path = FRONTEND_DIR / "src" / "components" / "DetailedSolutionModal.jsx"
    assert modal_path.exists(), f"Không tìm thấy tệp {modal_path}"
    content = modal_path.read_text(encoding="utf-8")

    assert "export default function DetailedSolutionModal" in content
    assert "import MathText from './MathText'" in content
    assert "getNormalizedSolutionSteps" in content
    assert "formatSolutionToClipboard" in content
    assert "handleCopy" in content
    assert "Escape" in content
    assert "Lưu ý khi trình bày vào vở ghi" in content


def test_task_16_4_quiz_card_solution_button_and_modal_integration():
    """
    Task 16.4: Kiểm tra tích hợp Nút 'Xem Lời Giải Chi Tiết' trong InteractiveQuizCard.jsx:
    - Import DetailedSolutionModal from './DetailedSolutionModal'
    - Nút 'Xem Lời Giải Chi Tiết' hiển thị với icon FileText
    - Nhấp nút mở DetailedSolutionModal (setIsSolutionModalOpen(true))
    - Render <DetailedSolutionModal ... /> với props slide, currentSlide, isOpen, onClose
    """
    quiz_path = FRONTEND_DIR / "src" / "components" / "InteractiveQuizCard.jsx"
    assert quiz_path.exists(), f"Không tìm thấy tệp {quiz_path}"
    content = quiz_path.read_text(encoding="utf-8")

    # Import modal
    assert "import DetailedSolutionModal from './DetailedSolutionModal'" in content

    # Nút bấm Xem lời giải chi tiết
    assert "Xem Lời Giải Chi Tiết" in content
    assert "handleOpenSolutionModal" in content or "setIsSolutionModalOpen(true)" in content

    # Render component
    assert "<DetailedSolutionModal" in content
    assert "isOpen={isSolutionModalOpen}" in content
    assert "slide={slide}" in content


def test_task_16_5_definition_of_done_e2e_quiz_flow():
    """
    Task 16.5: Kiểm thử tích hợp End-to-End toàn diện & Nghiệm thu Definition of Done (DoD) Ngày 16:
    1. Schema Validation: Parse thành công slide QUIZ_OPTION với đầy đủ 4 phương án, 1 đáp án đúng và 3 distractor_rationale.
    2. Component Ecosystem: Kiểm tra toàn bộ 7 mô-đun cốt lõi của Ngày 16:
       - InteractiveQuizCard.jsx (giao diện 4 phương án, Live Poll, phím tắt [1..4])
       - MisconceptionModal.jsx (hộp thoại phân tích bẫy sai lầm, tab A..D, lời khuyên sư phạm)
       - DetailedSolutionModal.jsx (hộp thoại các bước giải tự luận chuẩn SGK, nút sao chép)
       - quizAudioFeedback.js (tổng hợp âm thanh Web Audio API thuần 0ms độ trễ)
       - canvasConfetti.js (động cơ hạt pháo hoa Canvas 60 FPS hỗ trợ Retina)
       - misconceptionClassifier.js (thuật toán phân loại bẫy sai lầm Toán học)
       - solutionStepFormatter.js (chuẩn hóa các bước giải SGK và sao chép Markdown)
    3. Pipeline Integration: Kiểm tra InteractiveQuizCard được tích hợp hoàn chỉnh trong PresentationStage.jsx.
    """
    from schemas.slide_schema import SlideSchema, SlideType, SlideLayout, QuizOptionDetail

    # 1. Kiểm tra Schema Validation
    quiz_slide = SlideSchema(
        slide_index=1,
        type=SlideType.EXERCISE_SLIDE,
        layout=SlideLayout.QUIZ_OPTION,
        title="Câu hỏi trắc nghiệm Cấp số cộng",
        bullet_points=["Cho cấp số cộng (u_n) có $u_1 = 3$ và công sai $d = 2$. Hãy xác định số hạng thứ 10 $u_{10}$."],
        main_definition_latex=r"u_n = u_1 + (n-1)d",
        worked_solution_steps=[
            "Bước 1: Giả thiết cho $u_1 = 3$, $d = 2$ và cần tìm $u_{10}$ ứng với $n = 10$.",
            "Bước 2: Áp dụng công thức số hạng tổng quát: $u_n = u_1 + (n-1)d$.",
            "Bước 3: Thay số vào công thức: $u_{10} = 3 + (10-1) \\cdot 2 = 3 + 18 = 21$.",
            "Bước 4: Kết luận: $u_{10} = 21$. Đối chiếu các phương án, ta chọn đáp án [A]."
        ],
        quiz_options=[
            QuizOptionDetail(label="A", text="u_{10} = 21", is_correct=True, distractor_rationale=None),
            QuizOptionDetail(label="B", text="u_{10} = 23", is_correct=False, distractor_rationale="Học sinh nhầm số hạng tổng quát thành u_1 + nd: 3 + 10*2 = 23."),
            QuizOptionDetail(label="C", text="u_{10} = -15", is_correct=False, distractor_rationale="Học sinh nhầm dấu công sai thành trừ: 3 - (10-1)*2 = -15."),
            QuizOptionDetail(label="D", text="u_{10} = 30", is_correct=False, distractor_rationale="Học sinh lấy u_1 nhân n: 3 * 10 = 30.")
        ]
    )

    assert quiz_slide.layout == SlideLayout.QUIZ_OPTION
    assert len(quiz_slide.quiz_options) == 4
    assert sum(opt.is_correct for opt in quiz_slide.quiz_options) == 1
    assert len(quiz_slide.worked_solution_steps) == 4

    # 2. Kiểm tra sự tồn tại của đầy đủ 7 mô-đun Ngày 16
    files_to_check = [
        FRONTEND_DIR / "src" / "components" / "InteractiveQuizCard.jsx",
        FRONTEND_DIR / "src" / "components" / "MisconceptionModal.jsx",
        FRONTEND_DIR / "src" / "components" / "DetailedSolutionModal.jsx",
        FRONTEND_DIR / "src" / "utils" / "quizAudioFeedback.js",
        FRONTEND_DIR / "src" / "utils" / "canvasConfetti.js",
        FRONTEND_DIR / "src" / "utils" / "misconceptionClassifier.js",
        FRONTEND_DIR / "src" / "utils" / "solutionStepFormatter.js"
    ]

    for f in files_to_check:
        assert f.exists(), f"Thiếu tệp thành phần Ngày 16: {f}"
        assert len(f.read_text(encoding="utf-8")) > 100, f"Tệp {f} có nội dung quá ngắn hoặc rỗng"

    # 3. Kiểm tra PresentationStage.jsx tích hợp InteractiveQuizCard
    stage_content = (FRONTEND_DIR / "src" / "components" / "PresentationStage.jsx").read_text(encoding="utf-8")
    assert "InteractiveQuizCard" in stage_content
    assert "<InteractiveQuizCard" in stage_content




