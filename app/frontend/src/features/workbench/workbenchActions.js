import { listLessons, loadLesson, readLessonFile, saveLesson, storedCopy } from '../../shared/storage/lessonProject.js';
import { LESSON_SCHEMA_VERSION, UNSUPPORTED_VERSION } from '../../shared/storage/projectStore.js';

/**
 * Bàn làm việc: open, import, save and export a Bài giảng bản 3.
 * The session is App state (getSession/setSession); these actions never drop the Bản soạn. When a save
 * fails, the lesson stays open and marked unsaved, and nothing replaces it until it is saved.
 */
export const emptyWorkbench = () => ({
  lesson: null,        // Bản soạn đang mở (Bài giảng bản 3 đã chuẩn hóa)
  lessons: null,       // Bài giảng đã lưu trên máy; null khi chưa đọc xong
  legacyCount: 0,      // dự án bản 2, chỉ giao diện cũ mở được
  saveState: 'saved',  // 'saved' | 'saving' | 'unsaved' (lần lưu gần nhất thất bại)
  notice: null         // { kind: 'error' | 'save-failed', message } | { kind: 'conflict', message, lesson }
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

  async function persist(lesson) {
    patch({ lesson, saveState: 'saving', notice: null });
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
      patch({ lesson: await loadLesson(projectId), notice: null });
    } catch (error) {
      report('error', storageProblem(error));
    }
  }

  async function closeLesson() {
    if (holdUnsaved()) return;
    patch({ lesson: null, notice: null });
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
      patch({ lesson: incoming, saveState: 'saved', notice: null });
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

  const dismissNotice = () => patch({ notice: null });

  return { refreshLessons, openLesson, closeLesson, importFile, replaceStored, keepStored, retrySave, exportLesson, dismissNotice };
}
