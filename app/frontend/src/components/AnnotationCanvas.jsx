import React, { useRef, useEffect, useState, useCallback } from 'react';
import {
  getCanvasPoint,
  setupHighDpiCanvas,
  createStroke,
  redrawAllStrokes
} from '../utils/drawingCanvasHelper';
import { drawSmoothStroke } from '../utils/bezierSmoothing';
import { removeHitStrokes, isStrokeHitByEraser } from '../utils/eraserHitTesting';

/**
 * AnnotationCanvas (Task 17.1, 17.2, 17.3)
 * Lớp Canvas vẽ chú thích kỹ thuật số phủ toàn màn hình slide (Fullscreen Digital Inking Layer):
 * - Hỗ trợ chuẩn màn hình High-DPI / Retina qua window.devicePixelRatio.
 * - Bắt sự kiện Pointer Events đa nền tảng: Chuột (Mouse), Cảm ứng đa điểm (Touch), Bút thông minh (Stylus Pen / Apple Pencil).
 * - Thuật toán làm mượt nét vẽ Quadratic Bezier Interpolation (0ms latency, không gãy góc).
 * - Phân biệt Bút mực thường (Pen), Bút dạ quang (Highlighter) với alpha 0.35 và Công cụ tẩy nét (Stroke Eraser).
 * - Tẩy nét thông minh (Stroke-Level Eraser): Hit-testing khoảng cách Euclid trực giao tới từng đoạn thẳng nét vẽ.
 * - Quản lý cấu trúc dữ liệu đường nét (Stroke Data Model) phân tách theo từng Slide với lịch sử Undo/Redo.
 * - Khi isActive = false: Tự động chuyển pointer-events-none để không chặn click của nút bấm và mô hình 3D bên dưới.
 * - Khi isActive = true: Kích hoạt pointer-events-auto và con trỏ phù hợp với từng công cụ.
 */
