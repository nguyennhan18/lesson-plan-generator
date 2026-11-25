import assert from 'node:assert/strict';
import { test } from 'node:test';
import {
  addItemVisual,
  addSlideElement,
  convertLegacyProjectToV3,
  detectElementOverflow,
  listLessons,
  loadLesson,
  normalizeLesson,
  placeVisualOnItemSlide,
  readLessonFile,
  removeSlideElement,
  replaceItemSlides,
  saveLesson,
  updateItemVisual,
  updateSlideElement,
  updateSlidePoll,
} from '../src/shared/storage/lessonProject.js';
import { assertLegacyProject, restoreProject, saveProject } from '../src/shared/storage/projectStore.js';
import { createWorkbenchActions, emptyWorkbench } from '../src/features/workbench/workbenchActions.js';

// In-memory IndexedDB covering what projectStore.js uses: open with upgrade, one object store with a
// keyPath, get/put/getAll, transactions that commit once idle, abort(), and a commit that fails the way
// a browser fails when storage is full. It stands in for the browser database, the system boundary.
function installFakeIndexedDB() {
  const databases = new Map();
  let commitFailure = null;
  const later = callback => setImmediate(callback);
  const transaction = (store, mode) => {
    const staged = new Map(store.rows);
    let pending = 0, done = false;
    const finish = () => {
      if (done || pending) return;
      done = true;
      if (mode === 'readwrite' && commitFailure) {
        tx.error = commitFailure;
        commitFailure = null;
        tx.onabort?.();
        return;
      }
      if (mode === 'readwrite') store.rows = staged;
      tx.oncomplete?.();
    };
    const request = run => {
      const pendingRequest = {};
      pending++;
      later(() => {
        if (done) return;
        pendingRequest.result = run();
        pending--;
        pendingRequest.onsuccess?.();
        later(finish);
      });
      return pendingRequest;
    };
    const tx = {
      error: null,
      abort() { if (!done) { done = true; later(() => tx.onabort?.()); } },
      objectStore: () => ({
        get: key => request(() => structuredClone(staged.get(key))),
        getAll: () => request(() => [...staged.values()].map(row => structuredClone(row))),
        put: value => {
          const row = structuredClone(value);
          return request(() => { staged.set(row[store.keyPath], row); return row[store.keyPath]; });
        }
      })
    };
    return tx;
  };
  globalThis.indexedDB = {
    open(name) {
      const opening = {};
      later(() => {
        const created = !databases.has(name);
        if (created) databases.set(name, new Map());
        const stores = databases.get(name);
        opening.result = {
          createObjectStore: (storeName, { keyPath }) => stores.set(storeName, { keyPath, rows: new Map() }),
          transaction: (storeName, mode = 'readonly') => transaction(stores.get(storeName), mode),
          close() {}
        };
        if (created) opening.onupgradeneeded?.();
        opening.onsuccess?.();
      });
      return opening;
    }
  };
  return { failNextCommit(error) { commitFailure = error; } };
}
// projectStore remembers the versions this tab has seen, so every test uses its own Bài giảng IDs.
let saved = 0;
const storedLesson = overrides => normalizeLesson(lessonFile({ project_id: `luu-${++saved}`, ...overrides }));

// A Bài giảng bản 3 as a teacher's JSON file would hold it.
const lessonFile = (overrides = {}) => ({
  schema_version: 3,
  project_id: 'bai-giang-test',
  title: 'Khảo sát hàm số bậc ba $y = x^3 - 3x + 1$',
  sgk: 'Toán 12, Chương I, Bài 4',
  level: 'Trung bình',
  outline: {
    items: [
      { item_id: 'm1', activity: 'Khởi động', kind: 'Mở đầu', title: 'Khảo sát hàm số bậc ba', points: ['Toán 12, Chương I, Bài 4'], slide_count: 1, minutes: 2 },
      { item_id: 'm2', activity: 'Khởi động', kind: 'Tình huống khởi động', title: 'Hai bạn vẽ cùng một đồ thị', points: ['An chấm điểm, Bình xét dấu đạo hàm.'], slide_count: 1, minutes: 5 },
      {
        item_id: 'm3', activity: 'Hình thành kiến thức', kind: 'Ví dụ', title: 'Ví dụ 1. Khảo sát $y = x^3 - 3x + 1$',
        points: ['Đạo hàm và cực trị', 'Bảng biến thiên'], slide_count: 2, minutes: 15,
        visuals: [
          { visual_id: 'v-graph', kind: 'graph', origin: 'ai', status: 'confirmed', requirement_token: 'token-ky-tu-may-chu', data: { expression: 'x^3 - 3x + 1', x_min: -3, x_max: 3 } },
          { visual_id: 'v-bbt', kind: 'bbt', origin: 'ai', status: 'proposed', data: { expression: 'x^3 - 3x + 1' } }
        ]
      },
      { item_id: 'm4', activity: 'Luyện tập', kind: 'Bài luyện tập', title: 'Khảo sát $y = -x^3 + 3x^2 - 4$', points: ['Mức độ: thông hiểu'], slide_count: 1, minutes: 15, needs_review: true },
      { item_id: 'm5', activity: 'Vận dụng', kind: 'Tổng kết', title: 'Tổng kết', points: ['Ba bước khảo sát hàm số'], slide_count: 1, minutes: 8 }
    ]
  },
  deck: {
    slides: [
      { slide_id: 's1', item_id: 'm1', layout: 'Mở đầu', elements: [{ element_id: 'e1', type: 'title', x: 120, y: 280, w: 1360, h: 220, text: 'Khảo sát hàm số bậc ba' }] },
      { slide_id: 's3', item_id: 'm3', layout: 'Chữ trái, hình phải', elements: [{ element_id: 'e3', type: 'graph', x: 700, y: 140, w: 820, h: 680, visual_id: 'v-graph' }] }
    ]
  },
  ...overrides
});

test('chuẩn hóa bản 3 ghi rõ các giá trị mặc định của Mục, slide và phần tử', () => {
  const lesson = normalizeLesson(lessonFile());
  assert.equal(lesson.schema_version, 3);
  assert.deepEqual(lesson.outline.items[0].visuals, []);
  assert.equal(lesson.outline.items[0].needs_review, false);
  assert.equal(lesson.outline.items[3].needs_review, true);
  assert.equal(lesson.deck.revision, 0);
  assert.equal(lesson.deck.slides[0].notes, '');
  assert.deepEqual(lesson.deck.slides[0].elements[0], {
    element_id: 'e1', type: 'title', x: 120, y: 280, w: 1360, h: 220, text: 'Khảo sát hàm số bậc ba', reveal: 0, parts: 1
  });
  assert.equal(lesson.plan, null);
  assert.deepEqual(lesson.annotations, {});
  assert.deepEqual(lesson.polls, {});
});

