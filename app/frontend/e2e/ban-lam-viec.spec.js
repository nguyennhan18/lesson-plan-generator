import { test, expect } from '@playwright/test';
import { readFile } from 'node:fs/promises';

// A Bài giảng bản 3 as the teacher's JSON file holds it (spec #36, ticket #38). 45 minutes, 10 slides.
const lessonFile = () => ({
  schema_version: 3,
  project_id: 'e2e-bai-giang-ban-3',
  title: 'Khảo sát hàm số bậc ba $y = x^3 - 3x + 1$',
  sgk: 'Toán 12, Chương I, Bài 4',
  level: 'Trung bình',
  outline: {
    items: [
      { item_id: 'm1', activity: 'Khởi động', kind: 'Mở đầu', title: 'Khảo sát hàm số bậc ba', points: ['Toán 12, Chương I, Bài 4'], slide_count: 1, minutes: 2 },
      { item_id: 'm2', activity: 'Khởi động', kind: 'Tình huống khởi động', title: 'Hai bạn vẽ cùng một đồ thị', points: ['An chấm điểm rồi nối, Bình xét dấu đạo hàm trước.'], slide_count: 1, minutes: 5 },
      { item_id: 'm3', activity: 'Hình thành kiến thức', kind: 'Kiến thức trọng tâm', title: 'Sơ đồ khảo sát hàm số', points: ['Tập xác định', 'Sự biến thiên', 'Đồ thị'], slide_count: 2, minutes: 10 },
      {
        item_id: 'm4', activity: 'Hình thành kiến thức', kind: 'Ví dụ', title: 'Ví dụ 1. Khảo sát $y = x^3 - 3x + 1$',
        points: ['Đạo hàm và cực trị', 'Bảng biến thiên', 'Vẽ đồ thị'], slide_count: 3, minutes: 12,
        visuals: [
          { visual_id: 'v-bbt', kind: 'bbt', origin: 'ai', status: 'proposed', label: '$y = x^3 - 3x + 1$', data: { expression: 'x^3 - 3x + 1' } },
          { visual_id: 'v-graph', kind: 'graph', origin: 'ai', status: 'confirmed', requirement_token: 'e2e-token', label: '$y = x^3 - 3x + 1$', data: { expression: 'x^3 - 3x + 1', x_min: -3, x_max: 3 } }
        ]
      },
      { item_id: 'm5', activity: 'Luyện tập', kind: 'Câu hỏi trắc nghiệm', title: 'Hàm số $y = x^3 - 3x + 1$ đạt cực đại tại điểm nào?', points: ['Bốn phương án, một phương án đúng'], slide_count: 1, minutes: 4 },
      { item_id: 'm6', activity: 'Luyện tập', kind: 'Bài luyện tập', title: 'Khảo sát $y = -x^3 + 3x^2 - 4$', points: ['Mức độ: thông hiểu'], slide_count: 1, minutes: 7, needs_review: true },
      { item_id: 'm7', activity: 'Vận dụng', kind: 'Tổng kết', title: 'Tổng kết và nhiệm vụ về nhà', points: ['Ba bước khảo sát hàm số'], slide_count: 1, minutes: 5 }
    ]
  },
  deck: null
});

// Page errors, console errors, failed app requests, and any request that leaves this machine (the app
// must work offline). Desktop Chrome asks for /favicon.ico by itself; the app has none, so that miss is not a page error.
const browserFavicon = url => new URL(url).pathname === '/favicon.ico';
function watch(page) {
  const problems = [];
  page.on('pageerror', error => problems.push(`pageerror: ${error.message}`));
  page.on('console', message => {
    if (message.type() === 'error' && !browserFavicon(message.location().url || page.url())) problems.push(`console: ${message.text()} (${message.location().url})`);
  });
  page.on('response', response => {
    if (response.status() >= 400 && !browserFavicon(response.url())) problems.push(`HTTP ${response.status()}: ${response.url()}`);
  });
  page.on('request', request => {
    const url = new URL(request.url());
    if (!['data:', 'blob:'].includes(url.protocol) && !['127.0.0.1', 'localhost'].includes(url.hostname)) problems.push(`external request: ${request.url()}`);
  });
  return problems;
}

async function openWorkbench(page) {
  await page.goto('/');
  await expect(page.getByRole('complementary', { name: 'Bài giảng đã lưu' })).toBeVisible();
}

async function importLesson(page, data) {
  await page.getByRole('button', { name: 'Tệp', exact: true }).click();
  const chooser = page.waitForEvent('filechooser');
  await page.getByRole('button', { name: 'Nhập tệp JSON bản 3…' }).click();
  await (await chooser).setFiles({ name: 'bai-giang.json', mimeType: 'application/json', buffer: Buffer.from(JSON.stringify(data)) });
}

const outlineTree = page => page.getByRole('complementary', { name: 'Dàn ý' });
const treeItem = (page, text) => outlineTree(page).getByRole('listitem').filter({ hasText: text });