export default function AnnotationCanvas({
  isActive = false,
  tool = 'pen',
  color = '#ef4444',
  size = 3,
  slideIndex = 0,
  strokes = [],
  onStrokesChange,
  onEraseStroke,
  isPresentationMode = false,
  eraserRadius = 18
}) {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);
  const currentStrokeRef = useRef(null);
  const isDrawingRef = useRef(false);
  const isErasingRef = useRef(false);
  const initialStrokesRef = useRef([]);
  const workingStrokesRef = useRef([]);
  const [dimensions, setDimensions] = useState({ width: 800, height: 450 });
  const [eraserCursor, setEraserCursor] = useState({ x: 0, y: 0, visible: false });

  // 1. Cấu hình kích thước và High-DPI Canvas khi container thay đổi kích thước
  const updateCanvasDimensions = useCallback(() => {
    const container = containerRef.current;
    const canvas = canvasRef.current;
    if (!container || !canvas) return;

    const rect = container.getBoundingClientRect();
    const w = Math.max(100, Math.round(rect.width));
    const h = Math.max(100, Math.round(rect.height));

    setDimensions({ width: w, height: h });
    const ctx = setupHighDpiCanvas(canvas, w, h);

    // Vẽ lại toàn bộ các nét vẽ hiện có của slide này
    if (ctx) {
      redrawAllStrokes(ctx, strokes, w, h);
    }
  }, [strokes]);

  // Lắng nghe ResizeObserver của container cha
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    updateCanvasDimensions();

    const resizeObserver = new ResizeObserver(() => {
      updateCanvasDimensions();
    });

    resizeObserver.observe(container);

    return () => {
      resizeObserver.disconnect();
    };
  }, [updateCanvasDimensions, isPresentationMode]);

  // Vẽ lại toàn bộ nét vẽ khi danh sách strokes hoặc slideIndex thay đổi
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (ctx) {
      redrawAllStrokes(ctx, strokes, dimensions.width, dimensions.height);
    }
  }, [strokes, slideIndex, dimensions]);

  // 2. BẮT ĐẦU VẼ HOẶC TẨY (Pointer Down)
  const handlePointerDown = (e) => {
    if (!isActive) return;
    // Chỉ nhận nút chuột chính (Primary Button)
    if (e.button !== undefined && e.button !== 0 && e.pointerType === 'mouse') return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    e.preventDefault();
    try {
      e.target.setPointerCapture(e.pointerId);
    } catch (_) {}

    const pt = getCanvasPoint(e, canvas);

    // ================= XỬ LÝ CÔNG CỤ TẨY NÉT (ERASER) =================
    if (tool === 'eraser') {
      const currentList = strokes || [];
      initialStrokesRef.current = [...currentList];
      workingStrokesRef.current = [...currentList];
      isErasingRef.current = true;
      setEraserCursor({ x: pt.x, y: pt.y, visible: true });

      const result = removeHitStrokes(workingStrokesRef.current, pt.x, pt.y, eraserRadius);
      if (result.hitCount > 0) {
        workingStrokesRef.current = result.newStrokes;
        if (onEraseStroke && result.erasedIds.length > 0) {
          result.erasedIds.forEach((id) => onEraseStroke(id));
        }
        const ctx = canvas.getContext('2d');
        if (ctx) {
          redrawAllStrokes(ctx, result.newStrokes, dimensions.width, dimensions.height);
        }
      }
      return;
    }

    // ================= XỬ LÝ CÔNG CỤ VẼ (PEN / HIGHLIGHTER) =================
    const newStroke = createStroke({
      tool,
      color,
      size,
      slideIndex
    });

    newStroke.points.push(pt);
    currentStrokeRef.current = newStroke;
    isDrawingRef.current = true;

    // Vẽ ngay điểm đầu tiên (chấm tròn nhỏ)
    const ctx = canvas.getContext('2d');
    if (ctx) {
      ctx.save();
      ctx.strokeStyle = newStroke.color;
      ctx.fillStyle = newStroke.color;
      ctx.lineWidth = newStroke.size;
      ctx.globalAlpha = newStroke.alpha;
      ctx.lineCap = newStroke.tool === 'highlighter' ? 'square' : 'round';
      ctx.lineJoin = 'round';

      ctx.beginPath();
      ctx.arc(pt.x, pt.y, newStroke.size / 2, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }
  };

  // 3. ĐANG VẼ HOẶC TẨY (Pointer Move)
  const handlePointerMove = (e) => {
    if (!isActive) return;
    const canvas = canvasRef.current;
    if (!canvas) return;

    const pt = getCanvasPoint(e, canvas);

    // Cập nhật vị trí con trỏ đầu tẩy
    if (tool === 'eraser') {
      setEraserCursor({ x: pt.x, y: pt.y, visible: true });

      // Nếu đang ấn giữ để quét tẩy
      if (isErasingRef.current) {
        e.preventDefault();
        const result = removeHitStrokes(workingStrokesRef.current, pt.x, pt.y, eraserRadius);
        if (result.hitCount > 0) {
          workingStrokesRef.current = result.newStrokes;
          if (onEraseStroke && result.erasedIds.length > 0) {
            result.erasedIds.forEach((id) => onEraseStroke(id));
          }
          const ctx = canvas.getContext('2d');
          if (ctx) {
            redrawAllStrokes(ctx, result.newStrokes, dimensions.width, dimensions.height);
          }
        }
      }
      return;
    }

    // Đang vẽ nét (Pen / Highlighter)
    if (!isDrawingRef.current || !currentStrokeRef.current) return;

    e.preventDefault();
    const currentStroke = currentStrokeRef.current;
    const pts = currentStroke.points;

    pts.push(pt);

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.save();
    ctx.strokeStyle = currentStroke.color;
    ctx.lineWidth = currentStroke.size;
    ctx.globalAlpha = currentStroke.alpha;
    ctx.lineCap = currentStroke.tool === 'highlighter' ? 'square' : 'round';
    ctx.lineJoin = 'round';

    if (pts.length === 2) {
      // Đoạn nối ban đầu giữa 2 điểm đầu tiên
      ctx.beginPath();
      ctx.moveTo(pts[0].x, pts[0].y);
      ctx.lineTo(pts[1].x, pts[1].y);
      ctx.stroke();
    } else if (pts.length >= 3) {
      // Vẽ đoạn cong Bezier mượt mà từ trung điểm trước tới trung điểm sau
      const pPrev = pts[pts.length - 2];
      const pCurr = pts[pts.length - 1];
      const pBefore = pts[pts.length - 3];

      const mid1X = (pBefore.x + pPrev.x) / 2;
      const mid1Y = (pBefore.y + pPrev.y) / 2;
      const mid2X = (pPrev.x + pCurr.x) / 2;
      const mid2Y = (pPrev.y + pCurr.y) / 2;

      ctx.beginPath();
      ctx.moveTo(mid1X, mid1Y);
      ctx.quadraticCurveTo(pPrev.x, pPrev.y, mid2X, mid2Y);
      ctx.stroke();
    }

    ctx.restore();
  };

  // 4. KẾT THÚC VẼ HOẶC TẨY (Pointer Up / Cancel)
  const handlePointerUp = (e) => {
    e.preventDefault();

    try {
      e.target.releasePointerCapture(e.pointerId);
    } catch (_) {}

    // Kết thúc lượt tẩy
    if (tool === 'eraser') {
      if (isErasingRef.current) {
        isErasingRef.current = false;
        const prev = initialStrokesRef.current;
        const curr = workingStrokesRef.current;
        if (curr.length !== prev.length && onStrokesChange) {
          onStrokesChange(curr, prev);
        }
      }
      return;
    }

    // Kết thúc lượt vẽ nét
    if (!isDrawingRef.current) return;

    const finishedStroke = currentStrokeRef.current;
    isDrawingRef.current = false;
    currentStrokeRef.current = null;

    if (finishedStroke && finishedStroke.points.length > 0) {
      const prev = strokes || [];
      const updated = [...prev, finishedStroke];
      if (onStrokesChange) {
        onStrokesChange(updated, prev);
      }

      // Làm mới toàn bộ canvas bằng thuật toán Bezier toàn vẹn
      const canvas = canvasRef.current;
      if (canvas) {
        const ctx = canvas.getContext('2d');
        if (ctx) {
          redrawAllStrokes(ctx, updated, dimensions.width, dimensions.height);
        }
      }
    }
  };

  const handlePointerLeave = () => {
    if (tool === 'eraser') {
      setEraserCursor((prev) => ({ ...prev, visible: false }));
    }
  };

  return (
    <div
      ref={containerRef}
      onPointerLeave={handlePointerLeave}
      className={`absolute inset-0 z-40 overflow-hidden ${
        isActive
          ? 'pointer-events-auto cursor-crosshair select-none touch-none'
          : 'pointer-events-none'
      }`}
    >
      <canvas
        ref={canvasRef}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerCancel={handlePointerUp}
        className="w-full h-full block"
      />

      {/* Hiển thị vòng tròn con trỏ tẩy nét khi đang ở chế độ Eraser */}
      {isActive && tool === 'eraser' && eraserCursor.visible && (
        <div
          className="pointer-events-none absolute rounded-full border-2 border-rose-400 bg-rose-500/25 shadow-lg shadow-rose-950/40"
          style={{
            width: eraserRadius * 2,
            height: eraserRadius * 2,
            left: eraserCursor.x - eraserRadius,
            top: eraserCursor.y - eraserRadius,
            transition: 'none'
          }}
        />
      )}
    </div>
  );
}