test('chuẩn hóa giữ trường lạ, bỏ dấu phiên bản lưu trữ và không sửa dữ liệu gốc', () => {
  const input = lessonFile({ _storage_revision: 4, sources_used: [] });
  input.outline.items[2].visuals[0].label = '$y = x^3 - 3x + 1$';
  const before = structuredClone(input);
  const lesson = normalizeLesson(input);
  assert.deepEqual(input, before);
  assert.deepEqual(lesson.sources_used, []);
  assert.equal(lesson.outline.items[2].visuals[0].label, '$y = x^3 - 3x + 1$');
  assert.equal('_storage_revision' in lesson, false);
});

test('Hoạt động và Loại mục gõ ở dạng tổ hợp (NFD) được lưu ở dạng dựng sẵn (NFC)', () => {
  const input = lessonFile();
  input.outline.items[1].activity = 'Khởi động'.normalize('NFD');
  input.outline.items[1].kind = 'Tình huống khởi động'.normalize('NFD');
  const item = normalizeLesson(input).outline.items[1];
  assert.equal(item.activity, 'Khởi động');
  assert.equal(item.kind, 'Tình huống khởi động');
});

test('slide theo thứ tự Dàn ý được giữ nguyên thứ tự, kể cả nhiều slide trong một Mục', () => {
  const input = lessonFile();
  input.deck.slides = [
    { slide_id: 's1', item_id: 'm1', layout: 'Mở đầu', elements: [] },
    { slide_id: 's3b', item_id: 'm3', layout: 'Chữ trái, hình phải', elements: [] },
    { slide_id: 's3a', item_id: 'm3', layout: 'Ví dụ', elements: [] },
    { slide_id: 's5', item_id: 'm5', layout: 'Tổng kết', elements: [] }
  ];
  assert.deepEqual(normalizeLesson(input).deck.slides.map(slide => slide.slide_id), ['s1', 's3b', 's3a', 's5']);
});

const rejects = (mutate, message) => () => {
  const input = lessonFile();
  mutate(input);
  assert.throws(() => normalizeLesson(input), { name: 'LessonDataError', message });
};
const item = (input, n) => input.outline.items[n - 1];

test('dữ liệu sai báo rõ là dữ liệu Bài giảng không hợp lệ', rejects(input => { delete input.project_id; }, /^Dữ liệu Bài giảng không hợp lệ: /));

for (const [rule, mutate, message] of [
  ['tệp không phải một Bài giảng', input => { input.outline = 'Dàn ý'; }, /Dàn ý \(outline\) phải có danh sách Mục/],
  ['thiếu mã Bài giảng', input => { input.project_id = ''; }, /thiếu mã Bài giảng \(project_id\)/],
  ['Mục thiếu ID', input => { delete item(input, 2).item_id; }, /Mục 2: thiếu ID Mục \(item_id\)/],
  ['ID Mục bị trùng', input => { item(input, 2).item_id = 'm1'; }, /Mục 2: ID Mục «m1» bị trùng/],
  ['Hoạt động lạ', input => { item(input, 3).activity = 'Củng cố'; }, /Mục 3 \(«m3»\): Hoạt động «Củng cố» không hợp lệ; chỉ nhận Khởi động, Hình thành kiến thức, Luyện tập, Vận dụng/],
  ['Hoạt động sai thứ tự', input => { item(input, 4).activity = 'Khởi động'; item(input, 4).kind = 'Tình huống khởi động'; }, /Mục 4 \(«m4»\): Mục thuộc Khởi động đứng sau Mục thuộc Hình thành kiến thức/],
  ['Loại mục lạ', input => { item(input, 4).kind = 'Bài tập'; }, /Mục 4 \(«m4»\): Loại mục «Bài tập» không hợp lệ/],
  ['Mở đầu ngoài Khởi động', input => { item(input, 3).kind = 'Mở đầu'; }, /Mục 3 \(«m3»\): Mục Mở đầu phải thuộc Hoạt động Khởi động/],
  ['Tổng kết ngoài Vận dụng', input => { item(input, 4).kind = 'Tổng kết'; }, /Mục 4 \(«m4»\): Mục Tổng kết phải thuộc Hoạt động Vận dụng/],
  ['thiếu tiêu đề Mục', input => { item(input, 2).title = '   '; }, /Mục 2 \(«m2»\): thiếu tiêu đề/],
  ['các ý không phải chữ', input => { item(input, 2).points = ['Ý một', 2]; }, /Mục 2 \(«m2»\): các ý \(points\) phải là danh sách chữ/],
  ['số slide 0', input => { item(input, 1).slide_count = 0; }, /Mục 1 \(«m1»\): số slide phải là số nguyên từ 1 đến 4/],
  ['số slide 5', input => { item(input, 1).slide_count = 5; }, /số slide phải là số nguyên từ 1 đến 4/],
  ['số slide lẻ', input => { item(input, 1).slide_count = 1.5; }, /số slide phải là số nguyên từ 1 đến 4/],
  ['số slide dạng chữ', input => { item(input, 1).slide_count = '2'; }, /số slide phải là số nguyên từ 1 đến 4/],
  ['số phút 0', input => { item(input, 5).minutes = 0; }, /Mục 5 \(«m5»\): số phút phải là số nguyên từ 1 đến 45/],
  ['số phút quá một tiết', input => { item(input, 5).minutes = 46; }, /số phút phải là số nguyên từ 1 đến 45/],
  ['thiếu số phút', input => { delete item(input, 5).minutes; }, /số phút phải là số nguyên từ 1 đến 45/],
  ['dấu Cần xem lại không phải đúng/sai', input => { item(input, 4).needs_review = 'yes'; }, /Mục 4 \(«m4»\): dấu Cần xem lại \(needs_review\) phải là true hoặc false/]
]) test(`từ chối Mục dàn ý sai: ${rule}`, rejects(mutate, message));

