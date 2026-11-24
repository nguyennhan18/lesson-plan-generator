/**
 * PROTOTYPE, wipe me. Dữ liệu mẫu cho prototype giao diện Prompt → Dàn ý → Bộ slide → Trình chiếu.
 * Đây không phải nội dung đã duyệt. GRAPH_STUBS và BBT_STUBS đứng thay server (ADR 0006):
 * bản thật không bao giờ tính biểu thức trong trình duyệt.
 */
export const STAGE_W = 1600;
export const STAGE_H = 900;
export const LESSON_MINUTES = 45;
export const ACTIVITIES = ['Khởi động', 'Hình thành kiến thức', 'Luyện tập', 'Vận dụng'];

// STUB: thay cho điểm mẫu và điểm đặc biệt do server tính bằng SymPy.
export const GRAPH_STUBS = {
  'x^3 - 3x + 1': {
    fn: (x) => x ** 3 - 3 * x + 1,
    extrema: [
      { x: -1, y: 3, label: 'CĐ' },
      { x: 1, y: -1, label: 'CT' }
    ],
    intercepts: [
      { x: 0, y: 1 },
      { x: -1.8794, y: 0 },
      { x: 0.3473, y: 0 },
      { x: 1.5321, y: 0 }
    ],
    asymptotes: null
  },
  '-x^3 + 3x^2 - 4': {
    fn: (x) => -(x ** 3) + 3 * x ** 2 - 4,
    extrema: [
      { x: 0, y: -4, label: 'CT' },
      { x: 2, y: 0, label: 'CĐ' }
    ],
    intercepts: [
      { x: 0, y: -4 },
      { x: -1, y: 0 },
      { x: 2, y: 0 }
    ],
    asymptotes: null
  }
};

// STUB: thay cho bảng biến thiên do server tính từ biểu thức đã xác nhận.
export const BBT_STUBS = {
  'x^3 - 3x + 1': {
    family: 'hàm bậc ba',
    xs: ['−∞', '−1', '1', '+∞'],
    signs: ['+', '0', '−', '0', '+'],
    values: [
      { v: '−∞', at: 'low' },
      { v: '3', at: 'high' },
      { v: '−1', at: 'low' },
      { v: '+∞', at: 'high' }
    ]
  }
};

