import React, { useEffect, useRef, useState, useMemo } from 'react';
import { X, Check, Sparkles, Keyboard, Eye, Code2, CheckCircle2, AlertTriangle } from 'lucide-react';
import katex from 'katex';
import MathText from './MathText';

/**
 * Helper: Tách ký hiệu bao toán học ($...$ hoặc $$...$$) để nạp chuỗi LaTeX thuần
 * vào Web Component <math-field> của MathLive.
 */
function unwrapLatexDelimiters(rawText = '') {
  const trimmed = String(rawText).trim();
  if (trimmed.startsWith('$$') && trimmed.endsWith('$$') && trimmed.length >= 4) {
    return {
      cleanLatex: trimmed.slice(2, -2).trim(),
      delimiter: '$$'
    };
  }
  if (trimmed.startsWith('$') && trimmed.endsWith('$') && trimmed.length >= 2) {
    return {
      cleanLatex: trimmed.slice(1, -1).trim(),
      delimiter: '$'
    };
  }
  return {
    cleanLatex: trimmed,
    delimiter: '$$'
  };
}

/**
 * Helper: Đóng gói lại chuỗi LaTeX chuẩn khi lưu trả về Slide JSON.
 */
function wrapLatexDelimiters(cleanLatex = '', delimiter = '$$') {
  const trimmed = String(cleanLatex).trim();
  if (!trimmed) return '';
  if (delimiter === '$$') return `$$${trimmed}$$`;
  if (delimiter === '$') return `$${trimmed}$`;
  return trimmed;
}

/**
 * Task 8.3: Bộ bàn phím ảo Toán học tiếng Việt chuẩn GDPT 2018 (Toán 10, 11, 12)
 * Hỗ trợ đầy đủ: Phân số, Căn thức, Hệ phương trình, Giới hạn, Đạo hàm, Tích phân, Vectơ, Hình học.
 * Ký hiệu #@ đánh dấu vị trí con trỏ chính và #? là ô placeholder tiếp theo trên cây Math AST.
 */
