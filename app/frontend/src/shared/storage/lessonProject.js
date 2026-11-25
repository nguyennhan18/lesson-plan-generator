/**
 * Bài giảng bản 3 (schema_version 3): the project format of the Bàn làm việc (spec #36).
 *
 * {
 *   schema_version: 3, project_id, title, sgk?, level?,
 *   outline: { items: [Mục dàn ý] },
 *   deck: null | { revision, review_token?, slides: [Slide] },   // Bộ slide and its Xác nhận chuyên môn
 *   plan: null | {...},                                          // Kế hoạch bài dạy (optional)
 *   annotations: { [slide_id]: [...] }, polls: { [slide_id]: {...} }
 * }
 * Mục dàn ý: { item_id, activity, kind, title, points[], slide_count (1–4), minutes, visuals[], needs_review }
 * Yêu cầu trực quan: { visual_id, kind (graph|bbt|oxyz|solid), origin (ai|teacher), status (proposed|confirmed),
 *                      data {}, requirement_token (required when confirmed), source_fingerprint?, label? }
 * Slide: { slide_id, item_id, layout (Bố cục mẫu), notes, elements[] }, in Dàn ý order
 * Phần tử: { element_id, type, x, y, w, h (logical 1600 × 900), reveal (≥ 0), parts (≥ 1), visual_id (figures only) }
 *
 * Field names follow the snake_case of the v2 envelope and the API; visual confirmations are bound to
 * project_id + item_id (#37). Normalization makes defaults explicit and keeps unknown fields. It rejects
 * wrong data with a clear message and never fills in content.
 */
import { LEGACY_SCHEMA_VERSION, LESSON_SCHEMA_VERSION, UNSUPPORTED_VERSION, listProjects, loadProject, saveProject } from './projectStore.js';

export const LESSON_MINUTES = 45;
export const ACTIVITIES = ['Khởi động', 'Hình thành kiến thức', 'Luyện tập', 'Vận dụng'];
export const ITEM_KINDS = ['Mở đầu', 'Tình huống khởi động', 'Kiến thức trọng tâm', 'Ví dụ', 'Bài luyện tập', 'Câu hỏi trắc nghiệm', 'Tổng kết'];
export const KIND_ACTIVITY = { 'Mở đầu': 'Khởi động', 'Tổng kết': 'Vận dụng' };
export const VISUAL_KIND_NAMES = { graph: 'Đồ thị hàm số', bbt: 'Bảng biến thiên', oxyz: 'Hình Oxyz', solid: 'Khối đa diện' };
const VISUAL_KINDS = Object.keys(VISUAL_KIND_NAMES);
const VISUAL_ORIGINS = ['ai', 'teacher'];
const VISUAL_STATUSES = ['proposed', 'confirmed'];
const EXPRESSION_KINDS = new Set(['graph', 'bbt']); // these are computed from a function expression (#51, #55)
const STAGE = { width: 1600, height: 900 };
const ELEMENT_TYPES = ['title', 'paragraph', 'text', 'steps', 'formula', 'table', 'image', 'caption', 'graph', 'bbt', 'oxyz', 'solid', 'quiz'];
const FIGURE_TYPES = new Set(VISUAL_KINDS);
const EDGE = 1e-6; // tolerance for positions computed in floating point

export class LessonDataError extends Error {
  constructor(message) {
    super(message);
    this.name = 'LessonDataError';
  }
}
const fail = problem => { throw new LessonDataError(`Dữ liệu Bài giảng không hợp lệ: ${problem}`); };

const isRecord = value => value !== null && typeof value === 'object' && !Array.isArray(value);
const isFilledText = value => typeof value === 'string' && value.trim() !== '';
const isWholeNumberIn = (value, min, max) => Number.isInteger(value) && value >= min && value <= max;
const requireOptionalText = (value, name) => {
  if (value != null && typeof value !== 'string') fail(`${name} phải là chữ.`);
};
// Vietnamese values typed on some systems arrive decomposed (NFD); store the composed form (NFC).
const nfc = value => (typeof value === 'string' ? value.normalize('NFC').trim() : value);

// A visual is confirmed only by a server-signed token (ADR 0005). Beyond the expression of graphs and
// Bảng biến thiên, the data of each kind is checked by its confirmation endpoint, not here.
function normalizeVisuals(visuals, owner, seen) {
  if (!Array.isArray(visuals)) fail(`${owner}: Yêu cầu trực quan (visuals) phải là danh sách.`);
  return visuals.map((raw, index) => {
    const n = index + 1;
    if (!isRecord(raw)) fail(`${owner}, Yêu cầu trực quan ${n} không đúng cấu trúc.`);
    if (!isFilledText(raw.visual_id)) fail(`${owner}, Yêu cầu trực quan ${n}: thiếu ID (visual_id).`);
    if (seen.has(raw.visual_id)) fail(`${owner}, Yêu cầu trực quan ${n}: ID «${raw.visual_id}» bị trùng với hình của ${seen.get(raw.visual_id)}.`);
    seen.set(raw.visual_id, owner);
    const where = `${owner}, Yêu cầu trực quan ${n} («${raw.visual_id}»)`;
    if (!VISUAL_KINDS.includes(raw.kind)) fail(`${where}: loại hình «${raw.kind}» không hợp lệ; chỉ nhận ${VISUAL_KINDS.join(', ')}.`);
    if (!VISUAL_ORIGINS.includes(raw.origin)) fail(`${where}: nguồn «${raw.origin}» không hợp lệ; chỉ nhận ${VISUAL_ORIGINS.join(', ')}.`);
    if (!VISUAL_STATUSES.includes(raw.status)) fail(`${where}: trạng thái «${raw.status}» không hợp lệ; chỉ nhận ${VISUAL_STATUSES.join(', ')}.`);
    if (!isRecord(raw.data)) fail(`${where}: thiếu dữ kiện (data).`);
    if (EXPRESSION_KINDS.has(raw.kind) && !isFilledText(raw.data.expression)) fail(`${where}: ${VISUAL_KIND_NAMES[raw.kind]} cần biểu thức (data.expression).`);
    requireOptionalText(raw.label, `${where}: nhãn hình (label)`);
    if (raw.status === 'confirmed' && !isFilledText(raw.requirement_token))
      fail(`${where}: ghi đã xác nhận nhưng không có token xác nhận (requirement_token); dữ kiện hình chỉ được xác nhận qua máy chủ.`);
    return { ...raw };
  });
}