const visual = (input, n) => item(input, 3).visuals[n - 1];
for (const [rule, mutate, message] of [
  ['danh sách hình không phải mảng', input => { item(input, 3).visuals = {}; }, /Mục 3 \(«m3»\): Yêu cầu trực quan \(visuals\) phải là danh sách/],
  ['hình thiếu ID', input => { delete visual(input, 2).visual_id; }, /Mục 3 \(«m3»\), Yêu cầu trực quan 2: thiếu ID \(visual_id\)/],
  ['ID hình trùng giữa hai Mục', input => { item(input, 4).visuals = [{ ...structuredClone(visual(input, 1)), status: 'proposed' }]; }, /Mục 4 \(«m4»\), Yêu cầu trực quan 1: ID «v-graph» bị trùng/],
  ['loại hình lạ', input => { visual(input, 2).kind = 'chart'; }, /Mục 3 \(«m3»\), Yêu cầu trực quan 2 \(«v-bbt»\): loại hình «chart» không hợp lệ; chỉ nhận graph, bbt, oxyz, solid/],
  ['nguồn đề xuất lạ', input => { visual(input, 2).origin = 'llm'; }, /Yêu cầu trực quan 2 \(«v-bbt»\): nguồn «llm» không hợp lệ; chỉ nhận ai, teacher/],
  ['trạng thái lạ', input => { visual(input, 2).status = 'approved'; }, /Yêu cầu trực quan 2 \(«v-bbt»\): trạng thái «approved» không hợp lệ; chỉ nhận proposed, confirmed/],
  ['thiếu dữ kiện', input => { delete visual(input, 2).data; }, /Yêu cầu trực quan 2 \(«v-bbt»\): thiếu dữ kiện \(data\)/],
  ['đã xác nhận mà không có token', input => { delete visual(input, 1).requirement_token; }, /Yêu cầu trực quan 1 \(«v-graph»\): ghi đã xác nhận nhưng không có token xác nhận \(requirement_token\)/],
  ['nhãn hình không phải chữ', input => { visual(input, 2).label = { text: 'y' }; }, /Yêu cầu trực quan 2 \(«v-bbt»\): nhãn hình \(label\) phải là chữ/],
  ['đồ thị thiếu biểu thức', input => { visual(input, 1).data = { x_min: -3, x_max: 3 }; }, /Yêu cầu trực quan 1 \(«v-graph»\): Đồ thị hàm số cần biểu thức \(data\.expression\)/],
  ['bảng biến thiên thiếu biểu thức', input => { visual(input, 2).data = { expression: '  ' }; }, /Yêu cầu trực quan 2 \(«v-bbt»\): Bảng biến thiên cần biểu thức \(data\.expression\)/]
]) test(`từ chối Yêu cầu trực quan sai: ${rule}`, rejects(mutate, message));

const slide = (input, n) => input.deck.slides[n - 1];
const element = (input, n) => slide(input, n).elements[0];
for (const [rule, mutate, message] of [
  ['Bộ slide không phải đối tượng', input => { input.deck = []; }, /Bộ slide \(deck\) không đúng cấu trúc/],
  ['Bộ slide thiếu danh sách slide', input => { delete input.deck.slides; }, /Bộ slide phải có danh sách slide \(deck\.slides\)/],
  ['số phiên bản Bộ slide âm', input => { input.deck.revision = -1; }, /số phiên bản Bộ slide \(deck\.revision\) phải là số nguyên không âm/],
  ['slide thiếu ID', input => { delete slide(input, 1).slide_id; }, /Slide 1: thiếu ID slide \(slide_id\)/],
  ['ID slide bị trùng', input => { slide(input, 2).slide_id = 's1'; }, /Slide 2: ID slide «s1» bị trùng/],
  ['slide không thuộc Mục nào', input => { delete slide(input, 2).item_id; }, /Slide 2 \(«s3»\): thiếu ID Mục \(item_id\); mọi slide phải thuộc một Mục dàn ý/],
  ['slide trỏ tới Mục không có', input => { slide(input, 2).item_id = 'm9'; }, /Slide 2 \(«s3»\): ID Mục «m9» không có trong Dàn ý/],
  ['slide thiếu Bố cục mẫu', input => { delete slide(input, 1).layout; }, /Slide 1 \(«s1»\): thiếu tên Bố cục mẫu \(layout\)/],
  ['ghi chú giáo viên không phải chữ', input => { slide(input, 1).notes = ['ghi chú']; }, /Slide 1 \(«s1»\): ghi chú giáo viên \(notes\) phải là chữ/],
  ['danh sách phần tử không phải mảng', input => { slide(input, 1).elements = null; }, /Slide 1 \(«s1»\): danh sách phần tử \(elements\) phải là mảng/],
  ['phần tử thiếu ID', input => { delete element(input, 1).element_id; }, /Slide 1 \(«s1»\), phần tử 1: thiếu ID phần tử \(element_id\)/],
  ['ID phần tử bị trùng', input => { element(input, 2).element_id = 'e1'; }, /Slide 2 \(«s3»\), phần tử 1: ID phần tử «e1» bị trùng/],
  ['loại phần tử lạ', input => { element(input, 1).type = 'video'; }, /Slide 1 \(«s1»\), phần tử 1 \(«e1»\): loại phần tử «video» không hợp lệ/],
  ['vị trí không phải số', input => { element(input, 1).x = '120'; }, /phần tử 1 \(«e1»\): vị trí và kích thước \(x, y, w, h\) phải là số/],
  ['kích thước bằng 0', input => { element(input, 1).h = 0; }, /phần tử 1 \(«e1»\): kích thước \(w, h\) phải lớn hơn 0/],
  ['tràn mép phải khung 1600', input => { element(input, 1).w = 1481; }, /phần tử 1 \(«e1»\): nằm ngoài khung slide 1600 × 900/],
  ['tràn mép dưới khung 900', input => { element(input, 2).y = 221; }, /Slide 2 \(«s3»\), phần tử 1 \(«e3»\): nằm ngoài khung slide 1600 × 900/],
  ['vị trí âm', input => { element(input, 1).y = -1; }, /nằm ngoài khung slide 1600 × 900/],
  ['bước bắt đầu hiện âm', input => { element(input, 1).reveal = -1; }, /phần tử 1 \(«e1»\): bước bắt đầu hiện \(reveal\) phải là số nguyên không âm/],
  ['số bước hiện dần bằng 0', input => { element(input, 1).parts = 0; }, /phần tử 1 \(«e1»\): số bước hiện dần \(parts\) phải là số nguyên dương/],
  ['phần tử hình không trỏ tới Yêu cầu trực quan', input => { delete element(input, 2).visual_id; }, /Slide 2 \(«s3»\), phần tử 1 \(«e3»\): phần tử hình phải trỏ tới một Yêu cầu trực quan \(visual_id\) của Mục/],
  ['phần tử hình trỏ tới hình không có', input => { element(input, 2).visual_id = 'v-x'; }, /phần tử 1 \(«e3»\): Yêu cầu trực quan «v-x» không có trong Dàn ý/],
  ['hình đặt trên slide của Mục khác', input => { slide(input, 1).elements.push({ element_id: 'e9', type: 'graph', x: 0, y: 0, w: 800, h: 450, visual_id: 'v-graph' }); }, /Slide 1 \(«s1»\), phần tử 2 \(«e9»\): hình «v-graph» thuộc Mục «m3», không được đặt trên slide của Mục «m1»/],
  ['loại phần tử khác loại hình', input => { element(input, 2).type = 'bbt'; }, /phần tử 1 \(«e3»\): phần tử loại bbt không khớp loại hình graph của «v-graph»/],
  ['phần tử chữ trỏ tới hình', input => { element(input, 1).visual_id = 'v-graph'; }, /phần tử 1 \(«e1»\): chỉ phần tử hình \(graph, bbt, oxyz, solid\) mới trỏ tới Yêu cầu trực quan/],
  ['tiêu đề Bài giảng không phải chữ', input => { input.title = 42; }, /tiêu đề Bài giảng \(title\) phải là chữ/],
  ['bài SGK không phải chữ', input => { input.sgk = 12; }, /bài SGK \(sgk\) phải là chữ/],
  ['trình độ lớp không phải chữ', input => { input.level = 2; }, /trình độ lớp \(level\) phải là chữ/],
  ['slide sai thứ tự Dàn ý', input => { input.deck.slides.reverse(); }, /Slide 2 \(«s1»\): thuộc Mục 1 \(«m1»\) nhưng đứng sau slide của Mục 3; Bộ slide phải theo thứ tự Dàn ý/],
  ['Kế hoạch bài dạy sai cấu trúc', input => { input.plan = 'giáo án'; }, /Kế hoạch bài dạy \(plan\) không đúng cấu trúc/],
  ['chú thích bút sai cấu trúc', input => { input.annotations = []; }, /chú thích bút \(annotations\) không đúng cấu trúc/],
  ['phiếu trắc nghiệm sai cấu trúc', input => { input.polls = 'A'; }, /phiếu trắc nghiệm \(polls\) không đúng cấu trúc/]
]) test(`từ chối Bộ slide sai: ${rule}`, rejects(mutate, message));

