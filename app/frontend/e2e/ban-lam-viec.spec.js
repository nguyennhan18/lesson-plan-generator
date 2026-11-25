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
  await page.getByRole('switch', { name: 'Bàn làm việc' }).check();
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
  await expect(page.getByRole('switch', { name: 'Bàn làm việc' })).toBeChecked();
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
  await importLesson(page, { schema_version: 2, project_id: 'du-an-cu', deck: { slides: [] } });
  await expect(page.getByRole('alert')).toContainText('Phiên bản chưa hỗ trợ: tệp là dự án bản 2 của giao diện cũ.');
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

test('giao diện cũ vẫn là mặc định và không mở Bài giảng bản 3 mà báo phiên bản chưa hỗ trợ', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('switch', { name: 'Bàn làm việc' })).not.toBeChecked();
  await page.getByText('Phục hồi JSON', { exact: false }).locator('input').setInputFiles({ name: 'ban-3.json', mimeType: 'application/json', buffer: Buffer.from(JSON.stringify(lessonFile())) });
  await expect(page.getByRole('alert')).toContainText('Phiên bản chưa hỗ trợ: đây là Bài giảng bản 3, chỉ mở được trong Bàn làm việc.');

  await page.getByRole('switch', { name: 'Bàn làm việc' }).check();
  await importLesson(page, lessonFile());
  await expect(outlineTree(page)).toBeVisible();
  await page.getByRole('switch', { name: 'Bàn làm việc' }).uncheck();
  await page.reload();
  await page.getByLabel('Chọn dự án').selectOption('e2e-bai-giang-ban-3');
  await expect(page.getByRole('alert')).toContainText('Phiên bản chưa hỗ trợ: đây là Bài giảng bản 3');
  await page.getByRole('button', { name: 'Biên Tập Slide', exact: true }).click();
  await expect(page.getByLabel('Tên bài giảng')).toBeVisible();
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
  const toggle = await page.getByRole('switch', { name: 'Bàn làm việc' }).boundingBox();
  expect(toggle.x + toggle.width).toBeLessThanOrEqual(1280);

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