function normalizeItems(items) {
  if (!Array.isArray(items)) fail('Dàn ý (outline) phải có danh sách Mục (outline.items).');
  const seen = new Map(), visualIds = new Map();
  let previous = 0;
  return items.map((raw, index) => {
    const n = index + 1;
    if (!isRecord(raw)) fail(`Mục ${n} không đúng cấu trúc.`);
    if (!isFilledText(raw.item_id)) fail(`Mục ${n}: thiếu ID Mục (item_id).`);
    if (seen.has(raw.item_id)) fail(`Mục ${n}: ID Mục «${raw.item_id}» bị trùng với Mục ${seen.get(raw.item_id)}.`);
    seen.set(raw.item_id, n);
    const where = `Mục ${n} («${raw.item_id}»)`;
    const activity = nfc(raw.activity);
    if (!ACTIVITIES.includes(activity)) fail(`${where}: Hoạt động «${raw.activity}» không hợp lệ; chỉ nhận ${ACTIVITIES.join(', ')}.`);
    const order = ACTIVITIES.indexOf(activity);
    if (order < previous) fail(`${where}: Mục thuộc ${activity} đứng sau Mục thuộc ${ACTIVITIES[previous]}; Dàn ý phải theo thứ tự ${ACTIVITIES.join(' → ')}.`);
    previous = order;
    const kind = nfc(raw.kind);
    if (!ITEM_KINDS.includes(kind)) fail(`${where}: Loại mục «${raw.kind}» không hợp lệ; chỉ nhận ${ITEM_KINDS.join(', ')}.`);
    if (KIND_ACTIVITY[kind] && KIND_ACTIVITY[kind] !== activity) fail(`${where}: Mục ${kind} phải thuộc Hoạt động ${KIND_ACTIVITY[kind]}.`);
    if (!isFilledText(raw.title)) fail(`${where}: thiếu tiêu đề.`);
    const points = raw.points ?? [];
    if (!Array.isArray(points) || !points.every(point => typeof point === 'string')) fail(`${where}: các ý (points) phải là danh sách chữ.`);
    if (!isWholeNumberIn(raw.slide_count, 1, 4)) fail(`${where}: số slide phải là số nguyên từ 1 đến 4.`);
    if (!isWholeNumberIn(raw.minutes, 1, LESSON_MINUTES)) fail(`${where}: số phút phải là số nguyên từ 1 đến ${LESSON_MINUTES}.`);
    const needs_review = raw.needs_review ?? false;
    if (typeof needs_review !== 'boolean') fail(`${where}: dấu Cần xem lại (needs_review) phải là true hoặc false.`);
    const visuals = normalizeVisuals(raw.visuals ?? [], where, visualIds);
    return { ...raw, activity, kind, points, visuals, needs_review };
  });
}

function normalizeElement(raw, n, slide, context) {
  const owner = `Slide ${slide.n} («${slide.slide_id}»), phần tử ${n}`;
  if (!isRecord(raw)) fail(`${owner} không đúng cấu trúc.`);
  if (!isFilledText(raw.element_id)) fail(`${owner}: thiếu ID phần tử (element_id).`);
  if (context.elementIds.has(raw.element_id)) fail(`${owner}: ID phần tử «${raw.element_id}» bị trùng.`);
  context.elementIds.add(raw.element_id);
  const where = `${owner} («${raw.element_id}»)`;
  if (!ELEMENT_TYPES.includes(raw.type)) fail(`${where}: loại phần tử «${raw.type}» không hợp lệ; chỉ nhận ${ELEMENT_TYPES.join(', ')}.`);
  const { x, y, w, h } = raw;
  if (![x, y, w, h].every(Number.isFinite)) fail(`${where}: vị trí và kích thước (x, y, w, h) phải là số.`);
  if (w <= 0 || h <= 0) fail(`${where}: kích thước (w, h) phải lớn hơn 0.`);
  if (x < -EDGE || y < -EDGE || x + w > STAGE.width + EDGE || y + h > STAGE.height + EDGE)
    fail(`${where}: nằm ngoài khung slide ${STAGE.width} × ${STAGE.height}.`);
  const reveal = raw.reveal ?? 0, parts = raw.parts ?? 1;
  if (!isWholeNumberIn(reveal, 0, Infinity)) fail(`${where}: bước bắt đầu hiện (reveal) phải là số nguyên không âm.`);
  if (!isWholeNumberIn(parts, 1, Infinity)) fail(`${where}: số bước hiện dần (parts) phải là số nguyên dương.`);
  if (FIGURE_TYPES.has(raw.type)) {
    // ADR 0003: a figure exists only through a Yêu cầu trực quan of the slide's own Mục.
    if (!isFilledText(raw.visual_id)) fail(`${where}: phần tử hình phải trỏ tới một Yêu cầu trực quan (visual_id) của Mục.`);
    const found = context.visuals.get(raw.visual_id);
    if (!found) fail(`${where}: Yêu cầu trực quan «${raw.visual_id}» không có trong Dàn ý.`);
    if (found.item_id !== slide.item_id) fail(`${where}: hình «${raw.visual_id}» thuộc Mục «${found.item_id}», không được đặt trên slide của Mục «${slide.item_id}».`);
    if (found.kind !== raw.type) fail(`${where}: phần tử loại ${raw.type} không khớp loại hình ${found.kind} của «${raw.visual_id}».`);
  } else if (raw.visual_id != null) {
    fail(`${where}: chỉ phần tử hình (${VISUAL_KINDS.join(', ')}) mới trỏ tới Yêu cầu trực quan.`);
  }
  return { ...raw, reveal, parts };
}