test('nhập JSON bản 3 thì thấy cây Dàn ý theo bốn Hoạt động và thanh thời lượng, không có lỗi trang', async ({ page }) => {
  const problems = watch(page);
  await openWorkbench(page);
  await importLesson(page, lessonFile());

  const tree = outlineTree(page);
  await expect(tree.getByRole('heading', { level: 3 })).toHaveText([/^Khởi động\s*7 phút$/, /^Hình thành kiến thức\s*22 phút$/, /^Luyện tập\s*11 phút$/, /^Vận dụng\s*5 phút$/]);
  await expect(tree.getByRole('img', { name: /^Thời lượng:/ })).toHaveAttribute('aria-label',
    'Thời lượng: Khởi động 7 phút, Hình thành kiến thức 22 phút, Luyện tập 11 phút, Vận dụng 5 phút; tổng 45 trên 45 phút.');
  await expect(tree).toContainText('45/45 phút, 10 slide');

  const concept = treeItem(page, 'Sơ đồ khảo sát hàm số');
  await expect(concept).toContainText(/^3/);
  await expect(concept).toContainText('Kiến thức trọng tâm');
  await expect(concept.getByRole('img', { name: '2 slide' })).toBeVisible();
  const example = treeItem(page, 'Ví dụ 1.');
  await expect(example.getByRole('math')).toHaveCount(1);
  await expect(example.getByRole('img', { name: '3 slide' })).toBeVisible();
  await expect(example.getByRole('img', { name: 'Bảng biến thiên, chờ xác nhận' })).toHaveCSS('border-top-style', 'dashed');
  await expect(example.getByRole('img', { name: 'Đồ thị hàm số, đã xác nhận' })).toHaveCSS('border-top-style', 'solid');
  await expect(tree).not.toContainText('$'); // formulas in titles are typeset, never shown as raw LaTeX
  await expect(outlineTree(page).getByRole('listitem').nth(5)).toContainText('Cần xem lại');
  await expect(outlineTree(page).getByRole('listitem').filter({ hasText: 'Cần xem lại' })).toHaveCount(1);

  const top = page.getByRole('banner');
  await expect(top).toContainText('LessonAI');
  await expect(top.getByRole('navigation', { name: 'Đường dẫn' }).getByRole('button', { name: 'Bài giảng' })).toBeVisible();
  await expect(top.getByRole('navigation', { name: 'Đường dẫn' })).toContainText('Khảo sát hàm số bậc ba');
  await expect(top.getByText('Bản nháp', { exact: true })).toHaveCSS('border-top-style', 'dashed');

  const sheet = page.getByRole('main').getByRole('article');
  await expect(sheet).toContainText('Phiếu Dàn ý, chỉ xem');
  await expect(sheet.getByRole('heading', { level: 1 })).toContainText('Khảo sát hàm số bậc ba');
  await expect(sheet).toContainText('Toán 12, Chương I, Bài 4. Trình độ lớp: trung bình');
  await expect(sheet.getByRole('img', { name: /^Thời lượng:/ })).toBeVisible();
  await expect(sheet).toContainText('1 hình chờ xác nhận dữ kiện.');
  await expect(sheet.getByRole('button', { name: /Bảng biến thiên.*Mục 4, AI đề xuất, chờ xác nhận/ })).toHaveCSS('border-top-style', 'dashed');
  expect(await sheet.evaluate(element => getComputedStyle(element).animationName)).toBe('wb-fade');

  await concept.getByRole('button').click();
  const properties = page.getByRole('complementary', { name: 'Thuộc tính' });
  await expect(properties).toContainText('Mục 3, Hình thành kiến thức');
  await expect(properties).toContainText('Loại mụcKiến thức trọng tâm');
  await expect(properties).toContainText('Số phút10');
  await expect(properties.getByRole('listitem')).toHaveText(['Tập xác định', 'Sự biến thiên', 'Đồ thị']);
  expect(problems).toEqual([]);
});

test('Bài giảng đã nhập còn sau khi tải lại trang, và xuất JSON trả lại đúng Bài giảng', async ({ page }) => {
  const problems = watch(page);
  await openWorkbench(page);
  await importLesson(page, lessonFile());
  await expect(outlineTree(page)).toBeVisible();

  await page.getByRole('button', { name: 'Tệp', exact: true }).click();
  const download = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Xuất tệp JSON' }).click();
  const file = await download;
  expect(file.suggestedFilename()).toBe('bai-giang-khao-sat-ham-so-bac-ba-y-x-3-3x-1.json');
  const exported = JSON.parse(await readFile(await file.path(), 'utf8'));
  expect(exported.project_id).toBe('e2e-bai-giang-ban-3');
  expect(exported.outline.items.map(item => item.item_id)).toEqual(['m1', 'm2', 'm3', 'm4', 'm5', 'm6', 'm7']);
  expect(exported.outline.items[0]).toMatchObject({ visuals: [], needs_review: false });

  await page.reload();
  const saved = page.getByRole('complementary', { name: 'Bài giảng đã lưu' }).getByRole('button', { name: /Khảo sát hàm số bậc ba/ });
  await expect(saved).toContainText('7 Mục, chưa có slide');
  await saved.click();
  await expect(outlineTree(page).getByRole('heading', { level: 3 })).toHaveCount(4);
  await expect(outlineTree(page).getByRole('listitem')).toHaveCount(7);
  expect(problems).toEqual([]);
});

test('dữ liệu sai hoặc phiên bản khác bị từ chối kèm thông báo rõ', async ({ page }) => {
  const problems = watch(page);
  await openWorkbench(page);
  const wrong = lessonFile();
  wrong.outline.items[2].slide_count = 5;
  await importLesson(page, wrong);
  await expect(page.getByRole('alert')).toContainText('Dữ liệu Bài giảng không hợp lệ: Mục 3 («m3»): số slide phải là số nguyên từ 1 đến 4.');
  await importLesson(page, { schema_version: 4, project_id: 'du-an-la', deck: { slides: [] } });
  await expect(page.getByRole('alert')).toContainText('Phiên bản chưa hỗ trợ: tệp ghi bản 4; Bàn làm việc chỉ mở được Bài giảng bản 3.');
  await expect(page.getByRole('complementary', { name: 'Bài giảng đã lưu' })).toContainText('Chưa có Bài giảng bản 3 nào trên máy này.');
  expect(problems).toEqual([]);
});

test('lưu thất bại vì hết dung lượng vẫn giữ Bản soạn, báo lỗi và cho xuất bản dự phòng', async ({ page }) => {
  await openWorkbench(page);
  await page.evaluate(() => { IDBObjectStore.prototype.put = () => { throw new DOMException('quota test', 'QuotaExceededError'); }; });
  await importLesson(page, lessonFile());
  await expect(page.getByRole('alert')).toContainText('Chưa lưu: bộ nhớ trình duyệt đã hết dung lượng. Bản soạn vẫn đang mở');
  await expect(outlineTree(page).getByRole('listitem')).toHaveCount(7);
  await expect(page.getByRole('banner')).toContainText('Chưa lưu');

  const download = page.waitForEvent('download');
  await page.getByRole('alert').getByRole('button', { name: 'Xuất tệp JSON dự phòng' }).click();
  expect(JSON.parse(await readFile(await (await download).path(), 'utf8')).project_id).toBe('e2e-bai-giang-ban-3');

  await page.getByRole('navigation', { name: 'Đường dẫn' }).getByRole('button', { name: 'Bài giảng' }).click();
  await expect(page.getByRole('alert')).toContainText('Bản soạn đang mở chưa được lưu.');
  await expect(outlineTree(page).getByRole('listitem')).toHaveCount(7);
});

