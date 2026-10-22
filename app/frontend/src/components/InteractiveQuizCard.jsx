import React, { useState, useEffect, useRef } from 'react';
import {
  HelpCircle,
  CheckCircle2,
  XCircle,
  Users,
  RotateCcw,
  Sparkles,
  FileText,
  AlertTriangle,
  ChevronRight,
  Volume2,
  VolumeX,
  BookOpen
} from 'lucide-react';
import MathText from './MathText';
import { quizAudio } from '../utils/quizAudioFeedback';
import { launchCanvasConfetti } from '../utils/canvasConfetti';
import MisconceptionModal from './MisconceptionModal';
import DetailedSolutionModal from './DetailedSolutionModal';

/**
 * InteractiveQuizCard (Task 16.1, Task 16.2, Task 16.3 & Task 16.4)
 * Component hiển thị câu hỏi trắc nghiệm tương tác trên slide trình chiếu:
 * - 4 nút bấm phương án A, B, C, D to, rõ ràng, tối ưu cho máy chiếu và màn hình 16:9 Cinema.
 * - Hỗ trợ công thức Toán học chuẩn KaTeX (MathText).
 * - Hiển thị tỉ lệ bình chọn trực tiếp (Live Poll).
 * - Hỗ trợ phím tắt số [1], [2], [3], [4] tương ứng 4 phương án.
 * - Task 16.2: Âm thanh Web Audio API & hiệu ứng pháo hoa Canvas Confetti khi chọn Đúng.
 * - Task 16.3: Đổi màu đỏ + Bật hộp thoại phân tích chi tiết tại sao sai (distractor_rationale).
 * - Task 16.4: Nút "Xem Lời giải Chi tiết": Hiển thị từng bước biến đổi chuẩn mực SGK để ghi vào vở.
 */
