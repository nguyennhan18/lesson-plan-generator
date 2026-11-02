import React, { useState, useEffect } from 'react';
import {
  AlertTriangle,
  X,
  CheckCircle2,
  XCircle,
  Lightbulb,
  Sparkles,
  RotateCcw,
  BookOpen,
  ArrowRight
} from 'lucide-react';
import MathText from '../../shared/math/MathText';
import { classifyMisconception } from './misconceptionClassifier.js';

/**
 * MisconceptionModal (Task 16.3)
 * Hộp thoại phân tích bẫy sai lầm sư phạm chi tiết:
 * - Tự động kích hoạt khi học sinh bấm chọn đáp án SAI.
 * - Hiển thị bản chất sai lầm Toán học từ distractor_rationale (nhầm dấu, quên điều kiện, nhầm công thức).
 * - Phân loại danh mục sai lầm (Classification Taxonomy) kèm huy hiệu màu sắc.
 * - Đưa ra lời khuyên sư phạm (Pedagogical Advice) giúp học sinh phòng tránh.
 * - Cho phép giáo viên chuyển đổi qua lại giữa 4 phương án A, B, C, D để giảng giải cho cả lớp.
 */
export default function MisconceptionModal({
  isOpen = false,
  onClose,
  selectedOption = null,
  allOptions = [],
  questionText = '',
  onRetry
}) {
  // Phương án đang được chọn để xem giải thích trong modal (mặc định là phương án học sinh vừa bấm)
  const [activeTab, setActiveTab] = useState(selectedOption?.label || 'B');

  // Cập nhật tab active khi selectedOption thay đổi
  useEffect(() => {
    if (selectedOption?.label) {
      setActiveTab(selectedOption.label);
    } else if (allOptions.length > 0) {
      // Tìm phương án sai đầu tiên nếu không có option nào được truyền
      const firstWrong = allOptions.find((o) => !o.is_correct) || allOptions[0];
      setActiveTab(firstWrong.label);
    }
  }, [selectedOption, allOptions]);

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

  if (!isOpen) return null;

  // Lấy dữ liệu phương án đang hiển thị trong tab
  const currentOption = allOptions.find((o) => o.label === activeTab) || selectedOption || {};
  const isCorrect = Boolean(currentOption.is_correct);
  const rationale = currentOption.distractor_rationale || 'Không có ghi chú thêm.';
  const classification = classifyMisconception(rationale, currentOption.text || '');

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-[#141414]/30 backdrop-blur-sm animate-in fade-in duration-200">
      <div
        className="w-full max-w-2xl bg-[#ffffff] border border-[#e0e0e0] rounded-[24px] shadow-none overflow-hidden flex flex-col max-h-[92vh]"
        role="dialog"
        aria-modal="true"
        aria-labelledby="misconception-title"
      >
        {/* 1. HEADER MODAL */}
        <div className="p-5 sm:p-6 border-b border-[#e0e0e0] bg-[#ffffff] flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-[30%] bg-[#f3f3f3] text-[#141414] flex items-center justify-center shrink-0">
              <AlertTriangle size={20} />
            </div>
            <div>
              <h2 id="misconception-title" className="text-base sm:text-lg font-semibold text-[#141414] flex items-center gap-2">
                <span>Phân Tích Bẫy Sai Lầm Sư Phạm</span>
                <span className="hidden sm:inline-block px-2.5 py-0.5 rounded-full text-[10px] font-mono bg-[#f3f3f3] text-[#141414] border border-[#e0e0e0]">
                  Distractor Analysis
                </span>
              </h2>
              <p className="text-xs text-[#707070] mt-0.5">
                Chỉ rõ lỗ hổng biến đổi Toán học và phương pháp khắc phục chuẩn mực
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-full text-[#707070] hover:text-[#141414] hover:bg-[#f3f3f3] transition cursor-pointer"
            title="Đóng (phím Esc)"
          >
            <X size={18} />
          </button>
        </div>

        {/* 2. THANH CHỌN TỪNG PHƯƠNG ÁN (A, B, C, D) ĐỂ GIẢNG DẠY */}
        <div className="px-6 py-3 bg-[#f3f3f3] border-b border-[#e0e0e0] flex items-center justify-between gap-2 overflow-x-auto shrink-0">
          <span className="text-[11px] font-medium text-[#707070] shrink-0">
            Xem từng phương án:
          </span>
          <div className="flex items-center gap-1.5 sm:gap-2">
            {allOptions.map((opt) => {
              const isTabActive = opt.label === activeTab;
              return (
                <button
                  key={opt.label}
                  type="button"
                  onClick={() => setActiveTab(opt.label)}
                  className={`px-3.5 py-1.5 rounded-full text-xs font-semibold transition flex items-center gap-1.5 border cursor-pointer ${
                    isTabActive
                      ? 'bg-[#141414] text-white border-[#141414]'
                      : 'bg-[#ffffff] border-[#e0e0e0] text-[#141414] hover:bg-[#e0e0e0]'
                  }`}
                >
                  <span className="font-mono">{opt.label}</span>
                  {opt.is_correct ? (
                    <CheckCircle2 size={13} className={isTabActive ? 'text-white' : 'text-[#10b981]'} />
                  ) : (
                    <XCircle size={13} className={isTabActive ? 'text-white' : 'text-[#ef4444]'} />
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* 3. NỘI DUNG CHI TIẾT CỦA PHƯƠNG ÁN ĐƯỢC CHỌN */}
        <div className="p-6 overflow-y-auto space-y-4 flex-1">
          {/* Card hiển thị phương án */}
          <div className="p-4 rounded-2xl border border-[#e0e0e0] bg-[#ffffff]">
            <div className="flex items-center justify-between mb-1.5">
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold font-mono flex items-center gap-1.5 bg-[#f3f3f3] border border-[#e0e0e0] text-[#141414]">
                {isCorrect ? <CheckCircle2 size={12} className="text-[#10b981]" /> : <XCircle size={12} className="text-[#ef4444]" />}
                <span>Phương án [{currentOption.label}] {isCorrect ? '— ĐÁP ÁN ĐÚNG' : '— ĐÁP ÁN SAI (BẪY)'}</span>
              </span>

              {!isCorrect && (
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold border border-[#e0e0e0] bg-[#f3f3f3] text-[#141414]">
                  {classification.title}
                </span>
              )}
            </div>

            <div className="text-[#141414] text-sm sm:text-base font-medium mt-2 leading-relaxed">
              <MathText text={currentOption.text || ''} />
            </div>
          </div>

          {/* Phân tích bản chất sai lầm hoặc lý giải đáp án đúng */}
          {isCorrect ? (
            <div className="p-4 rounded-2xl bg-[#f3f3f3] border border-[#e0e0e0] space-y-2">
              <h3 className="text-[#141414] font-semibold text-xs uppercase tracking-wider flex items-center gap-1.5">
                <CheckCircle2 size={14} className="text-[#10b981]" />
                <span>Lý do chính xác:</span>
              </h3>
              <p className="text-[#707070] text-xs sm:text-sm leading-relaxed">
                Phương án này thỏa mãn đầy đủ các giả thiết và công thức định lý. Học sinh đã vận dụng chính xác các bước giải toán.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {/* Khối Giải thích bản chất sai lầm */}
              <div className="p-4 rounded-2xl bg-[#f3f3f3] border border-[#e0e0e0] space-y-2">
                <h3 className="text-[#141414] font-semibold text-xs uppercase tracking-wider flex items-center gap-1.5">
                  <AlertTriangle size={14} className="text-[#f59e0b]" />
                  <span>Vì sao phương án này Sai? (Bản chất Toán học):</span>
                </h3>
                <div className="text-[#141414] text-xs sm:text-sm leading-relaxed space-y-1">
                  <MathText text={rationale} />
                </div>
              </div>

              {/* Lời khuyên sư phạm phòng tránh */}
              <div className="p-4 rounded-2xl bg-[#ffffff] border border-[#e0e0e0] space-y-1.5">
                <h4 className="text-[#141414] font-semibold text-xs flex items-center gap-1.5">
                  <Lightbulb size={14} className="text-[#0066ff]" />
                  <span>Mẹo Sư Phạm & Lời Khuyên Phòng Tránh Bẫy:</span>
                </h4>
                <p className="text-[#707070] text-xs leading-relaxed">
                  {classification.advice}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* 4. FOOTER HÀNH ĐỘNG */}
        <div className="p-5 sm:p-6 border-t border-[#e0e0e0] bg-[#ffffff] flex flex-wrap items-center justify-between gap-2 shrink-0">
          <div className="text-[11px] text-[#707070]">
            Học sinh có thể chọn lại phương án để thử sức
          </div>

          <div className="flex items-center gap-2">
            {onRetry && (
              <button
                type="button"
                onClick={() => {
                  onRetry();
                  onClose?.();
                }}
                className="px-4 py-2 rounded-full bg-[#ffffff] hover:bg-[#f3f3f3] text-[#141414] text-xs font-semibold flex items-center gap-1.5 border border-[#e0e0e0] transition cursor-pointer"
              >
                <RotateCcw size={13} />
                <span>Thử chọn lại</span>
              </button>
            )}

            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-full bg-[#141414] hover:bg-[#262626] text-white text-xs font-semibold transition cursor-pointer shadow-none"
            >
              Đã hiểu & Tiếp tục
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