const KHAO_SAT = {
  key: 'khao-sat',
  title: 'Khảo sát sự biến thiên và vẽ đồ thị hàm số bậc ba',
  sgk: 'Toán 12, Chương I, Bài 4',
  prompt: 'Tiết khảo sát hàm số bậc ba cho lớp 12A3, lấy ví dụ y = x³ − 3x + 1, có một câu trắc nghiệm củng cố.',
  items: [
    {
      id: 'm1', activity: 'Khởi động', kind: 'Mở đầu',
      title: 'Khảo sát sự biến thiên và vẽ đồ thị hàm số bậc ba',
      points: ['Toán 12, Chương I, Bài 4'], slideCount: 1, minutes: 2, visuals: []
    },
    {
      id: 'm2', activity: 'Khởi động', kind: 'Tình huống khởi động',
      title: 'Hai bạn vẽ cùng một đồ thị',
      points: [
        'An chấm vài điểm rồi nối lại, Bình xét dấu đạo hàm trước khi vẽ.',
        'Đồ thị của bạn nào đáng tin hơn, vì sao?'
      ],
      slideCount: 1, minutes: 5, visuals: []
    },
    {
      id: 'm3', activity: 'Hình thành kiến thức', kind: 'Kiến thức trọng tâm',
      title: 'Sơ đồ khảo sát hàm số',
      points: ['Tìm tập xác định', 'Xét sự biến thiên: đạo hàm, cực trị, giới hạn, bảng biến thiên', 'Vẽ đồ thị'],
      slideCount: 2, minutes: 10, visuals: []
    },
    {
      id: 'm4', activity: 'Hình thành kiến thức', kind: 'Ví dụ',
      title: 'Ví dụ 1. Khảo sát và vẽ đồ thị hàm số $y = x^3 - 3x + 1$',
      points: ['Tập xác định và đạo hàm', 'Cực trị, giới hạn và bảng biến thiên', 'Vẽ đồ thị, chỉ ra tâm đối xứng'],
      slideCount: 3, minutes: 12,
      visuals: [
        { id: 'v-bbt', kind: 'bbt', origin: 'ai', label: '$y = x^3 - 3x + 1$', data: { expression: 'x^3 - 3x + 1' } },
        { id: 'v-graph', kind: 'graph', origin: 'ai', label: '$y = x^3 - 3x + 1$', data: { expression: 'x^3 - 3x + 1', xMin: -3, xMax: 3, yMin: -4, yMax: 5 } }
      ]
    },
    {
      id: 'm5', activity: 'Luyện tập', kind: 'Câu hỏi trắc nghiệm',
      title: 'Hàm số $y = x^3 - 3x + 1$ đạt cực đại tại điểm nào?',
      points: ['Bốn phương án, một phương án đúng: $x = -1$'], slideCount: 1, minutes: 4, visuals: []
    },
    {
      id: 'm6', activity: 'Luyện tập', kind: 'Bài luyện tập',
      title: 'Khảo sát và vẽ đồ thị hàm số $y = -x^3 + 3x^2 - 4$',
      points: ['Mức độ: thông hiểu', 'Đáp số: cực tiểu $(0; -4)$, cực đại $(2; 0)$'],
      slideCount: 1, minutes: 7,
      visuals: [
        { id: 'v-graph2', kind: 'graph', origin: 'ai', label: '$y = -x^3 + 3x^2 - 4$', data: { expression: '-x^3 + 3x^2 - 4', xMin: -2, xMax: 4, yMin: -6, yMax: 2 } }
      ]
    },
    {
      id: 'm7', activity: 'Vận dụng', kind: 'Tổng kết',
      title: 'Tổng kết và nhiệm vụ về nhà',
      points: ['Ba bước khảo sát hàm số', 'Bài về nhà trong SGK'], slideCount: 1, minutes: 5, visuals: []
    }
  ],
  bank: {
    m1: [{
      template: 'Mở đầu', elements: [
        { type: 'title', hero: true, x: 120, y: 280, w: 1360, h: 220, text: 'Khảo sát sự biến thiên và vẽ đồ thị hàm số bậc ba' },
        { type: 'caption', x: 124, y: 540, w: 900, h: 60, text: 'Toán 12, Chương I, Bài 4' }
      ]
    }],
    m2: [{
      template: 'Tình huống', elements: [
        { type: 'title', x: 100, y: 80, w: 1400, h: 100, text: 'Hai bạn vẽ cùng một đồ thị' },
        { type: 'text', x: 100, y: 230, w: 1300, h: 520, reveal: 1, parts: 3, items: [
          'An lập bảng giá trị tại $x = -2, -1, 0, 1, 2$ rồi nối các điểm.',
          'Bình xét dấu đạo hàm trước, rồi mới vẽ.',
          'Đồ thị của bạn nào đáng tin hơn? Vì sao?'
        ] }
      ]
    }],
    m3: [
      {
        template: 'Kiến thức trọng tâm', elements: [
          { type: 'title', x: 100, y: 80, w: 1400, h: 100, text: 'Sơ đồ khảo sát hàm số' },
          { type: 'steps', x: 100, y: 230, w: 1360, h: 560, reveal: 1, parts: 3, items: [
            'Tìm tập xác định của hàm số.',
            "Xét sự biến thiên: tính $y'$, tìm cực trị, giới hạn, lập bảng biến thiên.",
            'Vẽ đồ thị: xác định các điểm đặc biệt rồi nối theo chiều biến thiên.'
          ] }
        ]
      },
      {
        template: 'Kiến thức trọng tâm', elements: [
          { type: 'title', x: 100, y: 80, w: 1400, h: 100, text: 'Xét sự biến thiên' },
          { type: 'text', x: 100, y: 220, w: 1400, h: 400, reveal: 1, parts: 3, items: [
            "Tính $y'$ và tìm các điểm tại đó $y' = 0$ hoặc $y'$ không xác định.",
            'Tìm các giới hạn tại vô cực và tiệm cận (nếu có).',
            'Lập bảng biến thiên, kết luận khoảng đồng biến, nghịch biến và cực trị.'
          ] },
          { type: 'formula', x: 100, y: 660, w: 1400, h: 150, reveal: 4, latex: "f'(x) > 0,\\ \\forall x \\in K \\;\\Rightarrow\\; f \\text{ đồng biến trên } K" }
        ]
      }
    ],
    m4: [
      {
        template: 'Ví dụ: đề và lời giải', elements: [
          { type: 'title', x: 100, y: 80, w: 1400, h: 100, text: 'Ví dụ 1' },
          { type: 'paragraph', x: 100, y: 200, w: 1400, h: 100, text: 'Khảo sát sự biến thiên và vẽ đồ thị của hàm số $y = x^3 - 3x + 1$.' },
          { type: 'steps', x: 100, y: 340, w: 1400, h: 480, reveal: 1, parts: 3, items: [
            'Tập xác định: $D = \\mathbb{R}$.',
            "$y' = 3x^2 - 3$; $\\;y' = 0 \\Leftrightarrow x = -1$ hoặc $x = 1$.",
            '$\\lim\\limits_{x \\to -\\infty} y = -\\infty$, $\\;\\lim\\limits_{x \\to +\\infty} y = +\\infty$.'
          ] }
        ]
      },
      {
        template: 'Hình tương tác ở giữa', elements: [
          { type: 'title', x: 100, y: 70, w: 1400, h: 100, text: 'Bảng biến thiên' },
          { type: 'bbt', x: 200, y: 190, w: 1200, h: 420, visualId: 'v-bbt', reveal: 1, parts: 3 },
          { type: 'paragraph', x: 200, y: 650, w: 1200, h: 170, reveal: 4, text: 'Hàm số đồng biến trên $(-\\infty; -1)$ và $(1; +\\infty)$, nghịch biến trên $(-1; 1)$. Cực đại $y = 3$ tại $x = -1$, cực tiểu $y = -1$ tại $x = 1$.' }
        ]
      },
      {
        template: 'Chữ trái, hình phải', elements: [
          { type: 'title', x: 100, y: 70, w: 560, h: 100, text: 'Đồ thị' },
          { type: 'text', x: 100, y: 220, w: 560, h: 560, reveal: 1, parts: 3, items: [
            'Cắt trục $Oy$ tại $(0; 1)$.',
            'Đi qua $(-1; 3)$ và $(1; -1)$.',
            'Nhận $I(0; 1)$ làm tâm đối xứng.'
          ] },
          { type: 'graph', x: 700, y: 140, w: 820, h: 680, visualId: 'v-graph' }
        ]
      }
    ],
    m5: [{
      template: 'Câu hỏi trắc nghiệm', elements: [
        { type: 'title', x: 100, y: 70, w: 1400, h: 100, text: 'Câu hỏi củng cố' },
        {
          type: 'quiz', x: 100, y: 190, w: 1400, h: 660,
          question: 'Hàm số $y = x^3 - 3x + 1$ đạt cực đại tại điểm nào?',
          options: [
            { label: 'A', text: '$x = 1$', why: "Qua $x = 1$, $y'$ đổi dấu từ âm sang dương nên đó là điểm cực tiểu." },
            { label: 'B', text: '$x = -1$', correct: true, why: "Qua $x = -1$, $y'$ đổi dấu từ dương sang âm." },
            { label: 'C', text: '$x = 3$', why: '$3$ là giá trị cực đại của hàm số, không phải điểm cực đại.' },
            { label: 'D', text: '$x = 0$', why: "$y'(0) = -3 \\ne 0$ nên $x = 0$ không phải điểm cực trị." }
          ]
        }
      ]
    }],
    m6: [{
      template: 'Chữ trái, hình phải', elements: [
        { type: 'title', x: 100, y: 70, w: 700, h: 100, text: 'Bài luyện tập' },
        { type: 'paragraph', x: 100, y: 210, w: 700, h: 200, text: 'Khảo sát và vẽ đồ thị hàm số $y = -x^3 + 3x^2 - 4$.' },
        { type: 'caption', x: 100, y: 430, w: 700, h: 60, text: 'Mức độ: thông hiểu' },
        { type: 'graph', x: 860, y: 150, w: 660, h: 640, visualId: 'v-graph2' }
      ]
    }],
    m7: [{
      template: 'Tổng kết', elements: [
        { type: 'title', x: 100, y: 80, w: 1400, h: 100, text: 'Tổng kết' },
        { type: 'steps', x: 100, y: 230, w: 1400, h: 440, reveal: 1, parts: 3, items: [
          'Tìm tập xác định.',
          'Xét sự biến thiên và lập bảng biến thiên.',
          'Vẽ đồ thị từ các điểm đặc biệt.'
        ] },
        { type: 'caption', x: 100, y: 740, w: 1400, h: 60, reveal: 4, text: 'Về nhà: làm các bài khảo sát hàm số bậc ba cuối Bài 4 trong SGK.' }
      ]
    }]
  }
};

