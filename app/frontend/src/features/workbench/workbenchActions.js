import { postJson } from '../../shared/api/client.js';
import {
  ACTIVITIES,
  normalizeLesson,
  listLessons,
  loadLesson,
  readLessonFile,
  saveLesson,
  storedCopy,
  updateSlideElement,
  replaceItemSlides,
} from '../../shared/storage/lessonProject.js';
import { LESSON_SCHEMA_VERSION, UNSUPPORTED_VERSION } from '../../shared/storage/projectStore.js';

/**
 * Bàn làm việc: open, import, save and export a Bài giảng bản 3.
 * The session is App state (getSession/setSession); these actions never drop the Bản soạn. When a save
 * fails, the lesson stays open and marked unsaved, and nothing replaces it until it is saved.
 */
export const CLASS_LEVEL_LABELS = { basic: 'Cơ bản', standard: 'Trung bình', advanced: 'Khá' };
export const LEVEL_CODE_BY_LABEL = Object.fromEntries(
  Object.entries(CLASS_LEVEL_LABELS).map(([code, label]) => [label, code]),
);
const SETTINGS_KEY = 'lessonai-workbench-settings';

function readStoredSettings() {
  try {
    const raw = typeof localStorage !== 'undefined' ? localStorage.getItem(SETTINGS_KEY) : null;
    if (!raw) return { model_provider: '', model_id: '' };
    const parsed = JSON.parse(raw);
    return {
      model_provider: typeof parsed?.model_provider === 'string' ? parsed.model_provider : '',
      model_id: typeof parsed?.model_id === 'string' ? parsed.model_id : '',
    };
  } catch {
    return { model_provider: '', model_id: '' };
  }
}

export const emptyWorkbench = () => ({
  lesson: null,        // Bản soạn đang mở (Bài giảng bản 3 đã chuẩn hóa)
  lessons: null,       // Bài giảng đã lưu trên máy; null khi chưa đọc xong
  legacyCount: 0,      // dự án bản 2, chỉ giao diện cũ mở được
  saveState: 'saved',  // 'saved' | 'saving' | 'unsaved' (lần lưu gần nhất thất bại)
  notice: null,        // { kind: 'error' | 'save-failed', message } | { kind: 'conflict', message, lesson }
  settings: readStoredSettings(),
  preferredLevel: 'standard',
  analyticsData: null,
});

function storageProblem(error) {
  if (error?.name === 'QuotaExceededError') return 'bộ nhớ trình duyệt đã hết dung lượng';
  return error?.message || String(error);
}

function lessonFileName(lesson) {
  const slug = (lesson.title || '').normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/đ/g, 'd').replace(/Đ/g, 'D')
    .toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 60).replace(/-+$/, '');
  return `bai-giang-${slug || lesson.project_id}.json`;
}

function downloadFile(fileName, text) {
  const url = URL.createObjectURL(new Blob([text], { type: 'application/json' }));
  const link = document.createElement('a');
  link.href = url;
  link.download = fileName;
  link.click();
  URL.revokeObjectURL(url);
}

const UNSAVED_HOLD = 'Bản soạn đang mở chưa được lưu. Hãy bấm "Lưu lại" hoặc xuất tệp JSON dự phòng trước khi mở bài khác.';
const SAVING_HOLD = 'Bản soạn đang được lưu. Hãy thử lại sau giây lát.';

