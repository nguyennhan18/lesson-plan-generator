r"""
Automated Acceptance Test Suite — Day 9 (Cơ chế Đồng bộ 2 Chiều MathLive <-> Slide JSON)
Kiểm tra toàn diện 5 hạng mục của Ngày 9 theo Ke_Hoach_Phat_Trien.pdf:
- Task 9.1: Khi GV bấm "Lưu công thức", lấy chuỗi LaTeX chuẩn từ mathfield.getValue('latex-expanded') & bảo toàn ngữ cảnh prefix/suffix
- Task 9.2: Cập nhật chuỗi LaTeX mới vào cấu trúc Slide JSON đang lưu trữ trong bộ nhớ trình duyệt (slideDeckStorage.js)
- Task 9.3: Render lại ngay công thức đó bằng KaTeX trên slide preview kèm hiệu ứng highlight xác nhận kết quả
- Task 9.4: Viết hàm kiểm tra cú pháp LaTeX hợp lệ trước khi lưu để tránh hỏng slide (latexValidator.js - 4 tầng kiểm tra)
- Task 9.5 (DoD): Sửa công thức từ y = 2x thành y = x^2 + 1 bằng MathLive -> Nhấn Lưu -> Slide hiển thị đúng y = x^2 + 1 bằng KaTeX
"""

import json
import subprocess
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
FRONTEND_DIR = ROOT_DIR / "app" / "frontend"
MATHLIVE_MODAL = FRONTEND_DIR / "src" / "components" / "MathLiveModal.jsx"
MATHTEXT_JSX = FRONTEND_DIR / "src" / "components" / "MathText.jsx"
PRESENTATION_STAGE = FRONTEND_DIR / "src" / "components" / "PresentationStage.jsx"
SLIDE_EDITOR = FRONTEND_DIR / "src" / "components" / "SlideEditorScreen.jsx"
APP_JSX = FRONTEND_DIR / "src" / "App.jsx"
SLIDE_DECK_STORAGE = FRONTEND_DIR / "src" / "utils" / "slideDeckStorage.js"
LATEX_VALIDATOR = FRONTEND_DIR / "src" / "utils" / "latexValidator.js"


def test_task_9_1_latex_expanded_extraction_and_context_preservation():
    """
    Task 9.1: Kiểm tra trích xuất LaTeX chuẩn bằng mathfield.getValue('latex-expanded')
    và bảo toàn ngữ cảnh câu văn (prefix / suffix) khi sửa công thức nội dòng.
    """
    assert MATHLIVE_MODAL.exists(), "Không tìm thấy MathLiveModal.jsx"
    modal_code = MATHLIVE_MODAL.read_text(encoding="utf-8")

    # 1. Kiểm tra hàm trích xuất trực tiếp từ DOM <math-field> bằng getValue('latex-expanded')
    assert "getExpandedLatexFromMathField" in modal_code, (
        "Thiếu hàm getExpandedLatexFromMathField trong MathLiveModal.jsx"
    )
    assert "getValue('latex-expanded')" in modal_code, (
        "Phải gọi mathFieldEl.getValue('latex-expanded') khi trích xuất công thức"
    )

    # 2. Kiểm tra tách & đóng gói lại prefix / suffix để không làm mất lời dẫn tiếng Việt trong bullet_points
    assert "unwrapLatexDelimiters" in modal_code
    assert "wrapLatexDelimiters" in modal_code
    assert "prefix" in modal_code and "suffix" in modal_code, (
        "unwrapLatexDelimiters / wrapLatexDelimiters phải hỗ trợ bảo toàn prefix và suffix"
    )