function normalizeSlide(raw, index, context) {
  const n = index + 1;
  if (!isRecord(raw)) fail(`Slide ${n} không đúng cấu trúc.`);
  if (!isFilledText(raw.slide_id)) fail(`Slide ${n}: thiếu ID slide (slide_id).`);
  if (context.slideIds.has(raw.slide_id)) fail(`Slide ${n}: ID slide «${raw.slide_id}» bị trùng.`);
  context.slideIds.add(raw.slide_id);
  const where = `Slide ${n} («${raw.slide_id}»)`;
  if (!isFilledText(raw.item_id)) fail(`${where}: thiếu ID Mục (item_id); mọi slide phải thuộc một Mục dàn ý.`);
  if (!context.positions.has(raw.item_id)) fail(`${where}: ID Mục «${raw.item_id}» không có trong Dàn ý.`);
  if (!isFilledText(raw.layout)) fail(`${where}: thiếu tên Bố cục mẫu (layout).`);
  const notes = raw.notes ?? '';
  if (typeof notes !== 'string') fail(`${where}: ghi chú giáo viên (notes) phải là chữ.`);
  if (!Array.isArray(raw.elements)) fail(`${where}: danh sách phần tử (elements) phải là mảng.`);
  const slide = { n, slide_id: raw.slide_id, item_id: raw.item_id };
  return { ...raw, notes, elements: raw.elements.map((element, i) => normalizeElement(element, i + 1, slide, context)) };
}

// The Bộ slide follows the Dàn ý: slides grouped by Mục, in outline order.
function normalizeLessonDeck(deck, items) {
  if (!isRecord(deck)) fail('Bộ slide (deck) không đúng cấu trúc.');
  if (!Array.isArray(deck.slides)) fail('Bộ slide phải có danh sách slide (deck.slides).');
  const revision = deck.revision ?? 0;
  if (!isWholeNumberIn(revision, 0, Infinity)) fail('số phiên bản Bộ slide (deck.revision) phải là số nguyên không âm.');
  const context = {
    positions: new Map(items.map((item, index) => [item.item_id, index])),
    visuals: new Map(items.flatMap(item => item.visuals.map(visual => [visual.visual_id, { item_id: item.item_id, kind: visual.kind }]))),
    slideIds: new Set(), elementIds: new Set()
  };
  let previous = 0;
  const slides = deck.slides.map((raw, index) => {
    const slide = normalizeSlide(raw, index, context);
    const position = context.positions.get(slide.item_id);
    if (position < previous)
      fail(`Slide ${index + 1} («${slide.slide_id}»): thuộc Mục ${position + 1} («${slide.item_id}») nhưng đứng sau slide của Mục ${previous + 1}; Bộ slide phải theo thứ tự Dàn ý.`);
    previous = position;
    return slide;
  });
  return { ...deck, revision, slides };
}

function optionalRecord(value, name) {
  if (value == null) return {};
  if (!isRecord(value)) fail(`${name} không đúng cấu trúc.`);
  return value;
}

export const STAGE_SIZE = STAGE;
export const SNAP_GRID = 20;
const TEXT_ELEMENT_TYPES = new Set(['title', 'paragraph', 'text', 'steps', 'caption']);
const MIN_FONT_PX = 24;

export const snapToGrid = (value, grid = SNAP_GRID) => Math.round(value / grid) * grid;

/**
 * Estimate optimal font size (down to MIN_FONT_PX = 24pt equivalent on 1600×900) and whether text still overflows (#42).
 */
export function measureElementTextFit(element) {
  if (!element || !TEXT_ELEMENT_TYPES.has(element.type)) {
    return { fontSize: null, overflow: false };
  }
  const baseSizes = { title: element.hero ? 88 : 64, paragraph: 38, text: 36, steps: 34, caption: 26 };
  const base = baseSizes[element.type] || 34;
  const lines = Array.isArray(element.items)
    ? element.items
    : typeof element.text === 'string'
      ? element.text.split('\n')
      : [];
  const totalChars = lines.reduce((sum, line) => sum + (line || '').length, 0);
  if (totalChars === 0) return { fontSize: base, overflow: false };

  const padX = element.type === 'steps' ? 84 : element.type === 'text' ? 52 : 16;
  const padY = 16;
  const availW = Math.max(40, (element.w || 160) - padX);
  const availH = Math.max(24, (element.h || 60) - padY);

  const fitsAt = size => {
    const charW = size * 0.54;
    const cols = Math.max(1, Math.floor(availW / charW));
    const lineH = size * 1.38;
    const gap = (element.type === 'text' || element.type === 'steps') ? size * 0.45 : 0;
    const neededLines = lines.reduce((sum, line) => sum + Math.max(1, Math.ceil((line || '').length / cols)), 0);
    const neededH = neededLines * lineH + Math.max(0, lines.length - 1) * gap;
    return neededH <= availH;
  };

  for (let size = base; size >= MIN_FONT_PX; size -= 2) {
    if (fitsAt(size)) return { fontSize: size, overflow: false };
  }
  return { fontSize: MIN_FONT_PX, overflow: true };
}

export function detectElementOverflow(element) {
  return measureElementTextFit(element).overflow;
}

/**
 * Move, resize, or edit an element on a canvas slide (#42, #48).
 * Snaps x, y, w, h to the 20-unit grid within 1600×900, marks overflow when text exceeds minimum font size,
 * increments deck.revision, clears deck.review_token, and marks the slide edited: true. Dàn ý never changes.
 */