test('nhập tệp bản 3 trả về Bài giảng đã chuẩn hóa', () => {
  const lesson = readLessonFile(JSON.stringify(lessonFile()));
  assert.equal(lesson.project_id, 'bai-giang-test');
  assert.equal(lesson.deck.slides[0].elements[0].parts, 1);
});

for (const [file, message] of [
  ['{"schema_version": 3,', /^Tệp không phải JSON hợp lệ/],
  [JSON.stringify({ schema_version: 2, project_id: 'cu', deck: { slides: [] } }), /^Phiên bản chưa hỗ trợ: tệp là dự án bản 2 của giao diện cũ\. Bàn làm việc chưa chuyển được dự án bản 2; hãy tắt Bàn làm việc để mở bằng giao diện cũ\./],
  [JSON.stringify({ ...lessonFile(), schema_version: 4 }), /^Phiên bản chưa hỗ trợ: tệp ghi bản 4; Bàn làm việc chỉ mở được Bài giảng bản 3\./],
  [JSON.stringify({ project_id: 'khong-ro' }), /^Phiên bản chưa hỗ trợ: tệp không ghi phiên bản; Bàn làm việc chỉ mở được Bài giảng bản 3\./],
  ['[]', /^Phiên bản chưa hỗ trợ: tệp không ghi phiên bản/]
]) test(`nhập tệp bị từ chối: ${message.source.slice(1, 40)}`, () => {
  assert.throws(() => readLessonFile(file), { name: 'LessonDataError', message });
});

test('giao diện cũ không mở Bài giảng bản 3 mà báo phiên bản chưa hỗ trợ', () => {
  assert.throws(() => assertLegacyProject(lessonFile()), { message: /^Phiên bản chưa hỗ trợ: đây là Bài giảng bản 3, chỉ mở được trong Bàn làm việc\./ });
  assert.throws(() => assertLegacyProject({ schema_version: 7, project_id: 'moi' }), { message: /^Phiên bản chưa hỗ trợ: dự án ghi bản 7\./ });
});

test('giao diện cũ vẫn mở dự án bản 2 như trước', () => {
  const project = { schema_version: 2, project_id: 'cu', deck: { slides: [] } };
  assert.equal(assertLegacyProject(project), project);
  for (const broken of [null, { schema_version: 2 }, { schema_version: 1, project_id: 'rat-cu' }])
    assert.throws(() => assertLegacyProject(broken), { message: 'Dự án không đúng định dạng' });
});

test('Bài giảng bản 3 lưu vào IndexedDB rồi mở lại đúng như đã lưu', async () => {
  installFakeIndexedDB();
  const lesson = storedLesson();
  await saveLesson(lesson);
  assert.deepEqual(await loadLesson(lesson.project_id), lesson);
});

test('danh sách Bài giảng chỉ gồm bản 3, xếp theo tiêu đề, và đếm riêng dự án bản 2', async () => {
  installFakeIndexedDB();
  await saveProject({ schema_version: 2, project_id: `cu-${++saved}`, title: 'Dự án cũ', deck: null });
  const b = storedLesson({ title: 'Bài B' }), a = storedLesson({ title: 'Bài A', deck: { review_token: 'duyet', slides: storedLesson().deck.slides } });
  await saveLesson(b);
  await saveLesson(a);
  const { lessons, legacyCount } = await listLessons();
  assert.equal(legacyCount, 1);
  assert.deepEqual(lessons, [
    { project_id: a.project_id, title: 'Bài A', sgk: 'Toán 12, Chương I, Bài 4', items: 5, slides: 2, expert_confirmed: true },
    { project_id: b.project_id, title: 'Bài B', sgk: 'Toán 12, Chương I, Bài 4', items: 5, slides: 2, expert_confirmed: false }
  ]);
});

test('lưu thất bại vì hết dung lượng thì báo lỗi và giữ bản đã lưu trước đó', async () => {
  const database = installFakeIndexedDB();
  const lesson = storedLesson({ title: 'Bản đã lưu' });
  await saveLesson(lesson);
  database.failNextCommit(new DOMException('Quota exceeded', 'QuotaExceededError'));
  await assert.rejects(saveLesson({ ...lesson, title: 'Bản mới' }), { name: 'QuotaExceededError' });
  assert.equal((await loadLesson(lesson.project_id)).title, 'Bản đã lưu');
});

test('dữ liệu sai không được ghi vào IndexedDB', async () => {
  installFakeIndexedDB();
  const lesson = storedLesson();
  lesson.outline.items[0].slide_count = 9;
  await assert.rejects(saveLesson(lesson), { name: 'LessonDataError', message: /số slide phải là số nguyên từ 1 đến 4/ });
  await assert.rejects(loadLesson(lesson.project_id), { name: 'LessonDataError', message: 'Không tìm thấy Bài giảng trên máy.' });
});

test('mở dự án đã lưu không phải bản 3 hoặc đã hỏng thì báo rõ lý do', async () => {
  installFakeIndexedDB();
  const old = `cu-${++saved}`, broken = storedLesson();
  await saveProject({ schema_version: 2, project_id: old, deck: null });
  await saveProject({ ...broken, outline: { items: 'hỏng' } });
  await assert.rejects(loadLesson(old), { message: /^Phiên bản chưa hỗ trợ: dự án đã lưu là dự án bản 2 của giao diện cũ/ });
  await assert.rejects(loadLesson(broken.project_id), { message: /^Dữ liệu Bài giảng không hợp lệ: Dàn ý \(outline\)/ });
});

