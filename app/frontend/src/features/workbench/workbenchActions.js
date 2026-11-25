import { postJson } from '../../shared/api/client.js';
import {
  ACTIVITIES,
  addItemVisual,
  addSlideElement,
  convertLegacyProjectToV3,
  measureElementTextFit,
  normalizeLesson,
  listLessons,
  loadLesson,
  placeVisualOnItemSlide,
  readLessonFile,
  removeSlideElement,
  saveLesson,
  storedCopy,
  updateItemVisual,
  updateSlideElement,
  updateSlidePoll,
  replaceItemSlides,
} from '../../shared/storage/lessonProject.js';
import { LEGACY_SCHEMA_VERSION, LESSON_SCHEMA_VERSION, UNSUPPORTED_VERSION, loadProject } from '../../shared/storage/projectStore.js';

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
  legacyCount: 0,      // số dự án bản 2 trên máy
  legacyProjects: [],  // danh sách dự án bản 2 có thể chuyển sang bản 3 (#58)
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
      const record = await loadProject(projectId);
      if (record && record.schema_version === LEGACY_SCHEMA_VERSION) {
        const converted = convertLegacyProjectToV3(record);
        await persist(converted.lesson);
        report('info', converted.noticeMessage);
        return;
      }
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
    let text, incoming, stored, migrationNotice = null;
    try {
      text = typeof source === 'string' ? source : await source.text();
    } catch (error) {
      report('error', `Không đọc được tệp: ${storageProblem(error)}`);
      return;
    }
    try {
      const rawParsed = JSON.parse(text);
      if (rawParsed && typeof rawParsed === 'object' && !Array.isArray(rawParsed) && rawParsed.schema_version === LEGACY_SCHEMA_VERSION) {
        const converted = convertLegacyProjectToV3(rawParsed);
        incoming = converted.lesson;
        migrationNotice = converted.noticeMessage;
      } else {
        incoming = readLessonFile(text);
      }
    } catch (error) {
      report('error', error instanceof SyntaxError ? 'Tệp không phải JSON hợp lệ.' : storageProblem(error));
      return;
    }
    try {
      stored = await storedCopy(incoming);
    } catch {
      // Unreadable storage: open the file as the Bản soạn; saving it reports why it cannot be stored.
      stored = { state: 'none' };
    }
    if (stored.state === 'same') {
      patch({ lesson: incoming, introducedId: null, saveState: 'saved', notice: migrationNotice ? { kind: 'info', message: migrationNotice } : null });
      return;
    }
    if (stored.state === 'different' && stored.version !== LESSON_SCHEMA_VERSION) {
      report('error', `${UNSUPPORTED_VERSION}: trên máy có dự án bản ${stored.version ?? 'cũ'} «${stored.title}» cùng mã với tệp này. Bàn làm việc không ghi đè dự án đó.`);
      return;
    }
    if (stored.state === 'different') {
      patch({ notice: { kind: 'conflict', lesson: incoming,
        message: `Trên máy đã có Bài giảng «${stored.title}» cùng mã với tệp vừa nhập nhưng nội dung khác. Thay bản trên máy bằng bản trong tệp?` } });
      return;
    }
    await persist(incoming);
    if (migrationNotice) {
      report('info', migrationNotice);
    }
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

  async function addElement(slideId, elementInput) {
    if (holdUnsaved()) return false;
    const { lesson } = getSession();
    if (!lesson?.deck) return false;
    const updated = addSlideElement(lesson, slideId, elementInput);
    await persist(updated);
    return true;
  }

  async function removeElement(slideId, elementId) {
    if (holdUnsaved()) return false;
    const { lesson } = getSession();
    if (!lesson?.deck) return false;
    const updated = removeSlideElement(lesson, slideId, elementId);
    if (updated === lesson) return false;
    await persist(updated);
    return true;
  }

  async function updatePoll(slideId, counts) {
    const { lesson } = getSession();
    if (!lesson) return false;
    const updated = updateSlidePoll(lesson, slideId, counts);
    await persist(updated);
    return true;
  }

  async function addVisualToItem(itemId, visualInput, targetSlideId = null) {
    if (holdUnsaved()) return false;
    const { lesson } = getSession();
    if (!lesson) return false;
    const updated = addItemVisual(lesson, itemId, visualInput, targetSlideId);
    await persist(updated);
    return true;
  }

  async function confirmVisual(itemId, visualId, nextData) {
    if (holdUnsaved()) return false;
    const { lesson } = getSession();
    if (!lesson) return false;
    const item = lesson.outline.items.find(it => it.item_id === itemId);
    const visual = item?.visuals.find(v => v.visual_id === visualId);
    if (!item || !visual) throw new Error('Không tìm thấy Yêu cầu trực quan cần xác nhận.');
    const response = await outlineRequest('/api/v1/visuals/confirm', {
      project_id: lesson.project_id,
      item_id: itemId,
      kind: visual.kind,
      data: nextData,
      source: { title: item.title, points: item.points },
    });
    const updated = updateItemVisual(lesson, itemId, visualId, {
      status: 'confirmed',
      requirement_token: response.requirement_token,
      source_fingerprint: response.requirement?.spec?.source_fingerprint,
      data: { ...nextData, ...(response.requirement?.spec || {}) },
    });
    await persist(updated);
    return true;
  }

  async function placeVisualOnSlide(visualId, targetSlideId) {
    if (holdUnsaved()) return false;
    const { lesson } = getSession();
    if (!lesson?.deck) return false;
    const updated = placeVisualOnItemSlide(lesson, visualId, targetSlideId);
    await persist(updated);
    return true;
  }

  function deckWithOverflowCheck(deck) {
    if (!deck || !Array.isArray(deck.slides)) return deck;
    return {
      ...deck,
      slides: deck.slides.map(slide => ({
        ...slide,
        elements: (slide.elements || []).map(el => {
          const fit = measureElementTextFit(el);
          return (el.overflow || fit.overflow) ? { ...el, overflow: true } : el;
        }),
      })),
    };
  }

  async function checkDeckQuality() {
    const { lesson } = getSession();
    if (!lesson?.deck) throw new Error('Bài giảng chưa có Bộ slide để kiểm tra.');
    return outlineRequest('/api/v1/quality/workbench/check', {
      project_id: lesson.project_id,
      title: lesson.title || 'Bài giảng Toán 12',
      outline: lesson.outline,
      deck: deckWithOverflowCheck(lesson.deck),
    });
  }

  async function approveDeckQuality(contentFingerprint, reviewedIssueIds) {
    if (holdUnsaved()) return false;
    const { lesson } = getSession();
    if (!lesson?.deck) return false;
    const result = await outlineRequest('/api/v1/quality/workbench/approve', {
      project_id: lesson.project_id,
      title: lesson.title || 'Bài giảng Toán 12',
      outline: lesson.outline,
      deck: deckWithOverflowCheck(lesson.deck),
      acknowledged: true,
      content_fingerprint: contentFingerprint,
      reviewed_issue_ids: reviewedIssueIds,
    });
    const updated = normalizeLesson({
      ...lesson,
      deck: {
        ...lesson.deck,
        review_token: result.review_token,
      },
    });
    await persist(updated);
    return result;
  }

  async function askAssistant(slideId, userMessage) {
    const { lesson } = getSession();
    if (!lesson?.deck) throw new Error('Bài giảng chưa có Bộ slide.');
    const slide = lesson.deck.slides.find(s => s.slide_id === slideId);
    if (!slide) throw new Error('Không tìm thấy slide đang chọn.');
    return outlineRequest('/api/v1/chat/workbench/assistant', withModelSettings({
      project_id: lesson.project_id,
      title: lesson.title || 'Bài giảng Toán 12',
      slide,
      user_message: userMessage,
    }));
  }

  async function applyAssistantPatch(patchedSlide) {
    if (holdUnsaved()) return false;
    const { lesson } = getSession();
    if (!lesson?.deck || !patchedSlide?.slide_id) return false;
    const slides = lesson.deck.slides.map(s => (s.slide_id === patchedSlide.slide_id ? { ...patchedSlide, edited: true } : s));
    const { review_token, ...restDeck } = lesson.deck;
    const updated = normalizeLesson({
      ...lesson,
      deck: {
        ...restDeck,
        revision: (lesson.deck.revision ?? 0) + 1,
        slides,
      },
    });
    await persist(updated);
    return true;
  }

  async function generateLessonPlan() {
    if (holdUnsaved()) return false;
    const { lesson } = getSession();
    if (!lesson) return false;
    const levelCode = LEVEL_CODE_BY_LABEL[lesson.level] || 'standard';
    const response = await outlineRequest('/api/v1/workbench/lesson-plan', withModelSettings({
      title: lesson.title || 'Bài giảng Toán 12',
      sgk: lesson.sgk ?? null,
      lesson_id: lesson.lesson_id ?? null,
      level: levelCode,
      outline: lesson.outline,
    }));
    const updated = normalizeLesson({
      ...lesson,
      plan: {
        ...response.plan,
        needs_review: false,
      },
    });
    await persist(updated);
    return true;
  }

  async function updateLessonPlan(nextPlan) {
    if (holdUnsaved()) return false;
    const { lesson } = getSession();
    if (!lesson || !nextPlan) return false;
    const { review_token, ...restPlan } = nextPlan;
    const updated = normalizeLesson({
      ...lesson,
      plan: restPlan,
    });
    await persist(updated);
    return true;
  }

  async function downloadBinaryExport(url, payload, fallbackName) {
    const response = await postJson(url, payload);
    if (!response.ok) {
      let detailMsg = 'Không thể xuất tệp.';
      try {
        const err = await response.json();
        detailMsg = err.detail?.message || err.detail || detailMsg;
      } catch {
        // ignore
      }
      throw new Error(detailMsg);
    }
    const blob = await response.blob();
    if (typeof window !== 'undefined' && window.URL?.createObjectURL) {
      const objUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = objUrl;
      a.download = fallbackName;
      a.click();
      window.URL.revokeObjectURL(objUrl);
    }
    return blob;
  }

  async function exportPptx() {
    const { lesson } = getSession();
    if (!lesson?.deck?.slides?.length) throw new Error('Bài giảng chưa có Bộ slide để xuất PowerPoint.');
    return downloadBinaryExport('/api/v1/workbench/export-pptx', {
      project_id: lesson.project_id,
      title: lesson.title || 'Bài giảng Toán 12',
      outline: lesson.outline,
      deck: lesson.deck,
    }, `Slide_${(lesson.title || 'Bai_Giang').replace(/\s+/g, '_')}.pptx`);
  }

  async function exportDocx() {
    const { lesson } = getSession();
    if (!lesson?.plan) throw new Error('Bài giảng chưa có Kế hoạch bài dạy để xuất Word.');
    return downloadBinaryExport('/api/v1/lesson-plan/export-docx', {
      plan: lesson.plan,
    }, `Giao_An_5512_${(lesson.title || 'Bai_Giang').replace(/\s+/g, '_')}.docx`);
  }

  async function exportZip() {
    const { lesson } = getSession();
    if (!lesson?.plan && !lesson?.deck?.slides?.length) {
      throw new Error('Cần có Bộ slide hoặc Kế hoạch bài dạy để xuất gói ZIP.');
    }
    return downloadBinaryExport('/api/v1/lesson-plan/export-dual-package', {
      plan: lesson.plan,
      slide_deck: lesson.deck ? {
        schema_version: 3,
        project_id: lesson.project_id,
        title: lesson.title || 'Bài giảng Toán 12',
        outline: lesson.outline,
        deck: lesson.deck,
      } : null,
    }, `Tron_Bo_${(lesson.title || 'Bai_Giang').replace(/\s+/g, '_')}.zip`);
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
    checkDeckQuality, askAssistant, exportPptx, exportDocx, exportZip, updatePoll,
    openLesson: exclusive(openLesson), closeLesson: exclusive(closeLesson), importFile: exclusive(importFile),
    replaceStored: exclusive(replaceStored), keepStored: exclusive(keepStored), retrySave: exclusive(retrySave),
    generateLesson: exclusive(generateLesson), buildSlides: exclusive(buildSlides),
    regenerateItemSlides: exclusive(regenerateItemSlides), changeElement: exclusive(changeElement),
    addElement: exclusive(addElement), removeElement: exclusive(removeElement),
    addVisualToItem: exclusive(addVisualToItem), confirmVisual: exclusive(confirmVisual),
    placeVisualOnSlide: exclusive(placeVisualOnSlide), approveDeckQuality: exclusive(approveDeckQuality),
    applyAssistantPatch: exclusive(applyAssistantPatch), generateLessonPlan: exclusive(generateLessonPlan),
    updateLessonPlan: exclusive(updateLessonPlan),
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