export default function InteractiveQuizCard({
  slide = {},
  currentSlide = 0,
  votedOption = null,
  onVote,
  votes = { A: 28, B: 7, C: 4, D: 3 },
  onResetVotes,
  showExplanation = false,
  onToggleExplanation,
  onOpenSolution,
  isPresentationMode = false
}) {
  const confettiCanvasRef = useRef(null);
  const confettiControllerRef = useRef(null);
  const [isMuted, setIsMuted] = useState(false);
  const [isMisconceptionModalOpen, setIsMisconceptionModalOpen] = useState(false);
  const [misconceptionOption, setMisconceptionOption] = useState(null);
  const [isSolutionModalOpen, setIsSolutionModalOpen] = useState(false);

  // Lấy danh sách phương án trắc nghiệm chuẩn từ slide
  const defaultOptions = [
    { label: "A", text: "Phương án A", is_correct: true, distractor_rationale: "Đáp án chuẩn xác theo công thức định lý." },
    { label: "B", text: "Phương án B", is_correct: false, distractor_rationale: "Học sinh dễ nhầm dấu khi biến đổi đại số." },
    { label: "C", text: "Phương án C", is_correct: false, distractor_rationale: "Quên áp dụng điều kiện tồn tại của phương trình." },
    { label: "D", text: "Phương án D", is_correct: false, distractor_rationale: "Nhầm lẫn công thức hằng đẳng thức đáng nhớ." }
  ];

  const quizOptions = Array.isArray(slide.quiz_options) && slide.quiz_options.length > 0
    ? slide.quiz_options
    : defaultOptions;

  // Câu hỏi trắc nghiệm (bullet point đầu tiên hoặc tiêu đề)
  const questionText = slide.bullet_points?.[0] || slide.title || "Chọn khẳng định đúng trong các phương án sau:";

  // Tính tổng số phiếu bình chọn
  const totalVotes = Object.values(votes).reduce((a, b) => a + b, 0);

  // Xử lý dọn dẹp pháo hoa và đóng modal khi slide thay đổi hoặc unmount
  useEffect(() => {
    setIsMisconceptionModalOpen(false);
    setIsSolutionModalOpen(false);
    return () => {
      if (confettiControllerRef.current) {
        confettiControllerRef.current.cancel();
      }
    };
  }, [currentSlide]);

  /**
   * Xử lý khi người dùng chọn phương án (Bấm chuột hoặc gõ phím 1..4)
   * Task 16.2: Kiểm tra đáp án đúng -> Bật âm thanh Web Audio API & bắn pháo hoa Confetti
   * Task 16.3: Nếu chọn đáp án sai -> Nút đổi màu đỏ + Âm trầm + Bật hộp thoại phân tích bẫy sai lầm
   */
  const handleSelectOption = (label) => {
    const chosen = quizOptions.find((opt) => opt.label === label);

    if (chosen?.is_correct) {
      // 1. Âm thanh Web Audio API nốt cao chúc mừng (Ting-Ting)
      quizAudio.playCorrect();

      // 2. Bắn pháo hoa Canvas Confetti 60 FPS
      if (confettiControllerRef.current) {
        confettiControllerRef.current.cancel();
      }
      if (confettiCanvasRef.current) {
        confettiControllerRef.current = launchCanvasConfetti(confettiCanvasRef.current, {
          particleCount: 85,
          originY: window.innerHeight * 0.48
        });
      }
    } else if (chosen && !chosen.is_correct) {
      // Task 16.3: Phát âm trầm phản hồi chưa đúng
      quizAudio.playWrong();

      // Tự động mở hộp thoại phân tích chi tiết bẫy sai lầm
      setMisconceptionOption(chosen);
      setIsMisconceptionModalOpen(true);
    }

    // 3. Kích hoạt callback biểu quyết lên parent component
    if (onVote) {
      onVote(label);
    }
  };

  // Nhận diện phím tắt 1, 2, 3, 4 tương ứng phương án A, B, C, D
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (['INPUT', 'TEXTAREA', 'SELECT', 'MATH-FIELD'].includes(e.target.tagName)) return;

      const keyMap = {
        '1': 'A',
        '2': 'B',
        '3': 'C',
        '4': 'D'
      };

      if (keyMap[e.key]) {
        const targetLabel = keyMap[e.key];
        const exists = quizOptions.some((opt) => opt.label === targetLabel);
        if (exists) {
          e.preventDefault();
          handleSelectOption(targetLabel);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [quizOptions, onVote]);

  const toggleSound = () => {
    const nextMuted = !isMuted;
    setIsMuted(nextMuted);
    quizAudio.setMuted(nextMuted);
  };

  const handleOpenMisconception = () => {
    const currentWrong = quizOptions.find((o) => o.label === votedOption) ||
      quizOptions.find((o) => !o.is_correct) ||
      quizOptions[0];
    setMisconceptionOption(currentWrong);
    setIsMisconceptionModalOpen(true);
    if (onToggleExplanation) {
      onToggleExplanation();
    }
  };

  const handleOpenSolutionModal = () => {
    setIsSolutionModalOpen(true);
    if (onOpenSolution) {
      onOpenSolution();
    }
  };

  // Màu sắc chủ đạo của 4 thẻ A, B, C, D
  const labelStyles = {
    A: 'border-cyan-500/80 bg-cyan-950/60 text-cyan-300',
    B: 'border-indigo-500/80 bg-indigo-950/60 text-indigo-300',
    C: 'border-amber-500/80 bg-amber-950/60 text-amber-300',
    D: 'border-purple-500/80 bg-purple-950/60 text-purple-300'
  };

  return (
    <div className={`h-full flex flex-col justify-between relative ${isPresentationMode ? 'gap-3 md:gap-4' : 'gap-2.5'}`}>
      {/* CANVAS PHÁO HOA CONFETTI CHÚC MỪNG (TASK 16.2) */}
      <canvas
        ref={confettiCanvasRef}
        className="fixed inset-0 pointer-events-none z-50 w-full h-full"
      />

      {/* 1. KHUNG CÂU HỎI TRỌNG TÂM */}
      <div className={`rounded-2xl border border-slate-800 bg-slate-900/85 backdrop-blur-md shadow-xl ${
        isPresentationMode ? 'p-4 md:p-5' : 'p-3.5'
      }`}>
        <div className="flex items-center justify-between pb-2 border-b border-slate-800/80 text-xs">
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-lg bg-amber-500/20 border border-amber-500/60 text-amber-300 font-bold flex items-center gap-1.5 uppercase tracking-wider text-[11px]">
              <HelpCircle size={14} className="text-amber-400" />
              <span>Câu Hỏi Vận Dụng & Live Poll</span>
            </span>
            <span className="hidden sm:inline text-slate-500 text-[11px]">
              (Phím tắt nhanh: [1]=A, [2]=B, [3]=C, [4]=D)
            </span>
          </div>

          <div className="flex items-center gap-3 text-[11px] font-mono text-cyan-400">
            {/* Nút bật/tắt âm thanh phản hồi */}
            <button
              type="button"
              onClick={toggleSound}
              className={`p-1 rounded-lg border transition ${
                isMuted
                  ? 'border-rose-900 bg-rose-950/50 text-rose-400 hover:bg-rose-900/60'
                  : 'border-slate-800 bg-slate-800/60 text-slate-400 hover:text-white'
              }`}
              title={isMuted ? "Đã tắt âm thanh phản hồi" : "Âm thanh Web Audio phản hồi đang bật"}
            >
              {isMuted ? <VolumeX size={13} /> : <Volume2 size={13} />}
            </button>

            <div className="flex items-center gap-1.5">
              <Users size={13} className="text-cyan-400" />
              <span>Đã bình chọn: {totalVotes} HS</span>
            </div>
          </div>
        </div>

        {/* Nội dung đề bài */}
        <div className={`text-white font-medium leading-relaxed mt-2.5 ${
          isPresentationMode ? 'text-base md:text-lg lg:text-xl' : 'text-sm md:text-base'
        }`}>
          <MathText text={questionText} />
        </div>
      </div>

      {/* 2. LƯỚI 4 NÚT BẤM PHƯƠNG ÁN A, B, C, D (TASK 16.1, 16.2 & 16.3) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-3.5 flex-1 min-h-0">
        {quizOptions.map((opt, idx) => {
          const isSelected = votedOption === opt.label;
          const optVotes = votes[opt.label] || 0;
          const pct = Math.round((optVotes / (totalVotes || 1)) * 100);
          const badgeClass = labelStyles[opt.label] || labelStyles.A;

          // Trạng thái giao diện khi được chọn:
          // Task 16.2: Xanh lá cây nổi bật khi ĐÚNG
          // Task 16.3: Đỏ đậm viền nổi khi CHƯA ĐÚNG
          let cardStyle = 'border-slate-800 bg-slate-900/70 hover:bg-slate-800/80 hover:border-slate-700 text-slate-200';
          if (isSelected) {
            if (opt.is_correct) {
              cardStyle = 'border-emerald-400 bg-emerald-950/60 ring-2 ring-emerald-400/80 text-emerald-100 shadow-xl shadow-emerald-950/60';
            } else {
              cardStyle = 'border-rose-500 bg-rose-950/60 ring-2 ring-rose-400/80 text-rose-100 shadow-xl shadow-rose-950/60 animate-shake';
            }
          }

          return (
            <button
              key={opt.label || idx}
              type="button"
              onClick={() => handleSelectOption(opt.label)}
              className={`rounded-2xl border p-3.5 sm:p-4 text-left transition-all duration-200 flex flex-col justify-between relative overflow-hidden group shadow-md hover:scale-[1.008] active:scale-[0.99] ${cardStyle}`}
            >
              {/* Thanh tiến trình tỉ lệ bình chọn */}
              <div
                className={`absolute top-0 left-0 bottom-0 pointer-events-none transition-all duration-700 ${
                  isSelected
                    ? opt.is_correct
                      ? 'bg-emerald-500/20'
                      : 'bg-rose-500/20'
                    : 'bg-cyan-500/10'
                }`}
                style={{ width: `${pct}%` }}
              />

              {/* Dòng tiêu đề phương án: Nhãn + Trạng thái đúng/sai + Phím tắt */}
              <div className="flex items-center justify-between w-full relative z-10 mb-2">
                <div className="flex items-center gap-2.5">
                  <span className={`w-8 h-8 rounded-xl font-bold font-mono text-sm flex items-center justify-center border shadow-sm ${
                    isSelected
                      ? opt.is_correct
                        ? 'border-emerald-400 bg-emerald-500 text-slate-950 font-black shadow-emerald-500/30'
                        : 'border-rose-500 bg-rose-600 text-white font-black shadow-rose-500/30'
                      : badgeClass
                  }`}>
                    {opt.label}
                  </span>
                  <span className="text-[10px] font-mono text-slate-500 px-1.5 py-0.5 rounded bg-slate-950/60 border border-slate-800">
                    Phím [{idx + 1}]
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  {isSelected && (
                    <span className={`px-2.5 py-0.5 rounded-lg text-[11px] font-bold flex items-center gap-1.5 shadow-sm ${
                      opt.is_correct
                        ? 'bg-emerald-500 text-slate-950 border border-emerald-300 animate-pulse'
                        : 'bg-rose-500 text-white border border-rose-300'
                    }`}>
                      {opt.is_correct ? (
                        <>
                          <CheckCircle2 size={13} />
                          <span>CHÍNH XÁC</span>
                          <Sparkles size={11} className="text-slate-900" />
                        </>
                      ) : (
                        <>
                          <XCircle size={13} />
                          <span>CHƯA ĐÚNG</span>
                        </>
                      )}
                    </span>
                  )}

                  <span className="font-mono text-xs font-semibold text-slate-400">
                    {pct}% ({optVotes})
                  </span>
                </div>
              </div>

              {/* Nội dung phương án (Toán học KaTeX) */}
              <div className={`relative z-10 leading-relaxed font-medium pl-1 ${
                isPresentationMode ? 'text-sm md:text-base lg:text-lg' : 'text-xs md:text-sm'
              }`}>
                <MathText text={opt.text} />
              </div>

              {/* Thanh tiến trình phần trăm ở đáy thẻ */}
              <div className="w-full bg-slate-950/90 h-1.5 rounded-full overflow-hidden mt-3 relative z-10 border border-slate-800/80">
                <div
                  className={`h-full transition-all duration-500 ${
                    isSelected
                      ? opt.is_correct
                        ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]'
                        : 'bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.8)]'
                      : 'bg-cyan-500/70'
                  }`}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </button>
          );
        })}
      </div>

      {/* 3. THANH CÔNG CỤ DƯỚI CÂU HỎI (Hỗ trợ giải thích & bài giải chi tiết) */}
      <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-800/80 shrink-0">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleOpenMisconception}
            className={`px-3 py-1.5 rounded-xl border text-xs font-semibold flex items-center gap-1.5 transition ${
              isMisconceptionModalOpen || showExplanation
                ? 'bg-amber-500/30 border-amber-500 text-amber-200 shadow-md'
                : 'bg-slate-900 hover:bg-slate-800 border-slate-800 text-slate-300 hover:text-white'
            }`}
            title="Mở phân tích bẫy sai lầm của từng phương án (Task 16.3)"
          >
            <AlertTriangle size={14} className="text-amber-400" />
            <span>Phân Tích Bẫy Sai Lầm</span>
          </button>

          <button
            type="button"
            onClick={handleOpenSolutionModal}
            className={`px-3 py-1.5 rounded-xl border text-xs font-semibold flex items-center gap-1.5 transition ${
              isSolutionModalOpen
                ? 'bg-cyan-500/30 border-cyan-500 text-cyan-200 shadow-md'
                : 'bg-slate-900 hover:bg-slate-800 border-slate-800 text-slate-300 hover:text-white'
            }`}
            title="Xem các bước giải tự luận chuẩn SGK (Task 16.4)"
          >
            <FileText size={14} className="text-cyan-400" />
            <span>Xem Lời Giải Chi Tiết</span>
          </button>
        </div>

        {onResetVotes && (
          <button
            type="button"
            onClick={() => {
              if (confettiControllerRef.current) {
                confettiControllerRef.current.cancel();
              }
              setIsMisconceptionModalOpen(false);
              setIsSolutionModalOpen(false);
              setMisconceptionOption(null);
              onResetVotes();
            }}
            className="px-2.5 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-white text-xs flex items-center gap-1 transition"
            title="Xóa lựa chọn và bình chọn lại từ đầu"
          >
            <RotateCcw size={13} />
            <span>Bình chọn lại</span>
          </button>
        )}
      </div>

      {/* 4. MODAL PHÂN TÍCH BẪY SAI LẦM SƯ PHẠM (TASK 16.3) */}
      <MisconceptionModal
        isOpen={isMisconceptionModalOpen}
        onClose={() => setIsMisconceptionModalOpen(false)}
        selectedOption={misconceptionOption}
        allOptions={quizOptions}
        questionText={questionText}
        onRetry={() => {
          if (onResetVotes) onResetVotes();
        }}
      />

      {/* 5. MODAL LỜI GIẢI CHI TIẾT TỪNG BƯỚC CHUẨN SGK (TASK 16.4) */}
      <DetailedSolutionModal
        isOpen={isSolutionModalOpen}
        onClose={() => setIsSolutionModalOpen(false)}
        slide={slide}
        currentSlide={currentSlide}
      />
    </div>
  );
}
