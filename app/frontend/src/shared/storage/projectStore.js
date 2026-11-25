/** Durable project envelopes; failures are surfaced to the editor, never seeded. */
export const newId = () => crypto.randomUUID();

export function normalizeDeck(input) {
  if (!input || !Array.isArray(input.slides)) throw new Error('Dữ liệu bộ slide không hợp lệ');
  if (input.schema_version && input.schema_version > 2) throw new Error('Phiên bản dự án chưa được hỗ trợ');
  const ids = new Set();
  const slides = input.slides.map((slide, index) => {
    if (slide.slide_number != null && slide.slide_index != null && slide.slide_number !== slide.slide_index)
      throw new Error('Chỉ số trang cũ và mới không khớp');
    const { slide_number, ...rest } = slide;
    const id = slide.slide_id || newId();
    if (ids.has(id)) throw new Error('ID slide bị trùng');
    ids.add(id);
    return { ...rest, slide_id: id, revision: slide.revision || 0, slide_index: index + 1,
      source_refs: slide.source_refs?.map(ref => ({ ...ref, source_type: ref.source_type ?? ref.source, id: ref.id ?? ref.slide_id })) };
  });
  return { ...input, schema_version: 2, project_id: input.project_id || newId(),
    deck_id: input.deck_id || input.id || newId(), revision: input.revision || 0, slides };
}

export function mutateDeck(previous, input) {
  if (!input) return null;
  const next = normalizeDeck(input);
  if (!previous || next.deck_id !== previous.deck_id) return next;
  const content = value => JSON.stringify(value, (key, val) => ['revision', 'slide_index', 'quality_report', 'review_token', 'chart_image_base64', 'formula_image_base64', 'snapshot_3d_base64', 'chart_render_status', 'chart_render_error', 'has_chart'].includes(key) ? undefined : val);
  let changed = previous.slides.length !== next.slides.length || previous.slides.some((s, i) => s.slide_id !== next.slides[i]?.slide_id);
  next.slides = next.slides.map(slide => {
    const old = previous.slides.find(s => s.slide_id === slide.slide_id);
    if (!old || content(old) !== content(slide)) {
      changed = true;
      if(old && JSON.stringify([old.question,old.quiz_options])!==JSON.stringify([slide.question,slide.quiz_options])) {
        next.polls={...next.polls};delete next.polls[slide.slide_id];
      }
      const clean = { ...slide, revision: (old?.revision || 0) + 1 };
      for (const key of ['chart_image_base64', 'formula_image_base64', 'snapshot_3d_base64', 'snapshot_3d', 'quality_report']) delete clean[key];
      // New confirmation is explicit; ordinary content edits invalidate old tokens.
      for (const key of ['chart_spec', 'scene_spec']) {
        if (clean[key] && clean[key].requirement_token === old?.[key]?.requirement_token) {
          clean[key] = { ...clean[key] };
          delete clean[key].requirement_token;
        }
      }
      return clean;
    }
    return slide;
  });
  if (changed || content({ ...previous, slides: [] }) !== content({ ...next, slides: [] })) {
    next.revision = previous.revision + 1;
    delete next.quality_report;
    delete next.review_token;
  }
  return next;
}

export function mutatePlan(previous, input) {
  if (!input) return null;
  const next = structuredClone(input);
  const content = value => {
    const {review_token, quality_report, ...authored} = value || {};
    return JSON.stringify(authored);
  };
  if (previous && content(previous) !== content(next)) {
    delete next.review_token;
    delete next.quality_report;
  }
  return next;
}

function openDatabase() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('lessonai-projects', 1);
    request.onupgradeneeded = () => request.result.createObjectStore('projects', { keyPath: 'project_id' });
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function transaction(mode, action) {
  const db = await openDatabase();
  return new Promise((resolve, reject) => {
    const tx = db.transaction('projects', mode);
    const request = action(tx.objectStore('projects'));
    tx.oncomplete = () => { const result = request.result; db.close(); resolve(result); };
    tx.onerror = tx.onabort = () => { const error = tx.error || request.error; db.close(); reject(error || new Error('Không lưu được dự án')); };
  });
}

// Observed versions belong to this tab; compare and write in one IDB transaction.
const observedVersions = new Map();
export async function saveProject(project) {
  const db = await openDatabase();
  return new Promise((resolve, reject) => {
    const tx = db.transaction('projects', 'readwrite');
    const store = tx.objectStore('projects');
    let failure;
    const expected = observedVersions.get(project.project_id) ?? 0;
    const read = store.get(project.project_id);
    read.onsuccess = () => {
      if ((read.result?._storage_revision ?? 0) !== expected) {
        failure = new Error('Dự án đã được sửa ở tab khác. Tải JSON dự phòng trước khi mở lại dự án.');
        tx.abort();
        return;
      }
      try {store.put({...structuredClone(project), _storage_revision: expected + 1});}
      catch(error) {failure = error;tx.abort();}
    };
    tx.oncomplete = () => {observedVersions.set(project.project_id, expected + 1);db.close();resolve(project.project_id);};
    tx.onabort = tx.onerror = () => {db.close();reject(failure || tx.error || new Error('Không lưu được dự án'));};
  });
}
export const listProjects = () => transaction('readonly', store => store.getAll());
export const loadProject = async id => {
  const project = await transaction('readonly', store => store.get(id));
  observedVersions.set(id, project?._storage_revision ?? 0);
  return project;
};
export const blankProject = () => ({ schema_version: 2, project_id: newId(), title: '', deck: null, plan: null, outline: null, config: {}, annotations: {}, analytics: null });

export async function restoreProject() {
  const id = localStorage.getItem('lessonai-active-project');
  if (id) {
    const saved = await loadProject(id);
    if (saved) return saved;
  }
  const raw = sessionStorage.getItem('lessonai_slide_deck_json_v1');
  if (raw && !localStorage.getItem('lessonai-v1-migrated')) {
    const deck = normalizeDeck(JSON.parse(raw));
    delete deck.review_token;
    delete deck.quality_report;
    const project = { ...blankProject(), project_id: deck.project_id, title: deck.presentation_title, deck, legacy_backup: raw, migration_review: 'Nguồn gốc bài cũ chưa xác định; cần đối chiếu trước khi sử dụng.' };
    await saveProject(project); // Original session bytes remain intact, even after migration.
    localStorage.setItem('lessonai-v1-migrated', project.project_id);
    localStorage.setItem('lessonai-active-project', project.project_id);
    return project;
  }
  return blankProject();
}
