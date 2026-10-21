import React, { useState } from 'react';
import { AlertTriangle, X, CheckCircle2, Sparkles, Edit3, EyeOff, BookOpen, Calculator, SpellCheck } from 'lucide-react';
import MathText from './MathText';

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
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-3xl bg-slate-900 border-2 border-amber-500/70 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[86vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header màu vàng cảnh báo chuẩn Task 10.4 */}
        <div className="px-5 py-3.5 bg-gradient-to-r from-amber-950/90 via-slate-900 to-slate-900 border-b border-amber-500/40 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-amber-500/20 border border-amber-400/60 flex items-center justify-center text-amber-300 shadow-inner">
              <AlertTriangle size={20} />
            </div>
            <div>
              <h3 className="text-sm md:text-base font-bold text-amber-200 flex items-center gap-2">
                <span>⚠️ Danh Sách Cảnh Báo Sư Phạm (AI Linter & Proofreader)</span>
                <span className="px-2 py-0.5 text-[11px] rounded-full bg-amber-500/20 border border-amber-400/50 text-amber-300 font-mono">
                  {warnings.length} phát hiện
                </span>
              </h3>
              <p className="text-[11px] text-slate-300 mt-0.5">
                Kiểm duyệt Chính tả Tiếng Việt • Biến đổi Đại số SymPy • Đối chiếu Định lý SGK GDPT 2018
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition"
            title="Đóng bảng cảnh báo"
          >
            <X size={16} />
          </button>
        </div>

        {/* Thanh thông báo nguyên tắc Human-in-the-Loop */}
        <div className="px-5 py-2.5 bg-amber-950/30 border-b border-slate-800 flex flex-wrap items-center justify-between gap-2 text-xs">
          <div className="flex items-center gap-2 text-amber-200/90">
            <Sparkles size={14} className="text-amber-400 shrink-0" />
            <span>
              <strong>Nguyên tắc Sư phạm (Human-in-the-Loop):</strong> Hệ thống chỉ gợi ý cách sửa,{' '}
              <span className="underline decoration-amber-400 font-semibold">KHÔNG tự ý ghi đè bài của Giáo viên</span>.
            </span>
          </div>

          {/* Bộ lọc Slide hiện tại vs Toàn bộ bộ Slide */}
          <div className="flex items-center gap-1 bg-slate-950/80 p-0.5 rounded-lg border border-slate-800 text-[11px]">
            <button
              type="button"
              onClick={() => setFilterMode('current')}
              className={`px-2.5 py-1 rounded-md transition font-medium ${
                filterMode === 'current'
                  ? 'bg-amber-600 text-white'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Slide hiện tại ({currentSlideWarnings.length})
            </button>
            <button
              type="button"
              onClick={() => setFilterMode('all')}
              className={`px-2.5 py-1 rounded-md transition font-medium ${
                filterMode === 'all'
                  ? 'bg-amber-600 text-white'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Toàn bộ bài ({warnings.length})
            </button>
          </div>
        </div>

        {/* Danh sách chi tiết các cảnh báo */}
        <div className="p-5 overflow-y-auto space-y-3 flex-1">
          {displayedWarnings.length === 0 ? (
            <div className="py-10 text-center space-y-2">
              <CheckCircle2 size={36} className="text-emerald-400 mx-auto" />
              <div className="text-sm font-bold text-white">
                Slide hiện tại hoàn toàn chuẩn xác!
              </div>
              <p className="text-xs text-slate-400">
                Không phát hiện lỗi chính tả Tiếng Việt hay sai lệch công thức Toán học nào.
              </p>
            </div>
          ) : (
            displayedWarnings.map((item, idx) => {
              const meta = getCategoryMeta(item.category);
              const IconComp = meta.icon;
              const isError = item.severity === 'error';

              return (
                <div
                  key={`${item.slide_index}-${item.field}-${idx}`}
                  className={`p-3.5 rounded-xl border transition space-y-2.5 ${
                    isError
                      ? 'bg-amber-950/25 border-amber-500/60 hover:border-amber-400'
                      : 'bg-slate-950/70 border-yellow-600/50 hover:border-yellow-400'
                  }`}
                >
                  {/* Dòng 1: Huy hiệu Slide + Loại lỗi + Vị trí trường */}
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <button
                        type="button"
                        onClick={() => onJumpToSlide?.(Number(item.slide_index) - 1)}
                        className="px-2 py-0.5 rounded bg-amber-500/20 hover:bg-amber-500/30 border border-amber-400/60 text-amber-200 font-bold text-xs transition"
                        title="Nhảy tới trang Slide này"
                      >
                        ⚠️ Slide {item.slide_index}
                      </button>

                      <span className={`px-2 py-0.5 rounded border text-[11px] font-semibold flex items-center gap-1 ${meta.badgeClass}`}>
                        <IconComp size={12} />
                        <span>{meta.label}</span>
                      </span>

                      <span className="text-[11px] font-mono text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                        Vị trí: {formatFieldLabel(item.field)}
                      </span>
                    </div>

                    {item.detected_token && (
                      <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-rose-950/70 border border-rose-700/60 text-rose-200">
                        Phát hiện: &ldquo;{item.detected_token}&rdquo;
                      </span>
                    )}
                  </div>

                  {/* Dòng 2: Nội dung cảnh báo chi tiết */}
                  <div className="text-xs text-slate-200 leading-relaxed">
                    {item.message}
                  </div>

                  {/* Dòng 3: Hộp gợi ý sửa (Hiển thị cả công thức KaTeX nếu có) */}
                  {item.suggestion && (
                    <div className="p-2.5 rounded-lg bg-emerald-950/35 border border-emerald-600/50 text-xs text-emerald-200 flex items-start gap-2">
                      <span className="font-bold text-emerald-400 shrink-0">💡 Gợi ý sửa:</span>
                      <div className="flex-1">
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
                        className="px-3 py-1 rounded-lg bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow-sm transition"
                      >
                        <Edit3 size={12} />
                        <span>Mở khung để GV tự sửa</span>
                      </button>
                    )}

                    {onDismissWarning && (
                      <button
                        type="button"
                        onClick={() => onDismissWarning(item)}
                        className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs flex items-center gap-1 border border-slate-700 transition"
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
        <div className="px-5 py-3 bg-slate-950 border-t border-slate-800 flex items-center justify-between text-xs">
          <span className="text-slate-400">
            Mẹo: Nhấp đúp trực tiếp vào công thức trên Slide để mở bàn phím Toán học MathLive.
          </span>
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-semibold transition"
          >
            Đóng
          </button>
        </div>
      </div>
    </div>
  );
}
