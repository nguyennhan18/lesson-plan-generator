/**
 * eraserHitTesting.js (Task 17.3)
 * Tiện ích kiểm tra va chạm hình học (Geometric Hit-Testing) & Tẩy nét thông minh (Stroke-Level Eraser)
 * Dành cho Hệ thống Bút vẽ & Chú thích Sư phạm Toán học THPT (GDPT 2018).
 *
 * Khác với Pixel Eraser (dùng destination-out làm vỡ vụn pixel và để lại hàng ngàn điểm rác),
 * Stroke-Level Eraser (Object Eraser) coi mỗi nét vẽ là một thực thể hình học độc lập (Geometric Entity).
 * Khi đầu tẩy di chuyển qua bất kỳ phân đoạn nào của nét vẽ, toàn bộ nét vẽ đó sẽ được xóa sạch sẽ,
 * bảo toàn tính toàn vẹn của mô hình vector và hỗ trợ hoàn tác (Undo/Redo) chính xác 100%.
 */

/**
 * Tính khoảng cách Euclid ngắn nhất từ một điểm P(px, py) tới đoạn thẳng AB nối A(x1, y1) và B(x2, y2).
 * Sử dụng giải thuật hình chiếu vector trực giao (Orthogonal Vector Projection):
 * - Vector đoạn thẳng: v = B - A
 * - Vector nối từ A tới P: w = P - A
 * - Tích vô hướng c1 = w . v
 * - Bình phương độ dài c2 = v . v
 * 
 * @param {number} px - Tọa độ X của điểm kiểm tra (Eraser center X)
 * @param {number} py - Tọa độ Y của điểm kiểm tra (Eraser center Y)
 * @param {number} x1 - Tọa độ X của điểm đầu A
 * @param {number} y1 - Tọa độ Y của điểm đầu A
 * @param {number} x2 - Tọa độ X của điểm cuối B
 * @param {number} y2 - Tọa độ Y của điểm cuối B
 * @returns {number} Khoảng cách Euclid ngắn nhất (pixels)
 */
export function pointToSegmentDistance(px, py, x1, y1, x2, y2) {
  const vx = x2 - x1;
  const vy = y2 - y1;
  const wx = px - x1;
  const wy = py - y1;

  const c1 = wx * vx + wy * vy;
  const c2 = vx * vx + vy * vy;

  // Trường hợp đoạn thẳng suy biến thành 1 điểm duy nhất (A trùng B)
  if (c2 <= 0.000001) {
    const dx = px - x1;
    const dy = py - y1;
    return Math.sqrt(dx * dx + dy * dy);
  }

  // Trường hợp hình chiếu rơi ra ngoài về phía điểm đầu A (c1 <= 0)
  if (c1 <= 0) {
    const dx = px - x1;
    const dy = py - y1;
    return Math.sqrt(dx * dx + dy * dy);
  }

  // Trường hợp hình chiếu rơi ra ngoài về phía điểm cuối B (c2 <= c1)
  if (c2 <= c1) {
    const dx = px - x2;
    const dy = py - y2;
    return Math.sqrt(dx * dx + dy * dy);
  }

  // Trường hợp hình chiếu rơi vào bên trong đoạn thẳng AB (0 < c1 < c2)
  const t = c1 / c2;
  const projX = x1 + t * vx;
  const projY = y1 + t * vy;

  const dx = px - projX;
  const dy = py - projY;
  return Math.sqrt(dx * dx + dy * dy);
}

/**
 * Kiểm tra xem một đối tượng nét vẽ (Stroke) có bị chạm bởi đầu tẩy tròn hay không.
 *
 * @param {Object} stroke - Đối tượng nét vẽ { id, tool, color, size, points }
 * @param {number} eraserX - Tọa độ X của tâm đầu tẩy
 * @param {number} eraserY - Tọa độ Y của tâm đầu tẩy
 * @param {number} eraserRadius - Bán kính đầu tẩy (mặc định 16px)
 * @returns {boolean} True nếu đầu tẩy chạm vào bất kỳ đoạn nào của nét vẽ
 */
export function isStrokeHitByEraser(stroke, eraserX, eraserY, eraserRadius = 16) {
  if (!stroke || !stroke.points || stroke.points.length === 0) {
    return false;
  }

  // Bán kính va chạm hiệu dụng: bao gồm bán kính đầu tẩy + nửa độ dày nét vẽ
  const strokeHalfWidth = (stroke.size || 3) / 2;
  const threshold = eraserRadius + strokeHalfWidth;

  // Trường hợp nét chỉ có 1 điểm duy nhất (click chấm đơn)
  if (stroke.points.length === 1) {
    const pt = stroke.points[0];
    const dx = eraserX - pt.x;
    const dy = eraserY - pt.y;
    return (dx * dx + dy * dy) <= (threshold * threshold);
  }

  // Kiểm tra từng đoạn thẳng liên tiếp nối giữa các điểm trong nét vẽ
  for (let i = 0; i < stroke.points.length - 1; i++) {
    const p1 = stroke.points[i];
    const p2 = stroke.points[i + 1];

    const dist = pointToSegmentDistance(eraserX, eraserY, p1.x, p1.y, p2.x, p2.y);
    if (dist <= threshold) {
      return true;
    }
  }

  return false;
}

/**
 * Tìm chỉ số của nét vẽ bị chạm đầu tiên (quét từ trên xuống dưới, tức nét vẽ mới nhất trước).
 *
 * @param {Array<Object>} strokes - Danh sách các nét vẽ hiện có trên slide
 * @param {number} eraserX - Tọa độ X của đầu tẩy
 * @param {number} eraserY - Tọa độ Y của đầu tẩy
 * @param {number} eraserRadius - Bán kính đầu tẩy
 * @returns {number} Chỉ số của nét vẽ trong mảng, hoặc -1 nếu không chạm nét nào
 */
export function findHitStrokeIndex(strokes, eraserX, eraserY, eraserRadius = 16) {
  if (!strokes || strokes.length === 0) return -1;

  for (let i = strokes.length - 1; i >= 0; i--) {
    if (isStrokeHitByEraser(strokes[i], eraserX, eraserY, eraserRadius)) {
      return i;
    }
  }

  return -1;
}

/**
 * Loại bỏ toàn bộ các nét vẽ bị chạm bởi đầu tẩy trong một lượt quét.
 *
 * @param {Array<Object>} strokes - Danh sách các nét vẽ hiện có
 * @param {number} eraserX - Tọa độ X của đầu tẩy
 * @param {number} eraserY - Tọa độ Y của đầu tẩy
 * @param {number} eraserRadius - Bán kính đầu tẩy
 * @returns {{ newStrokes: Array<Object>, erasedIds: Array<string>, hitCount: number }}
 */
export function removeHitStrokes(strokes, eraserX, eraserY, eraserRadius = 16) {
  if (!strokes || strokes.length === 0) {
    return { newStrokes: [], erasedIds: [], hitCount: 0 };
  }

  const erasedIds = [];
  const newStrokes = [];

  for (const stroke of strokes) {
    if (isStrokeHitByEraser(stroke, eraserX, eraserY, eraserRadius)) {
      erasedIds.push(stroke.id);
    } else {
      newStrokes.push(stroke);
    }
  }

  return {
    newStrokes,
    erasedIds,
    hitCount: erasedIds.length
  };
}
