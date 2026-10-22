/**
 * Solution Step Formatter Utility - Task 16.4
 *
 * Chuẩn hóa các bước giải tự luận chi tiết chuẩn SGK GDPT 2018:
 * - Trích xuất các bước từ slide.worked_solution_steps nếu đã có.
 * - Tự động tổng hợp 4 bước tự luận chuẩn mực (Giả thiết -> Công thức -> Biến đổi -> Kết luận)
 *   dựa trên quiz_options và main_definition_latex nếu slide chưa có worked_solution_steps.
 */

export function getNormalizedSolutionSteps(slide = {}) {
  // 1. Nếu slide đã có sẵn worked_solution_steps
  if (Array.isArray(slide.worked_solution_steps) && slide.worked_solution_steps.length > 0) {
    return slide.worked_solution_steps.map((step, idx) => {
      // Chuẩn hóa định dạng chuỗi nếu cần
      if (typeof step === 'string') return step;
      return step.text || `Bước ${idx + 1}: ${JSON.stringify(step)}`;
    });
  }

  // 2. Tự động trích xuất từ dữ liệu slide và phương án đúng
  const correctOpt = Array.isArray(slide.quiz_options)
    ? slide.quiz_options.find((opt) => opt.is_correct)
    : null;

  const correctLabel = correctOpt?.label || 'A';
  const correctFormula = correctOpt?.text || slide.main_definition_latex || 'Công thức chuẩn SGK';
  const questionContext = slide.bullet_points?.[0] || slide.title || 'Bài toán rèn luyện vận dụng.';

  return [
    `Bước 1 (Xác định giả thiết & Điều kiện): Phân tích dữ kiện bài toán: "${questionContext}". Xác định rõ các đại lượng đã cho và yêu cầu cần tìm.`,
    `Bước 2 (Vận dụng công thức định lý chuẩn SGK): Sử dụng công thức toán học trọng tâm: $${slide.main_definition_latex || correctFormula}$.`,
    `Bước 3 (Biến đổi đại số & Tính toán): Thay các giá trị giả thiết vào công thức và thực hiện các bước biến đổi tương đương chuẩn xác: $${correctFormula}$.`,
    `Bước 4 (Kết luận & Đối chiếu phương án): So sánh với 4 phương án đã cho, ta kết luận chọn phương án [${correctLabel}]: $${correctFormula}$.`
  ];
}

/**
 * Xuất toàn bộ lời giải thành văn bản Markdown thuần để sao chép vào vở ghi
 */
export function formatSolutionToClipboard(slide = {}, steps = []) {
  const title = slide.title || 'Câu hỏi trắc nghiệm tương tác';
  const lines = [
    `# LỜI GIẢI CHI TIẾT CHUẨN MỰC SGK - BÀI HỌC TOÁN THPT`,
    `Đề bài: ${slide.bullet_points?.[0] || title}`,
    `--------------------------------------------------`,
    ...steps.map((st, i) => `${i + 1}. ${st}`),
    `--------------------------------------------------`,
    `Chuẩn kiến thức: Công văn 5512/BGDĐT - Chương trình GDPT 2018`
  ];
  return lines.join('\n\n');
}
