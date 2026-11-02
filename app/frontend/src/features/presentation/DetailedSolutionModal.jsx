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
import MathText from '../../shared/math/MathText';
import { getNormalizedSolutionSteps, formatSolutionToClipboard } from './solutionStepFormatter.js';

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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-[#141414]/30 backdrop-blur-sm animate-in fade-in duration-200">
      <div
        className="w-full max-w-2xl bg-[#ffffff] border border-[#e0e0e0] rounded-[24px] shadow-none overflow-hidden flex flex-col max-h-[92vh]"
        role="dialog"
        aria-modal="true"
        aria-labelledby="solution-modal-title"
      >
        {/* 1. HEADER MODAL */}
        <div className="p-5 sm:p-6 border-b border-[#e0e0e0] bg-[#ffffff] flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-[30%] bg-[#f3f3f3] text-[#141414] flex items-center justify-center shrink-0">
              <BookOpen size={20} />
            </div>
            <div>
              <h2 id="solution-modal-title" className="text-base sm:text-lg font-semibold text-[#141414] flex items-center gap-2">
                <span>Lời Giải Chi Tiết Chuẩn Mực SGK</span>
                <span className="hidden sm:inline-block px-2.5 py-0.5 rounded-full text-[10px] font-mono bg-[#f3f3f3] text-[#141414] border border-[#e0e0e0]">
                  SGK 2018
                </span>
              </h2>
              <p className="text-xs text-[#707070] mt-0.5">
                Các bước biến đổi tự luận chuẩn mực để học sinh ghi chép vào vở
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleCopy}
              className="px-3.5 py-1.5 rounded-full border border-[#e0e0e0] bg-[#ffffff] hover:bg-[#f3f3f3] text-[#141414] text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer"
              title="Sao chép toàn bộ lời giải vào bộ nhớ tạm"
            >
              {copied ? (
                <>
                  <Check size={14} className="text-[#10b981]" />
                  <span className="text-[#10b981]">Đã sao chép</span>
                </>
              ) : (
                <>
                  <Copy size={14} className="text-[#707070]" />
                  <span>Sao chép</span>
                </>
              )}
            </button>

            <button
              type="button"
              onClick={onClose}
              className="p-1.5 rounded-full text-[#707070] hover:text-[#141414] hover:bg-[#f3f3f3] transition cursor-pointer"
              title="Đóng (phím Esc)"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* 2. KHUNG ĐỀ BÀI NGẮN GỌN */}
        <div className="px-6 py-3.5 bg-[#f3f3f3] border-b border-[#e0e0e0] text-xs shrink-0">
          <span className="text-[#141414] font-semibold uppercase tracking-wider text-[10px] block mb-1">
            Đề bài trọng tâm:
          </span>
          <div className="text-[#141414] font-medium leading-relaxed">
            <MathText text={questionText} />
          </div>
        </div>

        {/* 3. DANH SÁCH TỪNG BƯỚC BIẾN ĐỔI CHUẨN MỰC */}
        <div className="p-6 overflow-y-auto space-y-3 flex-1">
          {steps.map((step, idx) => {
            const isLast = idx === steps.length - 1;

            return (
              <div
                key={idx}
                className={`p-4 rounded-2xl border flex items-start gap-3 transition ${
                  isLast
                    ? 'bg-[#f3f3f3] border-[#141414] text-[#141414]'
                    : 'bg-[#ffffff] border-[#e0e0e0] text-[#141414]'
                }`}
              >
                {/* Chỉ số bước */}
                <div className="w-7 h-7 rounded-full border border-[#e0e0e0] bg-[#ffffff] font-mono text-xs font-bold text-[#141414] flex items-center justify-center shrink-0 mt-0.5">
                  {idx + 1}
                </div>

                {/* Nội dung bước giải */}
                <div className="flex-1 text-xs sm:text-sm leading-relaxed font-medium">
                  <MathText text={step} />
                  {isLast && (
                    <div className="mt-2 flex items-center gap-1.5 text-[#10b981] text-xs font-bold">
                      <CheckCircle2 size={13} />
                      <span>Đáp án hoàn chỉnh chuẩn SGK</span>
                    </div>
                  )}
                </div>
              </div>
            );
          })}

          {/* Lời khuyên ghi chép vào vở */}
          <div className="p-4 rounded-2xl bg-[#f3f3f3] border border-[#e0e0e0] flex items-start gap-3 text-xs text-[#141414] leading-relaxed mt-2">
            <Info size={16} className="text-[#141414] shrink-0 mt-0.5" />
            <div>
              <strong className="font-semibold text-[#141414]">Lưu ý khi trình bày vào vở ghi:</strong>
              <p className="mt-0.5 text-[#707070]">
                Học sinh cần ghi rõ các bước biến đổi tương đương và điều kiện xác định. Không được bỏ qua bước thay số để đảm bảo tính chặt chẽ trong bài thi tự luận.
              </p>
            </div>
          </div>
        </div>

        {/* 4. FOOTER HÀNH ĐỘNG */}
        <div className="p-5 sm:p-6 border-t border-[#e0e0e0] bg-[#ffffff] flex items-center justify-between gap-2 shrink-0">
          <span className="text-[11px] text-[#707070]">
            Dành cho học sinh tự học và giáo viên sửa bài trên lớp
          </span>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleCopy}
              className="px-4 py-2 rounded-full bg-[#ffffff] hover:bg-[#f3f3f3] text-[#141414] text-xs font-semibold flex items-center gap-1.5 border border-[#e0e0e0] transition cursor-pointer"
            >
              {copied ? <Check size={13} className="text-[#10b981]" /> : <Copy size={13} />}
              <span>{copied ? "Đã chép vào bộ nhớ" : "Sao chép lời giải"}</span>
            </button>

            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-full bg-[#141414] hover:bg-[#262626] text-white text-xs font-semibold transition cursor-pointer shadow-none"
            >
              Đóng lời giải
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