const OXYZ = {
  key: 'oxyz',
  title: 'Phương trình mặt phẳng',
  sgk: 'Toán 12, Phương pháp tọa độ trong không gian',
  prompt: 'Tiết phương trình mặt phẳng, có ví dụ viết phương trình mặt phẳng qua một điểm khi biết vectơ pháp tuyến.',
  items: [
    {
      id: 'm1', activity: 'Khởi động', kind: 'Mở đầu', title: 'Phương trình mặt phẳng',
      points: ['Toán 12, Phương pháp tọa độ trong không gian'], slideCount: 1, minutes: 3, visuals: []
    },
    {
      id: 'm2', activity: 'Hình thành kiến thức', kind: 'Kiến thức trọng tâm',
      title: 'Vectơ pháp tuyến và phương trình tổng quát',
      points: ['Định nghĩa vectơ pháp tuyến', 'Phương trình mặt phẳng qua một điểm, biết vectơ pháp tuyến'],
      slideCount: 1, minutes: 12, visuals: []
    },
    {
      id: 'm3', activity: 'Hình thành kiến thức', kind: 'Ví dụ',
      title: 'Ví dụ 2. Mặt phẳng qua $A(1; 2; 3)$, vectơ pháp tuyến $\\vec n = (2; -1; 2)$',
      points: ['Thay vào phương trình qua một điểm', 'Biểu diễn $A$, $\\vec n$ và $(P)$ trong hệ $Oxyz$'],
      slideCount: 2, minutes: 15,
      visuals: [{
        id: 'v-oxyz', kind: 'oxyz', origin: 'ai', label: '$A$, $\\vec n$ và $(P)$',
        data: {
          objects: [
            { id: 'A', type: 'point', p: [1, 2, 3], svgLabel: 'A(1; 2; 3)', toggleLabel: 'Điểm A', label: 'Điểm $A(1; 2; 3)$' },
            { id: 'n', type: 'vector', from: [1, 2, 3], d: [2, -1, 2], svgLabel: 'n', toggleLabel: 'Vectơ n', label: 'Vectơ $\\vec n = (2; -1; 2)$ đặt tại $A$' },
            { id: 'P', type: 'plane', n: [2, -1, 2], center: [1, 2, 3], size: 2.4, svgLabel: '(P)', toggleLabel: 'Mặt phẳng (P)', label: 'Mặt phẳng $(P): 2x - y + 2z - 6 = 0$' }
          ]
        }
      }]
    },
    {
      id: 'm4', activity: 'Luyện tập', kind: 'Câu hỏi trắc nghiệm',
      title: 'Một vectơ pháp tuyến của mặt phẳng $2x - y + 2z - 6 = 0$',
      points: ['Bốn phương án, một phương án đúng: $(2; -1; 2)$'], slideCount: 1, minutes: 8, visuals: []
    },
    {
      id: 'm5', activity: 'Vận dụng', kind: 'Tổng kết', title: 'Tổng kết',
      points: ['Một điểm và một vectơ pháp tuyến xác định một mặt phẳng'], slideCount: 1, minutes: 7, visuals: []
    }
  ],
  bank: {
    m1: [{
      template: 'Mở đầu', elements: [
        { type: 'title', hero: true, x: 120, y: 300, w: 1360, h: 140, text: 'Phương trình mặt phẳng' },
        { type: 'caption', x: 124, y: 470, w: 1000, h: 60, text: 'Toán 12, Phương pháp tọa độ trong không gian' }
      ]
    }],
    m2: [{
      template: 'Kiến thức trọng tâm', elements: [
        { type: 'title', x: 100, y: 80, w: 1400, h: 100, text: 'Vectơ pháp tuyến' },
        { type: 'paragraph', x: 100, y: 210, w: 1400, h: 140, text: 'Vectơ $\\vec n \\ne \\vec 0$ có giá vuông góc với mặt phẳng $(P)$ được gọi là vectơ pháp tuyến của $(P)$.' },
        { type: 'formula', x: 100, y: 420, w: 1400, h: 150, reveal: 1, latex: 'A(x - x_0) + B(y - y_0) + C(z - z_0) = 0' },
        { type: 'caption', x: 100, y: 600, w: 1400, h: 100, reveal: 1, text: 'Mặt phẳng đi qua $M_0(x_0; y_0; z_0)$ và nhận $\\vec n = (A; B; C)$ làm vectơ pháp tuyến.' }
      ]
    }],
    m3: [
      {
        template: 'Ví dụ: đề và lời giải', elements: [
          { type: 'title', x: 100, y: 80, w: 1400, h: 100, text: 'Ví dụ 2' },
          { type: 'paragraph', x: 100, y: 200, w: 1400, h: 150, text: 'Viết phương trình mặt phẳng $(P)$ đi qua $A(1; 2; 3)$ và nhận $\\vec n = (2; -1; 2)$ làm vectơ pháp tuyến.' },
          { type: 'steps', x: 100, y: 390, w: 1400, h: 360, reveal: 1, parts: 2, items: [
            '$(P): 2(x - 1) - (y - 2) + 2(z - 3) = 0$',
            '$\\Leftrightarrow 2x - y + 2z - 6 = 0$.'
          ] }
        ]
      },
      {
        template: 'Chữ trái, hình phải', elements: [
          { type: 'title', x: 100, y: 70, w: 440, h: 100, text: 'Hình biểu diễn' },
          { type: 'text', x: 100, y: 220, w: 440, h: 420, reveal: 1, parts: 2, items: [
            '$A(1; 2; 3) \\in (P)$',
            '$\\vec n = (2; -1; 2)$ vuông góc với $(P)$'
          ] },
          { type: 'oxyz', x: 560, y: 120, w: 980, h: 740, visualId: 'v-oxyz' }
        ]
      }
    ],
    m4: [{
      template: 'Câu hỏi trắc nghiệm', elements: [
        { type: 'title', x: 100, y: 70, w: 1400, h: 100, text: 'Câu hỏi củng cố' },
        {
          type: 'quiz', x: 100, y: 190, w: 1400, h: 660,
          question: 'Một vectơ pháp tuyến của mặt phẳng $2x - y + 2z - 6 = 0$ là',
          options: [
            { label: 'A', text: '$(2; 1; 2)$', why: 'Hệ số của $y$ là $-1$, không phải $1$.' },
            { label: 'B', text: '$(2; -1; 2)$', correct: true, why: 'Vectơ pháp tuyến là bộ hệ số $(A; B; C)$ của $x, y, z$.' },
            { label: 'C', text: '$(-1; 2; -6)$', why: 'Đây là hệ số của $y$, $z$ và hệ số tự do, lệch một vị trí.' },
            { label: 'D', text: '$(2; -1; -6)$', why: 'Lấy nhầm hệ số tự do $-6$ thay cho hệ số của $z$.' }
          ]
        }
      ]
    }],
    m5: [{
      template: 'Tổng kết', elements: [
        { type: 'title', x: 100, y: 80, w: 1400, h: 100, text: 'Tổng kết' },
        { type: 'steps', x: 100, y: 230, w: 1400, h: 440, reveal: 1, parts: 2, items: [
          'Một điểm và một vectơ pháp tuyến xác định duy nhất một mặt phẳng.',
          'Phương trình tổng quát: $Ax + By + Cz + D = 0$ với $A^2 + B^2 + C^2 > 0$.'
        ] }
      ]
    }]
  }
};

