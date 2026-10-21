/**
 * Task 10.4: Client-side & Hybrid API Connector cho Bộ lọc Kiểm duyệt Sư phạm (AI Linter & Proofreader)
 * - Kết nối trực tiếp tới Backend API `POST /api/v1/validation/audit-deck` (Task 10.1, 10.2, 10.3).
 * - Tích hợp bộ quét nhanh tại trình duyệt (Zero-Latency Local Linter) để biểu tượng ⚠️ màu vàng
 *   phản hồi tức thì ngay khi Giáo viên sửa nội dung trên Slide hoặc trong Xưởng Biên Tập.
 * - Tuân thủ nghiêm ngặt nguyên tắc Human-in-the-Loop: Chỉ phát hiện và gợi ý, KHÔNG tự ý ghi đè bài của GV.
 */

const VIETNAMESE_TYPO_RULES = [
  ['học xinh', 'học sinh', "Sai phụ âm đầu x/s trong từ 'học sinh'"],
  ['giáo giục', 'giáo dục', "Sai phụ âm đầu gi/d trong từ 'giáo dục'"],
  ['phương chình', 'phương trình', "Sai phụ âm đầu ch/tr trong thuật ngữ 'phương trình'"],
  ['bất phương chình', 'bất phương trình', "Sai phụ âm đầu ch/tr trong thuật ngữ 'bất phương trình'"],
  ['hệ phương chình', 'hệ phương trình', "Sai phụ âm đầu ch/tr trong thuật ngữ 'hệ phương trình'"],
  ['trứng minh', 'chứng minh', "Sai phụ âm đầu tr/ch trong thuật ngữ 'chứng minh'"],
  ['giả thuyết', 'giả thiết', "Trong bài toán/định lý Toán học phổ thông, phần cho trước gọi là 'giả thiết' (không phải 'giả thuyết')"],
  ['sác định', 'xác định', "Sai phụ âm đầu s/x trong thuật ngữ 'xác định'"],
  ['tập sác định', 'tập xác định', "Sai phụ âm đầu s/x trong thuật ngữ 'tập xác định'"],
  ['tham xố', 'tham số', "Sai phụ âm đầu x/s trong thuật ngữ 'tham số'"],
  ['hằn đẳng thức', 'hằng đẳng thức', "Thiếu âm cuối 'g' trong thuật ngữ 'hằng đẳng thức'"],
  ['hằng đẵng thức', 'hằng đẳng thức', "Sai dấu thanh hỏi/ngã trong thuật ngữ 'hằng đẳng thức'"],
  ['bất đẵng thức', 'bất đẳng thức', "Sai dấu thanh hỏi/ngã trong thuật ngữ 'bất đẳng thức'"],
  ['vô ngiệm', 'vô nghiệm', "Sai quy tắc chính tả ng/ngh trước nguyên âm 'i' ('vô nghiệm')"],
  ['ngiệm kép', 'nghiệm kép', "Sai quy tắc chính tả ng/ngh trước nguyên âm 'i' ('nghiệm kép')"],
  ['ngiệm phân biệt', 'nghiệm phân biệt', "Sai quy tắc chính tả ng/ngh trước nguyên âm 'i' ('nghiệm phân biệt')"],
  ['đạo hàn', 'đạo hàm', "Sai âm cuối n/m trong thuật ngữ 'đạo hàm'"],
  ['nguyên hàn', 'nguyên hàm', "Sai âm cuối n/m trong thuật ngữ 'nguyên hàm'"],
  ['tít phân', 'tích phân', "Sai âm cuối t/ch trong thuật ngữ 'tích phân'"],
  ['tiệm cận ngan', 'tiệm cận ngang', "Thiếu âm cuối 'g' trong thuật ngữ 'tiệm cận ngang'"],
  ['tiệm cận đứn', 'tiệm cận đứng', "Thiếu âm cuối 'g' trong thuật ngữ 'tiệm cận đứng'"],
  ['cực chị', 'cực trị', "Sai phụ âm đầu ch/tr trong thuật ngữ 'cực trị'"],
  ['đồng biếng', 'đồng biến', "Dư âm cuối 'g' trong thuật ngữ 'đồng biến'"],
  ['nghịch biếng', 'nghịch biến', "Dư âm cuối 'g' trong thuật ngữ 'nghịch biến'"],
  ['ngịch biến', 'nghịch biến', "Sai quy tắc chính tả ng/ngh trước nguyên âm 'i' ('nghịch biến')"],
  ['tam giác câng', 'tam giác cân', "Dư âm cuối 'g' trong thuật ngữ 'tam giác cân'"],
  ['hình tróp', 'hình chóp', "Sai phụ âm đầu tr/ch trong thuật ngữ 'hình chóp'"],
  ['khối tróp', 'khối chóp', "Sai phụ âm đầu tr/ch trong thuật ngữ 'khối chóp'"],
  ['lăng chụ', 'lăng trụ', "Sai phụ âm đầu ch/tr trong thuật ngữ 'lăng trụ'"],
  ['năng trụ', 'lăng trụ', "Sai phụ âm đầu n/l trong thuật ngữ 'lăng trụ'"],
  ['mặt phẵng', 'mặt phẳng', "Sai dấu thanh hỏi/ngã trong thuật ngữ 'mặt phẳng'"],
  ['mặc phẳng', 'mặt phẳng', "Sai âm cuối c/t trong thuật ngữ 'mặt phẳng'"],
  ['vuông gốc', 'vuông góc', "Sai vần ốc/óc trong thuật ngữ 'vuông góc'"],
  ['xong xong', 'song song', "Sai phụ âm đầu x/s trong thuật ngữ 'song song'"],
  ['khoản cách', 'khoảng cách', "Thiếu âm cuối 'g' trong thuật ngữ 'khoảng cách'"],
  ['thể tít', 'thể tích', "Sai âm cuối t/ch trong thuật ngữ 'thể tích'"],
  ['diện tít', 'diện tích', "Sai âm cuối t/ch trong thuật ngữ 'diện tích'"],
  ['cấp xố cộng', 'cấp số cộng', "Sai phụ âm đầu x/s trong thuật ngữ 'cấp số cộng'"],
  ['cấp xố nhân', 'cấp số nhân', "Sai phụ âm đầu x/s trong thuật ngữ 'cấp số nhân'"],
  ['công xai', 'công sai', "Sai phụ âm đầu x/s trong thuật ngữ 'công sai'"],
  ['công bọi', 'công bội', "Sai nguyên âm o/ô trong thuật ngữ 'công bội'"],
  ['chục hoành', 'trục hoành', "Sai phụ âm đầu ch/tr trong thuật ngữ 'trục hoành'"],
  ['chục tung', 'trục tung', "Sai phụ âm đầu ch/tr trong thuật ngữ 'trục tung'"]
];

