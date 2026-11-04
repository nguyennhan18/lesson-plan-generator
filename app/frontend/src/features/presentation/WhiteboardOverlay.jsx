import React, { useState } from 'react';
import {
  X,
  Grid3X3,
  Pen,
  Highlighter,
  Eraser,
  Undo2,
  Redo2,
  Trash2,
  Sparkles,
  Maximize2
} from 'lucide-react';
import AnnotationCanvas from './AnnotationCanvas';
import { PEDAGOGICAL_COLORS } from './bezierSmoothing.js';

/**
 * WhiteboardOverlay (Task 17.4)
 * Chế độ Bảng Viết Toàn Màn Hình (Whiteboard / Blackboard Mode) dành cho Giáo viên:
 * - Hỗ trợ 3 giao diện bảng sư phạm:
 *   + 'blackboard': Bảng đen hiện đại với lưới ô vuông Toán học (Math Grid 28px)
 *   + 'chalkboard': Bảng xanh truyền thống trường học THPT (Emerald Chalkboard)
 *   + 'whiteboard': Bảng trắng văn phòng / phòng lab Toán học
 * - Cho phép viết nháp, giải phương trình, chứng minh định lý bước đệm mà không làm đè lên slide.
 * - Độc lập hoàn toàn với nét vẽ của từng Slide (không làm xáo trộn bài giảng).
 * - Tích hợp đầy đủ: Bút mực, Bút dạ quang, Tẩy nét thông minh, Hoàn tác (Undo/Redo) và Xóa sạch bảng.
 */