export const TEMPLATES = { 'khao-sat': KHAO_SAT, oxyz: OXYZ };

let seq = 0;
const nextId = (prefix) => `${prefix}-${++seq}`;

export function buildSlidesForItem(templateKey, lessonId, item) {
  const bank = TEMPLATES[templateKey].bank[item.tplId] || [];
  const slides = [];
  for (let i = 0; i < item.slideCount; i += 1) {
    const slideId = nextId(`${lessonId}-s`);
    const tpl = bank[i];
    if (tpl) {
      slides.push({
        id: slideId, itemId: item.id, template: tpl.template,
        elements: tpl.elements.map((el) => ({
          ...el, id: nextId(slideId), visualId: el.visualId ? `${lessonId}-${el.visualId}` : undefined
        }))
      });
    } else {
      // Khi giáo viên tăng số slide của mục, prototype thêm slide nối tiếp thay cho AI.
      const points = item.points.length ? item.points.slice(0, 3) : ['Nội dung bổ sung của mục này'];
      slides.push({
        id: slideId, itemId: item.id, template: 'Nội dung', elements: [
          { id: nextId(slideId), type: 'title', x: 100, y: 80, w: 1400, h: 110, text: `${item.title} (tiếp)` },
          { id: nextId(slideId), type: 'text', x: 100, y: 240, w: 1300, h: 460, reveal: 1, parts: points.length, items: points }
        ]
      });
    }
  }
  return slides;
}