const REPEATED_WORDS = ['là', 'của', 'cho', 'với', 'trong', 'khi', 'thì', 'mà', 'và', 'các', 'những', 'được', 'có'];

const LOCAL_THEOREM_AND_ALGEBRA_RULES = [
  {
    regex: /\\Delta\s*(?!')\s*=\s*b\s*\^\s*\{?2\}?\s*\+\s*4\s*\*?\s*a\s*\*?\s*c/i,
    category: 'textbook_theorem',
    severity: 'error',
    title: 'Công thức biệt thức Delta (SGK Toán 10)',
    reason: 'Ghi nhầm dấu cộng (+ 4ac) trong công thức biệt thức \\Delta',
    suggestion: 'Theo SGK Toán GDPT 2018, công thức đúng phải là: $\\Delta = b^2 - 4ac$.'
  },
  {
    regex: /\\Delta\s*(?!')\s*=\s*b\s*-\s*4\s*\*?\s*a\s*\*?\s*c/i,
    category: 'textbook_theorem',
    severity: 'error',
    title: 'Công thức biệt thức Delta (SGK Toán 10)',
    reason: 'Thiếu số mũ bình phương (b^2) trong công thức biệt thức \\Delta',
    suggestion: 'Theo SGK Toán GDPT 2018, công thức đúng phải là: $\\Delta = b^2 - 4ac$.'
  },
  {
    regex: /\\Delta'\s*=\s*b'\s*\^\s*\{?2\}?\s*\+\s*a\s*\*?\s*c/i,
    category: 'textbook_theorem',
    severity: 'error',
    title: "Công thức biệt thức thu gọn Delta' (SGK Toán 10)",
    reason: "Ghi nhầm dấu cộng (+ ac) trong công thức biệt thức thu gọn \\Delta'",
    suggestion: "Theo SGK Toán GDPT 2018, công thức đúng phải là: $\\Delta' = b'^2 - ac$."
  },
  {
    regex: /\\frac\{\s*\+?\s*b\s*\\pm\s*\\sqrt\{\\Delta\}\s*\}\{\s*2\s*a\s*\}/,
    category: 'textbook_theorem',
    severity: 'error',
    title: 'Công thức nghiệm phương trình bậc hai (SGK Toán 10)',
    reason: 'Thiếu dấu âm (-) trước hệ số b trên tử số của công thức nghiệm',
    suggestion: 'Theo SGK Toán GDPT 2018, công thức đúng phải là: $x_{1,2} = \\frac{-b \\pm \\sqrt{\\Delta}}{2a}$.'
  },
  {
    regex: /\\frac\{\s*-\s*b\s*\\pm\s*\\sqrt\{\\Delta\}\s*\}\{\s*a\s*\}/,
    category: 'textbook_theorem',
    severity: 'error',
    title: 'Công thức nghiệm phương trình bậc hai (SGK Toán 10)',
    reason: 'Thiếu hệ số 2 ở mẫu số (2a) trong công thức nghiệm tổng quát',
    suggestion: 'Theo SGK Toán GDPT 2018, công thức đúng phải là: $x_{1,2} = \\frac{-b \\pm \\sqrt{\\Delta}}{2a}$.'
  },
  {
    regex: /x_\{?0\}?\s*=\s*\\frac\{\s*b\s*\}\{\s*2\s*a\s*\}/,
    category: 'textbook_theorem',
    severity: 'error',
    title: 'Công thức nghiệm kép phương trình bậc hai (SGK Toán 10)',
    reason: 'Thiếu dấu âm (-) trong công thức nghiệm kép / hoành độ đỉnh Parabol',
    suggestion: 'Theo SGK Toán GDPT 2018, công thức đúng phải là: $x_0 = -\\frac{b}{2a}$.'
  },
  {
    regex: /x_\{?1\}?\s*\+\s*x_\{?2\}?\s*=\s*\\frac\{\s*b\s*\}\{\s*a\s*\}/,
    category: 'textbook_theorem',
    severity: 'error',
    title: 'Định lý Vi-ét — Tổng hai nghiệm (SGK Toán 10)',
    reason: 'Thiếu dấu âm (-) trong công thức tổng hai nghiệm Vi-ét',
    suggestion: 'Theo SGK Toán GDPT 2018, công thức đúng phải là: $x_1 + x_2 = -\\frac{b}{a}$.'
  },
  {
    regex: /x_\{?1\}?\s*(?:\\cdot|\*)?\s*x_\{?2\}?\s*=\s*-\s*\\frac\{\s*c\s*\}\{\s*a\s*\}/,
    category: 'textbook_theorem',
    severity: 'error',
    title: 'Định lý Vi-ét — Tích hai nghiệm (SGK Toán 10)',
    reason: 'Dư dấu âm (-) trong công thức tích hai nghiệm Vi-ét',
    suggestion: 'Theo SGK Toán GDPT 2018, công thức đúng phải là: $x_1 x_2 = \\frac{c}{a}$.'
  },
  {
    regex: /\\sin\s*\^\s*\{?2\}?\s*[a-zA-Z\\]+\s*-\s*\\cos\s*\^\s*\{?2\}?\s*[a-zA-Z\\]+\s*=\s*1/,
    category: 'textbook_theorem',
    severity: 'error',
    title: 'Hệ thức lượng giác cơ bản (SGK Toán 10 & 11)',
    reason: 'Ghi nhầm dấu trừ (-) thay vì dấu cộng (+) trong hằng đẳng thức lượng giác cơ bản',
    suggestion: 'Theo SGK Toán GDPT 2018, công thức đúng phải là: $\\sin^2 x + \\cos^2 x = 1$.'
  },
  {
    regex: /\(\s*\\cos\s*\(?x\)?\s*\)'\s*=\s*\+?\s*\\sin\s*\(?x\)?/,
    category: 'textbook_theorem',
    severity: 'error',
    title: 'Bảng đạo hàm lượng giác (SGK Toán 11)',
    reason: 'Quên dấu âm (-) trong công thức đạo hàm của hàm số cos(x)',
    suggestion: "Theo SGK Toán GDPT 2018, công thức đúng phải là: $(\\cos x)' = -\\sin x$."
  },
  {
    regex: /u_\{?n\}?\s*=\s*u_\{?1\}?\s*(?:\+\s*\(\s*n\s*\+\s*1\s*\)|-\s*\(\s*n\s*-\s*1\s*\))\s*(?:\\cdot|\*)?\s*d/,
    category: 'textbook_theorem',
    severity: 'error',
    title: 'Số hạng tổng quát của Cấp số cộng (SGK Toán 11)',
    reason: 'Sai dấu trong công thức số hạng tổng quát của cấp số cộng',
    suggestion: 'Theo SGK Toán GDPT 2018, công thức đúng phải là: $u_n = u_1 + (n - 1)d$.'
  },
  {
    regex: /\(\s*([a-zA-Z])\s*-\s*(\d+)\s*\)\s*\^\s*\{?2\}?\s*=\s*\1\s*\^\s*\{?2\}?\s*-\s*\d+\s*\1\s*-\s*\d+/,
    category: 'algebra_sympy',
    severity: 'error',
    title: 'Biến đổi hằng đẳng thức sai dấu',
    reason: 'Bình phương của một hiệu (A - B)^2 có hạng tử cuối +B^2 luôn dương, không phải dấu trừ (-)',
    suggestion: 'Kiểm tra lại dấu của hạng tử tự do khi khai triển hằng đẳng thức $(A - B)^2 = A^2 - 2AB + B^2$.'
  },
  {
    regex: /\(\s*([a-zA-Z])\s*\+\s*([a-zA-Z0-9]+)\s*\)\s*\^\s*\{?2\}?\s*=\s*\1\s*\^\s*\{?2\}?\s*-\s*2/,
    category: 'algebra_sympy',
    severity: 'error',
    title: 'Biến đổi hằng đẳng thức sai dấu',
    reason: 'Bình phương của một tổng (A + B)^2 phải có hạng tử +2AB mang dấu cộng (+)',
    suggestion: 'Kiểm tra lại dấu trong phép khai triển: $(A + B)^2 = A^2 + 2AB + B^2$.'
  }
];

function stripMathSegments(text = '') {
  return String(text).replace(/(\$\$[\s\S]*?\$\$|\$[^$\n]+\$|\\\[[\s\S]*?\\\]|\\\([\s\S]*?\\\))/g, ' ');
}

function scanTextForVietnameseTyposLocal(rawText, slideIndex, fieldName) {
  const warnings = [];
  if (!rawText || !String(rawText).trim()) return warnings;

  const naturalText = stripMathSegments(rawText);
  if (!naturalText.trim()) return warnings;

  for (const [wrong, correct, reason] of VIETNAMESE_TYPO_RULES) {
    const escaped = wrong.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const regex = new RegExp(`(?<![\\p{L}\\p{N}_])${escaped}(?![\\p{L}\\p{N}_])`, 'iu');
    const match = naturalText.match(regex);
    if (match) {
      const foundToken = match[0];
      warnings.push({
        slide_index: slideIndex,
        field: fieldName,
        category: 'spelling',
        severity: 'warning',
        detected_token: foundToken,
        message: `Phát hiện lỗi chính tả tiếng Việt trên Slide ${slideIndex}: "${foundToken}" (${reason}).`,
        suggestion: `Gợi ý sửa "${foundToken}" thành "${correct}".`
      });
    }
  }

  for (const word of REPEATED_WORDS) {
    const repRegex = new RegExp(`(?<![\\p{L}\\p{N}_])(${word})\\s+\\1(?![\\p{L}\\p{N}_])`, 'iu');
    const repMatch = naturalText.match(repRegex);
    if (repMatch) {
      const dup = repMatch[0];
      warnings.push({
        slide_index: slideIndex,
        field: fieldName,
        category: 'spelling',
        severity: 'warning',
        detected_token: dup,
        message: `Phát hiện từ bị gõ lặp 2 lần liên tiếp trên Slide ${slideIndex}: "${dup}".`,
        suggestion: `Gợi ý lược bỏ từ lặp, chỉ giữ lại 1 từ "${word}".`
      });
    }
  }

  return warnings;
}

function scanFormulasLocal(slide, slideIndex) {
  const warnings = [];
  if (!slide || typeof slide !== 'object') return warnings;

  const candidates = [];
  if (slide.main_definition_latex) {
    candidates.push([String(slide.main_definition_latex), 'main_definition_latex']);
  }
  if (Array.isArray(slide.math_formulas)) {
    slide.math_formulas.forEach((mf, idx) => {
      if (mf) candidates.push([String(mf), `math_formulas[${idx}]`]);
    });
  }
  if (Array.isArray(slide.bullet_points)) {
    slide.bullet_points.forEach((bp, idx) => {
      if (bp) candidates.push([String(bp), `bullet_points[${idx}]`]);
    });
  }

  for (const [rawContent, fieldLabel] of candidates) {
    for (const rule of LOCAL_THEOREM_AND_ALGEBRA_RULES) {
      const match = rawContent.match(rule.regex);
      if (match) {
        const found = match[0].trim();
        warnings.push({
          slide_index: slideIndex,
          field: fieldLabel,
          category: rule.category,
          severity: rule.severity,
          detected_token: found,
          message: `Phát hiện công thức lệch chuẩn ${rule.title} trên Slide ${slideIndex}: "${found}" (${rule.reason}).`,
          suggestion: rule.suggestion
        });
      }
    }
  }

  return warnings;
}

/**
 * Quét tức thì (0ms) toàn bộ Slide Deck tại trình duyệt để UI hiển thị ngay biểu tượng ⚠️ màu vàng.
 */
export function auditSlideDeckLocal(slideDeck) {
  const slides = slideDeck?.slides || [];
  if (!Array.isArray(slides) || slides.length === 0) {
    return { is_clean: true, total_warnings: 0, warnings: [] };
  }

  const allWarnings = [];

  slides.forEach((slide, idx) => {
    if (!slide || typeof slide !== 'object') return;
    const slideIndex = Number(slide.slide_index || slide.slide_number || idx + 1);

    if (slide.title) {
      allWarnings.push(...scanTextForVietnameseTyposLocal(slide.title, slideIndex, 'title'));
    }
    if (slide.subtitle) {
      allWarnings.push(...scanTextForVietnameseTyposLocal(slide.subtitle, slideIndex, 'subtitle'));
    }
    if (Array.isArray(slide.bullet_points)) {
      slide.bullet_points.forEach((bp, bIdx) => {
        if (bp) {
          allWarnings.push(...scanTextForVietnameseTyposLocal(bp, slideIndex, `bullet_points[${bIdx}]`));
        }
      });
    }
    if (slide.teacher_note) {
      allWarnings.push(...scanTextForVietnameseTyposLocal(slide.teacher_note, slideIndex, 'teacher_note'));
    }

    allWarnings.push(...scanFormulasLocal(slide, slideIndex));
  });

  return {
    is_clean: allWarnings.length === 0,
    total_warnings: allWarnings.length,
    warnings: allWarnings
  };
}

/**
 * Hợp nhất danh sách cảnh báo từ Local Linter và Backend SymPy/AI Endpoint (/api/v1/validation/audit-deck),
 * khử trùng lặp theo (slide_index, field, detected_token).
 */
export function mergeAuditWarnings(localWarnings = [], remoteWarnings = []) {
  const merged = [];
  const seenKeys = new Set();

  for (const w of [...remoteWarnings, ...localWarnings]) {
    if (!w) continue;
    const key = `${w.slide_index}::${w.field || ''}::${w.detected_token || w.message}`;
    if (!seenKeys.has(key)) {
      seenKeys.add(key);
      merged.push(w);
    }
  }

  merged.sort((a, b) => Number(a.slide_index || 0) - Number(b.slide_index || 0));
  return merged;
}

/**
 * Gọi API `POST /api/v1/validation/audit-deck` trên Backend (chạy SymPy + Bộ lọc chính tả + Định lý SGK).
 * Tự động fallback về kết quả Local Linter nếu Backend chưa bật hoặc đang chạy độc lập.
 */
export async function auditSlideDeckRemote(slideDeck) {
  const localResult = auditSlideDeckLocal(slideDeck);
  if (!slideDeck || !Array.isArray(slideDeck.slides)) {
    return localResult;
  }

  try {
    const response = await fetch('/api/v1/validation/audit-deck', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(slideDeck)
    });

    if (!response.ok) {
      return localResult;
    }

    const remoteData = await response.json();
    const combinedWarnings = mergeAuditWarnings(
      localResult.warnings,
      Array.isArray(remoteData?.warnings) ? remoteData.warnings : []
    );

    return {
      is_clean: combinedWarnings.length === 0,
      total_warnings: combinedWarnings.length,
      warnings: combinedWarnings
    };
  } catch {
    return localResult;
  }
}