test('dự án bản 2 không ghi đè được Bài giảng bản 3 cùng mã', async () => {
  installFakeIndexedDB();
  const lesson = storedLesson();
  await saveLesson(lesson);
  await assert.rejects(saveProject({ schema_version: 2, project_id: lesson.project_id, deck: null }),
    { message: /^Phiên bản chưa hỗ trợ: không ghi đè Bài giảng bản 3 bằng dự án bản 2/ });
  assert.deepEqual(await loadLesson(lesson.project_id), lesson);
});

// The session lives in App.jsx; here it is a plain variable with the same getter/updater contract.
function workbench(observe = () => {}) {
  let session = emptyWorkbench();
  const downloads = [];
  const actions = createWorkbenchActions({
    getSession: () => session,
    setSession: update => { session = typeof update === 'function' ? update(session) : update; observe(session); },
    download: (name, text) => downloads.push({ name, text })
  });
  return { actions, downloads, get session() { return session; } };
}
const quotaExceeded = () => new DOMException('Quota exceeded', 'QuotaExceededError');
const newFile = overrides => lessonFile({ project_id: `nhap-${++saved}`, ...overrides });

test('nhập tệp bản 3 thì mở Bài giảng, lưu vào máy và hiện trong danh sách', async () => {
  installFakeIndexedDB();
  const desk = workbench(), file = newFile();
  await desk.actions.importFile(JSON.stringify(file));
  assert.deepEqual(desk.session.lesson, normalizeLesson(file));
  assert.equal(desk.session.saveState, 'saved');
  assert.equal(desk.session.notice, null);
  assert.deepEqual(desk.session.lessons.map(lesson => lesson.project_id), [file.project_id]);
  assert.deepEqual(await loadLesson(file.project_id), normalizeLesson(file));
});

test('nhập tệp sai thì báo rõ lỗi và giữ nguyên Bài giảng đang mở', async () => {
  installFakeIndexedDB();
  const desk = workbench(), open = newFile(), broken = newFile();
  broken.outline.items[2].slide_count = 6;
  await desk.actions.importFile(JSON.stringify(open));
  await desk.actions.importFile(JSON.stringify(broken));
  assert.equal(desk.session.lesson.project_id, open.project_id);
  assert.equal(desk.session.notice.kind, 'error');
  assert.match(desk.session.notice.message, /Mục 3 \(«m3»\): số slide phải là số nguyên từ 1 đến 4/);
});

test('lưu thất bại vì hết dung lượng vẫn giữ Bản soạn và báo lỗi', async () => {
  const database = installFakeIndexedDB();
  const desk = workbench(), file = newFile();
  database.failNextCommit(quotaExceeded());
  await desk.actions.importFile(JSON.stringify(file));
  assert.deepEqual(desk.session.lesson, normalizeLesson(file));
  assert.equal(desk.session.saveState, 'unsaved');
  assert.equal(desk.session.notice.kind, 'save-failed');
  assert.match(desk.session.notice.message, /^Chưa lưu: bộ nhớ trình duyệt đã hết dung lượng\. Bản soạn vẫn đang mở/);
  desk.actions.exportLesson();
  assert.deepEqual(JSON.parse(desk.downloads[0].text), normalizeLesson(file));
});

test('Bản soạn chưa lưu không bị thay khi mở hay nhập bài khác, và lưu lại được', async () => {
  const database = installFakeIndexedDB();
  const desk = workbench(), other = storedLesson({ title: 'Bài khác' }), file = newFile();
  await saveLesson(other);
  database.failNextCommit(quotaExceeded());
  await desk.actions.importFile(JSON.stringify(file));
  await desk.actions.openLesson(other.project_id);
  await desk.actions.importFile(JSON.stringify(newFile()));
  await desk.actions.closeLesson();
  assert.equal(desk.session.lesson.project_id, file.project_id);
  assert.match(desk.session.notice.message, /^Bản soạn đang mở chưa được lưu\./);
  await desk.actions.retrySave();
  assert.equal(desk.session.saveState, 'saved');
  assert.equal(desk.session.notice, null);
  assert.deepEqual(await loadLesson(file.project_id), normalizeLesson(file));
  await desk.actions.openLesson(other.project_id);
  assert.equal(desk.session.lesson.title, 'Bài khác');
});

test('mở Bài giảng đã hỏng thì báo lỗi và giữ bài đang mở', async () => {
  installFakeIndexedDB();
  const desk = workbench(), open = newFile(), broken = storedLesson();
  await saveProject({ ...broken, deck: { slides: [{ slide_id: 'x', item_id: 'không-có', layout: 'Nội dung', elements: [] }] } });
  await desk.actions.importFile(JSON.stringify(open));
  await desk.actions.openLesson(broken.project_id);
  assert.equal(desk.session.lesson.project_id, open.project_id);
  assert.match(desk.session.notice.message, /Slide 1 \(«x»\): ID Mục «không-có» không có trong Dàn ý/);
});

test('nhập lại đúng tệp đã có trên máy thì mở bài, không hỏi lại', async () => {
  installFakeIndexedDB();
  const desk = workbench(), file = newFile();
  await desk.actions.importFile(JSON.stringify(file));
  await desk.actions.closeLesson();
  await desk.actions.importFile(JSON.stringify(file));
  assert.equal(desk.session.lesson.project_id, file.project_id);
  assert.equal(desk.session.notice, null);
});

test('tệp cùng mã nhưng khác nội dung: hỏi trước, giữ được bản trên máy', async () => {
  installFakeIndexedDB();
  const desk = workbench(), stored = newFile({ title: 'Bản trên máy' });
  await desk.actions.importFile(JSON.stringify(stored));
  await desk.actions.importFile(JSON.stringify({ ...stored, title: 'Bản trong tệp' }));
  assert.equal(desk.session.notice.kind, 'conflict');
  assert.match(desk.session.notice.message, /^Trên máy đã có Bài giảng «Bản trên máy» cùng mã với tệp vừa nhập nhưng nội dung khác\./);
  assert.equal(desk.session.lesson.title, 'Bản trên máy');
  await desk.actions.keepStored();
  assert.equal(desk.session.notice, null);
  assert.equal(desk.session.lesson.title, 'Bản trên máy');
  assert.equal((await loadLesson(stored.project_id)).title, 'Bản trên máy');
});