export function updateSlideElement(lesson, slideId, elementId, changes, { snap = true, minW = 160, minH = 60 } = {}) {
  if (!lesson?.deck?.slides) fail('Bài giảng chưa có Bộ slide.');
  let touched = false;
  let touchedItemId = null;
  let contentModified = false;
  let quizContentModified = false;

  const slides = lesson.deck.slides.map(slide => {
    if (slide.slide_id !== slideId) return slide;
    let slideChanged = false;
    const elements = slide.elements.map(el => {
      if (el.element_id !== elementId) return el;
      const next = { ...el, ...changes };
      if (changes.w !== undefined || changes.h !== undefined) {
        const rawW = changes.w !== undefined ? changes.w : el.w;
        const rawH = changes.h !== undefined ? changes.h : el.h;
        next.w = Math.max(minW, Math.min(STAGE.width - el.x, snap ? snapToGrid(rawW) : rawW));
        next.h = Math.max(minH, Math.min(STAGE.height - el.y, snap ? snapToGrid(rawH) : rawH));
      }
      if (changes.x !== undefined || changes.y !== undefined) {
        const rawX = changes.x !== undefined ? changes.x : el.x;
        const rawY = changes.y !== undefined ? changes.y : el.y;
        next.x = Math.max(0, Math.min(STAGE.width - next.w, snap ? snapToGrid(rawX) : rawX));
        next.y = Math.max(0, Math.min(STAGE.height - next.h, snap ? snapToGrid(rawY) : rawY));
      }
      if (Array.isArray(next.items) && (next.type === 'text' || next.type === 'steps') && changes.items !== undefined && changes.parts === undefined) {
        next.parts = Math.max(1, next.items.length);
      }
      if (TEXT_ELEMENT_TYPES.has(next.type)) {
        next.overflow = changes.overflow !== undefined ? Boolean(changes.overflow) : detectElementOverflow(next);
      }
      if (JSON.stringify(next) !== JSON.stringify(el)) {
        slideChanged = true;
        touched = true;
        touchedItemId = slide.item_id;
        for (const k of ['text', 'items', 'latex', 'headers', 'rows', 'question', 'options']) {
          if (changes[k] !== undefined && JSON.stringify(changes[k]) !== JSON.stringify(el[k])) {
            contentModified = true;
          }
        }
        if (next.type === 'quiz' && (
          (changes.question !== undefined && changes.question !== el.question) ||
          (changes.options !== undefined && JSON.stringify(changes.options) !== JSON.stringify(el.options))
        )) {
          quizContentModified = true;
        }
      }
      return next;
    });
    return slideChanged ? { ...slide, edited: true, elements } : slide;
  });
  if (!touched) return lesson;

  // #47: Editing quiz question or options clears the saved poll for that slide.
  const nextPolls = { ...(lesson.polls || {}) };
  if (quizContentModified) {
    delete nextPolls[slideId];
  }

  // #51: Editing problem text/formula on a slide resets confirmed visuals of that slide's Mục to proposed.
  const nextItems = contentModified && touchedItemId
    ? lesson.outline.items.map(item => {
        if (item.item_id !== touchedItemId) return item;
        return {
          ...item,
          visuals: item.visuals.map(visual => {
            if (visual.status !== 'confirmed') return visual;
            const { requirement_token, source_fingerprint, ...proposal } = visual;
            return { ...proposal, status: 'proposed' };
          }),
        };
      })
    : lesson.outline.items;

  const { review_token, ...restDeck } = lesson.deck;
  return normalizeLesson({
    ...lesson,
    outline: { ...lesson.outline, items: nextItems },
    polls: nextPolls,
    deck: {
      ...restDeck,
      revision: (lesson.deck.revision ?? 0) + 1,
      slides,
    },
  });
}

/**
 * Add a new non-figure element (paragraph, text, steps, formula, table, image) to a slide (#48).
 */
export function addSlideElement(lesson, slideId, elementInput) {
  if (!lesson?.deck?.slides) fail('Bài giảng chưa có Bộ slide.');
  const type = elementInput?.type || 'paragraph';
  if (FIGURE_TYPES.has(type)) fail('Hình tương tác phải được thêm qua Yêu cầu trực quan của Mục.');
  const defaultBoxes = {
    paragraph: { x: 100, y: 200, w: 1200, h: 140, text: 'Nội dung mới' },
    text: { x: 100, y: 240, w: 1200, h: 320, items: ['Ý thứ nhất', 'Ý thứ hai'], parts: 2 },
    steps: { x: 100, y: 240, w: 1200, h: 360, items: ['Bước 1', 'Bước 2'], parts: 2 },
    formula: { x: 100, y: 660, w: 1200, h: 140, latex: "f'(x) = 0" },
    table: { x: 100, y: 240, w: 1200, h: 360, headers: ['x', 'y'], rows: [['0', '1'], ['1', '0']] },
    image: { x: 200, y: 200, w: 800, h: 460, src: elementInput?.src || '', alt: elementInput?.alt || 'Hình ảnh trên slide' },
    caption: { x: 100, y: 780, w: 1200, h: 60, text: 'Chú thích' },
  };
  const base = defaultBoxes[type] || defaultBoxes.paragraph;
  const el = {
    element_id: elementInput?.element_id || crypto.randomUUID(),
    type,
    ...base,
    ...elementInput,
    x: snapToGrid(elementInput?.x ?? base.x),
    y: snapToGrid(elementInput?.y ?? base.y),
    w: snapToGrid(elementInput?.w ?? base.w),
    h: snapToGrid(elementInput?.h ?? base.h),
    reveal: elementInput?.reveal ?? 0,
    parts: elementInput?.parts ?? base.parts ?? 1,
  };
  if (TEXT_ELEMENT_TYPES.has(el.type)) {
    el.overflow = detectElementOverflow(el);
  }
  let added = false;
  const slides = lesson.deck.slides.map(slide => {
    if (slide.slide_id !== slideId) return slide;
    added = true;
    return { ...slide, edited: true, elements: [...slide.elements, el] };
  });
  if (!added) fail(`Không tìm thấy slide «${slideId}».`);
  const { review_token, ...restDeck } = lesson.deck;
  return normalizeLesson({
    ...lesson,
    deck: {
      ...restDeck,
      revision: (lesson.deck.revision ?? 0) + 1,
      slides,
    },
  });
}

/**
 * Remove an element from a slide (#48).
 */
export function removeSlideElement(lesson, slideId, elementId) {
  if (!lesson?.deck?.slides) fail('Bài giảng chưa có Bộ slide.');
  let removed = false;
  const slides = lesson.deck.slides.map(slide => {
    if (slide.slide_id !== slideId) return slide;
    const nextElements = slide.elements.filter(el => el.element_id !== elementId);
    if (nextElements.length === slide.elements.length) return slide;
    removed = true;
    return { ...slide, edited: true, elements: nextElements };
  });
  if (!removed) return lesson;
  const { review_token, ...restDeck } = lesson.deck;
  return normalizeLesson({
    ...lesson,
    deck: {
      ...restDeck,
      revision: (lesson.deck.revision ?? 0) + 1,
      slides,
    },
  });
}

