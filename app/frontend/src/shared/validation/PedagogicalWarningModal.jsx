import React, { useState } from 'react';
import { AlertTriangle, X, CheckCircle2, Sparkles, Edit3, EyeOff, BookOpen, Calculator, SpellCheck } from 'lucide-react';
import MathText from '../math/MathText';

/**
 * Task 10.4: Giao diện "Danh sách Cảnh báo Sư phạm" (Human-in-the-Loop Warning Panel)
 * - Hiển thị khi Giáo viên click vào biểu tượng ⚠️ màu vàng trên Slide có lỗi.
 * - Liệt kê chi tiết lỗi chính tả Tiếng Việt (Task 10.1), lỗi biến đổi đại số SymPy (Task 10.2),
 *   và lỗi đối chiếu định lý SGK Toán GDPT 2018 (Task 10.3).
 * - Đưa ra gợi ý cách sửa rõ ràng nhưng TUYỆT ĐỐI KHÔNG tự ý ghi đè bài của Giáo viên.
 */
export default function PedagogicalWarningModal({
  isOpen,
  onClose,
  warnings = [],
  currentSlideIndex = 0, // 0-based
  onJumpToSlide,
  onOpenManualEdit,
  onDismissWarning
}) {
  const [filterMode, setFilterMode] = useState('current'); // 'current' | 'all'

  if (!isOpen) return null;

  const currentSlideNum = currentSlideIndex + 1;
  const currentSlideWarnings = warnings.filter(
    (w) => Number(w.slide_index) === currentSlideNum
  );

  const displayedWarnings =
    filterMode === 'current' && currentSlideWarnings.length > 0
      ? currentSlideWarnings
      : warnings;

  const getCategoryMeta = (category) => {
    switch (category) {
      case 'algebra_sympy':
        return {
          label: 'Biến đổi Đại số (SymPy)',
          icon: Calculator,
          badgeClass: 'bg-rose-950/80 text-rose-300 border-rose-700/70'
        };
      case 'textbook_theorem':
        return {
          label: 'Đối chiếu Định lý SGK 2018',
          icon: BookOpen,
          badgeClass: 'bg-amber-950/80 text-amber-300 border-amber-600/70'
        };
      default:
        return {
          label: 'Chính tả Tiếng Việt',
          icon: SpellCheck,
          badgeClass: 'bg-yellow-950/80 text-yellow-300 border-yellow-600/70'
        };
    }
  };

  const formatFieldLabel = (field = '') => {
    if (!field) return 'Nội dung Slide';
    if (field === 'title') return 'Tiêu đề chính (title)';
    if (field === 'subtitle') return 'Tiêu đề phụ (subtitle)';
    if (field === 'main_definition_latex') return 'Công thức trọng tâm (main_definition_latex)';
    if (field === 'teacher_note') return 'Ghi chú Giáo viên (teacher_note)';
    const bulletMatch = field.match(/^bullet_points\[(\d+)\]/);
    if (bulletMatch) {
      return `Ý chính dòng #${Number(bulletMatch[1]) + 1}`;
    }
    return field;
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-[#141414]/30 backdrop-blur-sm p-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-3xl bg-[#ffffff] border border-[#e0e0e0] rounded-[24px] shadow-none overflow-hidden flex flex-col max-h-[86vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header cảnh báo chuẩn Mobbin Monochrome */}
        <div className="px-6 py-4 bg-[#ffffff] border-b border-[#e0e0e0] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-[30%] bg-[#f3f3f3] text-[#141414] flex items-center justify-center">
              <AlertTriangle size={18} />
            </div>
            <div>
              <h3 className="text-sm md:text-base font-semibold text-[#141414] flex items-center gap-2">
                <span>Danh Sách Cảnh Báo Sư Phạm</span>
                <span className="px-2.5 py-0.5 text-[11px] rounded-full bg-[#f3f3f3] border border-[#e0e0e0] text-[#141414] font-mono">
                  {warnings.length} phát hiện
                </span>
              </h3>
              <p className="text-[11px] text-[#707070] mt-0.5">
                Kiểm duyệt Chính tả Tiếng Việt • Biến đổi Đại số SymPy • Đối chiếu Định lý SGK GDPT 2018
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-full text-[#707070] hover:text-[#141414] hover:bg-[#f3f3f3] transition cursor-pointer"
            title="Đóng bảng cảnh báo"
          >
            <X size={16} />
          </button>
        </div>

        {/* Thanh thông báo nguyên tắc Human-in-the-Loop */}
        <div className="px-6 py-3 bg-[#f3f3f3] border-b border-[#e0e0e0] flex flex-wrap items-center justify-between gap-2 text-xs">
          <div className="flex items-center gap-2 text-[#141414]">
            <Sparkles size={14} className="text-[#0066ff] shrink-0" />
            <span>
              <strong>Nguyên tắc Sư phạm (Human-in-the-Loop):</strong> Hệ thống gợi ý cách sửa,{' '}
              <span className="font-semibold underline">không tự ý ghi đè bài giảng của giáo viên</span>.
            </span>
          </div>

          {/* Bộ lọc Slide hiện tại vs Toàn bộ bộ Slide */}
          <div className="flex items-center gap-1 bg-[#ffffff] p-1 rounded-full border border-[#e0e0e0] text-[11px]">
            <button
              type="button"
              onClick={() => setFilterMode('current')}
              className={`px-3 py-1 rounded-full transition font-semibold cursor-pointer ${
                filterMode === 'current'
                  ? 'bg-[#141414] text-white'
                  : 'text-[#707070] hover:text-[#141414]'
              }`}
            >
              Slide hiện tại ({currentSlideWarnings.length})
            </button>
            <button
              type="button"
              onClick={() => setFilterMode('all')}
              className={`px-3 py-1 rounded-full transition font-semibold cursor-pointer ${
                filterMode === 'all'
                  ? 'bg-[#141414] text-white'
                  : 'text-[#707070] hover:text-[#141414]'
              }`}
            >
              Toàn bộ bài ({warnings.length})
            </button>
          </div>
        </div>

        {/* Danh sách chi tiết các cảnh báo */}
        <div className="p-6 overflow-y-auto space-y-3 flex-1">
          {displayedWarnings.length === 0 ? (
            <div className="py-12 text-center space-y-2">
              <CheckCircle2 size={36} className="text-[#10b981] mx-auto" />
              <div className="text-sm font-semibold text-[#141414]">
                Slide hiện tại hoàn toàn chuẩn xác!
              </div>
              <p className="text-xs text-[#707070]">
                Không phát hiện lỗi chính tả Tiếng Việt hay sai lệch công thức Toán học nào.
              </p>
            </div>
          ) : (
            displayedWarnings.map((item, idx) => {
              const meta = getCategoryMeta(item.category);
              const IconComp = meta.icon;

              return (
                <div
                  key={`${item.slide_index}-${item.field}-${idx}`}
                  className="p-4 rounded-2xl border border-[#e0e0e0] bg-[#ffffff] space-y-3"
                >
                  {/* Dòng 1: Huy hiệu Slide + Loại lỗi + Vị trí trường */}
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <button
                        type="button"
                        onClick={() => onJumpToSlide?.(Number(item.slide_index) - 1)}
                        className="px-2.5 py-0.5 rounded-full bg-[#f3f3f3] hover:bg-[#e0e0e0] border border-[#e0e0e0] text-[#141414] font-semibold text-xs transition cursor-pointer"
                        title="Nhảy tới trang Slide này"
                      >
                        ⚠️ Slide {item.slide_index}
                      </button>

                      <span className="px-2.5 py-0.5 rounded-full border border-[#e0e0e0] text-[11px] font-semibold flex items-center gap-1 bg-[#f3f3f3] text-[#141414]">
                        <IconComp size={12} />
                        <span>{meta.label}</span>
                      </span>

                      <span className="text-[11px] font-mono text-[#707070] bg-[#f3f3f3] px-2.5 py-0.5 rounded-full border border-[#e0e0e0]">
                        Vị trí: {formatFieldLabel(item.field)}
                      </span>
                    </div>

                    {item.detected_token && (
                      <span className="text-[11px] font-mono px-2.5 py-0.5 rounded-full bg-rose-50 border border-rose-200 text-rose-700">
                        Phát hiện: &ldquo;{item.detected_token}&rdquo;
                      </span>
                    )}
                  </div>

                  {/* Dòng 2: Nội dung cảnh báo chi tiết */}
                  <div className="text-xs text-[#141414] leading-relaxed">
                    {item.message}
                  </div>

                  {/* Dòng 3: Hộp gợi ý sửa (Hiển thị cả công thức KaTeX nếu có) */}
                  {item.suggestion && (
                    <div className="p-3 rounded-2xl bg-[#f3f3f3] border border-[#e0e0e0] text-xs text-[#141414] flex items-start gap-2">
                      <span className="font-semibold text-[#141414] shrink-0">💡 Gợi ý sửa:</span>
                      <div className="flex-1 font-medium">
                        <MathText text={item.suggestion} />
                      </div>
                    </div>
                  )}

                  {/* Dòng 4: Nút thao tác dành cho Giáo viên (Tự mở trình sửa hoặc Bỏ qua) */}
                  <div className="flex flex-wrap items-center justify-end gap-2 pt-1">
                    {onOpenManualEdit && (
                      <button
                        type="button"
                        onClick={() => onOpenManualEdit(item)}
                        className="px-3.5 py-1.5 rounded-full bg-[#141414] hover:bg-[#262626] text-white text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer shadow-none"
                      >
                        <Edit3 size={12} />
                        <span>Mở khung để GV tự sửa</span>
                      </button>
                    )}

                    {onDismissWarning && (
                      <button
                        type="button"
                        onClick={() => onDismissWarning(item)}
                        className="px-3 py-1.5 rounded-full bg-[#ffffff] hover:bg-[#f3f3f3] text-[#707070] hover:text-[#141414] text-xs flex items-center gap-1 border border-[#e0e0e0] transition cursor-pointer"
                        title="Bỏ qua nếu lỗi này là chủ đích sư phạm của Giáo viên"
                      >
                        <EyeOff size={12} />
                        <span>Giữ nguyên (Chủ đích GV)</span>
                      </button>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3.5 bg-[#ffffff] border-t border-[#e0e0e0] flex items-center justify-between text-xs">
          <span className="text-[#707070]">
            Mẹo: Nhấp đúp trực tiếp vào công thức trên Slide để mở bàn phím Toán học MathLive.
          </span>
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-full border border-[#e0e0e0] bg-[#ffffff] hover:bg-[#f3f3f3] text-[#141414] font-semibold transition cursor-pointer"
          >
            Đóng
          </button>
        </div>
      </div>
    </div>
  );
}
