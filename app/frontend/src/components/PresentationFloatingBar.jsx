import React, { useState, useEffect, useRef } from 'react';
import {
  Clock,
  Play,
  Pause,
  RotateCcw,
  ChevronLeft,
  ChevronRight,
  Moon,
  Minimize2,
  Eye,
  LineChart,
  Box,
  FileText,
  Layers,
  ChevronUp,
  X,
  Pen,
  Highlighter,
  Eraser,
  Undo2,
  Redo2,
  Trash2,
  Grid3X3,
  Palette
} from 'lucide-react';
import { PEDAGOGICAL_COLORS } from '../utils/bezierSmoothing';

/**
 * PresentationFloatingBar (Task 15.4)
 * Thanh điều khiển mờ (Floating Control Bar HUD) ở đáy màn hình trong Chế độ Trình Chiếu Toàn Màn Hình.
 * Tích hợp:
 * - Đồng hồ đếm thời gian tiết dạy chuẩn mực (45 phút theo chuẩn GDPT 2018 / Công văn 5512)
 * - Cảnh báo sư phạm tự động: Xanh lục (>10p) -> Vàng cam (5-10p) -> Đỏ nhấp nháy (<5p)
 * - Tự động mờ (Auto-hide on idle) sau 3.5 giây không di chuột, lập tức hiện lại khi di chuột
 * - Bộ điều hướng slide (Trước/Sau, Nhảy slide trực tiếp qua Filmstrip popover)
 * - Nút Tối màn hình (Blackout mode - Phím B)
 * - Nút Thoát Trình Chiếu (Phím Esc)
 */