/**
 * Update poll tally counts for a quiz slide during presentation (#47).
 */
export function updateSlidePoll(lesson, slideId, counts) {
  const cleanCounts = {
    A: Math.max(0, Math.trunc(Number(counts?.A || 0))),
    B: Math.max(0, Math.trunc(Number(counts?.B || 0))),
    C: Math.max(0, Math.trunc(Number(counts?.C || 0))),
    D: Math.max(0, Math.trunc(Number(counts?.D || 0))),
  };
  return normalizeLesson({
    ...lesson,
    polls: {
      ...(lesson.polls || {}),
      [slideId]: cleanCounts,
    },
  });
}

/**
 * Add a new Yêu cầu trực quan to an outline item, and optionally place it on a slide of that item (#51, #53, #54, #55).
 */
export function addItemVisual(lesson, itemId, visualInput, targetSlideId = null) {
  const visual = {
    visual_id: visualInput?.visual_id || crypto.randomUUID(),
    kind: visualInput.kind,
    origin: visualInput.origin || 'teacher',
    status: 'proposed',
    label: visualInput.label || undefined,
    data: visualInput.data || {},
  };
  let foundItem = false;
  const items = lesson.outline.items.map(item => {
    if (item.item_id !== itemId) return item;
    foundItem = true;
    return { ...item, visuals: [...item.visuals, visual] };
  });
  if (!foundItem) fail(`Không tìm thấy Mục «${itemId}».`);

  let nextDeck = lesson.deck;
  if (nextDeck?.slides?.length) {
    const itemSlides = nextDeck.slides.filter(s => s.item_id === itemId);
    const chosenSlide = itemSlides.find(s => s.slide_id === targetSlideId) || itemSlides[0];
    if (chosenSlide) {
      const figEl = {
        element_id: crypto.randomUUID(),
        type: visual.kind,
        x: 700,
        y: 140,
        w: 820,
        h: 680,
        reveal: 0,
        parts: visual.kind === 'bbt' ? 3 : 1,
        visual_id: visual.visual_id,
      };
      const { review_token, ...restDeck } = nextDeck;
      nextDeck = {
        ...restDeck,
        revision: (nextDeck.revision ?? 0) + 1,
        slides: nextDeck.slides.map(s => (s.slide_id === chosenSlide.slide_id ? { ...s, edited: true, elements: [...s.elements, figEl] } : s)),
      };
    }
  }
  return normalizeLesson({
    ...lesson,
    outline: { ...lesson.outline, items },
    deck: nextDeck,
  });
}

/**
 * Update or confirm a Yêu cầu trực quan on an outline item (#51, #53, #54, #55, #56).
 * Editing visual data without providing a new requirement_token resets status to 'proposed'.
 */
export function updateItemVisual(lesson, itemId, visualId, updates) {
  let changed = false;
  const items = lesson.outline.items.map(item => {
    if (item.item_id !== itemId) return item;
    const visuals = item.visuals.map(v => {
      if (v.visual_id !== visualId) return v;
      changed = true;
      if (updates.status === 'confirmed' && updates.requirement_token) {
        return {
          ...v,
          ...updates,
          data: updates.data ? { ...v.data, ...updates.data } : v.data,
          status: 'confirmed',
          requirement_token: updates.requirement_token,
        };
      }
      const { requirement_token, source_fingerprint, ...rest } = v;
      return {
        ...rest,
        ...updates,
        data: updates.data ? { ...v.data, ...updates.data } : v.data,
        status: 'proposed',
      };
    });
    return { ...item, visuals };
  });
  if (!changed) return lesson;
  const nextDeck = lesson.deck ? (() => {
    const { review_token, ...rest } = lesson.deck;
    return { ...rest, revision: (lesson.deck.revision ?? 0) + 1 };
  })() : null;
  return normalizeLesson({
    ...lesson,
    outline: { ...lesson.outline, items },
    deck: nextDeck,
  });
}

/**
 * Place or duplicate a visual element onto another slide of the SAME Mục dàn ý (#51, ADR 0003).
 */
export function placeVisualOnItemSlide(lesson, visualId, targetSlideId) {
  if (!lesson?.deck?.slides) fail('Bài giảng chưa có Bộ slide.');
  const ownerItem = lesson.outline.items.find(item => item.visuals.some(v => v.visual_id === visualId));
  if (!ownerItem) fail(`Yêu cầu trực quan «${visualId}» không có trong Dàn ý.`);
  const visual = ownerItem.visuals.find(v => v.visual_id === visualId);
  const targetSlide = lesson.deck.slides.find(s => s.slide_id === targetSlideId);
  if (!targetSlide) fail(`Không tìm thấy slide «${targetSlideId}».`);
  if (targetSlide.item_id !== ownerItem.item_id) {
    fail(`Hình «${visualId}» thuộc Mục «${ownerItem.item_id}», không được đặt trên slide của Mục «${targetSlide.item_id}».`);
  }
  const figEl = {
    element_id: crypto.randomUUID(),
    type: visual.kind,
    x: 700,
    y: 140,
    w: 820,
    h: 680,
    reveal: 0,
    parts: visual.kind === 'bbt' ? 3 : 1,
    visual_id: visual.visual_id,
  };
  const { review_token, ...restDeck } = lesson.deck;
  return normalizeLesson({
    ...lesson,
    deck: {
      ...restDeck,
      revision: (lesson.deck.revision ?? 0) + 1,
      slides: lesson.deck.slides.map(s => (s.slide_id === targetSlideId ? { ...s, edited: true, elements: [...s.elements, figEl] } : s)),
    },
  });
}

/**
 * Convert a legacy schema_version: 2 project into a valid schema_version: 3 Bài giảng (#58).
 * Preserves the original v2 project_id untouched in IndexedDB by assigning a distinct v3 project_id.
 */