test('Bộ slide có Xác nhận chuyên môn thì nhãn trên thanh trên có viền nét liền', async ({ page }) => {
  await openWorkbench(page);
  await importLesson(page, {
    ...lessonFile(),
    project_id: 'e2e-da-xac-nhan',
    deck: {
      review_token: 'e2e-review',
      slides: [{ slide_id: 's1', item_id: 'm1', layout: 'Mở đầu', elements: [{ element_id: 'e1', type: 'title', x: 120, y: 280, w: 1360, h: 220, text: 'Khảo sát hàm số bậc ba' }] }]
    }
  });
  await expect(page.getByRole('banner').getByText('Đã xác nhận chuyên môn', { exact: true })).toHaveCSS('border-top-style', 'solid');
  await expect(page.getByRole('banner').getByText('Bản nháp', { exact: true })).toHaveCount(0);
});

test('Bàn làm việc là giao diện mặc định duy nhất và tự động chuyển dự án bản 2 sang Bài giảng bản 3 (#58, #59)', async ({ page }) => {
  const problems = watch(page);
  await page.goto('/');
  await expect(page.getByRole('switch', { name: 'Bàn làm việc' })).toHaveCount(0);
  await expect(page.getByRole('complementary', { name: 'Bài giảng đã lưu' })).toBeVisible();

  await importLesson(page, {
    schema_version: 2,
    project_id: 'e2e-du-an-ban-2',
    title: 'Bài giảng từ bản 2',
    deck: {
      presentation_title: 'Bài giảng từ bản 2',
      slides: [
        { slide_id: 'v2-s1', type: 'TITLE_SLIDE', title: 'Mở đầu bản 2', bullet_points: ['Giới thiệu'] },
        {
          slide_id: 'v2-s2',
          type: 'CONCEPT_SLIDE',
          title: 'Đồ thị bản 2',
          bullet_points: ['Hàm bậc ba'],
          chart_spec: { kind: 'function_plot', expression: 'x^3 - 3*x', x_min: -3, x_max: 3 },
        },
        {
          slide_id: 'v2-s3',
          type: 'CONCEPT_SLIDE',
          title: 'Slide cấp số cộng cũ',
          bullet_points: ['Dãy số'],
          chart_spec: { kind: 'arithmetic_sequence', first_term: 1, common_difference: 2, count: 5 },
        },
      ],
    },
  });

  await expect(page.getByRole('alert')).toContainText('Đã chuyển dự án bản 2 sang Bài giảng bản 3');
  await expect(page.getByRole('alert')).toContainText('Slide cấp số cộng cũ');
  await expect(outlineTree(page).getByRole('listitem')).toHaveCount(3);
  await expect(page.getByTestId('wb-canvas')).toContainText('Mở đầu bản 2');
  expect(problems).toEqual([]);
});

