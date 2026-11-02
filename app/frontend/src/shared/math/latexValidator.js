import katex from 'katex';

/**
 * Task 9.4: Bộ Kiểm Duyệt Cú Pháp LaTeX Đa Tầng (4-Layer LaTeX Syntax Validator)
 * Đảm bảo mọi công thức Toán học từ MathLive hoặc ô nhập LaTeX đều hợp lệ 100%
 * trước khi ghi vào cấu trúc Slide JSON để tránh làm hỏng giao diện Slide hoặc lỗi xuất PPTX.
 */

/**
 * Tầng 3A: Kiểm tra cân bằng cặp ngoặc nhọn `{` và `}` (bỏ qua `\{` và `\}` đã escape).
 */
export function checkBraceBalance(latexStr = '') {
  const s = String(latexStr);
  let depth = 0;

  for (let i = 0; i < s.length; i += 1) {
    const ch = s[i];
    const prev = i > 0 ? s[i - 1] : '';

    // Bỏ qua ngoặc nhọn đã được escape (\{ hoặc \})
    if (prev === '\\') {
      continue;
    }

    if (ch === '{') {
      depth += 1;
    } else if (ch === '}') {
      depth -= 1;
      if (depth < 0) {
        return {
          isBalanced: false,
          reason: `Dư dấu đóng ngoặc nhọn "}" tại vị trí ký tự thứ ${i + 1}.`
        };
      }
    }
  }

  if (depth > 0) {
    return {
      isBalanced: false,
      reason: `Thiếu ${depth} dấu đóng ngoặc nhọn "}" ở cuối biểu thức.`
    };
  }

  return { isBalanced: true, reason: null };
}

/**
 * Tầng 3B: Kiểm tra cân bằng môi trường `\begin{...}` / `\end{...}` và cặp `\left` / `\right`.
 */
export function checkEnvironmentBalance(latexStr = '') {
  const s = String(latexStr);

  // 1. Kiểm tra ngăn xếp (Stack) cho \begin{env} và \end{env}
  const envRegex = /\\(begin|end)\{([^}]*)\}/g;
  const stack = [];
  let match;

  while ((match = envRegex.exec(s)) !== null) {
    const type = match[1];
    const envName = match[2].trim();
    if (type === 'begin') {
      stack.push(envName);
    } else {
      if (stack.length === 0) {
        return {
          isBalanced: false,
          reason: `Gặp lệnh \\end{${envName}} nhưng không có \\begin{${envName}} mở đầu.`
        };
      }
      const lastOpen = stack.pop();
      if (lastOpen !== envName) {
        return {
          isBalanced: false,
          reason: `Môi trường không khớp: mở \\begin{${lastOpen}} nhưng lại đóng \\end{${envName}}.`
        };
      }
    }
  }

  if (stack.length > 0) {
    const unclosed = stack[stack.length - 1];
    return {
      isBalanced: false,
      reason: `Thiếu lệnh đóng \\end{${unclosed}} cho môi trường \\begin{${unclosed}}.`
    };
  }

  // 2. Kiểm tra số lượng \left và \right (loại trừ \leftarrow, \rightarrow, \leftrightarrow...)
  const leftMatches = s.match(/\\left(?![a-zA-Z])/g) || [];
  const rightMatches = s.match(/\\right(?![a-zA-Z])/g) || [];
  if (leftMatches.length !== rightMatches.length) {
    return {
      isBalanced: false,
      reason: `Cặp ngoặc co giãn \\left (${leftMatches.length}) và \\right (${rightMatches.length}) không cân bằng.`
    };
  }

  return { isBalanced: true, reason: null };
}

/**
 * Tầng 2: Kiểm tra còn sót ô trống chưa điền giá trị (\placeholder{}, tử/mẫu rỗng, căn rỗng).
 */
export function checkUnfilledPlaceholders(latexStr = '') {
  const s = String(latexStr).trim();

  // Kiểm tra token #@ hoặc #? chưa được thay thế
  if (/#@|#\?/.test(s)) {
    return {
      hasUnfilled: true,
      reason: 'Công thức còn ô giữ chỗ (#@ / #?) chưa điền giá trị.'
    };
  }

  // Kiểm tra \placeholder{} rỗng của MathLive
  if (/\\placeholder\{\s*\}/.test(s)) {
    return {
      hasUnfilled: true,
      reason: 'Công thức còn ô trống (□) chưa điền số hoặc biến số.'
    };
  }

  // Kiểm tra phân số có tử số hoặc mẫu số rỗng: \frac{}{...} hoặc \frac{...}{}
  if (/\\frac\{\s*\}/.test(s) || /\\frac\{[^{}]+\}\{\s*\}/.test(s)) {
    return {
      hasUnfilled: true,
      reason: 'Phân số (\\frac) đang bị bỏ trống tử số hoặc mẫu số.'
    };
  }

  // Kiểm tra căn thức rỗng: \sqrt{} hoặc \sqrt[]{}
  if (/\\sqrt(?:\[[^\]]*\])?\{\s*\}/.test(s)) {
    return {
      hasUnfilled: true,
      reason: 'Biểu thức bên trong dấu căn (\\sqrt) không được để trống.'
    };
  }

  return { hasUnfilled: false, reason: null };
}

/**
 * Dịch thông báo lỗi kỹ thuật của KaTeX sang hướng dẫn sư phạm Tiếng Việt dễ hiểu cho Giáo viên.
 */