test('tệp cùng mã nhưng khác nội dung: thay bản trên máy khi giáo viên đồng ý', async () => {
  installFakeIndexedDB();
  const desk = workbench(), stored = newFile({ title: 'Bản trên máy' });
  await desk.actions.importFile(JSON.stringify(stored));
  await desk.actions.importFile(JSON.stringify({ ...stored, title: 'Bản trong tệp' }));
  await desk.actions.replaceStored();
  assert.equal(desk.session.notice, null);
  assert.equal(desk.session.lesson.title, 'Bản trong tệp');
  assert.equal((await loadLesson(stored.project_id)).title, 'Bản trong tệp');
});

test('xuất tệp JSON của Bài giảng đang mở rồi nhập lại được đúng bài đó', async () => {
  installFakeIndexedDB();
  const desk = workbench();
  await desk.actions.importFile(JSON.stringify(newFile()));
  desk.actions.exportLesson();
  assert.equal(desk.downloads[0].name, 'bai-giang-khao-sat-ham-so-bac-ba-y-x-3-3x-1.json');
  assert.deepEqual(readLessonFile(desk.downloads[0].text), desk.session.lesson);
});

test('nhập được tệp giáo viên chọn từ máy, và báo rõ khi không đọc được tệp', async () => {
  installFakeIndexedDB();
  const desk = workbench(), file = newFile();
  await desk.actions.importFile(new Blob([JSON.stringify(file)], { type: 'application/json' }));
  assert.equal(desk.session.lesson.project_id, file.project_id);
  await desk.actions.importFile({ text: () => Promise.reject(new Error('NotReadableError')) });
  assert.equal(desk.session.lesson.project_id, file.project_id);
  assert.equal(desk.session.notice.message, 'Không đọc được tệp: NotReadableError');
});

test('khi lưu thành công, Bản soạn chỉ hiện là đang lưu, không lúc nào hiện là chưa lưu', async () => {
  installFakeIndexedDB();
  const states = [];
  const desk = workbench(session => states.push(session.saveState));
  await desk.actions.importFile(JSON.stringify(newFile()));
  assert.ok(states.includes('saving'));
  assert.equal(states.includes('unsaved'), false);
  assert.equal(states.at(-1), 'saved');
});

test('khi khởi động, giao diện cũ không mở lại Bài giảng bản 3 dù đó là dự án mở gần nhất', async () => {
  installFakeIndexedDB();
  const lesson = storedLesson();
  await saveLesson(lesson);
  const store = values => ({ getItem: key => values[key] ?? null, setItem: (key, value) => { values[key] = String(value); } });
  globalThis.localStorage = store({ 'lessonai-active-project': lesson.project_id });
  globalThis.sessionStorage = store({});
  const project = await restoreProject();
  assert.equal(project.schema_version, 2);
  assert.notEqual(project.project_id, lesson.project_id);
  assert.deepEqual(await loadLesson(lesson.project_id), lesson);
});

test('tệp bản 3 trùng mã với dự án bản 2 trên máy thì không ghi đè dự án đó', async () => {
  installFakeIndexedDB();
  const desk = workbench(), file = newFile();
  const old = { schema_version: 2, project_id: file.project_id, title: 'Dự án cũ', deck: null };
  await saveProject(old);
  await desk.actions.importFile(JSON.stringify(file));
  assert.equal(desk.session.lesson, null);
  assert.equal(desk.session.notice.kind, 'error');
  assert.match(desk.session.notice.message, /^Phiên bản chưa hỗ trợ: trên máy có dự án bản 2 «Dự án cũ» cùng mã với tệp này\./);
  await assert.rejects(loadLesson(file.project_id), { message: /dự án đã lưu là dự án bản 2/ });
});

test('sửa, thêm, đổi thứ tự và xóa Mục rồi mở lại đúng Dàn ý đã lưu', async () => {
  installFakeIndexedDB();
  const desk = workbench(), file = newFile();
  await desk.actions.importFile(JSON.stringify(file));
  const original = desk.session.lesson.outline.items[0];
  await desk.actions.editItem(original.item_id, { title: 'Sửa tiêu đề', points: ['Ý đã sửa'], slide_count: 4, minutes: 8 });
  const newId = await desk.actions.addItem(original.activity, 'Tình huống khởi động');
  assert.ok(newId);
  const initialIndex = desk.session.lesson.outline.items.findIndex(item => item.item_id === newId);
  await desk.actions.moveItem(newId, -1);
  assert.equal(desk.session.lesson.outline.items[initialIndex - 1].item_id, newId);
  await desk.actions.removeItem(newId);
  const saved = await loadLesson(file.project_id);
  assert.deepEqual(saved.outline.items[0], { ...original, title: 'Sửa tiêu đề', points: ['Ý đã sửa'], slide_count: 4, minutes: 8, needs_review: true });
});

test('lỗi lưu Mục giữ Bản soạn vừa sửa để lưu lại', async () => {
  const db = installFakeIndexedDB();
  const desk = workbench(), file = newFile();
  await desk.actions.importFile(JSON.stringify(file));
  const original = desk.session.lesson.outline.items[0];
  db.failNextCommit(quotaExceeded());
  await desk.actions.editItem(original.item_id, { title: 'Sửa khi hết dung lượng' });
  assert.equal(desk.session.saveState, 'unsaved');
  assert.equal(desk.session.lesson.outline.items[0].title, 'Sửa khi hết dung lượng');
  assert.equal((await loadLesson(file.project_id)).outline.items[0].title, original.title);
});

test('sửa dữ kiện trong chữ Mục đưa hình đã xác nhận về đề xuất', async () => {
  installFakeIndexedDB();
  const desk = workbench(), file = newFile();
  await desk.actions.importFile(JSON.stringify(file));
  const item = desk.session.lesson.outline.items.find(item => item.visuals.some(visual => visual.status === 'confirmed'));
  await desk.actions.editItem(item.item_id, { minutes: item.minutes + 1 });
  assert.deepEqual(desk.session.lesson.outline.items.find(current => current.item_id === item.item_id).visuals, item.visuals);
  await desk.actions.editItem(item.item_id, { points: ['Dữ kiện mới'] });
  const revised = desk.session.lesson.outline.items.find(current => current.item_id === item.item_id);
  assert.ok(revised.visuals.length > 0);
  for (const visual of revised.visuals) {
    assert.equal(visual.status, 'proposed');
    assert.equal(visual.requirement_token, undefined);
  }
});