export function convertLegacyProjectToV3(record) {
  if (!isRecord(record) || record.schema_version !== LEGACY_SCHEMA_VERSION) {
    fail('Chỉ hỗ trợ chuyển dự án bản 2 sang bản 3.');
  }
  const oldSlides = Array.isArray(record.deck?.slides) && record.deck.slides.length > 0
    ? record.deck.slides
    : Array.isArray(record.outline?.outline_slides)
      ? record.outline.outline_slides
      : [];

  let hadVisualsToReconfirm = false;
  const droppedDiscreteSlides = [];

  const mapSlideRole = (s, idx, total) => {
    const stype = String(s.type || '').toUpperCase();
    const actRaw = String(s.activity_type || '').toLowerCase();
    const hasQuiz = stype === 'QUIZ_SLIDE' || s.layout === 'QUIZ_OPTION' || (Array.isArray(s.quiz_options) && s.quiz_options.length === 4);
    const hasSteps = Array.isArray(s.worked_solution_steps) && s.worked_solution_steps.length > 0;
    if (idx === 0 && (stype === 'TITLE_SLIDE' || s.layout === 'TITLE_ONLY')) {
      return { activity: 'Khởi động', kind: 'Mở đầu', layout: 'Mở đầu' };
    }
    if (stype === 'WARM_UP_SLIDE' || actRaw.includes('khoi_dong') || actRaw.includes('khởi động')) {
      return { activity: 'Khởi động', kind: 'Tình huống khởi động', layout: 'Tình huống' };
    }
    if (stype === 'SUMMARY_SLIDE' || actRaw.includes('van_dung') || actRaw.includes('vận dụng') || actRaw.includes('tong_ket') || idx === total - 1) {
      return { activity: 'Vận dụng', kind: 'Tổng kết', layout: 'Tổng kết' };
    }
    if (hasQuiz) {
      return { activity: 'Luyện tập', kind: 'Câu hỏi trắc nghiệm', layout: 'Câu hỏi trắc nghiệm' };
    }
    if (stype === 'EXERCISE_SLIDE' || actRaw.includes('luyen_tap') || actRaw.includes('luyện tập')) {
      return { activity: 'Luyện tập', kind: hasSteps ? 'Ví dụ' : 'Bài luyện tập', layout: hasSteps ? 'Ví dụ (đề và lời giải)' : 'Nội dung' };
    }
    return {
      activity: 'Hình thành kiến thức',
      kind: hasSteps ? 'Ví dụ' : 'Kiến thức trọng tâm',
      layout: hasSteps ? 'Ví dụ (đề và lời giải)' : 'Kiến thức trọng tâm',
    };
  };

  const rawEntries = (oldSlides.length > 0 ? oldSlides : [{ title: record.title || 'Bài giảng chuyển từ bản 2', type: 'TITLE_SLIDE' }]).map((s, idx, arr) => {
    const role = mapSlideRole(s, idx, arr.length);
    return { s, idx, ...role };
  });

  // Sort by activity order so Dàn ý strictly obeys Khởi động -> Hình thành kiến thức -> Luyện tập -> Vận dụng
  rawEntries.sort((a, b) => ACTIVITIES.indexOf(a.activity) - ACTIVITIES.indexOf(b.activity) || a.idx - b.idx);

  const count = rawEntries.length;
  const baseMin = Math.max(1, Math.floor(LESSON_MINUTES / count));
  let remMin = Math.max(0, LESSON_MINUTES - baseMin * count);

  const items = [];
  const v3Slides = [];

  rawEntries.forEach((entry, orderIdx) => {
    const { s, activity, kind } = entry;
    let layout = entry.layout;
    const itemId = `m-v2-${orderIdx + 1}`;
    const slideId = s.slide_id || `s-v2-${orderIdx + 1}`;
    const title = (typeof s.title === 'string' && s.title.trim()) ? s.title.trim() : `Mục ${orderIdx + 1}`;
    const bullets = Array.isArray(s.bullet_points) ? s.bullet_points.filter(b => typeof b === 'string' && b.trim()) : [];
    const steps = Array.isArray(s.worked_solution_steps) ? s.worked_solution_steps.filter(st => typeof st === 'string' && st.trim()) : [];
    const formulas = [
      ...(typeof s.main_definition_latex === 'string' && s.main_definition_latex.trim() ? [s.main_definition_latex.trim()] : []),
      ...(Array.isArray(s.math_formulas) ? s.math_formulas.filter(f => typeof f === 'string' && f.trim()) : []),
    ];
    const points = [...bullets, ...steps, ...formulas.map(f => (f.startsWith('$') ? f : `$${f}$`))];
    const minutes = Math.min(LESSON_MINUTES, baseMin + (remMin > 0 ? (remMin--, 1) : 0));

    const visuals = [];
    const chartKind = s.chart_spec?.kind;
    if (chartKind === 'arithmetic_sequence' || chartKind === 'inequality_system') {
      droppedDiscreteSlides.push(title);
    } else if (chartKind === 'function_plot' && typeof s.chart_spec?.expression === 'string' && s.chart_spec.expression.trim()) {
      hadVisualsToReconfirm = true;
      visuals.push({
        visual_id: `v-graph-${orderIdx + 1}`,
        kind: 'graph',
        origin: 'teacher',
        status: 'proposed',
        label: `$y = ${s.chart_spec.expression.trim()}$`,
        data: {
          expression: s.chart_spec.expression.trim(),
          x_min: Number.isFinite(Number(s.chart_spec.x_min)) ? Number(s.chart_spec.x_min) : -4,
          x_max: Number.isFinite(Number(s.chart_spec.x_max)) ? Number(s.chart_spec.x_max) : 4,
        },
      });
      layout = 'Chữ trái, hình phải';
    }

    const polyType = typeof s.polyhedron_type === 'string' ? s.polyhedron_type.trim().toLowerCase() : (s.scene_spec?.polyhedron_type || '');
    if ((s.has_3d || s.scene_spec) && ['cube', 'square_pyramid_regular', 'square_pyramid_at_a'].includes(polyType)) {
      hadVisualsToReconfirm = true;
      const a = Number(s.scene_spec?.base_edge) > 0 ? Number(s.scene_spec.base_edge) : 2;
      const h = polyType === 'cube' ? a : (Number(s.scene_spec?.height) > 0 ? Number(s.scene_spec.height) : 3);
      visuals.push({
        visual_id: `v-solid-${orderIdx + 1}`,
        kind: 'solid',
        origin: 'teacher',
        status: 'proposed',
        label: polyType,
        data: { polyhedron_type: polyType, base_edge: a, height: h },
      });
      layout = 'Chữ trái, hình phải';
    }

    items.push({
      item_id: itemId,
      activity,
      kind,
      title,
      points,
      slide_count: 1,
      minutes,
      visuals,
      needs_review: false,
    });

    const hasVisual = visuals.length > 0;
    const textW = hasVisual ? 560 : 1400;
    const elements = [
      {
        element_id: `${slideId}-title`,
        type: 'title',
        hero: layout === 'Mở đầu',
        x: layout === 'Mở đầu' ? 120 : 100,
        y: layout === 'Mở đầu' ? 280 : 80,
        w: layout === 'Mở đầu' ? 1360 : textW,
        h: layout === 'Mở đầu' ? 220 : 100,
        reveal: 0,
        parts: 1,
        text: title,
      },
    ];

    if (typeof s.subtitle === 'string' && s.subtitle.trim()) {
      elements.push({
        element_id: `${slideId}-sub`,
        type: 'paragraph',
        x: 100,
        y: 200,
        w: textW,
        h: 120,
        reveal: 0,
        parts: 1,
        text: s.subtitle.trim(),
      });
    }

    if (bullets.length > 0) {
      elements.push({
        element_id: `${slideId}-bullets`,
        type: 'text',
        x: 100,
        y: 240,
        w: textW,
        h: 320,
        reveal: 1,
        parts: bullets.length,
        items: bullets,
      });
    }

    if (steps.length > 0) {
      elements.push({
        element_id: `${slideId}-steps`,
        type: 'steps',
        x: 100,
        y: bullets.length > 0 ? 480 : 240,
        w: textW,
        h: 300,
        reveal: 1,
        parts: steps.length,
        items: steps,
      });
    }

    if (formulas.length > 0) {
      elements.push({
        element_id: `${slideId}-formula`,
        type: 'formula',
        x: 100,
        y: 660,
        w: textW,
        h: 140,
        reveal: 1,
        parts: 1,
        latex: formulas[0],
      });
    }

    if (Array.isArray(s.quiz_options) && s.quiz_options.length === 4) {
      const normalizedOpts = ['A', 'B', 'C', 'D'].map((lbl, i) => {
        const rawOpt = s.quiz_options[i] || {};
        return {
          label: lbl,
          text: String(rawOpt.text || `Phương án ${lbl}`),
          correct: Boolean(rawOpt.is_correct ?? rawOpt.correct ?? (i === 0)),
          why: String(rawOpt.distractor_rationale || rawOpt.why || 'Giải thích phương án'),
        };
      });
      if (normalizedOpts.filter(o => o.correct).length !== 1) {
        normalizedOpts.forEach((o, i) => { o.correct = i === 0; });
      }
      elements.push({
        element_id: `${slideId}-quiz`,
        type: 'quiz',
        x: 100,
        y: 200,
        w: 1400,
        h: 640,
        reveal: 0,
        parts: 1,
        question: String(s.question || title),
        options: normalizedOpts,
      });
    }

    visuals.forEach((v, vIdx) => {
      elements.push({
        element_id: `${slideId}-vis-${vIdx + 1}`,
        type: v.kind,
        x: 700,
        y: 140,
        w: 820,
        h: 680,
        reveal: 0,
        parts: 1,
        visual_id: v.visual_id,
      });
    });

    v3Slides.push({
      slide_id: slideId,
      item_id: itemId,
      layout,
      notes: typeof s.teacher_note === 'string' ? s.teacher_note : '',
      elements,
    });
  });

  const baseId = String(record.project_id || 'du-an-ban-2').trim();
  const v3Id = baseId.endsWith('-v3') ? baseId : `${baseId}-v3`;
  const title = record.title || record.deck?.presentation_title || record.plan?.lesson_title || 'Bài giảng chuyển từ bản 2';
  const plan = isRecord(record.plan) ? { ...structuredClone(record.plan), review_token: undefined, needs_review: false } : null;

  const lesson = normalizeLesson({
    schema_version: LESSON_SCHEMA_VERSION,
    project_id: v3Id,
    migrated_from_v2: baseId,
    title,
    sgk: typeof record.sgk === 'string' ? record.sgk : undefined,
    level: 'Trung bình',
    outline: { items },
    deck: { revision: 1, slides: v3Slides },
    plan,
    annotations: {},
    polls: {},
  });

  const notices = ['Đã chuyển dự án bản 2 sang Bài giảng bản 3 (bản 2 gốc vẫn được giữ nguyên trên máy).'];
  if (hadVisualsToReconfirm) {
    notices.push('Các hình từ dự án bản 2 đã chuyển sang trạng thái chờ xác nhận dữ kiện lại.');
  }
  if (droppedDiscreteSlides.length > 0) {
    notices.push(`Đã lược bỏ hình dãy số cộng / hệ bất phương trình không còn hỗ trợ ở các slide: ${droppedDiscreteSlides.join(', ')}.`);
  }

  return {
    lesson,
    hadVisualsToReconfirm,
    droppedDiscreteSlides,
    noticeMessage: notices.join(' '),
  };
}