export const VIETNAMESE_MATH_KEYBOARD_TABS = [
  {
    id: 'algebra',
    label: '📐 Đại số & Căn thức (Toán 10)',
    buttons: [
      { label: 'Phân số a/b', display: 'a/b', latex: '\\frac{#@}{#?}', tooltip: 'Chèn phân số \\frac{a}{b}' },
      { label: 'Căn bậc 2', display: '√x', latex: '\\sqrt{#@}', tooltip: 'Chèn căn bậc hai \\sqrt{x}' },
      { label: 'Căn bậc n', display: 'ⁿ√x', latex: '\\sqrt[#?]{#@}', tooltip: 'Chèn căn bậc n \\sqrt[n]{x}' },
      { label: 'Bình phương', display: 'x²', latex: '#@^2', tooltip: 'Chèn bình phương x^2' },
      { label: 'Số mũ n', display: 'xⁿ', latex: '#@^{#?}', tooltip: 'Chèn lũy thừa x^n' },
      { label: 'Chỉ số dưới', display: 'xᵢ', latex: '#@_{#?}', tooltip: 'Chèn chỉ số dưới x_i' },
      { label: 'Biệt thức Δ', display: 'Δ = b²-4ac', latex: '\\Delta = b^2 - 4ac', tooltip: 'Công thức biệt thức Delta' },
      { label: 'Nghiệm PT bậc 2', display: 'x₁,₂', latex: 'x = \\frac{-b \\pm \\sqrt{\\Delta}}{2a}', tooltip: 'Công thức nghiệm phương trình bậc hai' },
      { label: 'Hệ 2 PT', display: '{ Hệ PT', latex: '\\begin{cases} #@ \\\\ #? \\end{cases}', tooltip: 'Chèn hệ phương trình 2 ẩn' },
      { label: 'Cộng trừ ±', display: '±', latex: '\\pm', tooltip: 'Dấu cộng trừ \\pm' },
      { label: 'Nhỏ hơn bằng', display: '≤', latex: '\\le', tooltip: 'Bất đẳng thức nhỏ hơn hoặc bằng \\le' },
      { label: 'Lớn hơn bằng', display: '≥', latex: '\\ge', tooltip: 'Bất đẳng thức lớn hơn hoặc bằng \\ge' },
      { label: 'Khác ≠', display: '≠', latex: '\\neq', tooltip: 'Khác \\neq' },
      { label: 'Thuộc ∈', display: '∈', latex: '\\in', tooltip: 'Phần tử thuộc tập hợp \\in' },
      { label: 'Tập số thực ℝ', display: 'ℝ', latex: '\\mathbb{R}', tooltip: 'Tập hợp số thực \\mathbb{R}' },
      { label: 'Tập rỗng ∅', display: '∅', latex: '\\varnothing', tooltip: 'Tập hợp rỗng \\varnothing' }
    ]
  },
  {
    id: 'calculus',
    label: '∫ Giới hạn & Tích phân (Toán 11–12)',
    buttons: [
      { label: 'Giới hạn lim', display: 'lim (x→x₀)', latex: '\\lim_{x \\to #@}', tooltip: 'Giới hạn khi x tiến tới x_0' },
      { label: 'Giới hạn vô cực', display: 'lim (x→+∞)', latex: '\\lim_{x \\to +\\infty} #@', tooltip: 'Giới hạn tại vô cực' },
      { label: 'Tích phân a→b', display: '∫ₐᵇ f(x)dx', latex: '\\int_{#@}^{#?} f(x)\\,dx', tooltip: 'Tích phân xác định từ a đến b' },
      { label: 'Nguyên hàm', display: '∫ f(x)dx', latex: '\\int #@\\,dx', tooltip: 'Nguyên hàm \\int f(x)dx' },
      { label: 'Đạo hàm f\'(x)', display: 'f\'(x)', latex: 'f\'(x) = #@', tooltip: 'Ký hiệu đạo hàm cấp 1' },
      { label: 'Tổng Sigma', display: '∑ᵢ₌₁ⁿ', latex: '\\sum_{i=1}^{n} #@', tooltip: 'Tổng cấp số / dãy số \\sum' },
      { label: 'Logarit cơ số a', display: 'logₐ(b)', latex: '\\log_{#@}{#?}', tooltip: 'Logarit cơ số a của b' },
      { label: 'Logarit tự nhiên', display: 'ln(x)', latex: '\\ln\\left(#@\\right)', tooltip: 'Logarit tự nhiên ln(x)' },
      { label: 'Hàm mũ eˣ', display: 'eˣ', latex: 'e^{#@}', tooltip: 'Hàm số mũ cơ số tự nhiên e^x' },
      { label: 'Dương vô cực', display: '+∞', latex: '+\\infty', tooltip: 'Dương vô cực +\\infty' },
      { label: 'Âm vô cực', display: '-∞', latex: '-\\infty', tooltip: 'Âm vô cực -\\infty' },
      { label: 'Tương đương ⇔', display: '⇔', latex: '\\iff', tooltip: 'Dấu tương đương \\iff' }
    ]
  },
  {
    id: 'geometry',
    label: '🧊 Hình học & Vectơ (Toán 10–12)',
    buttons: [
      { label: 'Vectơ đơn', display: 'u⃗', latex: '\\vec{#@}', tooltip: 'Ký hiệu vectơ đơn \\vec{u}' },
      { label: 'Vectơ 2 điểm', display: 'AB⃗', latex: '\\overrightarrow{#@}', tooltip: 'Vectơ đi qua 2 điểm \\overrightarrow{AB}' },
      { label: 'Độ dài vectơ', display: '|AB⃗|', latex: '\\left|\\overrightarrow{#@}\\right|', tooltip: 'Độ dài (mô-đun) của vectơ' },
      { label: 'Tích vô hướng', display: 'u⃗ · v⃗', latex: '\\vec{u} \\cdot \\vec{v}', tooltip: 'Tích vô hướng hai vectơ' },
      { label: 'Góc ABC', display: '∠ABC', latex: '\\widehat{#@}', tooltip: 'Ký hiệu góc \\widehat{ABC}' },
      { label: 'Vuông góc ⊥', display: '⊥', latex: '\\perp', tooltip: 'Quan hệ vuông góc \\perp' },
      { label: 'Song song ∥', display: '∥', latex: '\\parallel', tooltip: 'Quan hệ song song \\parallel' },
      { label: 'Độ °', display: '°', latex: '^\\circ', tooltip: 'Đơn vị độ góc ^\\circ' },
      { label: 'Số Pi π', display: 'π', latex: '\\pi', tooltip: 'Hằng số Pi \\pi' },
      { label: 'sin(x)', display: 'sin', latex: '\\sin\\left(#@\\right)', tooltip: 'Hàm lượng giác sin' },
      { label: 'cos(x)', display: 'cos', latex: '\\cos\\left(#@\\right)', tooltip: 'Hàm lượng giác cos' },
      { label: 'tan(x)', display: 'tan', latex: '\\tan\\left(#@\\right)', tooltip: 'Hàm lượng giác tan' },
      { label: 'Thể tích chóp', display: 'V = ⅓S·h', latex: 'V = \\frac{1}{3} S_{\\text{đáy}} \\cdot h', tooltip: 'Công thức thể tích khối chóp' },
      { label: 'Thể tích lăng trụ', display: 'V = S·h', latex: 'V = S_{\\text{đáy}} \\cdot h', tooltip: 'Công thức thể tích khối lăng trụ' }
    ]
  }
];

