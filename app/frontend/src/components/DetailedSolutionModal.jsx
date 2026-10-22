import React, { useState, useEffect } from 'react';
import {
  FileText,
  X,
  CheckCircle2,
  Copy,
  Check,
  BookOpen,
  ArrowRight,
  Info,
  Sparkles
} from 'lucide-react';
import MathText from './MathText';
import { getNormalizedSolutionSteps, formatSolutionToClipboard } from '../utils/solutionStepFormatter';

/**
 * DetailedSolutionModal (Task 16.4)
 * Hộp thoại hiển thị từng bước biến đổi tự luận chuẩn mực của bài toán:
 * - Chuẩn hóa từng bước: Giả thiết -> Công thức -> Biến đổi đại số -> Kết luận phương án.
 * - Hỗ trợ công thức Toán học KaTeX chuẩn mực (MathText).
 * - Nút sao chép văn bản lời giải để học sinh/giáo viên lưu vào vở ghi.
 * - Hướng dẫn trình bày chuẩn bài thi tự luận tốt nghiệp THPT theo CV 5512.
 */
export default function DetailedSolutionModal({
  isOpen = false,
  onClose,
  slide = {},
  currentSlide = 0
}) {
  const [copied, setCopied] = useState(false);

  // Lấy danh sách các bước giải chuẩn hóa
  const steps = getNormalizedSolutionSteps(slide);
  const questionText = slide.bullet_points?.[0] || slide.title || "Câu hỏi trắc nghiệm rèn luyện:";

  // Hỗ trợ phím Escape để đóng hộp thoại
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onClose?.();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  // Sao chép toàn bộ lời giải vào bộ nhớ tạm
  const handleCopy = async () => {
    try {
      const text = formatSolutionToClipboard(slide, steps);
      if (navigator?.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      }
    } catch (e) {
      console.warn('[DetailedSolutionModal] Không thể sao chép:', e);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-200">
      <div
        className="w-full max-w-2xl bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[92vh] border-t-cyan-500/80"
        role="dialog"
        aria-modal="true"
        aria-labelledby="solution-modal-title"
      >
        {/* 1. HEADER MODAL */}
        <div className="p-4 sm:p-5 border-b border-slate-800 bg-slate-950/60 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-cyan-500/15 border border-cyan-500/40 flex items-center justify-center text-cyan-400 shrink-0">
              <BookOpen size={20} />
            </div>
            <div>
              <h2 id="solution-modal-title" className="text-base sm:text-lg font-bold text-white flex items-center gap-2">
                <span>Lời Giải Chi Tiết Chuẩn Mực SGK</span>
                <span className="hidden sm:inline-block px-2 py-0.5 rounded-md text-[10px] font-mono uppercase bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
                  Chuẩn SGK 2018
                </span>
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Các bước biến đổi tự luận chuẩn mực để học sinh ghi chép vào vở
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleCopy}
              className="px-2.5 py-1.5 rounded-xl border border-slate-700 bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white text-xs font-semibold flex items-center gap-1.5 transition"
              title="Sao chép toàn bộ lời giải vào bộ nhớ tạm"
            >
              {copied ? (
                <>
                  <Check size={14} className="text-emerald-400" />
                  <span className="text-emerald-300">Đã sao chép</span>
                </>
              ) : (
                <>
                  <Copy size={14} className="text-slate-400" />
                  <span>Sao chép</span>
                </>
              )}
            </button>

            <button
              type="button"
              onClick={onClose}
              className="p-1.5 rounded-xl border border-slate-800 hover:border-slate-700 bg-slate-800/40 hover:bg-slate-800 text-slate-400 hover:text-white transition"
              title="Đóng (phím Esc)"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* 2. KHUNG ĐỀ BÀI NGẮN GỌN */}
        <div className="px-4 sm:px-5 py-3 bg-slate-950/40 border-b border-slate-800/80 text-xs shrink-0">
          <span className="text-cyan-400 font-bold uppercase tracking-wider text-[10px] block mb-1">
            Đề bài trọng tâm:
          </span>
          <div className="text-slate-200 font-medium leading-relaxed">
            <MathText text={questionText} />
          </div>
        </div>

        {/* 3. DANH SÁCH TỪNG BƯỚC BIẾN ĐỔI CHUẨN MỰC */}
        <div className="p-4 sm:p-5 overflow-y-auto space-y-3 flex-1">
          {steps.map((step, idx) => {
            const isFirst = idx === 0;
            const isLast = idx === steps.length - 1;

            let cardTheme = 'bg-slate-950/60 border-slate-800 text-slate-200';
            let stepBadge = 'bg-slate-800 border-slate-700 text-slate-300';

            if (isFirst) {
              cardTheme = 'bg-amber-950/25 border-amber-800/40 text-amber-100';
              stepBadge = 'bg-amber-500/20 border-amber-500/50 text-amber-300';
            } else if (isLast) {
              cardTheme = 'bg-emerald-950/30 border-emerald-500/40 text-emerald-100 shadow-md shadow-emerald-950/40';
              stepBadge = 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300 font-bold';
            }

            return (
              <div
                key={idx}
                className={`p-3.5 rounded-xl border flex items-start gap-3 transition ${cardTheme}`}
              >
                {/* Chỉ số bước */}
                <div className={`w-7 h-7 rounded-lg border font-mono text-xs font-bold flex items-center justify-center shrink-0 mt-0.5 ${stepBadge}`}>
                  {idx + 1}
                </div>

                {/* Nội dung bước giải */}
                <div className="flex-1 text-xs sm:text-sm leading-relaxed font-medium">
                  <MathText text={step} />
                  {isLast && (
                    <div className="mt-2 flex items-center gap-1.5 text-emerald-400 text-xs font-bold">
                      <CheckCircle2 size={13} />
                      <span>Đáp án hoàn chỉnh chuẩn SGK</span>
                    </div>
                  )}
                </div>
              </div>
            );
          })}

          {/* Lời khuyên ghi chép vào vở */}
          <div className="p-3.5 rounded-xl bg-cyan-950/30 border border-cyan-800/40 flex items-start gap-2.5 text-xs text-cyan-200 leading-relaxed mt-2">
            <Info size={16} className="text-cyan-400 shrink-0 mt-0.5" />
            <div>
              <strong className="font-bold text-cyan-300">Lưu ý khi trình bày vào vở ghi:</strong>
              <p className="mt-0.5 text-slate-300">
                Học sinh cần ghi rõ các bước biến đổi tương đương và điều kiện xác định. Không được bỏ qua bước thay số để đảm bảo tính chặt chẽ trong bài thi tự luận.
              </p>
            </div>
          </div>
        </div>

        {/* 4. FOOTER HÀNH ĐỘNG */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/60 flex items-center justify-between gap-2 shrink-0">
          <span className="text-[11px] text-slate-500">
            Dành cho học sinh tự học và giáo viên sửa bài trên lớp
          </span>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleCopy}
              className="px-3.5 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center gap-1.5 border border-slate-700 transition"
            >
              {copied ? <Check size={13} className="text-emerald-400" /> : <Copy size={13} />}
              <span>{copied ? "Đã chép vào bộ nhớ" : "Sao chép lời giải"}</span>
            </button>

            <button
              type="button"
              onClick={onClose}
              className="px-4 py-1.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold transition shadow-md shadow-cyan-950/50"
            >
              Đóng lời giải
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
