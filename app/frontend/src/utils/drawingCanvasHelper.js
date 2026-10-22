/**
 * Drawing Canvas Helper Utilities - Task 17.1
 *
 * Tiện ích hỗ trợ hệ thống vẽ tương tác (Interactive Inking):
 * - Chuyển đổi tọa độ con trỏ màn hình sang tọa độ Canvas chính xác theo tỉ lệ co giãn (CSS vs Internal Resolution).
 * - Cấu hình Canvas độ nét cao (High-DPI / Retina Scaling) với window.devicePixelRatio.
 * - Khởi tạo mô hình dữ liệu đường nét Stroke theo chuẩn JSON cấu trúc.
 * - Render các nét vẽ với độ dày và màu sắc tùy biến.
 */

import { drawSmoothStroke } from './bezierSmoothing';

/**
 * Lấy tọa độ chuẩn xác của con trỏ trên Canvas kèm lực nhấn (pressure)
 */
export function getCanvasPoint(e, canvas) {
  if (!canvas) return { x: 0, y: 0, pressure: 0.5 };

  const rect = canvas.getBoundingClientRect();
  const scaleX = canvas.width / (rect.width || 1);
  const scaleY = canvas.height / (rect.height || 1);

  const clientX = e.clientX !== undefined ? e.clientX : (e.touches?.[0]?.clientX ?? 0);
  const clientY = e.clientY !== undefined ? e.clientY : (e.touches?.[0]?.clientY ?? 0);

  // Ánh xạ tọa độ client sang tọa độ logic của canvas
  const x = (clientX - rect.left);
  const y = (clientY - rect.top);

  // Lực nhấn bút cảm ứng (Apple Pencil / Stylus hỗ trợ e.pressure từ 0.0 đến 1.0)
  let pressure = 0.5;
  if (typeof e.pressure === 'number' && e.pressure > 0) {
    pressure = e.pressure;
  }

  return { x, y, pressure };
}

/**
 * Cấu hình canvas theo độ phân giải màn hình Retina (High-DPI)
 */
export function setupHighDpiCanvas(canvas, width, height) {
  if (!canvas) return null;

  const dpr = typeof window !== 'undefined' ? (window.devicePixelRatio || 1) : 1;
  const ctx = canvas.getContext('2d');
  if (!ctx) return null;

  canvas.width = Math.round(width * dpr);
  canvas.height = Math.round(height * dpr);
  canvas.style.width = `${width}px`;
  canvas.style.height = `${height}px`;

  // Scale hệ tọa độ theo DPR để vẽ các điểm bằng kích thước CSS pixel logic
  ctx.scale(dpr, dpr);
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';

  return ctx;
}

/**
 * Khởi tạo đối tượng nét vẽ mới (Stroke Data Model)
 */
export function createStroke({
  tool = 'pen',
  color = '#ef4444',
  size = 3,
  alpha = 1.0,
  slideIndex = 0
} = {}) {
  const id = `stroke_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
  const isHighlighter = tool === 'highlighter';

  return {
    id,
    tool,
    color,
    size: isHighlighter ? Math.max(size, 16) : size,
    alpha: isHighlighter ? 0.35 : alpha,
    compositeOperation: isHighlighter ? 'source-over' : 'source-over',
    points: [],
    slideIndex
  };
}

/**
 * Vẽ lại toàn bộ danh sách nét vẽ lên canvas
 */
export function redrawAllStrokes(ctx, strokes = [], width, height) {
  if (!ctx) return;

  ctx.clearRect(0, 0, width, height);

  for (let i = 0; i < strokes.length; i++) {
    const stroke = strokes[i];
    if (!stroke || !Array.isArray(stroke.points) || stroke.points.length === 0) continue;
    drawSmoothStroke(ctx, stroke);
  }
}