/**
 * Replace only the slides of a single Mục (#43) while keeping all other Mục slides intact and clearing needs_review.
 */
export function replaceItemSlides(lesson, itemId, newItemSlides) {
  if (!lesson?.deck?.slides) fail('Bài giảng chưa có Bộ slide.');
  const kept = lesson.deck.slides.filter(slide => slide.item_id !== itemId);
  const byItem = new Map(lesson.outline.items.map(item => [item.item_id, []]));
  for (const slide of kept) {
    byItem.get(slide.item_id)?.push(slide);
  }
  for (const slide of newItemSlides) {
    byItem.get(itemId)?.push(slide);
  }
  const orderedSlides = lesson.outline.items.flatMap(item => byItem.get(item.item_id) || []);
  const items = lesson.outline.items.map(item => (item.item_id === itemId ? { ...item, needs_review: false } : item));
  const { review_token, ...restDeck } = lesson.deck;
  return normalizeLesson({
    ...lesson,
    outline: { ...lesson.outline, items },
    deck: {
      ...restDeck,
      revision: (lesson.deck.revision ?? 0) + 1,
      slides: orderedSlides,
    },
  });
}

export function normalizeLesson(input) {
  if (!isRecord(input)) fail('tệp không chứa một Bài giảng.');
  // _storage_revision is the IndexedDB write counter (projectStore.saveProject), not lesson content.
  const { _storage_revision, ...lesson } = structuredClone(input);
  if (!isFilledText(lesson.project_id)) fail('thiếu mã Bài giảng (project_id).');
  const title = lesson.title ?? '';
  if (typeof title !== 'string') fail('tiêu đề Bài giảng (title) phải là chữ.');
  requireOptionalText(lesson.sgk, 'bài SGK (sgk)');
  requireOptionalText(lesson.level, 'trình độ lớp (level)');
  if (!isRecord(lesson.outline)) fail('Dàn ý (outline) phải có danh sách Mục (outline.items).');
  const items = normalizeItems(lesson.outline.items);
  const deck = lesson.deck == null ? null : normalizeLessonDeck(lesson.deck, items);
  const plan = lesson.plan ?? null;
  if (plan !== null && !isRecord(plan)) fail('Kế hoạch bài dạy (plan) không đúng cấu trúc.');
  return {
    ...lesson,
    schema_version: LESSON_SCHEMA_VERSION,
    title,
    outline: { ...lesson.outline, items },
    deck,
    plan,
    annotations: optionalRecord(lesson.annotations, 'chú thích bút (annotations)'),
    polls: optionalRecord(lesson.polls, 'phiếu trắc nghiệm (polls)')
  };
}