export function buildLesson(templateKey, { id, prompt, level = 'Trung bình', confirmed = [], withSlides = true, updatedAt = 'Vừa xong' }) {
  const template = TEMPLATES[templateKey];
  const items = template.items.map((item) => ({
    ...item,
    id: `${id}-${item.id}`,
    tplId: item.id,
    points: [...item.points],
    visuals: item.visuals.map((v) => ({
      ...v, id: `${id}-${v.id}`, data: structuredClone(v.data),
      status: confirmed.includes(v.id) ? 'confirmed' : 'proposed'
    }))
  }));
  return {
    id, templateKey, title: template.title, sgk: template.sgk, level,
    prompt: prompt || template.prompt, updatedAt, approved: false,
    items, slides: withSlides ? items.flatMap((item) => buildSlidesForItem(templateKey, id, item)) : [],
    generating: null, queue: []
  };
}

export function detectTemplate(prompt) {
  return /mặt phẳng|oxyz|pháp tuyến/i.test(prompt) ? 'oxyz' : 'khao-sat';
}

export function detectSgk(prompt) {
  const text = prompt.toLowerCase();
  if (text.trim().length < 6) return null;
  if (/mặt phẳng|oxyz|pháp tuyến/.test(text)) return 'Toán 12, Phương pháp tọa độ trong không gian, Phương trình mặt phẳng';
  if (/khảo sát|bậc ba|đồ thị|cực trị/.test(text)) return 'Toán 12, Chương I, Bài 4. Khảo sát sự biến thiên và vẽ đồ thị của hàm số';
  return null;
}
