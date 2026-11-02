/**
 * Misconception Classifier & Pedagogical Advice - Task 16.3
 *
 * Thuật toán phân loại bẫy sai lầm Toán học THPT dựa trên nội dung distractor_rationale:
 * - SIGN_ERROR: Lỗi dấu đại số (nhầm dấu +, -, chuyển vế đổi dấu).
 * - DOMAIN_ERROR: Lỗi điều kiện xác định (quên mẫu số khác 0, căn bậc hai >= 0, logarit > 0).
 * - FORMULA_ERROR: Lỗi nhầm lẫn công thức định lý (nhầm chỉ số n và n-1, hằng đẳng thức).
 * - GEOMETRY_ERROR: Lỗi trực quan hình học không gian (nhầm đường cao, góc, mặt phẳng).
 * - CALCULATION_ERROR: Lỗi tính toán số học & biến đổi tương đương.
 */

export const MISCONCEPTION_TYPES = {
  SIGN_ERROR: {
    id: 'SIGN_ERROR',
    title: 'Lỗi Biến Đổi Dấu Đại Số',
    badgeClass: 'bg-rose-500/20 text-rose-300 border-rose-500/50',
    iconColor: 'text-rose-400',
    advice: 'Cẩn thận khi chuyển vế hoặc nhân chia hai vế với số âm. Luôn kiểm tra lại dấu của từng hạng tử trước khi kết luận.'
  },
  DOMAIN_ERROR: {
    id: 'DOMAIN_ERROR',
    title: 'Lỗi Thiếu Điều Kiện Xác Định',
    badgeClass: 'bg-amber-500/20 text-amber-300 border-amber-500/50',
    iconColor: 'text-amber-400',
    advice: 'Luôn tìm điều kiện xác định (mẫu khác 0, biểu thức dưới căn bậc hai không âm) trước khi thực hiện các phép biến đổi hệ quả.'
  },
  FORMULA_ERROR: {
    id: 'FORMULA_ERROR',
    title: 'Lỗi Nhầm Lẫn Công Thức & Chỉ Số',
    badgeClass: 'bg-violet-500/20 text-violet-300 border-violet-500/50',
    iconColor: 'text-violet-400',
    advice: 'Đọc kỹ giả thiết đề bài, phân biệt rõ các chỉ số (ví dụ n so với n-1 trong cấp số cộng/nhân) trước khi thay số vào công thức.'
  },
  GEOMETRY_ERROR: {
    id: 'GEOMETRY_ERROR',
    title: 'Lỗi Trực Quan Hình Học Không Gian',
    badgeClass: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/50',
    iconColor: 'text-cyan-400',
    advice: 'Vẽ hình chuẩn xác, xác định đúng chân đường vuông góc và hình chiếu để tránh nhầm lẫn giữa đường sinh, chiều cao và cạnh bên.'
  },
  CALCULATION_ERROR: {
    id: 'CALCULATION_ERROR',
    title: 'Lỗi Tính Toán & Biến Đổi Đại Số',
    badgeClass: 'bg-slate-700/60 text-slate-300 border-slate-600',
    iconColor: 'text-slate-400',
    advice: 'Thực hiện từng bước biến đổi cẩn thận hoặc thử lại bằng các giá trị nghiệm đặc biệt để kiểm chứng kết quả.'
  }
};

/**
 * Phân tích văn bản distractor_rationale và phân loại bẫy sai lầm
 */
export function classifyMisconception(rationaleText = '', optionText = '') {
  const combined = `${rationaleText} ${optionText}`.toLowerCase();

  // 1. Kiểm tra lỗi dấu đại số
  if (
    combined.includes('dấu') ||
    combined.includes('nhầm dấu') ||
    combined.includes('đổi dấu') ||
    combined.includes('dấu trừ') ||
    combined.includes('dấu cộng') ||
    combined.includes('âm') ||
    combined.includes('dương')
  ) {
    return MISCONCEPTION_TYPES.SIGN_ERROR;
  }

  // 2. Kiểm tra lỗi điều kiện xác định
  if (
    combined.includes('điều kiện') ||
    combined.includes('tồn tại') ||
    combined.includes('mẫu số') ||
    combined.includes('mẫu') ||
    combined.includes('khác 0') ||
    combined.includes('trong căn') ||
    combined.includes('dưới căn') ||
    combined.includes('tập xác định') ||
    combined.includes('loại nghiệm')
  ) {
    return MISCONCEPTION_TYPES.DOMAIN_ERROR;
  }

  // 3. Kiểm tra lỗi trực quan hình học
  if (
    combined.includes('hình học') ||
    combined.includes('đường cao') ||
    combined.includes('chân đường cao') ||
    combined.includes('chiều cao') ||
    combined.includes('cạnh bên') ||
    combined.includes('đáy') ||
    combined.includes('vuông góc') ||
    combined.includes('song song') ||
    combined.includes('góc') ||
    combined.includes('khoảng cách')
  ) {
    return MISCONCEPTION_TYPES.GEOMETRY_ERROR;
  }

  // 4. Kiểm tra lỗi công thức định lý
  if (
    combined.includes('công thức') ||
    combined.includes('định lý') ||
    combined.includes('hằng đẳng thức') ||
    combined.includes('nhầm lẫn') ||
    combined.includes('áp dụng nhầm') ||
    combined.includes('số hạng') ||
    combined.includes('chỉ số') ||
    combined.includes('lũy thừa')
  ) {
    return MISCONCEPTION_TYPES.FORMULA_ERROR;
  }

  // 5. Mặc định: Lỗi tính toán chung
  return MISCONCEPTION_TYPES.CALCULATION_ERROR;
}