export default function PresentationFloatingBar({
  currentSlide = 0,
  totalSlides = 1,
  onPrevSlide,
  onNextSlide,
  onSelectSlide,
  slides = [],
  isBlackout = false,
  onToggleBlackout,
  onExitPresentation,
  visualMode = 'auto',
  onSelectVisualMode,
  // Task 17.2: Quản lý Công cụ Bút vẽ Sư phạm
  isDrawingMode = false,
  onToggleDrawingMode,
  currentTool = 'pen',
  onSelectTool,
  drawingColor = '#ef4444',
  onSelectColor,
  brushSize = 3,
  onSelectBrushSize,
  // Task 17.3: Quản lý Tẩy nét, Hoàn tác & Xóa sạch canvas
  canUndo = false,
  canRedo = false,
  onUndo,
  onRedo,
  onClearCanvas,
  hasStrokes = false,
  // Task 17.4: Chế độ Bảng trắng Toàn màn hình & Đồng bộ trạng thái nét vẽ
  isWhiteboardOpen = false,
  onToggleWhiteboard,
  slideDrawingsMap = {}
}) {
  // ================= 1. QUẢN LÝ ĐỒNG HỒ TIẾT DẠY 45 PHÚT =================
  const [durationMinutes, setDurationMinutes] = useState(45); // Mặc định 45 phút chuẩn GDPT
  const [timeLeft, setTimeLeft] = useState(45 * 60); // Đếm ngược số giây (2700s)
  const [isRunning, setIsRunning] = useState(true); // Tự động đếm khi vào tiết dạy
  const [showDurationMenu, setShowDurationMenu] = useState(false);
  const [showThumbnails, setShowThumbnails] = useState(false);

  // Cập nhật khi đổi mốc thời gian (15p, 30p, 45p, 90p)
  const handleSelectDuration = (minutes) => {
    setDurationMinutes(minutes);
    setTimeLeft(minutes * 60);
    setIsRunning(true);
    setShowDurationMenu(false);
  };

  // Đồng hồ đếm ngược mỗi giây
  useEffect(() => {
    if (!isRunning) return;

    const interval = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [isRunning]);

  const handleToggleTimer = () => {
    setIsRunning((prev) => !prev);
  };

  const handleResetTimer = (e) => {
    e.stopPropagation();
    setTimeLeft(durationMinutes * 60);
    setIsRunning(true);
  };

  // Format mm:ss
  const formatTime = (totalSeconds) => {
    const m = Math.floor(totalSeconds / 60);
    const s = totalSeconds % 60;
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  };

  // Màu sắc cảnh báo thời gian sư phạm:
  // > 10 phút: Xanh lục (tiết dạy diễn ra bình thường)
  // 5 - 10 phút: Vàng cam (bước sang Hoạt động Luyện tập & Củng cố)
  // < 5 phút: Đỏ cảnh báo nhấp nháy (chuẩn bị kết thúc & dặn dò bài tập)
  // 0 phút: Đỏ chuông hết giờ
  const timerColorStyles = () => {
    if (timeLeft === 0) {
      return {
        badge: 'bg-rose-950/80 border-rose-500 text-rose-300 animate-pulse',
        ring: 'text-rose-400',
        label: 'Hết giờ tiết dạy'
      };
    }
    if (timeLeft <= 5 * 60) {
      return {
        badge: 'bg-rose-950/60 border-rose-600/80 text-rose-300 animate-pulse',
        ring: 'text-rose-400',
        label: 'Sắp hết giờ (<5p)'
      };
    }
    if (timeLeft <= 10 * 60) {
      return {
        badge: 'bg-amber-950/60 border-amber-600/80 text-amber-300',
        ring: 'text-amber-400',
        label: 'Tổng kết (5-10p)'
      };
    }
    return {
      badge: 'bg-emerald-950/60 border-emerald-600/70 text-emerald-300',
      ring: 'text-emerald-400',
      label: 'Đúng tiến độ'
    };
  };

  const timerStyle = timerColorStyles();

  // ================= 2. QUẢN LÝ TỰ ĐỘNG MỜ KHI IDLE (3.5 GIÂY) =================
  const [isVisible, setIsVisible] = useState(true);
  const [isHovered, setIsHovered] = useState(false);
  const idleTimerRef = useRef(null);

  const resetIdleTimer = () => {
    setIsVisible(true);
    if (idleTimerRef.current) {
      clearTimeout(idleTimerRef.current);
    }
    idleTimerRef.current = setTimeout(() => {
      // Chỉ ẩn khi không hover vào thanh, không mở menu thumbnails/duration và timer đang chạy
      if (!isHovered && !showThumbnails && !showDurationMenu) {
        setIsVisible(false);
      }
    }, 3500);
  };

  useEffect(() => {
    const handleMouseMove = () => {
      resetIdleTimer();
    };

    window.addEventListener('mousemove', handleMouseMove);
    resetIdleTimer();

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      if (idleTimerRef.current) clearTimeout(idleTimerRef.current);
    };
  }, [isHovered, showThumbnails, showDurationMenu]);

  // Giữ thanh luôn hiển thị khi hover hoặc khi đang mở popover
  const effectiveVisible = isVisible || isHovered || showThumbnails || showDurationMenu || !isRunning;

  return (
    <>
      {/* Vùng kích hoạt hover ở đáy màn hình khi thanh đang ẩn */}
      <div
        onMouseEnter={() => setIsVisible(true)}
        className="fixed bottom-0 left-0 right-0 h-12 z-40 pointer-events-auto"
        aria-hidden="true"
      />

      {/* Popover danh sách Slide Thumbnails nhanh */}
      {showThumbnails && (
        <div
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
          className="fixed bottom-20 left-1/2 -translate-x-1/2 z-50 bg-[#090d1c]/95 backdrop-blur-xl border border-slate-700/80 rounded-2xl shadow-2xl p-3 max-w-2xl w-[90vw] max-h-56 overflow-y-auto"
        >
          <div className="flex items-center justify-between pb-2 border-b border-slate-800 text-xs">
            <span className="font-semibold text-cyan-300 flex items-center gap-1.5">
              <Layers size={14} /> Danh Mục Slide Bài Giảng
            </span>
            <button
              onClick={() => setShowThumbnails(false)}
              className="p-1 rounded-md text-slate-400 hover:text-white hover:bg-slate-800 transition"
            >
              <X size={14} />
            </button>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2 pt-2.5">
            {slides.map((s, idx) => (
              <button
                key={idx}
                onClick={() => {
                  onSelectSlide?.(idx);
                  setShowThumbnails(false);
                }}
                className={`p-2 rounded-xl text-left border text-xs transition flex flex-col justify-between ${
                  currentSlide === idx
                    ? 'bg-cyan-600/30 border-cyan-400 text-cyan-200 ring-2 ring-cyan-500/50'
                    : 'bg-slate-900/80 hover:bg-slate-800/90 border-slate-800 text-slate-300'
                }`}
              >
                <div className="font-mono text-[10px] text-cyan-400 font-bold mb-1 flex items-center justify-between">
                  <span>#{idx + 1}</span>
                  {slideDrawingsMap[idx]?.length > 0 && (
                    <span className="text-[9px] text-amber-300 font-normal px-1 py-0.2 bg-amber-950/60 border border-amber-700/50 rounded">
                      ✎ {slideDrawingsMap[idx].length}
                    </span>
                  )}
                </div>
                <div className="text-[11px] font-medium line-clamp-2 leading-snug">
                  {s.title?.split('•')[0] || `Slide ${idx + 1}`}
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* THANH ĐIỀU KHIỂN NỔI (FLOATING CONTROL BAR HUD) */}
      <div
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        className={`fixed bottom-4 left-1/2 -translate-x-1/2 z-50 transition-all duration-300 transform select-none ${
          effectiveVisible
            ? 'opacity-100 translate-y-0 pointer-events-auto'
            : 'opacity-0 translate-y-4 pointer-events-none'
        }`}
      >
        <div className="glass-panel bg-slate-950/85 backdrop-blur-xl border border-slate-700/80 rounded-2xl shadow-2xl px-3.5 py-2 flex items-center gap-2.5 sm:gap-3 text-slate-100">
          {/* ================= 1. ĐỒNG HỒ TIẾT DẠY 45 PHÚT ================= */}
          <div className="flex items-center gap-1.5 relative">
            <div
              onClick={handleToggleTimer}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-xl border cursor-pointer transition shadow-inner ${timerStyle.badge}`}
              title={isRunning ? "Bấm để Tạm dừng đồng hồ" : "Bấm để Tiếp tục đếm giờ"}
            >
              <Clock size={14} className={timerStyle.ring} />
              <span className="font-mono font-bold text-xs sm:text-sm tracking-wider">
                {formatTime(timeLeft)}
              </span>
              <button
                type="button"
                className="ml-0.5 text-slate-300 hover:text-white transition"
                title={isRunning ? "Tạm dừng" : "Tiếp tục"}
              >
                {isRunning ? <Pause size={12} /> : <Play size={12} className="text-emerald-400" />}
              </button>
            </div>

            {/* Nút reset đồng hồ */}
            <button
              onClick={handleResetTimer}
              className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/80 border border-transparent hover:border-slate-700 transition"
              title="Đặt lại đồng hồ về 45:00"
            >
              <RotateCcw size={12} />
            </button>

            {/* Nút chọn thời lượng tiết học (15p, 30p, 45p, 90p) */}
            <div className="relative">
              <button
                onClick={() => setShowDurationMenu((prev) => !prev)}
                className="px-1.5 py-1 rounded-lg text-[10px] font-mono text-slate-400 hover:text-cyan-300 hover:bg-slate-900 border border-slate-800 transition flex items-center gap-0.5"
                title="Thay đổi thời lượng tiết học"
              >
                <span>{durationMinutes}p</span>
                <ChevronUp size={10} className={showDurationMenu ? 'rotate-180 transition' : 'transition'} />
              </button>

              {showDurationMenu && (
                <div className="absolute bottom-full mb-2 left-0 bg-slate-900 border border-slate-700 rounded-xl shadow-xl p-1 text-xs space-y-0.5 min-w-[100px] z-50">
                  <div className="text-[10px] text-slate-400 px-2 py-0.5 font-bold uppercase tracking-wider">
                    Thời lượng:
                  </div>
                  {[15, 30, 45, 90].map((mins) => (
                    <button
                      key={mins}
                      onClick={() => handleSelectDuration(mins)}
                      className={`w-full text-left px-2 py-1 rounded-lg text-xs transition flex items-center justify-between ${
                        durationMinutes === mins
                          ? 'bg-cyan-600 text-white font-bold'
                          : 'text-slate-300 hover:bg-slate-800'
                      }`}
                    >
                      <span>{mins} phút</span>
                      {mins === 45 && <span className="text-[9px] text-emerald-300">Chuẩn</span>}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Dải phân cách dọc */}
          <div className="h-5 w-px bg-slate-800 hidden sm:block" />

          {/* ================= 2. ĐIỀU HƯỚNG SLIDE ================= */}
          <div className="flex items-center gap-1">
            <button
              onClick={onPrevSlide}
              disabled={currentSlide === 0}
              className="p-1.5 rounded-xl bg-slate-900/90 hover:bg-slate-800 disabled:opacity-30 text-slate-300 hover:text-white border border-slate-800 transition"
              title="Lùi Slide (Phím ← hoặc PageUp)"
            >
              <ChevronLeft size={16} />
            </button>

            {/* Bộ đếm slide kiêm nút mở danh mục Filmstrip */}
            <button
              onClick={() => setShowThumbnails((prev) => !prev)}
              className="px-2.5 py-1 rounded-xl bg-slate-900/90 hover:bg-slate-800 border border-slate-800 hover:border-cyan-600 text-xs font-mono text-cyan-300 transition flex items-center gap-1.5 shadow-inner"
              title="Nhấn để mở danh sách toàn bộ Slide"
            >
              <Layers size={13} className="text-cyan-400" />
              <span>
                {currentSlide + 1} / {totalSlides}
              </span>
            </button>

            <button
              onClick={onNextSlide}
              disabled={currentSlide >= totalSlides - 1}
              className="p-1.5 rounded-xl bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 disabled:opacity-30 text-white border border-cyan-500/50 shadow-md shadow-cyan-950/40 transition"
              title="Tiến Slide (Phím →, Spacebar hoặc PageDown)"
            >
              <ChevronRight size={16} />
            </button>
          </div>

          {/* Dải phân cách dọc */}
          <div className="h-5 w-px bg-slate-800 hidden md:block" />

          {/* ================= 3. CÔNG CỤ NHANH: 2D/3D/PPTX ================= */}
          {onSelectVisualMode && (
            <div className="hidden lg:flex items-center bg-slate-900/90 border border-slate-800 rounded-xl p-0.5 text-xs">
              <button
                onClick={() => onSelectVisualMode('auto')}
                className={`px-2 py-0.5 rounded-lg flex items-center gap-1 transition ${
                  visualMode === 'auto'
                    ? 'bg-cyan-600 text-white font-semibold'
                    : 'text-slate-400 hover:text-white'
                }`}
                title="Tự động chuẩn PowerPoint"
              >
                <Eye size={12} />
                <span>Auto</span>
              </button>
              <button
                onClick={() => onSelectVisualMode('2d')}
                className={`px-2 py-0.5 rounded-lg flex items-center gap-1 transition ${
                  visualMode === '2d'
                    ? 'bg-cyan-600 text-white font-semibold'
                    : 'text-slate-400 hover:text-white'
                }`}
                title="Ép hiển thị Đồ thị 2D"
              >
                <LineChart size={12} />
                <span>2D</span>
              </button>
              <button
                onClick={() => onSelectVisualMode('3d')}
                className={`px-2 py-0.5 rounded-lg flex items-center gap-1 transition ${
                  visualMode === '3d'
                    ? 'bg-cyan-600 text-white font-semibold'
                    : 'text-slate-400 hover:text-white'
                }`}
                title="Ép hiển thị Không gian 3D"
              >
                <Box size={12} />
                <span>3D</span>
              </button>
              <button
                onClick={() => onSelectVisualMode('pptx')}
                className={`px-2 py-0.5 rounded-lg flex items-center gap-1 transition ${
                  visualMode === 'pptx'
                    ? 'bg-amber-600 text-white font-semibold'
                    : 'text-slate-400 hover:text-white'
                }`}
                title="Bản in PowerPoint 1:1"
              >
                <FileText size={12} />
                <span>PPTX</span>
              </button>
            </div>
          )}

          {/* ================= 3.5. CÔNG CỤ BÚT VẼ SƯ PHẠM (TASK 17.2) ================= */}
          <div className="flex items-center gap-1 bg-slate-900/90 border border-slate-800 rounded-xl p-0.5 text-xs">
            {/* Nút Bút mực (Phím P) */}
            <button
              type="button"
              onClick={() => {
                if (!isDrawingMode) {
                  onToggleDrawingMode?.(true);
                  onSelectTool?.('pen');
                } else if (currentTool === 'pen') {
                  onToggleDrawingMode?.(false);
                } else {
                  onSelectTool?.('pen');
                }
              }}
              className={`px-2 py-1 rounded-lg flex items-center gap-1 transition ${
                isDrawingMode && currentTool === 'pen'
                  ? 'bg-rose-600 text-white font-semibold shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
              title="Bút vẽ mực thường (Phím P)"
            >
              <Pen size={12} />
              <span className="hidden xl:inline">Bút (P)</span>
            </button>

            {/* Nút Bút dạ quang Highlighter (Phím H) */}
            <button
              type="button"
              onClick={() => {
                if (!isDrawingMode) {
                  onToggleDrawingMode?.(true);
                  onSelectTool?.('highlighter');
                } else if (currentTool === 'highlighter') {
                  onToggleDrawingMode?.(false);
                } else {
                  onSelectTool?.('highlighter');
                }
              }}
              className={`px-2 py-1 rounded-lg flex items-center gap-1 transition ${
                isDrawingMode && currentTool === 'highlighter'
                  ? 'bg-amber-600 text-white font-semibold shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
              title="Bút dạ quang làm nổi bật (Phím H)"
            >
              <Highlighter size={12} />
              <span className="hidden xl:inline">Dạ quang (H)</span>
            </button>

            {/* Nút Tẩy nét Eraser (Phím E) - Task 17.3 */}
            <button
              type="button"
              onClick={() => {
                if (!isDrawingMode) {
                  onToggleDrawingMode?.(true);
                  onSelectTool?.('eraser');
                } else if (currentTool === 'eraser') {
                  onToggleDrawingMode?.(false);
                } else {
                  onSelectTool?.('eraser');
                }
              }}
              className={`px-2 py-1 rounded-lg flex items-center gap-1 transition ${
                isDrawingMode && currentTool === 'eraser'
                  ? 'bg-rose-500 text-white font-semibold shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
              title="Tẩy nét thông minh (Phím E)"
            >
              <Eraser size={12} />
              <span className="hidden xl:inline">Tẩy (E)</span>
            </button>

            {/* Bảng chọn 5 màu sư phạm (ẩn khi đang chọn tẩy nét) */}
            {isDrawingMode && currentTool !== 'eraser' && onSelectColor && (
              <div className="flex items-center gap-1 pl-1.5 border-l border-slate-800">
                {PEDAGOGICAL_COLORS.map((c) => (
                  <button
                    key={c.id}
                    type="button"
                    onClick={() => onSelectColor(c.value)}
                    className={`w-3.5 h-3.5 rounded-full transition transform hover:scale-125 ${
                      drawingColor === c.value ? 'ring-2 ring-offset-1 ring-offset-slate-900 ring-white scale-110' : 'opacity-70 hover:opacity-100'
                    }`}
                    style={{ backgroundColor: c.value }}
                    title={c.name}
                  />
                ))}
              </div>
            )}
          </div>

          {/* ================= 3.6. HOÀN TÁC (UNDO), LÀM LẠI (REDO) & XÓA TOÀN BỘ (TASK 17.3) ================= */}
          <div className="flex items-center gap-0.5 bg-slate-900/90 border border-slate-800 rounded-xl p-0.5 text-xs">
            {/* Nút Hoàn tác (Undo - Ctrl+Z) */}
            <button
              type="button"
              onClick={onUndo}
              disabled={!canUndo}
              className="p-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 disabled:opacity-30 disabled:pointer-events-none transition"
              title="Hoàn tác nét vẽ vừa thao tác (Ctrl+Z)"
            >
              <Undo2 size={13} />
            </button>

            {/* Nút Làm lại (Redo - Ctrl+Y) */}
            <button
              type="button"
              onClick={onRedo}
              disabled={!canRedo}
              className="p-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 disabled:opacity-30 disabled:pointer-events-none transition"
              title="Làm lại thao tác vừa hoàn tác (Ctrl+Y)"
            >
              <Redo2 size={13} />
            </button>

            {/* Nút Xóa toàn bộ nét vẽ của slide */}
            <button
              type="button"
              onClick={onClearCanvas}
              disabled={!hasStrokes}
              className="p-1.5 rounded-lg text-rose-400 hover:text-rose-200 hover:bg-rose-950/60 disabled:opacity-30 disabled:pointer-events-none transition"
              title="Xóa toàn bộ nét vẽ của slide hiện tại"
            >
              <Trash2 size={13} />
            </button>
          </div>

          {/* ================= 3.7. BẢNG PHỤ TOÀN MÀN HÌNH (TASK 17.4) ================= */}
          {onToggleWhiteboard && (
            <button
              type="button"
              onClick={() => onToggleWhiteboard(!isWhiteboardOpen)}
              className={`px-2.5 py-1.5 rounded-xl border text-xs font-semibold flex items-center gap-1.5 transition shadow-sm ${
                isWhiteboardOpen
                  ? 'bg-indigo-600 border-indigo-400 text-white ring-2 ring-indigo-500/50 shadow-indigo-950/60'
                  : 'bg-slate-900/90 hover:bg-slate-800 border-slate-800 text-slate-300 hover:text-white'
              }`}
              title="Mở Bảng phụ toàn màn hình để viết nháp/giải toán (Phím W)"
            >
              <Grid3X3 size={13} className={isWhiteboardOpen ? 'text-white' : 'text-indigo-400'} />
              <span className="hidden sm:inline">Bảng (W)</span>
            </button>
          )}

          {/* Dải phân cách dọc */}
          <div className="h-5 w-px bg-slate-800" />

          {/* ================= 4. TỐI MÀN HÌNH (B) & THOÁT (ESC) ================= */}
          <div className="flex items-center gap-1.5">
            {onToggleBlackout && (
              <button
                onClick={() => onToggleBlackout(!isBlackout)}
                className={`px-2.5 py-1 rounded-xl border text-xs font-semibold flex items-center gap-1.5 transition shadow-sm ${
                  isBlackout
                    ? 'bg-amber-500/30 border-amber-500 text-amber-200'
                    : 'bg-slate-900/90 hover:bg-slate-800 border-slate-800 text-slate-300 hover:text-white'
                }`}
                title="Làm tối màn hình để học sinh tập trung vào lời giảng (Phím B)"
              >
                <Moon size={13} />
                <span className="hidden sm:inline">Tối (B)</span>
              </button>
            )}

            {onExitPresentation && (
              <button
                onClick={onExitPresentation}
                className="px-2.5 py-1 rounded-xl bg-rose-500/20 hover:bg-rose-500/30 border border-rose-500/60 text-rose-300 text-xs font-semibold flex items-center gap-1.5 transition shadow-sm"
                title="Thoát Chế độ Trình chiếu (Phím Esc hoặc F5)"
              >
                <Minimize2 size={13} />
                <span className="hidden sm:inline">Thoát</span>
                <kbd className="hidden md:inline px-1 py-0.2 bg-rose-950/80 border border-rose-700/60 rounded text-[9px] font-mono">
                  Esc
                </kbd>
              </button>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