export function createWorkbenchActions({ getSession, setSession, download = downloadFile }) {
  let busy = false;
  const exclusive = action => async (...args) => {
    if (busy) return;
    busy = true;
    try { return await action(...args); }
    finally { busy = false; }
  };
  const patch = changes => setSession(previous => ({ ...previous, ...changes }));
  const report = (kind, message) => patch({ notice: { kind, message } });
  const holdUnsaved = () => {
    const { saveState } = getSession();
    if (saveState === 'saved') return false;
    if (saveState === 'saving') report('error', SAVING_HOLD);
    else report('save-failed', UNSAVED_HOLD);
    return true;
  };

  async function refreshLessons() {
    try {
      patch(await listLessons());
    } catch (error) {
      report('error', `Không đọc được danh sách Bài giảng: ${storageProblem(error)}`);
    }
  }

  async function persist(lesson, introducedId = null) {
    patch({ lesson, introducedId, saveState: 'saving', notice: null });
    try {
      await saveLesson(lesson);
    } catch (error) {
      patch({ saveState: 'unsaved' });
      report('save-failed', `Chưa lưu: ${storageProblem(error)}. Bản soạn vẫn đang mở; hãy bấm "Lưu lại" hoặc xuất tệp JSON dự phòng.`);
      return;
    }
    patch({ saveState: 'saved' });
    await refreshLessons();
  }

  async function openLesson(projectId) {
    if (holdUnsaved()) return;
    try {
      patch({ lesson: await loadLesson(projectId), introducedId: null, notice: null });
    } catch (error) {
      report('error', storageProblem(error));
    }
  }

  async function closeLesson() {
    if (holdUnsaved()) return;
    patch({ lesson: null, introducedId: null, notice: null });
    await refreshLessons();
  }

  /** `source` is the File the teacher picked, or its text. */
  async function importFile(source) {
    if (holdUnsaved()) return;
    let text, incoming, stored;
    try {
      text = typeof source === 'string' ? source : await source.text();
    } catch (error) {
      report('error', `Không đọc được tệp: ${storageProblem(error)}`);
      return;
    }
    try {
      incoming = readLessonFile(text);
    } catch (error) {
      report('error', storageProblem(error));
      return;
    }
    try {
      stored = await storedCopy(incoming);
    } catch {
      // Unreadable storage: open the file as the Bản soạn; saving it reports why it cannot be stored.
      stored = { state: 'none' };
    }
    if (stored.state === 'same') {
      patch({ lesson: incoming, introducedId: null, saveState: 'saved', notice: null });
      return;
    }
    if (stored.state === 'different' && stored.version !== LESSON_SCHEMA_VERSION) {
      // An older project keeps its data: moving it to bản 3, with the original kept, belongs to #58.
      report('error', `${UNSUPPORTED_VERSION}: trên máy có dự án bản ${stored.version ?? 'cũ'} «${stored.title}» cùng mã với tệp này. Bàn làm việc không ghi đè dự án đó; hãy mở nó bằng giao diện cũ.`);
      return;
    }
    if (stored.state === 'different') {
      patch({ notice: { kind: 'conflict', lesson: incoming,
        message: `Trên máy đã có Bài giảng «${stored.title}» cùng mã với tệp vừa nhập nhưng nội dung khác. Thay bản trên máy bằng bản trong tệp?` } });
      return;
    }
    await persist(incoming);
  }

  const pendingImport = () => {
    const { notice } = getSession();
    return notice?.kind === 'conflict' ? notice.lesson : null;
  };

  async function replaceStored() {
    const incoming = pendingImport();
    if (incoming) await persist(incoming);
  }

  async function keepStored() {
    const incoming = pendingImport();
    patch({ notice: null });
    if (incoming) await openLesson(incoming.project_id);
  }

  async function retrySave() {
    const { lesson } = getSession();
    if (lesson) await persist(lesson);
  }

  function exportLesson() {
    const { lesson } = getSession();
    if (lesson) download(lessonFileName(lesson), JSON.stringify(lesson, null, 2));
  }

  function withModelSettings(payload) {
    const settings = getSession().settings || {};
    const extra = {};
    if (settings.model_provider) extra.model_provider = settings.model_provider;
    if (settings.model_id) extra.model_id = settings.model_id;
    return { ...payload, ...extra };
  }

  function updateSettings(nextSettings) {
    const clean = {
      model_provider: (nextSettings?.model_provider || '').trim(),
      model_id: (nextSettings?.model_id || '').trim(),
    };
    try {
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem(SETTINGS_KEY, JSON.stringify(clean));
      }
    } catch {
      // preference only
    }
    patch({ settings: clean });
  }

  function setAnalyticsResult(analyticsData) {
    patch({ analyticsData });
  }

  function applyClassLevel(level) {
    if (level && CLASS_LEVEL_LABELS[level]) {
      patch({ preferredLevel: level });
    }
  }

  async function generateLesson(payload) {
    if (holdUnsaved()) return false;
    const generated = await outlineRequest('/api/v1/workbench/outline', withModelSettings(payload));
    if (generated.schema_version !== LESSON_SCHEMA_VERSION) {
      throw new Error('[invalid_ai_output] Máy chủ không trả Dàn ý bản 3.');
    }
    const { warnings, ...draft } = generated; // The sheet derives time feedback from the current items.
    const lesson = normalizeLesson({
      ...draft,
      project_id: crypto.randomUUID(),
      level: CLASS_LEVEL_LABELS[payload.level]
    });
    await persist(lesson, lesson.project_id);
    return true;
  }

  async function buildSlides() {
    if (holdUnsaved()) return false;
    const { lesson } = getSession();
    if (!lesson) return false;
    const levelCode = LEVEL_CODE_BY_LABEL[lesson.level] || 'standard';
    const response = await outlineRequest('/api/v1/workbench/slides', withModelSettings({
      title: lesson.title || 'Bài giảng Toán 12',
      sgk: lesson.sgk ?? null,
      lesson_id: lesson.lesson_id ?? null,
      level: levelCode,
      outline: lesson.outline,
    }));
    const clearedItems = lesson.outline.items.map(item => ({ ...item, needs_review: false }));
    const updated = normalizeLesson({
      ...lesson,
      outline: { ...lesson.outline, items: clearedItems },
      deck: {
        revision: (lesson.deck?.revision ?? 0) + 1,
        slides: response.slides,
      },
    });
    await persist(updated);
    return true;
  }

  async function regenerateItemSlides(itemId) {
    if (holdUnsaved()) return false;
    const { lesson } = getSession();
    if (!lesson?.deck) return false;
    const levelCode = LEVEL_CODE_BY_LABEL[lesson.level] || 'standard';
    const response = await outlineRequest('/api/v1/workbench/slides/item', withModelSettings({
      title: lesson.title || 'Bài giảng Toán 12',
      sgk: lesson.sgk ?? null,
      lesson_id: lesson.lesson_id ?? null,
      level: levelCode,
      outline: lesson.outline,
      item_id: itemId,
    }));
    const updated = replaceItemSlides(lesson, itemId, response.slides);
    await persist(updated);
    return true;
  }

  async function changeElement(slideId, elementId, changes) {
    if (holdUnsaved()) return false;
    const { lesson } = getSession();
    if (!lesson?.deck) return false;
    const updated = updateSlideElement(lesson, slideId, elementId, changes);
    if (updated === lesson) return false;
    await persist(updated);
    return true;
  }

  async function changeItems(change) {
    if (holdUnsaved()) return false;
    const { lesson } = getSession();
    if (!lesson) return false;
    const items = change(lesson.outline.items);
    if (items.length === lesson.outline.items.length && items.every((item, index) => item === lesson.outline.items[index])) return false;

    const positions = new Map(items.map(({ item_id }, index) => [item_id, index]));
    const deck = lesson.deck && {
      ...lesson.deck,
      review_token: undefined,
      revision: lesson.deck.revision + 1,
      slides: lesson.deck.slides.filter(slide => positions.has(slide.item_id))
        .sort((a, b) => positions.get(a.item_id) - positions.get(b.item_id))
    };
    const removedSlides = new Set(lesson.deck?.slides.filter(slide => !positions.has(slide.item_id)).map(slide => slide.slide_id));
    const keepSlideData = data => Object.fromEntries(Object.entries(data).filter(([id]) => !removedSlides.has(id)));
    const plan = lesson.plan && { ...lesson.plan, review_token: undefined, needs_review: true };
    const revised = normalizeLesson({
      ...lesson,
      outline: { ...lesson.outline, items }, deck, plan,
      annotations: keepSlideData(lesson.annotations), polls: keepSlideData(lesson.polls)
    });
    await persist(revised);
    return true;
  }

  const editItem = (id, fields) => changeItems(items => items.map(item => {
    if (item.item_id !== id) return item;
    const sourceChanged = (fields.title !== undefined && fields.title !== item.title)
      || (fields.points !== undefined && JSON.stringify(fields.points) !== JSON.stringify(item.points));
    const contentChanged = sourceChanged || (fields.slide_count !== undefined && fields.slide_count !== item.slide_count);
    if (!contentChanged && (fields.minutes === undefined || fields.minutes === item.minutes)) return item;
    const hasSlides = getSession().lesson.deck?.slides.some(slide => slide.item_id === id);
    // #37 signs the Mục's title and points together with the visual data.
    const visuals = sourceChanged ? item.visuals.map(visual => {
      if (visual.status !== 'confirmed') return visual;
      const { requirement_token, source_fingerprint, ...proposal } = visual;
      return { ...proposal, status: 'proposed' };
    }) : item.visuals;
    return { ...item, ...fields, visuals, needs_review: item.needs_review || Boolean(contentChanged && hasSlides) };
  }));

  async function addItem(activity, kind) {
    const id = crypto.randomUUID();
    const created = await changeItems(items => {
      const index = items.findIndex(item => ACTIVITIES.indexOf(item.activity) > ACTIVITIES.indexOf(activity));
      const next = [...items];
      next.splice(index < 0 ? next.length : index, 0, {
        item_id: id, activity, kind, title: 'Mục mới', points: [], slide_count: 1, minutes: 1
      });
      return next;
    });
    if (created) return id;
  }

  const removeItem = id => changeItems(items => items.filter(item => item.item_id !== id));

  const moveItem = (id, direction) => changeItems(items => {
    const index = items.findIndex(item => item.item_id === id);
    const neighbor = index + direction;
    if (index < 0 || items[neighbor]?.activity !== items[index].activity) return items;
    const next = [...items];
    [next[index], next[neighbor]] = [next[neighbor], next[index]];
    return next;
  });

  const dismissNotice = () => patch({ notice: null });

  return {
    refreshLessons, exportLesson, dismissNotice, updateSettings, setAnalyticsResult, applyClassLevel,
    openLesson: exclusive(openLesson), closeLesson: exclusive(closeLesson), importFile: exclusive(importFile),
    replaceStored: exclusive(replaceStored), keepStored: exclusive(keepStored), retrySave: exclusive(retrySave),
    generateLesson: exclusive(generateLesson), buildSlides: exclusive(buildSlides),
    regenerateItemSlides: exclusive(regenerateItemSlides), changeElement: exclusive(changeElement),
    editItem: exclusive(editItem), addItem: exclusive(addItem),
    moveItem: exclusive(moveItem), removeItem: exclusive(removeItem)
  };
}

export async function outlineRequest(url, payload, options) {
  try {
    const response = await postJson(url, payload, options);
    const result = await response.json();
    if (response.ok) return result;
    throw new Error(`[${result.detail?.code || 'request_failed'}] ${result.detail?.message || 'Yêu cầu Dàn ý thất bại.'}`);
  } catch (error) {
    if (error.name === 'AbortError' || error.message.startsWith('[')) throw error;
    throw new Error('[connection_error] Không nhận được phản hồi từ máy chủ. Hãy thử lại.', { cause: error });
  }
}