/**
 * Cấu hình trực tiếp bàn phím ảo gốc của MathLive (window.mathVirtualKeyboard.layouts)
 * sang giao diện Tiếng Việt chuẩn THPT nếu giáo viên bật bàn phím nổi của hệ thống.
 */
function configureVietnameseNativeVirtualKeyboard() {
  if (typeof window === 'undefined' || !window.mathVirtualKeyboard) return;
  try {
    window.mathVirtualKeyboard.layouts = [
      {
        label: 'Đại số THPT',
        tooltip: 'Phân số, căn thức, mũ, hệ phương trình (Toán 10)',
        rows: [
          [
            { latex: '\\frac{#@}{#?}', label: 'Phân số' },
            { latex: '\\sqrt{#@}', label: '√x' },
            { latex: '\\sqrt[#?]{#@}', label: 'ⁿ√x' },
            { latex: '#@^2', label: 'x²' },
            { latex: '#@^{#?}', label: 'xⁿ' },
            { latex: '#@_{#?}', label: 'xᵢ' },
            { latex: '\\Delta', label: 'Δ' },
            { latex: '\\pm', label: '±' }
          ],
          [
            { latex: '\\begin{cases} #@ \\\\ #? \\end{cases}', label: '{ Hệ PT' },
            { latex: '\\le', label: '≤' },
            { latex: '\\ge', label: '≥' },
            { latex: '\\neq', label: '≠' },
            { latex: '\\in', label: '∈' },
            { latex: '\\subset', label: '⊂' },
            { latex: '\\mathbb{R}', label: 'ℝ' },
            { latex: '\\varnothing', label: '∅' }
          ],
          [
            '7', '8', '9', '+', '-',
            { command: ['performWithFeedback', 'deleteBackward'], label: '⌫' }
          ],
          [
            '4', '5', '6', '\\times', '\\div', '='
          ],
          [
            '1', '2', '3', '0', 'x', 'y'
          ]
        ]
      },
      {
        label: 'Giải tích 11-12',
        tooltip: 'Giới hạn, đạo hàm, nguyên hàm, tích phân, logarit',
        rows: [
          [
            { latex: '\\lim_{x \\to #@}', label: 'lim x→x₀' },
            { latex: '\\lim_{x \\to +\\infty}', label: 'lim x→+∞' },
            { latex: '\\int_{#@}^{#?}', label: '∫ₐᵇ' },
            { latex: '\\int #@\\,dx', label: '∫dx' },
            { latex: '\\sum_{i=1}^{n}', label: '∑' },
            { latex: 'f\'(x)', label: 'f\'(x)' }
          ],
          [
            { latex: '\\log_{#@}{#?}', label: 'logₐb' },
            { latex: '\\ln(#@)', label: 'ln(x)' },
            { latex: 'e^{#@}', label: 'eˣ' },
            { latex: '+\\infty', label: '+∞' },
            { latex: '-\\infty', label: '-∞' },
            { latex: '\\iff', label: '⇔' }
          ]
        ]
      },
      {
        label: 'Hình học & Vectơ',
        tooltip: 'Vectơ, góc, quan hệ vuông góc, song song, lượng giác',
        rows: [
          [
            { latex: '\\vec{#@}', label: 'u⃗' },
            { latex: '\\overrightarrow{#@}', label: 'AB⃗' },
            { latex: '\\left|\\overrightarrow{#@}\\right|', label: '|AB⃗|' },
            { latex: '\\widehat{#@}', label: '∠ABC' },
            { latex: '\\perp', label: '⊥' },
            { latex: '\\parallel', label: '∥' }
          ],
          [
            { latex: '\\sin(#@)', label: 'sin' },
            { latex: '\\cos(#@)', label: 'cos' },
            { latex: '\\tan(#@)', label: 'tan' },
            { latex: '^\\circ', label: '°' },
            { latex: '\\pi', label: 'π' },
            { latex: '\\alpha', label: 'α' }
          ]
        ]
      }
    ];
  } catch {
    // Fallback an toàn nếu phiên bản MathLive giới hạn ghi đè layouts
  }
}

