/**
 * Quadratic Bezier Curve Smoothing & Inking Toolkit - Task 17.2
 *
 * Thuật toán làm mượt nét vẽ và bảng công cụ bút sư phạm:
 * - Nội suy đường cong Bezier bậc 2 (Quadratic Bezier Interpolation) biến các chuỗi điểm rời rạc
 *   thành nét cong trơn tru, loại bỏ 100% hiện tượng nét vẽ gấp khúc góc cạnh (polygonization).
 * - Hỗ trợ phân biệt Bút Mực Thường (Pen - nét thanh mảnh, alpha 1.0) và Bút Dạ Quang (Highlighter - nét rộng, alpha 0.35).
 * - Bảng 5 màu sư phạm chuẩn mực cho môn Toán THPT.
 * - Điều chỉnh độ dày nét theo lực nhấn bút cảm ứng (Pressure Sensitivity).
 */

export const PEDAGOGICAL_COLORS = [
  { id: 'red', name: 'Đỏ Lưu Ý', value: '#ef4444', ring: 'ring-rose-500', hexName: 'Rose Red' },
  { id: 'yellow', name: 'Vàng Điểm Nhấn', value: '#f59e0b', ring: 'ring-amber-500', hexName: 'Amber Yellow' },
  { id: 'green', name: 'Xanh Kết Luận', value: '#10b981', ring: 'ring-emerald-500', hexName: 'Emerald Green' },
  { id: 'cyan', name: 'Xanh Hình Học', value: '#38bdf8', ring: 'ring-sky-400', hexName: 'Sky Blue' },
  { id: 'white', name: 'Trắng Phấn Bảng', value: '#f8fafc', ring: 'ring-white', hexName: 'Chalk White' }
];

export const TOOL_PRESETS = {
  pen: {
    id: 'pen',
    name: 'Bút Viết Mực',
    defaultSize: 3,
    minSize: 1,
    maxSize: 8,
    alpha: 1.0,
    compositeOperation: 'source-over'
  },
  highlighter: {
    id: 'highlighter',
    name: 'Bút Dạ Quang',
    defaultSize: 20,
    minSize: 12,
    maxSize: 36,
    alpha: 0.35,
    compositeOperation: 'source-over'
  }
};

/**
 * Tính toán độ dày biến thiên dựa trên lực nhấn bút Stylus
 */
export function getAdjustedLineWidth(baseSize = 3, pressure = 0.5) {
  if (typeof pressure !== 'number' || pressure <= 0) return baseSize;
  // Hệ số biến thiên từ 0.6x đến 1.4x tùy theo lực nhấn
  return baseSize * (0.6 + pressure * 0.8);
}

/**
 * Vẽ một nét vẽ mượt mà bằng giải thuật Quadratic Bezier Curve Interpolation
 */
export function drawSmoothStroke(ctx, stroke) {
  if (!ctx || !stroke || !Array.isArray(stroke.points) || stroke.points.length === 0) return;

  const pts = stroke.points;
  const isHighlighter = stroke.tool === 'highlighter';
  const strokeColor = stroke.color || '#ef4444';
  const baseSize = stroke.size || (isHighlighter ? 20 : 3);
  const alpha = isHighlighter ? 0.35 : (stroke.alpha !== undefined ? stroke.alpha : 1.0);

  ctx.save();
  ctx.strokeStyle = strokeColor;
  ctx.fillStyle = strokeColor;
  ctx.lineWidth = baseSize;
  ctx.globalAlpha = alpha;
  ctx.lineCap = isHighlighter ? 'square' : 'round';
  ctx.lineJoin = 'round';

  // 1. Nếu chỉ có đúng 1 điểm (chấm tròn hoặc vệt nhấn)
  if (pts.length === 1) {
    const p0 = pts[0];
    const dotRadius = (baseSize / 2) * (p0.pressure ? (0.6 + p0.pressure * 0.8) : 1);
    ctx.beginPath();
    ctx.arc(p0.x, p0.y, Math.max(1, dotRadius), 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
    return;
  }

  // 2. Nếu có 2 điểm: Nối đường thẳng ngắn
  if (pts.length === 2) {
    ctx.beginPath();
    ctx.moveTo(pts[0].x, pts[0].y);
    ctx.lineTo(pts[1].x, pts[1].y);
    ctx.stroke();
    ctx.restore();
    return;
  }

  // 3. Nếu từ 3 điểm trở lên: Áp dụng thuật toán Nội suy Bezier bậc 2 qua các trung điểm
  ctx.beginPath();
  ctx.moveTo(pts[0].x, pts[0].y);

  for (let i = 1; i < pts.length - 1; i++) {
    const current = pts[i];
    const next = pts[i + 1];

    // Tính trung điểm Mi giữa điểm hiện tại và điểm kế tiếp
    const midX = (current.x + next.x) / 2;
    const midY = (current.y + next.y) / 2;

    // Đường cong Bezier bậc 2 với điểm hiện tại làm điểm điều khiển (Control Point)
    ctx.quadraticCurveTo(current.x, current.y, midX, midY);
  }

  // Nối đoạn cuối cùng đến điểm kết thúc
  const last = pts[pts.length - 1];
  ctx.lineTo(last.x, last.y);
  ctx.stroke();

  ctx.restore();
}