/** Why the Bàn làm việc cannot open this data, or null for a Bài giảng bản 3. */
export function lessonVersionProblem(data, source = 'tệp') {
  const version = isRecord(data) ? data.schema_version : undefined;
  if (version === LESSON_SCHEMA_VERSION) return null;
  if (version === LEGACY_SCHEMA_VERSION) return `${UNSUPPORTED_VERSION}: ${source} là dự án bản 2 của giao diện cũ. Bàn làm việc chưa chuyển được dự án bản 2; hãy tắt Bàn làm việc để mở bằng giao diện cũ.`;
  if (version == null) return `${UNSUPPORTED_VERSION}: ${source} không ghi phiên bản; Bàn làm việc chỉ mở được Bài giảng bản 3.`;
  return `${UNSUPPORTED_VERSION}: ${source} ghi bản ${typeof version === 'number' ? version : JSON.stringify(version)}; Bàn làm việc chỉ mở được Bài giảng bản 3.`;
}

/** Text of an imported JSON file → normalized Bài giảng bản 3, or a LessonDataError explaining why not. */
export function readLessonFile(text) {
  let data;
  try {
    data = JSON.parse(text);
  } catch {
    throw new LessonDataError('Tệp không phải JSON hợp lệ.');
  }
  const problem = lessonVersionProblem(data);
  if (problem) throw new LessonDataError(problem);
  return normalizeLesson(data);
}

/**
 * Whether the Bộ slide carries a stored Xác nhận chuyên môn. This browser cannot check the signature:
 * the server verifies the token when it is used (ADR 0005), as the old studio does.
 */
export const isExpertConfirmed = lesson => Boolean(lesson?.deck?.slides?.length) && isFilledText(lesson.deck.review_token);

/** Validates, then writes through projectStore's compare-and-write. The caller's lesson is never changed. */
export async function saveLesson(lesson) {
  const normalized = normalizeLesson(lesson);
  await saveProject(normalized);
  return normalized;
}

export async function loadLesson(projectId) {
  const record = await loadProject(projectId);
  if (!record) throw new LessonDataError('Không tìm thấy Bài giảng trên máy.');
  const problem = lessonVersionProblem(record, 'dự án đã lưu');
  if (problem) throw new LessonDataError(problem);
  return normalizeLesson(record);
}

// Read defensively: one damaged record must not hide the other Bài giảng; opening it reports the problem.
const lessonSummary = record => ({
  project_id: record.project_id,
  title: typeof record.title === 'string' ? record.title : '',
  sgk: typeof record.sgk === 'string' ? record.sgk : '',
  items: Array.isArray(record.outline?.items) ? record.outline.items.length : 0,
  slides: Array.isArray(record.deck?.slides) ? record.deck.slides.length : 0,
  expert_confirmed: isExpertConfirmed(record)
});

/** Bài giảng bản 3 saved on this browser, plus legacy v2 projects that can be converted to v3 (#58). */
export async function listLessons() {
  const records = await listProjects();
  const lessons = records.filter(record => record?.schema_version === LESSON_SCHEMA_VERSION).map(lessonSummary)
    .sort((a, b) => a.title.localeCompare(b.title, 'vi') || String(a.project_id).localeCompare(String(b.project_id)));
  const legacyProjects = records.filter(record => record?.schema_version === LEGACY_SCHEMA_VERSION).map(record => ({
    project_id: record.project_id,
    title: typeof record.title === 'string' && record.title.trim() ? record.title : (record.deck?.presentation_title || 'Dự án bản 2 chưa đặt tên'),
    slides: Array.isArray(record.deck?.slides) ? record.deck.slides.length : 0,
  }));
  return { lessons, legacyCount: records.length - lessons.length, legacyProjects };
}

// Key-order-independent JSON, to tell whether two Bài giảng hold the same content.
const stableJson = value => JSON.stringify(value, (key, nested) =>
  (isRecord(nested) ? Object.fromEntries(Object.keys(nested).sort().map(name => [name, nested[name]])) : nested));

/**
 * What this browser already holds under the lesson's project_id: nothing, the same Bài giảng, or a
 * different record (another version of it, or an older project) that importing would replace.
 */
export async function storedCopy(lesson) {
  const record = await loadProject(lesson.project_id);
  if (!record) return { state: 'none' };
  let same = false;
  if (record.schema_version === LESSON_SCHEMA_VERSION) {
    try { same = stableJson(normalizeLesson(record)) === stableJson(lesson); } catch { same = false; }
  }
  return { state: same ? 'same' : 'different', version: record.schema_version, title: typeof record.title === 'string' ? record.title : '' };
}