test('kéo thả và đổi cỡ phần tử bám lưới 20, tăng revision, xóa Xác nhận chuyên môn, đánh dấu slide đã sửa tay và giữ nguyên Dàn ý (#42)', async () => {
  installFakeIndexedDB();
  const desk = workbench(), file = newFile();
  file.deck.review_token = 'signed-expert-token';
  await desk.actions.importFile(JSON.stringify(file));
  const beforeOutline = structuredClone(desk.session.lesson.outline);
  const beforeRevision = desk.session.lesson.deck.revision;
  const slideId = desk.session.lesson.deck.slides[0].slide_id;
  const elId = desk.session.lesson.deck.slides[0].elements[0].element_id;

  await desk.actions.changeElement(slideId, elId, { x: 133, y: 247, w: 611, h: 189 });
  const after = desk.session.lesson;
  const movedEl = after.deck.slides[0].elements[0];
  assert.equal(movedEl.x, 140);
  assert.equal(movedEl.y, 240);
  assert.equal(movedEl.w, 620);
  assert.equal(movedEl.h, 180);
  assert.equal(after.deck.revision, beforeRevision + 1);
  assert.equal(after.deck.review_token, undefined);
  assert.equal(after.deck.slides[0].edited, true);
  assert.deepEqual(after.outline, beforeOutline);
});

test('chữ quá dài vượt ngưỡng thu nhỏ tối thiểu 24pt thì phần tử mang dấu tràn (#42)', () => {
  const shortEl = { element_id: 'e1', type: 'paragraph', x: 100, y: 100, w: 800, h: 200, text: 'Hàm số đồng biến trên R.' };
  const longEl = {
    element_id: 'e2',
    type: 'paragraph',
    x: 100,
    y: 100,
    w: 240,
    h: 80,
    text: 'Đoạn văn rất dài vượt quá kích thước hộp chứa sau khi đã thu nhỏ tới cỡ chữ tối thiểu 24pt trên khung trình chiếu 16:9. '.repeat(4),
  };
  assert.equal(detectElementOverflow(shortEl), false);
  assert.equal(detectElementOverflow(longEl), true);
  const file = normalizeLesson(newFile());
  const updated = updateSlideElement(file, file.deck.slides[0].slide_id, file.deck.slides[0].elements[0].element_id, {
    w: 200,
    h: 60,
    text: longEl.text,
  });
  assert.equal(updated.deck.slides[0].elements[0].overflow, true);
});

test('quy tắc đánh dấu Cần xem lại khi sửa Mục và sinh lại chỉ thay slide của đúng Mục đó (#43)', async () => {
  installFakeIndexedDB();
  const desk = workbench(), file = newFile();
  for (const item of file.outline.items) item.needs_review = false;
  await desk.actions.importFile(JSON.stringify(file));

  const target = desk.session.lesson.outline.items[0];
  // Sửa số phút không đánh dấu Cần xem lại
  await desk.actions.editItem(target.item_id, { minutes: target.minutes + 2 });
  assert.equal(desk.session.lesson.outline.items[0].needs_review, false);

  // Sửa số slide đánh dấu Cần xem lại
  await desk.actions.editItem(target.item_id, { slide_count: 2 });
  assert.equal(desk.session.lesson.outline.items[0].needs_review, true);

  // Sinh lại chỉ thay slide của Mục đó và xóa dấu Cần xem lại
  const otherSlidesBefore = desk.session.lesson.deck.slides.filter(s => s.item_id !== target.item_id);
  const replaced = replaceItemSlides(desk.session.lesson, target.item_id, [
    { slide_id: 's-regen-1', item_id: target.item_id, layout: 'Mở đầu', notes: '', elements: [{ element_id: 'el-r1', type: 'title', x: 120, y: 280, w: 1360, h: 220, text: 'Slide mới 1' }] },
    { slide_id: 's-regen-2', item_id: target.item_id, layout: 'Nội dung', notes: '', elements: [{ element_id: 'el-r2', type: 'title', x: 100, y: 80, w: 1400, h: 100, text: 'Slide mới 2' }] },
  ]);
  assert.equal(replaced.outline.items[0].needs_review, false);
  assert.deepEqual(
    replaced.deck.slides.filter(s => s.item_id === target.item_id).map(s => s.slide_id),
    ['s-regen-1', 's-regen-2'],
  );
  assert.deepEqual(replaced.deck.slides.filter(s => s.item_id !== target.item_id), otherSlidesBefore);
});

test('Cài đặt lưu nhà cung cấp và model, Phân tích lớp học cập nhật trình độ lớp (#46)', () => {
  const desk = workbench();
  desk.actions.updateSettings({ model_provider: 'groq', model_id: 'llama-3.3-70b-versatile' });
  assert.deepEqual(desk.session.settings, { model_provider: 'groq', model_id: 'llama-3.3-70b-versatile' });
  desk.actions.applyClassLevel('advanced');
  assert.equal(desk.session.preferredLevel, 'advanced');
});

test('bỏ phiếu trắc nghiệm lưu vào polls[slide_id] và tự xóa khi sửa câu hỏi hoặc phương án (#47)', () => {
  const base = normalizeLesson({
    ...newFile(),
    deck: {
      revision: 1,
      slides: [
        {
          slide_id: 's-quiz',
          item_id: 'm4',
          layout: 'Câu hỏi trắc nghiệm',
          elements: [
            {
              element_id: 'el-q',
              type: 'quiz',
              x: 100,
              y: 200,
              w: 1400,
              h: 640,
              question: 'Cực đại tại đâu?',
              options: [
                { label: 'A', text: '1', correct: false, why: 'Sai' },
                { label: 'B', text: '-1', correct: true, why: 'Đúng' },
                { label: 'C', text: '0', correct: false, why: 'Sai' },
                { label: 'D', text: '2', correct: false, why: 'Sai' },
              ],
            },
          ],
        },
      ],
    },
  });
  const voted = updateSlidePoll(base, 's-quiz', { A: 3, B: 18, C: 2, D: 1 });
  assert.deepEqual(voted.polls['s-quiz'], { A: 3, B: 18, C: 2, D: 1 });

  // Sửa vị trí phần tử quiz không xóa phiếu
  const moved = updateSlideElement(voted, 's-quiz', 'el-q', { x: 120 });
  assert.deepEqual(moved.polls['s-quiz'], { A: 3, B: 18, C: 2, D: 1 });

  // Sửa nội dung câu hỏi xóa phiếu cũ
  const editedQ = updateSlideElement(moved, 's-quiz', 'el-q', { question: 'Câu hỏi đã đổi?' });
  assert.equal(editedQ.polls['s-quiz'], undefined);
});

