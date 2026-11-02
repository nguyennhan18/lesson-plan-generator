/**
 * Task 9.2: Quản lý Đồng bộ 2 Chiều & Lưu trữ Cấu trúc Slide JSON trong Bộ nhớ Trình duyệt
 * (React In-Memory State <-> Browser sessionStorage / window.__LESSONAI_SLIDE_DECK_JSON__)
 */

export const SLIDE_DECK_STORAGE_KEY = 'lessonai_slide_deck_json_v1';

/**
 * Đọc cấu trúc Slide JSON từ bộ nhớ trình duyệt (sessionStorage) khi khởi tạo.
 * Nếu chưa có hoặc dữ liệu không hợp lệ, trả về bộ Slide mẫu mặc định (fallbackDeck).
 */
export function loadSlideDeckFromBrowserMemory(fallbackDeck) {
  if (typeof window === 'undefined') {
    return fallbackDeck;
  }
  try {
    const raw = window.sessionStorage.getItem(SLIDE_DECK_STORAGE_KEY);
    if (!raw) {
      return fallbackDeck;
    }
    const parsed = JSON.parse(raw);
    if (parsed && Array.isArray(parsed.slides) && parsed.slides.length > 0) {
      window.__LESSONAI_SLIDE_DECK_JSON__ = parsed;
      return parsed;
    }
  } catch {
    // Fallback an toàn nếu sessionStorage bị chặn hoặc JSON lỗi
  }
  return fallbackDeck;
}

/**
 * Lưu trữ cấu trúc Slide JSON hiện hành vào bộ nhớ trình duyệt (sessionStorage & biến toàn cục).
 */
export function saveSlideDeckToBrowserMemory(slideDeck) {
  if (typeof window === 'undefined' || !slideDeck || !Array.isArray(slideDeck.slides)) {
    return;
  }
  try {
    window.__LESSONAI_SLIDE_DECK_JSON__ = slideDeck;
    window.sessionStorage.setItem(SLIDE_DECK_STORAGE_KEY, JSON.stringify(slideDeck));
  } catch {
    // Bỏ qua nếu bộ nhớ trình duyệt đầy
  }
}

/**
 * Task 9.2: Cập nhật bất biến (Immutable Update) chuỗi LaTeX mới từ MathLive
 * vào đúng vị trí của cấu trúc Slide JSON đang lưu trữ trong bộ nhớ trình duyệt.
 *
 * @param {Object} slideDeck - Cấu trúc SlideDeck JSON hiện tại
 * @param {Object} payload - Thông tin vị trí và giá trị công thức mới
 * @param {number} payload.slideIndex - Chỉ số trang slide đang sửa (0-indexed)
 * @param {'main_definition_latex' | 'bullet_point'} payload.targetField - Trường mục tiêu trong Slide JSON
 * @param {number|null} payload.bulletIndex - Chỉ số dòng bullet_points (nếu targetField === 'bullet_point')
 * @param {string} payload.formattedLatex - Chuỗi LaTeX hoàn chỉnh (kèm delimiter $ / $$ và ngữ cảnh câu)
 * @param {string} [payload.rawExpandedLatex] - Chuỗi LaTeX nguyên bản trích xuất từ getValue('latex-expanded')
 * @returns {Object} Bản sao SlideDeck JSON mới đã cập nhật và lưu vào bộ nhớ trình duyệt
 */
export function updateSlideFormulaInDeck(
  slideDeck,
  {
    slideIndex,
    targetField = 'main_definition_latex',
    bulletIndex = null,
    formattedLatex = '',
    rawExpandedLatex = ''
  } = {}
) {
  if (!slideDeck || !Array.isArray(slideDeck.slides) || !slideDeck.slides[slideIndex]) {
    return slideDeck;
  }

  const updatedSlides = [...slideDeck.slides];
  const targetSlide = { ...updatedSlides[slideIndex] };

  if (targetField === 'main_definition_latex') {
    targetSlide.main_definition_latex = formattedLatex;
  } else if (targetField === 'bullet_point' && typeof bulletIndex === 'number') {
    const updatedBullets = [...(targetSlide.bullet_points || [])];
    if (bulletIndex >= 0 && bulletIndex < updatedBullets.length) {
      updatedBullets[bulletIndex] = formattedLatex;
    }
    targetSlide.bullet_points = updatedBullets;
  }

  targetSlide.last_formula_updated_at = new Date().toISOString();
  targetSlide.last_updated_field = targetField;
  if (rawExpandedLatex) {
    targetSlide.last_expanded_latex = rawExpandedLatex;
  }

  updatedSlides[slideIndex] = targetSlide;

  const updatedDeck = {
    ...slideDeck,
    last_synced_at: new Date().toISOString(),
    slides: updatedSlides
  };

  saveSlideDeckToBrowserMemory(updatedDeck);
  return updatedDeck;
}

// ================= TASK 17.4: LƯU TRỮ VÀ ĐỒNG BỘ TRẠNG THÁI VẼ THEO TỪNG SLIDE =================
export const SLIDE_DRAWINGS_STORAGE_KEY = 'lessonai_slide_drawings_v1';

/**
 * Đọc toàn bộ dữ liệu nét vẽ (slideDrawingsMap) của bộ bài giảng từ bộ nhớ trình duyệt.
 * @param {string} deckId - Mã định danh của bộ bài giảng
 * @returns {Object} Bản đồ các nét vẽ { [slideIndex]: Stroke[] }
 */
export function loadSlideDrawingsFromStorage(deckId = 'default') {
  if (typeof window === 'undefined') return {};
  try {
    const raw = window.sessionStorage.getItem(`${SLIDE_DRAWINGS_STORAGE_KEY}_${deckId}`);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (parsed && typeof parsed === 'object') {
        return parsed;
      }
    }
  } catch {
    // Bỏ qua lỗi parse
  }
  return {};
}

/**
 * Lưu trữ trạng thái nét vẽ hiện thời theo từng slide vào bộ nhớ trình duyệt.
 * @param {Object} drawingsMap - Bản đồ các nét vẽ { [slideIndex]: Stroke[] }
 * @param {string} deckId - Mã định danh của bộ bài giảng
 */
export function saveSlideDrawingsToStorage(drawingsMap, deckId = 'default') {
  if (typeof window === 'undefined' || !drawingsMap) return;
  try {
    window.sessionStorage.setItem(`${SLIDE_DRAWINGS_STORAGE_KEY}_${deckId}`, JSON.stringify(drawingsMap));
  } catch {
    // Bỏ qua lỗi quota
  }
}

/**
 * Xóa sạch dữ liệu vẽ lưu trữ của bộ bài giảng.
 * @param {string} deckId - Mã định danh của bộ bài giảng
 */
export function clearSlideDrawingsFromStorage(deckId = 'default') {
  if (typeof window === 'undefined') return;
  try {
    window.sessionStorage.removeItem(`${SLIDE_DRAWINGS_STORAGE_KEY}_${deckId}`);
  } catch {
    // Bỏ qua
  }
}

