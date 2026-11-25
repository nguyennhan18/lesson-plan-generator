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
const ITEM_KINDS = ['Mở đầu', 'Tình huống khởi động', 'Kiến thức trọng tâm', 'Ví dụ', 'Bài luyện tập', 'Câu hỏi trắc nghiệm', 'Tổng kết'];
const KIND_ACTIVITY = { 'Mở đầu': 'Khởi động', 'Tổng kết': 'Vận dụng' };
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

/** Bài giảng bản 3 saved on this browser, plus how many older projects only the old studio opens. */
export async function listLessons() {
  const records = await listProjects();
  const lessons = records.filter(record => record?.schema_version === LESSON_SCHEMA_VERSION).map(lessonSummary)
    .sort((a, b) => a.title.localeCompare(b.title, 'vi') || String(a.project_id).localeCompare(String(b.project_id)));
  return { lessons, legacyCount: records.length - lessons.length };
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