def test_task_9_2_browser_memory_slide_json_sync():
    """
    Task 9.2: Kiểm tra cập nhật chuỗi LaTeX mới vào cấu trúc Slide JSON
    đang lưu trữ trong bộ nhớ trình duyệt (sessionStorage + window.__LESSONAI_SLIDE_DECK_JSON__).
    """
    assert SLIDE_DECK_STORAGE.exists(), "Không tìm thấy app/frontend/src/utils/slideDeckStorage.js"
    storage_code = SLIDE_DECK_STORAGE.read_text(encoding="utf-8")

    # Kiểm tra các hàm cốt lõi trong slideDeckStorage.js
    required_exports = [
        "SLIDE_DECK_STORAGE_KEY",
        "loadSlideDeckFromBrowserMemory",
        "saveSlideDeckToBrowserMemory",
        "updateSlideFormulaInDeck",
    ]
    for symbol in required_exports:
        assert symbol in storage_code, f"Thiếu {symbol} trong slideDeckStorage.js"

    assert "sessionStorage" in storage_code, "slideDeckStorage.js phải đồng bộ với sessionStorage"
    assert "__LESSONAI_SLIDE_DECK_JSON__" in storage_code, (
        "slideDeckStorage.js phải đồng bộ với biến bộ nhớ window.__LESSONAI_SLIDE_DECK_JSON__"
    )

    # Kiểm tra kết nối đồng bộ 2 chiều trong App.jsx, PresentationStage.jsx và SlideEditorScreen.jsx
    app_code = APP_JSX.read_text(encoding="utf-8")
    stage_code = PRESENTATION_STAGE.read_text(encoding="utf-8")
    editor_code = SLIDE_EDITOR.read_text(encoding="utf-8")

    assert "loadSlideDeckFromBrowserMemory" in app_code
    assert "saveSlideDeckToBrowserMemory" in app_code
    assert "updateSlideFormulaInDeck" in stage_code
    assert "updateSlideFormulaInDeck" in editor_code


def test_task_9_3_katex_instant_rerender_and_visual_highlight():
    """
    Task 9.3: Kiểm tra cơ chế render lại ngay công thức bằng KaTeX trên slide preview
    kèm hiệu ứng highlight xác nhận kết quả (✓ Đã cập nhật KaTeX).
    """
    assert MATHTEXT_JSX.exists(), "Không tìm thấy MathText.jsx"
    mathtext_code = MATHTEXT_JSX.read_text(encoding="utf-8")
    stage_code = PRESENTATION_STAGE.read_text(encoding="utf-8")
    editor_code = SLIDE_EDITOR.read_text(encoding="utf-8")

    # Kiểm tra MathText.jsx chuẩn hóa delimiter và gọi katex.renderToString
    assert "stripOuterMathDelimiters" in mathtext_code, (
        "MathText.jsx phải có hàm stripOuterMathDelimiters để chuẩn hóa công thức trước khi render"
    )
    assert "katex.renderToString" in mathtext_code

    # Kiểm tra hiệu ứng highlight xác nhận kết quả trên cả Sân khấu (PresentationStage) và Xưởng Slide (SlideEditorScreen)
    assert "recentlyUpdatedFormula" in stage_code
    assert "isFormulaRecentlyUpdated" in stage_code
    assert "Đã cập nhật KaTeX" in stage_code

    assert "isFormulaUpdated" in editor_code
    assert "Đã cập nhật & kết xuất KaTeX mới" in editor_code


def test_task_9_4_latex_syntax_validator_four_layers():
    """
    Task 9.4: Kiểm tra bộ kiểm duyệt cú pháp LaTeX 4 tầng (latexValidator.js)
    và chốt chặn an toàn trước khi lưu trong MathLiveModal.jsx + SlideEditorScreen.jsx.
    """
    assert LATEX_VALIDATOR.exists(), "Không tìm thấy app/frontend/src/utils/latexValidator.js"
    validator_code = LATEX_VALIDATOR.read_text(encoding="utf-8")

    for fn_name in [
        "checkUnfilledPlaceholders",
        "checkBraceBalance",
        "checkEnvironmentBalance",
        "validateLatexSyntax",
    ]:
        assert fn_name in validator_code, f"Thiếu hàm {fn_name} trong latexValidator.js"

    # Kiểm tra tích hợp chốt chặn trong MathLiveModal.jsx và SlideEditorScreen.jsx
    modal_code = MATHLIVE_MODAL.read_text(encoding="utf-8")
    editor_code = SLIDE_EDITOR.read_text(encoding="utf-8")
    assert "validateLatexSyntax" in modal_code
    assert "validateLatexSyntax" in editor_code