function translateKatexErrorToVietnamese(rawErrorMsg = '') {
  const cleanMsg = String(rawErrorMsg).replace(/^KaTeX parse error:\s*/i, '').trim();

  if (/Expected 'EOF', got '\}'/i.test(cleanMsg)) {
    return `Dư dấu đóng ngoặc nhọn "}" trong công thức (${cleanMsg}).`;
  }
  if (/Expected '\}', got 'EOF'/i.test(cleanMsg)) {
    return `Thiếu dấu đóng ngoặc nhọn "}" ở cuối công thức (${cleanMsg}).`;
  }
  if (/Undefined control sequence:\s*(\\[a-zA-Z]+)/i.test(cleanMsg)) {
    const cmdMatch = cleanMsg.match(/Undefined control sequence:\s*(\\[a-zA-Z]+)/i);
    return `Lệnh LaTeX không tồn tại hoặc gõ sai chính tả: "${cmdMatch?.[1] || ''}".`;
  }
  if (/Double superscript/i.test(cleanMsg)) {
    return 'Lỗi hai dấu mũ (^) liên tiếp không có ngoặc nhọn bao quanh.';
  }
  if (/Double subscript/i.test(cleanMsg)) {
    return 'Lỗi hai chỉ số dưới (_) liên tiếp không có ngoặc nhọn bao quanh.';
  }

  return `Lỗi cú pháp LaTeX: ${cleanMsg}`;
}

/**
 * Task 9.4: Hàm chính kiểm tra cú pháp LaTeX hợp lệ trước khi lưu vào Slide JSON.
 *
 * @param {string} rawLatex - Chuỗi LaTeX cần kiểm tra (lấy từ mathfield.getValue('latex-expanded'))
 * @param {Object} options - Tùy chọn kiểm tra
 * @param {boolean} [options.displayMode=true] - Chế độ khối ($$) hay nội dòng ($)
 * @param {boolean} [options.allowPlaceholdersForPreview=false] - Cho phép hiển thị ô vuông \square khi đang gõ preview
 * @returns {{
 *   isValid: boolean,
 *   code: 'VALID' | 'EMPTY_FORMULA' | 'UNFILLED_PLACEHOLDER' | 'UNBALANCED_BRACES' | 'UNBALANCED_ENVIRONMENT' | 'KATEX_PARSE_ERROR',
 *   errorMessage: string | null,
 *   normalizedLatex: string
 * }}
 */
export function validateLatexSyntax(
  rawLatex = '',
  { displayMode = true, allowPlaceholdersForPreview = false } = {}
) {
  const trimmed = String(rawLatex ?? '')
    .replace(/^\$\$|\$\$$/g, '')
    .replace(/^\$|\$$/g, '')
    .trim();

  // Tầng 1: Kiểm tra rỗng
  if (!trimmed) {
    return {
      isValid: false,
      code: 'EMPTY_FORMULA',
      errorMessage: 'Công thức không được để trống. Vui lòng nhập biểu thức Toán học trước khi lưu.',
      normalizedLatex: ''
    };
  }

  // Tầng 2: Kiểm tra còn sót ô trống chưa điền (chỉ chặn nghiêm ngặt khi bấm Lưu)
  if (!allowPlaceholdersForPreview) {
    const placeholderCheck = checkUnfilledPlaceholders(trimmed);
    if (placeholderCheck.hasUnfilled) {
      return {
        isValid: false,
        code: 'UNFILLED_PLACEHOLDER',
        errorMessage: placeholderCheck.reason,
        normalizedLatex: trimmed
      };
    }
  }

  // Chuẩn hóa nội dung bên trong \placeholder{content} -> content (hoặc \square nếu đang preview)
  const normalizedLatex = allowPlaceholdersForPreview
    ? trimmed.replace(/\\placeholder\{([^}]*)\}/g, (_, inner) => (inner.trim() ? inner : '\\square'))
    : trimmed.replace(/\\placeholder\{([^}]*)\}/g, '$1').trim();

  // Tầng 3A: Kiểm tra cân bằng ngoặc nhọn { }
  const braceCheck = checkBraceBalance(normalizedLatex);
  if (!braceCheck.isBalanced) {
    return {
      isValid: false,
      code: 'UNBALANCED_BRACES',
      errorMessage: braceCheck.reason,
      normalizedLatex
    };
  }

  // Tầng 3B: Kiểm tra cân bằng môi trường \begin...\end và \left...\right
  const envCheck = checkEnvironmentBalance(normalizedLatex);
  if (!envCheck.isBalanced) {
    return {
      isValid: false,
      code: 'UNBALANCED_ENVIRONMENT',
      errorMessage: envCheck.reason,
      normalizedLatex
    };
  }

  // Tầng 4: Kiểm tra biên dịch thực tế qua KaTeX Parser (throwOnError: true)
  try {
    katex.renderToString(normalizedLatex, {
      displayMode: Boolean(displayMode),
      throwOnError: true,
      strict: false
    });
    return {
      isValid: true,
      code: 'VALID',
      errorMessage: null,
      normalizedLatex
    };
  } catch (err) {
    return {
      isValid: false,
      code: 'KATEX_PARSE_ERROR',
      errorMessage: translateKatexErrorToVietnamese(err?.message || 'Cấu trúc LaTeX không hợp lệ'),
      normalizedLatex
    };
  }
}