/**
 * Task 8.2, 8.3 & 8.4: Modal Popup chỉnh sửa công thức Toán trực quan (MathLive <math-field>)
 * - Task 8.2: Mở Popup khi giáo viên click đúp vào công thức trên Slide.
 * - Task 8.3: Bàn phím ảo Toán học tiếng Việt chuẩn THPT (Toán 10, 11, 12).
 * - Task 8.4: Lắng nghe sự kiện `input` trên MathLive để hiển thị bản xem trước (Preview)
 *   bằng KaTeX theo thời gian thực kèm kiểm tra cú pháp tức thì.
 */
export default function MathLiveModal({
  isOpen,
  initialLatex = '',
  fieldLabel = 'Công thức Toán học trọng tâm',
  onClose,
  onSave
}) {
  const mathFieldRef = useRef(null);
  const [delimiter, setDelimiter] = useState('$$');
  const [currentLatex, setCurrentLatex] = useState('');
  const [activeKeyboardTab, setActiveKeyboardTab] = useState('algebra');

  // Khởi tạo giá trị cho <math-field> và cấu hình bàn phím ảo tiếng Việt mỗi khi mở Modal
  useEffect(() => {
    if (!isOpen) return;

    configureVietnameseNativeVirtualKeyboard();

    const { cleanLatex, delimiter: detectedDelim } = unwrapLatexDelimiters(initialLatex);
    setDelimiter(detectedDelim);
    setCurrentLatex(cleanLatex);

    const mf = mathFieldRef.current;
    if (mf) {
      if (typeof mf.setValue === 'function') {
        mf.setValue(cleanLatex, { silenceNotifications: true });
      } else {
        mf.value = cleanLatex;
      }
      setTimeout(() => {
        try {
          mf.focus();
        } catch {
          // Ignore focus errors if DOM not ready
        }
      }, 60);
    }
  }, [isOpen, initialLatex]);

  // Task 8.4: Lắng nghe trực tiếp sự kiện DOM `input` trên Web Component <math-field>
  // để trích xuất chuỗi LaTeX mở rộng (`latex-expanded`) và cập nhật KaTeX Preview theo thời gian thực.
  useEffect(() => {
    if (!isOpen) return;
    const mf = mathFieldRef.current;
    if (!mf) return;

    const handleMathLiveInput = (evt) => {
      const target = evt.target;
      const expandedLatex =
        target && typeof target.getValue === 'function'
          ? target.getValue('latex-expanded') || target.value
          : target?.value || '';
      setCurrentLatex(expandedLatex);
    };

    mf.addEventListener('input', handleMathLiveInput);
    return () => {
      mf.removeEventListener('input', handleMathLiveInput);
    };
  }, [isOpen]);

  // Task 8.4: Kiểm tra tính hợp lệ cú pháp KaTeX theo thời gian thực khi currentLatex thay đổi
  const katexValidation = useMemo(() => {
    const clean = String(currentLatex || '').trim();
    if (!clean) {
      return { isValid: true, errorMsg: null };
    }
    try {
      // Loại bỏ ký hiệu placeholder tạm thời của MathLive (\placeholder{}) khi kiểm thử KaTeX
      const normalizedForCheck = clean.replace(/\\placeholder\{[^}]*\}/g, '\\square');
      katex.renderToString(normalizedForCheck, {
        displayMode: delimiter === '$$',
        throwOnError: true,
        strict: false
      });
      return { isValid: true, errorMsg: null };
    } catch (err) {
      return {
        isValid: false,
        errorMsg: err?.message ? String(err.message).replace(/^KaTeX parse error:\s*/i, '') : 'Cấu trúc LaTeX chưa hoàn chỉnh'
      };
    }
  }, [currentLatex, delimiter]);

  // Chuỗi LaTeX đã chuẩn hóa placeholder để hiển thị mượt trên KaTeX Preview
  const previewLatexForKatex = useMemo(() => {
    const clean = String(currentLatex || '').trim();
    if (!clean) return '';
    return clean.replace(/\\placeholder\{[^}]*\}/g, '\\square');
  }, [currentLatex]);

  // Đóng Modal khi nhấn phím Escape
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        if (window.mathVirtualKeyboard?.visible) {
          window.mathVirtualKeyboard.hide();
        }
        onClose?.();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  /**
   * Task 8.3: Chèn cấu trúc Toán học từ nút bấm bàn phím ảo Tiếng Việt vào đúng vị trí con trỏ của <math-field>
   */
  const handleInsertMathTemplate = (latexTemplate) => {
    const mf = mathFieldRef.current;
    if (mf) {
      try {
        mf.focus();
        if (typeof mf.executeCommand === 'function') {
          mf.executeCommand(['insert', latexTemplate, { focus: true, feedback: true, mode: 'math' }]);
        } else if (typeof mf.insert === 'function') {
          mf.insert(latexTemplate, { focus: true, mode: 'math' });
        } else {
          const cleanSnippet = latexTemplate.replace(/#@|#\?/g, '');
          mf.value = `${mf.value || ''}${cleanSnippet}`;
        }
        const updatedValue =
          typeof mf.getValue === 'function' ? mf.getValue('latex-expanded') || mf.value : mf.value;
        setCurrentLatex(updatedValue || '');
        return;
      } catch {
        // Fallback nếu Web Component chưa kịp mount method
      }
    }

    // Fallback thuần React state
    const fallbackSnippet = latexTemplate.replace(/#@|#\?/g, '');
    setCurrentLatex((prev) => `${prev ? `${prev} ` : ''}${fallbackSnippet}`);
  };

  /**
   * Cho phép giáo viên chỉnh sửa nhanh mã nguồn LaTeX và đồng bộ ngược lên <math-field>
   */
  const handleRawLatexInputChange = (e) => {
    const nextVal = e.target.value;
    setCurrentLatex(nextVal);
    const mf = mathFieldRef.current;
    if (mf) {
      if (typeof mf.setValue === 'function') {
        mf.setValue(nextVal, { silenceNotifications: true });
      } else {
        mf.value = nextVal;
      }
    }
  };

  const handleConfirmSave = () => {
    const mf = mathFieldRef.current;
    const rawLatex =
      mf && typeof mf.getValue === 'function'
        ? mf.getValue('latex-expanded') || mf.value
        : currentLatex;

    const cleanedFinalLatex = String(rawLatex || '').replace(/\\placeholder\{[^}]*\}/g, '');
    const formatted = wrapLatexDelimiters(cleanedFinalLatex, delimiter);
    if (window.mathVirtualKeyboard?.visible) {
      window.mathVirtualKeyboard.hide();
    }
    onSave?.(formatted, cleanedFinalLatex);
    onClose?.();
  };

  const handleToggleVirtualKeyboard = () => {
    const mf = mathFieldRef.current;
    if (mf) mf.focus();
    configureVietnameseNativeVirtualKeyboard();
    if (window.mathVirtualKeyboard) {
      if (window.mathVirtualKeyboard.visible) {
        window.mathVirtualKeyboard.hide();
      } else {
        window.mathVirtualKeyboard.show();
      }
    }
  };

  const currentTabConfig =
    VIETNAMESE_MATH_KEYBOARD_TABS.find((t) => t.id === activeKeyboardTab) ||
    VIETNAMESE_MATH_KEYBOARD_TABS[0];

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4"
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          if (window.mathVirtualKeyboard?.visible) {
            window.mathVirtualKeyboard.hide();
          }
          onClose?.();
        }
      }}
    >
      <div className="w-full max-w-3xl rounded-2xl bg-slate-900 border border-cyan-700/70 shadow-2xl shadow-cyan-950/60 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header Modal */}
        <div className="px-5 py-3.5 bg-gradient-to-r from-slate-900 via-cyan-950/50 to-slate-900 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/40 flex items-center justify-center text-cyan-400">
              <Sparkles size={16} />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                Trình Gõ Công Thức Toán Trực Quan (MathLive WYSIWYG)
              </h3>
              <p className="text-[11px] text-cyan-300/80">
                Đang chỉnh sửa: <span className="font-semibold text-white">{fieldLabel}</span>
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={() => {
              if (window.mathVirtualKeyboard?.visible) {
                window.mathVirtualKeyboard.hide();
              }
              onClose?.();
            }}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
            title="Đóng cửa sổ (Esc)"
          >
            <X size={18} />
          </button>
        </div>

        {/* Body: Ô nhập công thức WYSIWYG <math-field>, Bàn phím ảo Tiếng Việt & KaTeX Real-time Preview */}
        <div className="p-5 space-y-4 max-h-[82vh] overflow-y-auto">
          <div className="flex items-center justify-between text-xs">
            <label className="text-slate-300 font-medium">
              1. Ô nhập công thức trực quan (Click vào ô hoặc chọn nút bên dưới):
            </label>
            <button
              type="button"
              onClick={handleToggleVirtualKeyboard}
              className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-cyan-800/60 text-[11px] flex items-center gap-1.5 transition"
              title="Bật/tắt bàn phím nổi MathLive toàn màn hình"
            >
              <Keyboard size={13} />
              <span>Bàn phím nổi hệ thống</span>
            </button>
          </div>

          {/* Web Component <math-field> của MathLive */}
          <div className="p-1.5 rounded-xl bg-slate-950 border-2 border-cyan-600/70 focus-within:border-cyan-400 shadow-inner">
            <math-field
              ref={mathFieldRef}
              onInput={(e) => {
                const target = e.target;
                const val =
                  target && typeof target.getValue === 'function'
                    ? target.getValue('latex-expanded') || target.value
                    : target?.value || '';
                setCurrentLatex(val);
              }}
              style={{
                width: '100%',
                minHeight: '64px',
                padding: '12px 16px',
                fontSize: '1.35rem',
                backgroundColor: '#020617',
                color: '#67e8f9',
                borderRadius: '0.5rem',
                outline: 'none',
                border: 'none'
              }}
            >
              {currentLatex}
            </math-field>
          </div>

          {/* Task 8.3: BÀN PHÍM ẢO TOÁN HỌC TIẾNG VIỆT (Tích hợp trực tiếp trong Modal) */}
          <div className="rounded-xl bg-slate-950/90 border border-slate-800 p-3.5 space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/80 pb-2.5">
              <span className="text-xs font-bold text-cyan-400 flex items-center gap-1.5">
                <Keyboard size={14} /> 2. Bàn phím Toán học Tiếng Việt (THPT 2018):
              </span>

              {/* Tabs chuyển nhóm ký hiệu: Đại số 10 | Giải tích 11-12 | Hình học & Vectơ */}
              <div className="flex flex-wrap items-center gap-1 bg-slate-900 p-1 rounded-lg border border-slate-800">
                {VIETNAMESE_MATH_KEYBOARD_TABS.map((tab) => (
                  <button
                    key={tab.id}
                    type="button"
                    onClick={() => setActiveKeyboardTab(tab.id)}
                    className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition ${
                      activeKeyboardTab === tab.id
                        ? 'bg-cyan-600 text-white shadow-sm'
                        : 'text-slate-400 hover:text-white hover:bg-slate-800'
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Lưới các nút bấm ký hiệu Toán học Tiếng Việt */}
            <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-4 gap-2">
              {currentTabConfig.buttons.map((btn, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleInsertMathTemplate(btn.latex)}
                  title={btn.tooltip}
                  className="px-2.5 py-2 rounded-xl bg-slate-900 hover:bg-cyan-950/60 border border-slate-800 hover:border-cyan-500/70 flex flex-col items-center justify-center gap-0.5 transition group shadow-sm"
                >
                  <span className="text-sm font-bold font-mono text-cyan-300 group-hover:text-white">
                    {btn.display}
                  </span>
                  <span className="text-[10px] text-slate-400 group-hover:text-cyan-200 truncate max-w-full">
                    {btn.label}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* Task 8.4: KHUNG XEM TRƯỚC KaTeX THỜI GIAN THỰC (REAL-TIME KaTeX PREVIEW) */}
          <div className="rounded-xl bg-gradient-to-br from-slate-950 via-cyan-950/20 to-slate-950 border border-cyan-800/60 p-3.5 space-y-2.5 shadow-inner">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className="text-xs font-bold text-emerald-400 flex items-center gap-1.5">
                <Eye size={14} /> 3. Xem trước hiển thị trên Slide (KaTeX Real-time Preview):
              </span>

              <div className="flex items-center gap-2">
                {/* Trạng thái kiểm tra cú pháp KaTeX tức thì */}
                {katexValidation.isValid ? (
                  <span className="px-2 py-0.5 rounded-full bg-emerald-950/80 border border-emerald-700/60 text-emerald-300 text-[10px] font-semibold flex items-center gap-1">
                    <CheckCircle2 size={11} /> Cú pháp KaTeX hợp lệ
                  </span>
                ) : (
                  <span className="px-2 py-0.5 rounded-full bg-amber-950/80 border border-amber-700/60 text-amber-300 text-[10px] font-semibold flex items-center gap-1">
                    <AlertTriangle size={11} /> Đang chờ hoàn tất biểu thức
                  </span>
                )}

                {/* Chuyển đổi kiểu bao công thức $$ (Block) hoặc $ (Inline) */}
                <div className="flex items-center bg-slate-900 border border-slate-800 rounded-lg p-0.5 text-[10px]">
                  <button
                    type="button"
                    onClick={() => setDelimiter('$$')}
                    className={`px-2 py-0.5 rounded transition ${
                      delimiter === '$$'
                        ? 'bg-cyan-600 text-white font-semibold'
                        : 'text-slate-400 hover:text-white'
                    }`}
                    title="Hiển thị khối công thức chính giữa (Display Mode $$...$$)"
                  >
                    $$ Khối (Block)
                  </button>
                  <button
                    type="button"
                    onClick={() => setDelimiter('$')}
                    className={`px-2 py-0.5 rounded transition ${
                      delimiter === '$'
                        ? 'bg-cyan-600 text-white font-semibold'
                        : 'text-slate-400 hover:text-white'
                    }`}
                    title="Hiển thị công thức nội dòng (Inline Mode $...$)"
                  >
                    $ Nội dòng
                  </button>
                </div>
              </div>
            </div>

            {/* Vùng kết xuất KaTeX trực tiếp giống 100% trên Slide */}
            <div className="min-h-[60px] px-4 py-3 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center justify-center text-cyan-200 text-base md:text-lg font-bold">
              {previewLatexForKatex ? (
                <MathText
                  text={wrapLatexDelimiters(previewLatexForKatex, delimiter)}
                  block={delimiter === '$$'}
                />
              ) : (
                <span className="text-xs font-normal text-slate-500 italic">
                  (Chưa có công thức — Hãy gõ hoặc bấm nút trên bàn phím Toán học Tiếng Việt)
                </span>
              )}
            </div>

            {/* Hiển thị & cho phép chỉnh sửa chuỗi mã nguồn LaTeX thực tế */}
            <div className="flex items-center gap-2 pt-1">
              <span className="text-[11px] text-slate-400 flex items-center gap-1 shrink-0 font-mono">
                <Code2 size={12} className="text-cyan-400" /> Chuỗi LaTeX:
              </span>
              <input
                type="text"
                value={currentLatex}
                onChange={handleRawLatexInputChange}
                placeholder="Chuỗi LaTeX tự động sinh ra tại đây..."
                className="flex-1 bg-slate-950 border border-slate-800 focus:border-cyan-600 rounded-lg px-2.5 py-1 text-[11px] font-mono text-cyan-300 focus:outline-none"
              />
            </div>

            {!katexValidation.isValid && katexValidation.errorMsg && (
              <div className="text-[11px] text-amber-300/90 bg-amber-950/30 border border-amber-800/50 rounded-lg px-2.5 py-1.5 font-mono">
                ⚠️ Chi tiết cú pháp: {katexValidation.errorMsg}
              </div>
            )}
          </div>
        </div>

        {/* Footer Modal */}
        <div className="px-5 py-3 bg-slate-950/90 border-t border-slate-800 flex items-center justify-end gap-2.5">
          <button
            type="button"
            onClick={() => {
              if (window.mathVirtualKeyboard?.visible) {
                window.mathVirtualKeyboard.hide();
              }
              onClose?.();
            }}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition"
          >
            Hủy bỏ
          </button>
          <button
            type="button"
            onClick={handleConfirmSave}
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow-lg shadow-cyan-950/50 transition"
          >
            <Check size={15} />
            <span>Áp dụng vào Slide</span>
          </button>
        </div>
      </div>
    </div>
  );
}