export default function WhiteboardOverlay({
  isOpen = false,
  onClose,
  tool = 'pen',
  color = '#f8fafc',
  size = 3,
  onSelectTool,
  onSelectColor,
  strokes = [],
  onStrokesChange,
  onEraseStroke,
  canUndo = false,
  canRedo = false,
  onUndo,
  onRedo,
  onClear
}) {
  const [boardTheme, setBoardTheme] = useState('blackboard'); // 'blackboard' | 'chalkboard' | 'whiteboard'

  if (!isOpen) return null;

  // Cấu hình phong cách bảng
  const getThemeStyles = () => {
    switch (boardTheme) {
      case 'chalkboard':
        return {
          container: 'bg-[#064e3b]',
          pattern: 'radial-gradient(rgba(255, 255, 255, 0.15) 1px, transparent 1px)',
          borderColor: 'border-emerald-600/50',
          textColor: 'text-emerald-100',
          badge: 'bg-emerald-950/80 text-emerald-300 border-emerald-700/60'
        };
      case 'whiteboard':
        return {
          container: 'bg-slate-50',
          pattern: 'radial-gradient(rgba(15, 23, 42, 0.12) 1px, transparent 1px)',
          borderColor: 'border-slate-300',
          textColor: 'text-slate-800',
          badge: 'bg-white text-slate-700 border-slate-300 shadow-sm'
        };
      case 'blackboard':
      default:
        return {
          container: 'bg-[#090d1c]',
          pattern: 'radial-gradient(rgba(56, 189, 248, 0.15) 1px, transparent 1px)',
          borderColor: 'border-cyan-500/30',
          textColor: 'text-slate-100',
          badge: 'bg-slate-900/90 text-cyan-300 border-cyan-800/60'
        };
    }
  };

  const themeStyle = getThemeStyles();

  return (
    <div className="fixed inset-0 z-50 flex flex-col select-none animate-fadeIn">
      {/* Vùng Bảng Viết Toàn Màn Hình */}
      <div
        className={`relative flex-1 w-full h-full overflow-hidden transition-colors duration-300 ${themeStyle.container}`}
        style={{
          backgroundImage: themeStyle.pattern,
          backgroundSize: '28px 28px'
        }}
      >
        {/* THANH ĐIỀU KHIỂN ĐỈNH BẢNG (WHITEBOARD TOP BAR HUD) */}
        <div className="absolute top-4 left-4 right-4 z-50 flex items-center justify-between pointer-events-auto">
          {/* Nhãn Tiêu đề & Chọn Giao diện Bảng */}
          <div className="flex items-center gap-2">
            <div className="px-3.5 py-1.5 rounded-full border border-[#e0e0e0] flex items-center gap-2 font-mono text-xs bg-[#ffffff] text-[#141414]">
              <Grid3X3 size={15} />
              <span className="font-semibold">BẢNG PHỤ TOÁN HỌC (W)</span>
            </div>

            {/* Các nút chuyển nền bảng */}
            <div className="flex items-center bg-[#ffffff] border border-[#e0e0e0] rounded-full p-1 gap-1 text-[11px]">
              <button
                type="button"
                onClick={() => setBoardTheme('blackboard')}
                className={`px-3 py-1 rounded-full transition cursor-pointer ${
                  boardTheme === 'blackboard'
                    ? 'bg-[#141414] text-white font-semibold'
                    : 'text-[#707070] hover:text-[#141414]'
                }`}
              >
                Bảng Đen
              </button>
              <button
                type="button"
                onClick={() => setBoardTheme('chalkboard')}
                className={`px-3 py-1 rounded-full transition cursor-pointer ${
                  boardTheme === 'chalkboard'
                    ? 'bg-[#141414] text-white font-semibold'
                    : 'text-[#707070] hover:text-[#141414]'
                }`}
              >
                Bảng Xanh
              </button>
              <button
                type="button"
                onClick={() => setBoardTheme('whiteboard')}
                className={`px-3 py-1 rounded-full transition cursor-pointer ${
                  boardTheme === 'whiteboard'
                    ? 'bg-[#141414] text-white font-semibold'
                    : 'text-[#707070] hover:text-[#141414]'
                }`}
              >
                Bảng Trắng
              </button>
            </div>
          </div>

          {/* Cụm công cụ vẽ trên bảng */}
          <div className="flex items-center gap-2">
            {/* Bộ công cụ: Bút, Dạ quang, Tẩy */}
            <div className="flex items-center gap-1 bg-[#ffffff] border border-[#e0e0e0] rounded-full p-1 text-xs">
              <button
                type="button"
                onClick={() => onSelectTool?.('pen')}
                className={`px-3 py-1 rounded-full flex items-center gap-1 transition cursor-pointer ${
                  tool === 'pen'
                    ? 'bg-[#141414] text-white font-semibold'
                    : 'text-[#707070] hover:text-[#141414]'
                }`}
                title="Bút phấn viết bảng (P)"
              >
                <Pen size={12} />
                <span>Bút</span>
              </button>

              <button
                type="button"
                onClick={() => onSelectTool?.('highlighter')}
                className={`px-3 py-1 rounded-full flex items-center gap-1 transition cursor-pointer ${
                  tool === 'highlighter'
                    ? 'bg-[#141414] text-white font-semibold'
                    : 'text-[#707070] hover:text-[#141414]'
                }`}
                title="Bút dạ quang đánh dấu (H)"
              >
                <Highlighter size={12} />
                <span>Dạ quang</span>
              </button>

              <button
                type="button"
                onClick={() => onSelectTool?.('eraser')}
                className={`px-3 py-1 rounded-full flex items-center gap-1 transition cursor-pointer ${
                  tool === 'eraser'
                    ? 'bg-[#141414] text-white font-semibold'
                    : 'text-[#707070] hover:text-[#141414]'
                }`}
                title="Khăn lau bảng / Tẩy nét (E)"
              >
                <Eraser size={12} />
                <span>Tẩy</span>
              </button>

              {/* Bảng chọn màu nét phấn */}
              {tool !== 'eraser' && onSelectColor && (
                <div className="flex items-center gap-1 pl-2 border-l border-[#e0e0e0]">
                  {PEDAGOGICAL_COLORS.map((c) => (
                    <button
                      key={c.id}
                      type="button"
                      onClick={() => onSelectColor(c.value)}
                      className={`w-3.5 h-3.5 rounded-full transition transform hover:scale-125 cursor-pointer ${
                        color === c.value
                          ? 'ring-2 ring-offset-1 ring-[#141414] scale-110'
                          : 'opacity-70 hover:opacity-100'
                      }`}
                      style={{ backgroundColor: c.value }}
                      title={c.name}
                    />
                  ))}
                </div>
              )}
            </div>

            {/* Cụm Hoàn tác, Làm lại, Xóa bảng */}
            <div className="flex items-center gap-1 bg-[#ffffff] border border-[#e0e0e0] rounded-full p-1 text-xs">
              <button
                type="button"
                onClick={onUndo}
                disabled={!canUndo}
                className="p-1.5 rounded-full text-[#707070] hover:text-[#141414] hover:bg-[#f3f3f3] disabled:opacity-30 disabled:pointer-events-none transition cursor-pointer"
                title="Hoàn tác nét viết (Ctrl+Z)"
              >
                <Undo2 size={13} />
              </button>

              <button
                type="button"
                onClick={onRedo}
                disabled={!canRedo}
                className="p-1.5 rounded-full text-[#707070] hover:text-[#141414] hover:bg-[#f3f3f3] disabled:opacity-30 disabled:pointer-events-none transition cursor-pointer"
                title="Làm lại nét viết (Ctrl+Y)"
              >
                <Redo2 size={13} />
              </button>

              <button
                type="button"
                onClick={onClear}
                disabled={!strokes || strokes.length === 0}
                className="p-1.5 rounded-full text-rose-500 hover:text-rose-700 hover:bg-rose-50 disabled:opacity-30 disabled:pointer-events-none transition cursor-pointer"
                title="Lau sạch toàn bộ bảng"
              >
                <Trash2 size={13} />
              </button>
            </div>

            {/* Nút Đóng / Thu nhỏ Bảng viết */}
            <button
              type="button"
              onClick={onClose}
              className="px-3.5 py-1.5 rounded-full bg-[#141414] hover:bg-[#262626] text-white transition flex items-center gap-1.5 text-xs font-semibold cursor-pointer shadow-none"
              title="Đóng Bảng viết (Phím W hoặc Esc)"
            >
              <X size={15} />
              <span className="hidden sm:inline">Đóng (W)</span>
            </button>
          </div>
        </div>

        {/* Lớp Canvas Vẽ Chú Thích trên Bảng Phụ */}
        <AnnotationCanvas
          isActive={isOpen}
          tool={tool}
          color={color}
          size={size}
          slideIndex="whiteboard"
          strokes={strokes}
          onStrokesChange={onStrokesChange}
          onEraseStroke={onEraseStroke}
          isPresentationMode={true}
        />
      </div>
    </div>
  );
}