def test_task_9_5_dod_end_to_end_formula_update_y_2x_to_x2_plus_1():
    """
    Task 9.5 (DoD Ngày 9):
    Chạy kịch bản thực thi End-to-End bằng Node.js runtime:
    1. Khởi tạo Slide JSON chứa công thức $$y = 2x$$ và bullet "Xét hàm số $y = 2x$ trên tập số thực".
    2. Giả lập GV sửa công thức từ y = 2x thành y = x^2 + 1 trong MathLive -> Nhấn Lưu.
    3. Kiểm tra validateLatexSyntax('y = x^2 + 1') trả về isValid=True và render ra HTML KaTeX chuẩn.
    4. Cập nhật vào Slide JSON bằng updateSlideFormulaInDeck & lưu vào bộ nhớ trình duyệt giả lập (sessionStorage).
    5. Kiểm tra dữ liệu đọc lại từ bộ nhớ trình duyệt có đúng $$y = x^2 + 1$$ và tính bất biến (immutability).
    6. Kiểm tra các công thức lỗi (\\frac{1}{, \\sqrt{}, \\begin{cases} x, rỗng) bị chặn 100%, không làm hỏng slide.
    """
    node_script = r"""
import katex from 'katex';
import { validateLatexSyntax } from './src/utils/latexValidator.js';
import {
  SLIDE_DECK_STORAGE_KEY,
  saveSlideDeckToBrowserMemory,
  loadSlideDeckFromBrowserMemory,
  updateSlideFormulaInDeck,
} from './src/utils/slideDeckStorage.js';

// Giả lập môi trường bộ nhớ trình duyệt (window + sessionStorage)
const memoryStore = new Map();
globalThis.window = {
  sessionStorage: {
    getItem: (k) => (memoryStore.has(k) ? memoryStore.get(k) : null),
    setItem: (k, v) => memoryStore.set(k, String(v)),
    removeItem: (k) => memoryStore.delete(k),
  },
};

// 1. Khởi tạo Slide Deck ban đầu với công thức y = 2x
const initialDeck = {
  presentation_title: 'Bài giảng Hàm số Bậc hai',
  slides: [
    {
      slide_number: 1,
      title: 'Khảo sát hàm số bậc hai',
      layout: 'CONCEPT_HIGHLIGHT',
      main_definition_latex: '$$y = 2x$$',
      bullet_points: ['Xét hàm số $y = 2x$ trên tập số thực'],
    },
  ],
};
saveSlideDeckToBrowserMemory(initialDeck);

// 2. GV sửa công thức từ "y = 2x" sang "y = x^2 + 1" trên MathLive và bấm Lưu
const newCleanLatex = 'y = x^2 + 1';
const validation = validateLatexSyntax(newCleanLatex, { displayMode: true });

if (!validation.isValid) {
  throw new Error('DoD Failed: Công thức hợp lệ y = x^2 + 1 bị báo lỗi: ' + validation.errorMessage);
}

// Render ngay bằng KaTeX để xác nhận HTML hiển thị trên Slide Preview
const renderedHtml = katex.renderToString(validation.normalizedLatex, {
  displayMode: true,
  throwOnError: true,
});

// 3. Cập nhật vào Slide JSON (main_definition_latex và bullet_points[0])
const wrappedDisplayLatex = `$$${validation.normalizedLatex}$$`;
const deckAfterMathUpdate = updateSlideFormulaInDeck(initialDeck, {
  slideIndex: 0,
  targetField: 'main_definition_latex',
  formattedLatex: wrappedDisplayLatex,
  rawExpandedLatex: validation.normalizedLatex,
});

const wrappedInlineBullet = `Xét hàm số $${validation.normalizedLatex}$ trên tập số thực`;
const deckAfterBulletUpdate = updateSlideFormulaInDeck(deckAfterMathUpdate, {
  slideIndex: 0,
  targetField: 'bullet_point',
  bulletIndex: 0,
  formattedLatex: wrappedInlineBullet,
  rawExpandedLatex: validation.normalizedLatex,
});

// 4. Đọc lại từ bộ nhớ trình duyệt (sessionStorage) để kiểm chứng đồng bộ 2 chiều
const persistedDeck = loadSlideDeckFromBrowserMemory(null);

// 5. Kiểm chứng các trường hợp công thức lỗi phải bị chặn 100% trước khi lưu
const invalidCases = [
  '\\frac{1}{',
  '\\sqrt{}',
  '\\frac{x}{\\placeholder{}}',
  '\\begin{cases} x + y = 1',
  '   ',
];
const blockedResults = invalidCases.map((expr) => ({
  expr,
  result: validateLatexSyntax(expr, { displayMode: true }),
}));

console.log(JSON.stringify({
  dodValid: validation.isValid,
  normalizedLatex: validation.normalizedLatex,
  katexHtmlHasSup2: renderedHtml.includes('2') && renderedHtml.includes('katex'),
  initialFormulaUnchanged: initialDeck.slides[0].main_definition_latex === '$$y = 2x$$',
  updatedFormulaInMemory: persistedDeck.slides[0].main_definition_latex,
  updatedBulletInMemory: persistedDeck.slides[0].bullet_points[0],
  lastExpandedLatexRecorded: persistedDeck.slides[0].last_expanded_latex,
  windowGlobalSynced: globalThis.window.__LESSONAI_SLIDE_DECK_JSON__.slides[0].main_definition_latex,
  storageKeyExists: memoryStore.has(SLIDE_DECK_STORAGE_KEY),
  allInvalidBlocked: blockedResults.every((item) => item.result.isValid === false && Boolean(item.result.errorMessage)),
  blockedDetails: blockedResults.map((item) => ({
    expr: item.expr,
    code: item.result.code,
    isValid: item.result.isValid,
    errorMessage: item.result.errorMessage,
  })),
}));
"""
    proc = subprocess.run(
        ["node", "--input-type=module", "-e", node_script],
        cwd=str(FRONTEND_DIR),
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(proc.stdout.strip())

    assert payload["dodValid"] is True, "Công thức DoD y = x^2 + 1 phải hợp lệ"
    assert payload["normalizedLatex"] == "y = x^2 + 1"
    assert payload["katexHtmlHasSup2"] is True, "KaTeX phải render thành công HTML cho y = x^2 + 1"
    assert payload["initialFormulaUnchanged"] is True, "Phải đảm bảo tính bất biến (Immutability) của initialDeck"
    assert payload["updatedFormulaInMemory"] == "$$y = x^2 + 1$$", (
        f"Slide JSON trong sessionStorage phải được cập nhật thành $$y = x^2 + 1$$, nhận được: {payload['updatedFormulaInMemory']}"
    )
    assert payload["updatedBulletInMemory"] == "Xét hàm số $y = x^2 + 1$ trên tập số thực", (
        "Câu văn chứa công thức nội dòng trong bullet_points phải bảo toàn ngữ cảnh tiếng Việt"
    )
    assert payload["lastExpandedLatexRecorded"] == "y = x^2 + 1"
    assert payload["windowGlobalSynced"] == "$$y = x^2 + 1$$"
    assert payload["storageKeyExists"] is True
    assert payload["allInvalidBlocked"] is True, (
        f"Tất cả công thức lỗi phải bị chặn trước khi lưu: {payload['blockedDetails']}"
    )


class TestDay9TwoWaySync(unittest.TestCase):
    def test_9_1_latex_expanded_extraction(self):
        test_task_9_1_latex_expanded_extraction_and_context_preservation()

    def test_9_2_browser_memory_sync(self):
        test_task_9_2_browser_memory_slide_json_sync()

    def test_9_3_katex_instant_rerender(self):
        test_task_9_3_katex_instant_rerender_and_visual_highlight()

    def test_9_4_latex_syntax_validator(self):
        test_task_9_4_latex_syntax_validator_four_layers()

    def test_9_5_dod_y_2x_to_x2_plus_1(self):
        test_task_9_5_dod_end_to_end_formula_update_y_2x_to_x2_plus_1()


if __name__ == "__main__":
    unittest.main()