test('màn soạn đủ ba cột ở độ rộng 1280 px, chữ dùng font đóng gói, hiệu ứng tắt khi giảm chuyển động', async ({ page }) => {
  const problems = watch(page), fonts = [];
  page.on('response', response => { if (/\.woff$/.test(new URL(response.url()).pathname)) fonts.push(new URL(response.url()).pathname); });
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await openWorkbench(page);
  await importLesson(page, lessonFile());
  await treeItem(page, 'Sơ đồ khảo sát hàm số').getByRole('button').click();

  expect(await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBe(0);
  const left = await outlineTree(page).boundingBox(), centre = await page.getByRole('main').boundingBox();
  const right = await page.getByRole('complementary', { name: 'Thuộc tính' }).boundingBox();
  expect(left.x).toBe(0);
  expect(left.x + left.width).toBeLessThanOrEqual(centre.x + 1);
  expect(centre.x + centre.width).toBeLessThanOrEqual(right.x + 1);
  expect(right.x + right.width).toBeLessThanOrEqual(1280);
  const sheet = await page.getByRole('main').getByRole('article').boundingBox();
  expect(sheet.x).toBeGreaterThanOrEqual(centre.x);
  expect(sheet.x + sheet.width).toBeLessThanOrEqual(centre.x + centre.width);

  await page.evaluate(() => document.fonts.ready);
  const faces = await page.evaluate(() => [...document.fonts].filter(face => !face.family.startsWith('KaTeX')).map(face => `${face.family} ${face.weight} ${face.status}`));
  expect(faces.sort()).toEqual(['Be Vietnam Pro 400 loaded', 'Be Vietnam Pro 500 loaded', 'Be Vietnam Pro 600 loaded', 'Source Serif 4 200 900 loaded']);
  expect(fonts.filter(path => /SourceSerif4|BeVietnamPro/.test(path))).toHaveLength(4);
  expect(await page.getByRole('main').getByRole('heading', { level: 1 }).evaluate(element => getComputedStyle(element).fontFamily)).toMatch(/^"Source Serif 4"/);
  expect(await page.getByRole('button', { name: 'Tệp', exact: true }).evaluate(element => getComputedStyle(element).fontFamily)).toMatch(/^"Be Vietnam Pro"/);

  expect(await page.getByRole('main').getByRole('article').evaluate(element => getComputedStyle(element).animationName)).toBe('none');
  expect(await page.getByRole('complementary', { name: 'Thuộc tính' }).locator('.wb-fade').evaluate(element => getComputedStyle(element).animationName)).toBe('none');
  expect(problems).toEqual([]);
});

test('sửa Mục nhập từ JSON thì cây và thời lượng cập nhật', async ({ page }) => {
  await openWorkbench(page);
  const file = lessonFile();
  file.outline.items[2].points = ['Tập xác định\nSự biến thiên'];
  await importLesson(page, file);
  const tree = outlineTree(page);
  await tree.getByRole('button', { name: /Sơ đồ khảo sát/ }).click();
  const properties = page.getByRole('complementary', { name: 'Thuộc tính' });
  await properties.getByLabel('Tiêu đề Mục').fill('Quy trình khảo sát');
  await properties.getByLabel('Số phút dự kiến').fill('14');
  await properties.getByRole('button', { name: 'Lưu Mục' }).click();
  await expect(tree.getByRole('button', { name: /Quy trình khảo sát/ })).toBeVisible();
  await expect(tree).toContainText('49/45 phút, 10 slide, vượt 4 phút');
  await expect(properties.getByRole('listitem')).toHaveCount(1);
});

test('đổi bài SGK rồi thử lại sau lỗi AI, Bản soạn cũ vẫn còn', async ({ page }) => {
  await openWorkbench(page);
  await importLesson(page, lessonFile());
  await page.route('**/api/v1/workbench/outline/identify', route => route.fulfill({ json: {
    lesson_id: 'M12-C4-B2',
    lessons: [{ lesson_id: 'M12-C4-B2', title: 'Tích phân' }, { lesson_id: 'M12-C4-B1', title: 'Nguyên hàm' }]
  } }));
  const calls = [];
  await page.route('**/api/v1/workbench/outline', route => {
    calls.push(route.request().postDataJSON());
    if (calls.length === 1) return route.fulfill({ status: 503, json: {
      detail: { code: 'generation_unavailable', message: 'Dịch vụ AI gián đoạn.', request_id: 'e2e' }
    } });
    return route.fulfill({ json: {
      schema_version: 3, title: 'Nguyên hàm', sgk: 'Nguyên hàm',
      outline: lessonFile().outline, warnings: [], source_refs: []
    } });
  });

  await page.getByRole('button', { name: 'Soạn bài mới' }).click();
  const modal = page.getByRole('dialog', { name: 'Soạn bài mới' });
  await modal.getByLabel('Yêu cầu soạn bài').fill('Soạn bài tích phân');
  await expect(modal.getByText('Bài SGK: Tích phân')).toBeVisible();
  await modal.getByRole('button', { name: 'Đổi bài' }).click();
  await modal.getByRole('combobox', { name: 'Bài SGK', exact: true }).selectOption('M12-C4-B1');
  await modal.getByRole('combobox', { name: 'Trình độ lớp', exact: true }).selectOption('advanced');
  await modal.getByRole('button', { name: 'Lập dàn ý' }).click();
  await expect(modal.getByRole('alert')).toContainText('[generation_unavailable]');
  await expect(page.locator('.wb-sheet-title').filter({ hasText: 'Khảo sát hàm số bậc ba' })).toBeVisible();
  await modal.getByRole('button', { name: 'Thử lại', exact: true }).click();
  await expect(modal).toBeHidden();
  await expect(page.getByRole('main').getByRole('heading', { name: 'Nguyên hàm' })).toBeVisible();
  await expect(page.getByText('Chưa có nguồn đã duyệt cho bài này')).toBeVisible();
  await expect(outlineTree(page).getByRole('listitem').first()).toHaveCSS('animation-name', 'wb-ink');
  expect(calls).toHaveLength(2);
  expect(calls[0]).toEqual({ request: 'Soạn bài tích phân', lesson_id: 'M12-C4-B1', level: 'advanced' });
  expect(calls[1]).toEqual(calls[0]);
});

const lessonFileWithSlides = () => ({
  ...lessonFile(),
  project_id: 'e2e-bai-giang-co-slide',
  deck: {
    revision: 1,
    slides: [
      {
        slide_id: 's1',
        item_id: 'm1',
        layout: 'Mở đầu',
        notes: 'Ghi chú chỉ dành cho giáo viên, không hiện khi chiếu',
        elements: [
          { element_id: 'e1-title', type: 'title', hero: true, x: 120, y: 280, w: 1360, h: 220, reveal: 0, parts: 1, text: 'Khảo sát hàm số bậc ba' },
          { element_id: 'e1-cap', type: 'caption', x: 120, y: 540, w: 900, h: 60, reveal: 0, parts: 1, text: 'Toán 12, Chương I, Bài 4' },
        ],
      },
      {
        slide_id: 's2',
        item_id: 'm3',
        layout: 'Kiến thức trọng tâm',
        notes: '',
        elements: [
          { element_id: 'e2-title', type: 'title', x: 100, y: 80, w: 1400, h: 100, reveal: 0, parts: 1, text: 'Sơ đồ khảo sát hàm số' },
          {
            element_id: 'e2-steps',
            type: 'steps',
            x: 100,
            y: 220,
            w: 1400,
            h: 400,
            reveal: 1,
            parts: 3,
            items: ['Bước 1: Tìm tập xác định', 'Bước 2: Xét sự biến thiên', 'Bước 3: Vẽ đồ thị'],
          },
          { element_id: 'e2-formula', type: 'formula', x: 100, y: 660, w: 1400, h: 140, reveal: 4, parts: 1, latex: "f'(x) = 3x^2 - 3" },
        ],
      },
      {
        slide_id: 's3',
        item_id: 'm5',
        layout: 'Câu hỏi trắc nghiệm',
        notes: '',
        elements: [
          {
            element_id: 'e3-title',
            type: 'title',
            x: 100,
            y: 80,
            w: 220,
            h: 60,
            reveal: 0,
            parts: 1,
            text: 'Tiêu đề rất dài để kiểm tra tự thu nhỏ chữ xuống ngưỡng tối thiểu 24pt và đánh dấu tràn khung trên canvas 16:9 khi hộp quá hẹp '.repeat(2),
          },
          {
            element_id: 'e3-quiz',
            type: 'quiz',
            x: 100,
            y: 200,
            w: 1400,
            h: 640,
            reveal: 0,
            parts: 1,
            question: 'Hàm số $y = x^3 - 3x + 1$ đạt cực đại tại điểm nào?',
            options: [
              { label: 'A', text: '$x = 1$', correct: false, why: 'Cực tiểu' },
              { label: 'B', text: '$x = -1$', correct: true, why: 'Đổi dấu từ + sang -' },
              { label: 'C', text: '$x = 3$', correct: false, why: 'Giá trị cực đại' },
              { label: 'D', text: '$x = 0$', correct: false, why: 'Không phải điểm dừng' },
            ],
          },
        ],
      },
    ],
  },
});

test('nạp JSON bản 3 có slide thì canvas và dải slide hiển thị, chọn được slide, kéo phần tử bám lưới 20 và chữ dài sinh dấu tràn (#40, #42)', async ({ page }) => {
  const problems = watch(page);
  await openWorkbench(page);
  await importLesson(page, lessonFileWithSlides());

  const canvas = page.getByTestId('wb-canvas');
  await expect(canvas).toBeVisible();
  const strip = page.getByRole('region', { name: 'Dải slide' });
  await expect(strip.getByRole('button', { name: /^Slide \d+$/ })).toHaveCount(3);

  // Chọn slide 2 từ Dải slide
  await strip.getByRole('button', { name: 'Slide 2' }).click();
  await expect(canvas).toContainText('Sơ đồ khảo sát hàm số');
  await expect(canvas.getByRole('math')).toHaveCount(1);

  // Chọn phần tử tiêu đề trên slide 2 và kéo sang vị trí mới -> bám lưới bội số của 20
  const titleEl = canvas.locator('[data-element-id="e2-title"]');
  const box = await titleEl.boundingBox();
  await page.mouse.move(box.x + 30, box.y + 20);
  await page.mouse.down();
  await page.mouse.move(box.x + 95, box.y + 75, { steps: 4 });
  await page.mouse.up();

  const properties = page.getByRole('complementary', { name: 'Thuộc tính' });
  await expect(properties).toContainText('Loại phần tửTiêu đề');
  const posText = await properties.locator('.wb-props').textContent();
  const match = posText.match(/Vị trí(\d+),\s*(\d+)/);
  expect(match).not.toBeNull();
  expect(Number(match[1]) % 20).toBe(0);
  expect(Number(match[2]) % 20).toBe(0);

  // Chọn slide 3 từ cây Dàn ý -> kiểm tra dấu tràn chữ và câu hỏi trắc nghiệm tĩnh
  await treeItem(page, 'đạt cực đại').getByRole('button').first().click();
  await outlineTree(page).getByRole('button', { name: 'Mục 5, Slide 3' }).click();
  await expect(canvas.locator('[data-element-id="e3-title"]')).toHaveAttribute('data-overflow', 'true');
  await expect(canvas).toContainText('Tràn chữ');
  expect(problems).toEqual([]);
});

test('trình chiếu cơ bản: các bước hiện dần đúng thứ tự, sang slide sau, Esc đưa về đúng slide và không có lỗi trang (#41)', async ({ page }) => {
  const problems = watch(page);
  await openWorkbench(page);
  await importLesson(page, lessonFileWithSlides());

  await page.getByRole('button', { name: 'Trình chiếu' }).click();
  const presenter = page.getByRole('region', { name: 'Màn trình chiếu' });
  await expect(presenter).toBeVisible();
  await expect(presenter).not.toContainText('Ghi chú chỉ dành cho giáo viên');
  await expect(presenter.getByLabel('Số trang')).toHaveText('1/3');

  // Slide 1 có 0 bước hiện dần -> bấm ArrowRight sang Slide 2 ở bước 0 (chỉ hiện tiêu đề, chưa hiện các bước giải)
  await page.keyboard.press('ArrowRight');
  await expect(presenter.getByLabel('Số trang')).toHaveText('2/3');
  await expect(presenter).toContainText('Sơ đồ khảo sát hàm số');
  await expect(presenter).not.toContainText('Bước 1: Tìm tập xác định');

  // Bước 1, 2, 3 hiện từng ý; Bước 4 hiện công thức
  await page.keyboard.press('ArrowRight');
  await expect(presenter).toContainText('Bước 1: Tìm tập xác định');
  await expect(presenter).not.toContainText('Bước 2: Xét sự biến thiên');

  await page.keyboard.press('Space');
  await expect(presenter).toContainText('Bước 2: Xét sự biến thiên');

  await page.keyboard.press('PageDown');
  await expect(presenter).toContainText('Bước 3: Vẽ đồ thị');

  await page.keyboard.press('ArrowRight');
  await expect(presenter.getByRole('math')).toHaveCount(1);

  // Bấm Esc thoát trình chiếu -> quay về đúng Slide 2 đang chiếu
  await page.keyboard.press('Escape');
  await expect(presenter).toBeHidden();
  await expect(page.getByRole('region', { name: 'Dải slide' }).getByRole('button', { name: 'Slide 2' })).toHaveAttribute('aria-current', 'true');
  expect(problems).toEqual([]);
});

test('đổi số slide khi đã có Bộ slide thì hiện Cần xem lại và nút sinh lại, chỉ thay slide của Mục đó (#43)', async ({ page }) => {
  const problems = watch(page);
  await openWorkbench(page);
  await importLesson(page, lessonFileWithSlides());

  await page.route('**/api/v1/workbench/slides/item', route => route.fulfill({
    json: {
      prompt_chars: 520,
      slides: [
        {
          slide_id: 's1-new-a',
          item_id: 'm1',
          layout: 'Mở đầu',
          notes: '',
          elements: [{ element_id: 'en-1', type: 'title', x: 120, y: 280, w: 1360, h: 220, reveal: 0, parts: 1, text: 'Mở đầu mới 1' }],
        },
        {
          slide_id: 's1-new-b',
          item_id: 'm1',
          layout: 'Nội dung',
          notes: '',
          elements: [{ element_id: 'en-2', type: 'title', x: 100, y: 80, w: 1400, h: 100, reveal: 0, parts: 1, text: 'Mở đầu mới 2' }],
        },
      ],
    },
  }));

  await outlineTree(page).getByRole('listitem').first().getByRole('button').first().click();
  const properties = page.getByRole('complementary', { name: 'Thuộc tính' });
  await properties.getByLabel('Số slide dự kiến').fill('2');
  await properties.getByRole('button', { name: 'Lưu Mục' }).click();

  await expect(outlineTree(page).getByRole('listitem').first()).toContainText('Cần xem lại');
  const regenBtn = properties.getByRole('button', { name: 'Sinh lại slide của mục này' });
  await expect(regenBtn).toBeVisible();
  await regenBtn.click();

  await expect(outlineTree(page).getByRole('listitem').first()).not.toContainText('Cần xem lại');
  await expect(page.getByRole('region', { name: 'Dải slide' }).getByRole('button', { name: /^Slide \d+$/ })).toHaveCount(4);
  expect(problems).toEqual([]);
});

test('đổi model trong Cài đặt thì Lập Dàn ý gửi đúng model, Phân tích lớp học điền sẵn trình độ lớp (#46)', async ({ page }) => {
  const problems = watch(page);
  await openWorkbench(page);

  await page.route('**/api/v1/workbench/outline/identify', route => route.fulfill({
    json: { lesson_id: 'M12-C4-B2', lessons: [{ lesson_id: 'M12-C4-B2', title: 'Tích phân' }] },
  }));
  const outlineCalls = [];
  await page.route('**/api/v1/workbench/outline', route => {
    outlineCalls.push(route.request().postDataJSON());
    return route.fulfill({
      json: {
        schema_version: 3,
        title: 'Tích phân',
        sgk: 'Tích phân',
        lesson_id: 'M12-C4-B2',
        outline: lessonFile().outline,
        source_refs: [],
        warnings: [],
      },
    });
  });
  await page.route('**/api/v1/ingest/classify-grades', route => route.fulfill({
    json: {
      filename: 'diem-12a1.csv',
      total_students: 30,
      mean: 8.4,
      std_dev: 0.7,
      cv: 0.083,
      class_label: 'advanced',
      target_outcome: 'Lớp khá giỏi',
      counts: { below_5: 0, between_5_8: 6, above_8: 24 },
      student_evaluations: [],
    },
  }));

  // 1. Đổi nhà cung cấp và model trong Cài đặt
  await page.getByRole('button', { name: 'Menu phụ' }).click();
  await page.getByRole('button', { name: 'Cài đặt' }).click();
  const settingsModal = page.getByRole('dialog', { name: 'Cài đặt' });
  await settingsModal.getByLabel('Nhà cung cấp AI').selectOption('groq');
  await settingsModal.getByLabel('Model AI').fill('llama-3.3-70b-versatile');
  await settingsModal.getByRole('button', { name: 'Lưu cài đặt' }).click();

  // 2. Mở Phân tích lớp học từ Menu phụ và áp dụng kết quả
  await page.getByRole('button', { name: 'Menu phụ' }).click();
  await page.getByRole('button', { name: 'Phân tích lớp học' }).click();
  const analyticsModal = page.getByRole('dialog', { name: 'Phân tích lớp học' });
  await analyticsModal.getByLabel('Nhập bảng điểm').setInputFiles({
    name: 'diem-12a1.csv',
    mimeType: 'text/csv',
    buffer: Buffer.from('score\n8.5\n9.0\n'),
  });
  await analyticsModal.getByRole('button', { name: 'Áp dụng phân hóa vào bài dạy' }).click();
  await expect(analyticsModal).toBeHidden();

  // 3. Trình độ lớp ở ô yêu cầu đã được điền sẵn 'advanced' (Khá), và Lập dàn ý gửi đúng model đã chọn
  const mainForm = page.getByRole('main');
  await expect(mainForm.getByLabel('Trình độ lớp')).toHaveValue('advanced');
  await mainForm.getByLabel('Yêu cầu soạn bài').fill('Soạn bài tích phân');
  await expect(mainForm.getByText('Bài SGK: Tích phân')).toBeVisible();
  await mainForm.getByRole('button', { name: 'Lập dàn ý' }).click();

  expect(outlineCalls).toHaveLength(1);
  expect(outlineCalls[0]).toEqual({
    request: 'Soạn bài tích phân',
    lesson_id: 'M12-C4-B2',
    level: 'advanced',
    model_provider: 'groq',
    model_id: 'llama-3.3-70b-versatile',
  });
  expect(problems).toEqual([]);
});

test('sửa phần tử trên canvas, từ chối ảnh hỏng, bỏ phiếu trắc nghiệm khi chiếu và xóa phiếu khi sửa câu hỏi (#47, #48)', async ({ page }) => {
  const problems = watch(page);
  await openWorkbench(page);
  await importLesson(page, lessonFileWithSlides());

  const canvas = page.getByTestId('wb-canvas');
  // Nhấp đúp sửa tiêu đề trên Slide 1 kèm công thức $y = x^3$
  const titleEl = canvas.locator('[data-element-id="e1-title"]');
  await titleEl.dblclick();
  const inlineInput = canvas.getByLabel('Sửa nội dung phần tử trên canvas');
  await inlineInput.fill('Khảo sát $y = x^3 - 3x$');
  await inlineInput.blur();
  await expect(titleEl.getByRole('math')).toHaveCount(1);

  // Tải tệp ảnh hỏng lên slide -> báo lỗi rõ và không làm hỏng slide
  const props = page.getByRole('complementary', { name: 'Thuộc tính' });
  await props.getByLabel('Tải ảnh lên slide').setInputFiles({
    name: 'anh-hong.png',
    mimeType: 'image/png',
    buffer: Buffer.from('not-a-valid-png-file'),
  });
  await expect(props.getByRole('alert')).toContainText('Tệp ảnh bị hỏng');

  // Chuyển sang Slide 3 (Câu hỏi trắc nghiệm) và vào Trình chiếu để bỏ phiếu (#47)
  await page.getByRole('region', { name: 'Dải slide' }).getByRole('button', { name: 'Slide 3' }).click();
  await page.getByRole('button', { name: 'Trình chiếu' }).click();
  const presenter = page.getByRole('region', { name: 'Màn trình chiếu' });
  await expect(presenter.getByTestId('wb-quiz-total')).toHaveText('0 phiếu');

  await presenter.getByRole('button', { name: 'Tăng phiếu B' }).click();
  await presenter.getByRole('button', { name: 'Tăng phiếu B' }).click();
  await presenter.getByRole('button', { name: 'Tăng phiếu A' }).click();
  await expect(presenter.getByTestId('wb-quiz-count-B')).toHaveText('2');
  await expect(presenter.getByTestId('wb-quiz-total')).toHaveText('3 phiếu');

  await presenter.getByRole('button', { name: 'Hiện đáp án' }).click();
  await expect(presenter.locator('[data-quiz-option="B"]')).toHaveClass(/is-correct/);
  await expect(presenter.getByTestId('wb-quiz-why-B')).toContainText('Đổi dấu từ + sang -');

  await page.keyboard.press('Escape');
  await expect(presenter).toBeHidden();

  // Sửa câu hỏi trắc nghiệm trên Slide 3 -> số phiếu cũ được xóa về 0
  await canvas.locator('[data-element-id="e3-quiz"]').click();
  await props.getByRole('textbox', { name: 'Câu hỏi trắc nghiệm' }).fill('Câu hỏi trắc nghiệm mới sau khi sửa?');
  await props.getByRole('button', { name: 'Lưu nội dung phần tử' }).click();

  await page.getByRole('button', { name: 'Trình chiếu' }).click();
  await expect(presenter.getByTestId('wb-quiz-total')).toHaveText('0 phiếu');
  await page.keyboard.press('Escape');
  expect(problems).toEqual([]);
});

test('Kiểm tra bài, Xác nhận chuyên môn, nhắc trước khi chiếu, Trợ giảng AI, Kế hoạch bài dạy và Xuất PPTX (#44, #45, #49, #50)', async ({ page }) => {
  const problems = watch(page);
  await openWorkbench(page);
  const file = lessonFileWithSlides();
  // Đặt hình chưa xác nhận v-bbt lên slide s2 của Mục m4 để kiểm tra nhắc trước khi chiếu (#49)
  file.deck.slides[1].item_id = 'm4';
  file.deck.slides[1].elements.push({
    element_id: 'e2-bbt',
    type: 'bbt',
    x: 700,
    y: 140,
    w: 820,
    h: 680,
    reveal: 0,
    parts: 3,
    visual_id: 'v-bbt',
  });
  await importLesson(page, file);

  // 1. Bấm Trình chiếu khi còn hình chưa xác nhận trên slide -> hiện hộp thoại "Trước khi trình chiếu"
  await page.getByRole('button', { name: 'Trình chiếu' }).click();
  const preflight = page.getByRole('dialog', { name: 'Trước khi trình chiếu' });
  await expect(preflight).toBeVisible();
  await expect(preflight).toContainText('Bảng biến thiên');
  await preflight.getByRole('button', { name: 'Quay lại kiểm tra' }).click();

  // 2. Bảng Kiểm tra bài & Xác nhận chuyên môn hiện hình chưa xác nhận và phần tử tràn chữ, cho phép lưu Xác nhận chuyên môn
  const qualityModal = page.getByRole('dialog', { name: 'Kiểm tra bài & Xác nhận chuyên môn' });
  await expect(qualityModal).toBeVisible();
  await expect(qualityModal).toContainText('Hình chưa xác nhận dữ kiện');
  await expect(qualityModal).toContainText('Phần tử tràn chữ (1)');
  await qualityModal.getByLabel('Tôi đã đối chiếu đề, điều kiện, lời giải, nguồn và tiến trình của phiên bản này').check();
  await qualityModal.getByRole('button', { name: 'Lưu Xác nhận chuyên môn' }).click();
  await expect(qualityModal).toBeHidden();
  await expect(page.getByRole('banner').getByText('Đã xác nhận chuyên môn', { exact: true })).toHaveCSS('border-top-style', 'solid');

  // 3. Trợ giảng AI đề xuất sửa chữ cho slide đang chọn; áp dụng làm mất Xác nhận chuyên môn (#45)
  await page.route('**/api/v1/chat/workbench/assistant', route => route.fulfill({
    json: {
      ai_response: 'Đã tinh chỉnh tiêu đề ngắn gọn hơn.',
      slide_id: 's1',
      diffs: [{ element_id: 'e1-title', type: 'title', before: { text: 'Khảo sát hàm số bậc ba' }, after: { text: 'Khảo sát hàm bậc 3' } }],
      patched_slide: {
        ...file.deck.slides[0],
        edited: true,
        elements: [
          { ...file.deck.slides[0].elements[0], text: 'Khảo sát hàm bậc 3' },
          file.deck.slides[0].elements[1],
        ],
      },
    },
  }));
  await page.getByRole('tab', { name: 'Trợ giảng AI' }).click();
  const rightPane = page.getByRole('complementary', { name: 'Thuộc tính' });
  await rightPane.getByLabel('Yêu cầu cho slide đang chọn').fill('Rút gọn tiêu đề');
  await rightPane.getByRole('button', { name: 'Gửi yêu cầu' }).click();
  await expect(rightPane.getByTestId('wb-assistant-proposal')).toContainText('Khảo sát hàm bậc 3');
  await rightPane.getByRole('button', { name: 'Áp dụng' }).click();
  await expect(page.getByTestId('wb-canvas')).toContainText('Khảo sát hàm bậc 3');
  await expect(page.getByRole('banner').getByText('Bản nháp', { exact: true })).toBeVisible();

  // 4. Soạn Kế hoạch bài dạy 5512 từ Dàn ý và đánh dấu lệch Dàn ý khi sửa Mục (#50)
  const steps = {
    step_1_assign: 'Giáo viên chuyển giao nhiệm vụ học tập.',
    step_2_excute: 'Học sinh thực hiện nhiệm vụ.',
    step_3_report: 'Học sinh báo cáo kết quả.',
    step_4_conclusion: 'Giáo viên nhận xét và kết luận.',
  };
  await page.route('**/api/v1/workbench/lesson-plan', route => route.fulfill({
    json: {
      warnings: [],
      plan: {
        lesson_title: 'Khảo sát hàm số bậc ba',
        subject: 'Toán học',
        grade: 12,
        knowledge_goals: ['Nắm sơ đồ khảo sát hàm số'],
        competency_goals: ['Tư duy toán học'],
        skills_goals: ['Vẽ đồ thị'],
        character_goals: ['Chăm chỉ'],
        teaching_equipment: ['SGK Toán 12'],
        activities: [
          { activity_number: 1, time_minutes: 7, goal: 'Hoạt động 1 (Khởi động): Khảo sát hàm số bậc ba', expected_product: 'Trả lời mở đầu', execution: steps },
          { activity_number: 2, time_minutes: 22, goal: 'Hoạt động 2 (Hình thành kiến thức): Sơ đồ khảo sát hàm số', expected_product: 'Bảng biến thiên và đồ thị', execution: steps },
          { activity_number: 3, time_minutes: 11, goal: 'Hoạt động 3 (Luyện tập): Bài tập cực trị', expected_product: 'Lời giải đúng', execution: steps },
          { activity_number: 4, time_minutes: 5, goal: 'Hoạt động 4 (Vận dụng): Tổng kết và nhiệm vụ về nhà', expected_product: 'Ba bước khảo sát', execution: steps },
        ],
      },
    },
  }));
  await page.getByRole('tab', { name: /Kế hoạch bài dạy/ }).click();
  await page.getByRole('button', { name: 'Soạn Kế hoạch bài dạy' }).click();
  await expect(page.getByRole('main')).toContainText('Hoạt động 1 (Khởi động)');

  // Sửa một Mục dàn ý -> Kế hoạch bài dạy hiện nhãn "Lệch Dàn ý"
  await page.getByRole('tab', { name: 'Thuộc tính' }).click();
  await outlineTree(page).getByRole('listitem').first().getByRole('button').first().click();
  await rightPane.getByLabel('Tiêu đề Mục').fill('Khảo sát hàm số bậc ba (đã cập nhật)');
  await rightPane.getByRole('button', { name: 'Lưu Mục' }).click();
  await expect(page.getByTestId('wb-plan-stale-badge')).toHaveText('Lệch Dàn ý');

  // 5. Xuất PPTX từ menu Tệp (#44)
  await page.getByRole('tab', { name: 'Bộ slide' }).click();
  await page.getByRole('button', { name: 'Tệp', exact: true }).click();
  const pptxDownload = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Xuất PPTX' }).click();
  const pptxFile = await pptxDownload;
  expect(pptxFile.suggestedFilename()).toMatch(/\.pptx$/);
  expect(problems).toEqual([]);
});

test('xác nhận và trình chiếu Đồ thị tương tác (miền tô, cực trị, giao điểm, tiệm cận) và Bảng biến thiên 3 bước (#51–#57)', async ({ page }) => {
  const problems = watch(page);
  await openWorkbench(page);
  const file = lessonFileWithSlides();
  // Đặt cả Đồ thị v-graph và Bảng biến thiên v-bbt của Mục m4 lên slide s2
  file.outline.items[3].title = 'Ví dụ 1. Khảo sát $y = x^3 - 3x$';
  file.outline.items[3].visuals = [
    { visual_id: 'v-graph', kind: 'graph', origin: 'ai', status: 'proposed', label: '$y = x^3 - 3x$', data: { expression: 'x^3 - 3*x', x_min: -3, x_max: 3, area: { target: 'ox', a: -1, b: 1 } } },
    { visual_id: 'v-bbt', kind: 'bbt', origin: 'ai', status: 'proposed', label: '$y = x^3 - 3x$', data: { expression: 'x^3 - 3*x' } },
  ];
  file.deck.slides[1] = {
    slide_id: 's2',
    item_id: 'm4',
    layout: 'Chữ trái, hình phải',
    notes: '',
    elements: [
      { element_id: 'e2-title', type: 'title', x: 100, y: 40, w: 1400, h: 80, reveal: 0, parts: 1, text: 'Ví dụ khảo sát và vẽ đồ thị' },
      { element_id: 'e2-graph', type: 'graph', x: 80, y: 140, w: 700, h: 680, reveal: 0, parts: 1, visual_id: 'v-graph' },
      { element_id: 'e2-bbt', type: 'bbt', x: 820, y: 140, w: 700, h: 680, reveal: 1, parts: 3, visual_id: 'v-bbt' },
    ],
  };
  await importLesson(page, file);

  // Chọn Mục 4 và xác nhận dữ kiện cho cả v-graph (kèm miền tô [-1; 1]) và v-bbt
  await treeItem(page, 'Ví dụ 1.').getByRole('button').first().click();
  const cardGraph = page.getByTestId('wb-confirm-v-graph');
  await cardGraph.getByLabel('Dữ kiện khớp đề bài').check();
  await cardGraph.getByRole('button', { name: 'Xác nhận dữ kiện' }).click();
  await expect(cardGraph).toContainText('(đã xác nhận)');

  const cardBbt = page.getByTestId('wb-confirm-v-bbt');
  await expect(cardBbt).toContainText('Hàm bậc ba');
  await cardBbt.getByLabel('Dữ kiện khớp đề bài').check();
  await cardBbt.getByRole('button', { name: 'Xác nhận dữ kiện' }).click();
  await expect(cardBbt).toContainText('(đã xác nhận)');

  // Chọn Slide 2 và vào Trình chiếu
  await page.getByRole('region', { name: 'Dải slide' }).getByRole('button', { name: 'Slide 2' }).click();
  await expect(page.getByTestId('wb-canvas').getByTestId('wb-graph-widget')).toBeVisible();
  await expect(page.getByTestId('wb-canvas').getByTestId('wb-bbt-widget')).toBeVisible();

  await page.getByRole('button', { name: 'Trình chiếu' }).click();
  const presenter = page.getByRole('region', { name: 'Màn trình chiếu' });
  await expect(presenter).toBeVisible();

  // Ở bước 0 trên Slide 2: Đồ thị và miền tô hiện ra, Bảng biến thiên chưa hiện (reveal=1)
  await expect(presenter.getByTestId('wb-graph-curve').first()).toBeVisible();
  await expect(presenter.getByTestId('wb-graph-area').first()).toBeVisible();
  await expect(presenter.getByTestId('wb-bbt-widget')).toHaveCount(0);

  // Bật Cực trị và Giao với trục trên đồ thị; nút Tiệm cận bị vô hiệu với hàm bậc ba (#57)
  await presenter.getByRole('button', { name: 'Cực trị' }).click();
  await expect(presenter.getByTestId('wb-graph-extremum')).toHaveCount(2);
  await expect(presenter.getByTestId('wb-graph-widget')).toContainText('CĐ(−1; 2)');
  await expect(presenter.getByTestId('wb-graph-widget')).toContainText('CT(1; −2)');

  await presenter.getByRole('button', { name: 'Giao với trục' }).click();
  await expect(presenter.getByTestId('wb-graph-intercept').first()).toBeVisible();
  await expect(presenter.getByRole('button', { name: 'Tiệm cận' })).toBeDisabled();

  // Tiến 3 bước tiếp theo: Bảng biến thiên hiện dần dòng x -> dòng y' -> dòng y (#55)
  await page.keyboard.press('ArrowRight');
  await expect(presenter.getByTestId('wb-bbt-row-x')).toBeVisible();
  await expect(presenter.getByTestId('wb-bbt-row-yp')).toHaveCount(0);

  await page.keyboard.press('ArrowRight');
  await expect(presenter.getByTestId('wb-bbt-row-yp')).toBeVisible();
  await expect(presenter.getByTestId('wb-bbt-row-y')).toHaveCount(0);

  await page.keyboard.press('ArrowRight');
  await expect(presenter.getByTestId('wb-bbt-row-y')).toBeVisible();

  await page.keyboard.press('Escape');
  expect(problems).toEqual([]);
});