test('thêm và xóa phần tử trên canvas tăng revision, xóa review_token và đánh dấu slide đã sửa tay (#48)', () => {
  const base = normalizeLesson({
    ...newFile(),
    deck: {
      revision: 2,
      review_token: 'token-chuyen-mon',
      slides: [
        {
          slide_id: 's1',
          item_id: 'm1',
          layout: 'Mở đầu',
          elements: [{ element_id: 'e1', type: 'title', x: 120, y: 280, w: 1360, h: 220, text: 'Tiêu đề' }],
        },
      ],
    },
  });
  const withFormula = addSlideElement(base, 's1', { element_id: 'e-f', type: 'formula', latex: 'x^2 + 1 = 0' });
  assert.equal(withFormula.deck.revision, 3);
  assert.equal(withFormula.deck.review_token, undefined);
  assert.equal(withFormula.deck.slides[0].edited, true);
  assert.equal(withFormula.deck.slides[0].elements.length, 2);

  const afterRemove = removeSlideElement(withFormula, 's1', 'e-f');
  assert.equal(afterRemove.deck.revision, 4);
  assert.equal(afterRemove.deck.slides[0].elements.length, 1);
});

test('thêm Yêu cầu trực quan, đặt hình sang slide khác trong cùng Mục và chặn đặt sang Mục khác (#51)', () => {
  const base = normalizeLesson({
    ...newFile(),
    deck: {
      revision: 1,
      slides: [
        { slide_id: 's1', item_id: 'm1', layout: 'Mở đầu', elements: [] },
        { slide_id: 's3a', item_id: 'm3', layout: 'Chữ trái, hình phải', elements: [] },
        { slide_id: 's3b', item_id: 'm3', layout: 'Nội dung', elements: [] },
      ],
    },
  });
  const withVis = addItemVisual(base, 'm3', {
    visual_id: 'v-new-graph',
    kind: 'graph',
    label: '$y = x^3$',
    data: { expression: 'x^3', x_min: -2, x_max: 2 },
  }, 's3a');
  assert.ok(withVis.deck.slides[1].elements.some(el => el.visual_id === 'v-new-graph'));

  // Đặt thêm lên slide s3b cùng thuộc Mục m3 -> thành công
  const duplicated = placeVisualOnItemSlide(withVis, 'v-new-graph', 's3b');
  assert.ok(duplicated.deck.slides[2].elements.some(el => el.visual_id === 'v-new-graph'));

  // Đặt sang slide s1 thuộc Mục m1 -> bị chặn theo ADR 0003
  assert.throws(
    () => placeVisualOnItemSlide(duplicated, 'v-new-graph', 's1'),
    { name: 'LessonDataError', message: /thuộc Mục «m3», không được đặt trên slide của Mục «m1»/ },
  );

  // Sửa dữ kiện của hình đã xác nhận đưa hình về trạng thái proposed
  const resetVis = updateItemVisual(duplicated, 'm3', 'v-graph', { data: { expression: 'x^3 - 3x + 1', x_min: -5, x_max: 5 } });
  const updatedGraph = resetVis.outline.items.find(it => it.item_id === 'm3').visuals.find(v => v.visual_id === 'v-graph');
  assert.equal(updatedGraph.status, 'proposed');
  assert.equal(updatedGraph.requirement_token, undefined);
});

test('chuyển dự án bản 2 sang Bài giảng bản 3 giữ nguyên bản 2 gốc trong IndexedDB, giữ giáo án/trắc nghiệm và lược bỏ hình dãy số/bất phương trình (#58)', async () => {
  installFakeIndexedDB();
  const v2Project = {
    schema_version: 2,
    project_id: 'du-an-ban-2-goc',
    title: 'Khảo sát và hình không gian',
    deck: {
      presentation_title: 'Khảo sát và hình không gian',
      slides: [
        { slide_id: 'old-1', type: 'TITLE_SLIDE', title: 'Mở đầu bài học', bullet_points: ['Giới thiệu'] },
        {
          slide_id: 'old-2',
          type: 'CONCEPT_SLIDE',
          title: 'Đồ thị hàm bậc ba',
          bullet_points: ['Xét $y = x^3 - 3x$'],
          main_definition_latex: "y' = 3x^2 - 3",
          chart_spec: { kind: 'function_plot', expression: 'x^3 - 3*x', x_min: -3, x_max: 3, requirement_token: 'old-tok' },
        },
        {
          slide_id: 'old-3',
          type: 'CONCEPT_SLIDE',
          title: 'Cấp số cộng lớp 11',
          bullet_points: ['Dãy số cộng'],
          chart_spec: { kind: 'arithmetic_sequence', first_term: 1, common_difference: 2, count: 5 },
        },
        {
          slide_id: 'old-4',
          type: 'EXERCISE_SLIDE',
          layout: 'QUIZ_OPTION',
          title: 'Câu hỏi củng cố',
          question: 'Đạo hàm của $x^3$ là?',
          quiz_options: [
            { label: 'A', text: '$3x^2$', is_correct: true, distractor_rationale: 'Đúng' },
            { label: 'B', text: '$x^2$', is_correct: false, distractor_rationale: 'Thiếu hệ số 3' },
            { label: 'C', text: '$3x$', is_correct: false, distractor_rationale: 'Sai số mũ' },
            { label: 'D', text: '$1$', is_correct: false, distractor_rationale: 'Sai' },
          ],
        },
      ],
    },
    plan: {
      lesson_title: 'Khảo sát và hình không gian',
      subject: 'Toán học',
      grade: 12,
      knowledge_goals: ['Nắm khảo sát hàm số'],
      activities: [],
    },
  };
  await saveProject(v2Project);

  const desk = workbench();
  await desk.actions.openLesson('du-an-ban-2-goc');

  const migrated = desk.session.lesson;
  assert.ok(migrated);
  assert.equal(migrated.schema_version, 3);
  assert.equal(migrated.project_id, 'du-an-ban-2-goc-v3');
  assert.equal(migrated.migrated_from_v2, 'du-an-ban-2-goc');
  assert.equal(migrated.outline.items.length, 4);
  assert.equal(migrated.deck.slides.length, 4);
  assert.equal(migrated.plan.lesson_title, 'Khảo sát và hình không gian');

  // Hình đồ thị được chuyển sang proposed để xác nhận lại
  const itemWithGraph = migrated.outline.items.find(it => it.title === 'Đồ thị hàm bậc ba');
  assert.equal(itemWithGraph.visuals.length, 1);
  assert.equal(itemWithGraph.visuals[0].kind, 'graph');
  assert.equal(itemWithGraph.visuals[0].status, 'proposed');
  assert.equal(itemWithGraph.visuals[0].requirement_token, undefined);

  // Hình arithmetic_sequence bị lược bỏ và thông báo nêu rõ tên slide
  const itemDropped = migrated.outline.items.find(it => it.title === 'Cấp số cộng lớp 11');
  assert.equal(itemDropped.visuals.length, 0);
  assert.match(desk.session.notice.message, /Cấp số cộng lớp 11/);

  // Bản ghi bản 2 gốc trong IndexedDB vẫn còn nguyên vẹn
  const rawList = await listLessons();
  assert.ok(rawList.legacyProjects.some(p => p.project_id === 'du-an-ban-2-goc'));
});
