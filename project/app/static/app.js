/**
 * LessonAI-5512 Studio - Frontend Application Logic
 */

// Global State
const state = {
  apiBase: window.location.origin.startsWith('http') ? window.location.origin : 'http://localhost:8000',
  currentPlan: null,
  currentValidation: null,
  currentDeck: null,
  activeTab: 'studio',
  activeJsonTab: 'plan',
  slideViewMode: 'grid', // 'grid' | 'present'
  currentSlideIndex: 0,
  isGenerating: false,
  timerInterval: null,
  timerSeconds: 0,
  history: [],
  testCases: []
};

// Preset Quick Chips
const DEFAULT_PRESETS = [
  { topic: "Cấp số cộng", subject: "Toán học", grade: 11 },
  { topic: "Đạo hàm và ứng dụng", subject: "Toán học", grade: 11 },
  { topic: "Phương trình bậc hai một ẩn", subject: "Toán học", grade: 9 },
  { topic: "Sóng cơ và sự truyền sóng cơ", subject: "Vật lý", grade: 12 },
  { topic: "Khảo sát và vẽ đồ thị hàm số", subject: "Toán học", grade: 12 },
  { topic: "Định luật bảo toàn cơ năng", subject: "Vật lý", grade: 10 }
];

// Rich Demo Sample Data
const DEMO_SAMPLE_PLAN = {
  lesson_title: "Bài 3: Cấp số cộng",
  subject: "Toán học",
  grade: 11,
  knowledge_goals: [
    "Nhận biết được định nghĩa cấp số cộng và công sai $d$.",
    "Nắm vững công thức số hạng tổng quát của cấp số cộng: $u_n = u_1 + (n-1)d$.",
    "Hiểu và áp dụng được công thức tính tổng $n$ số hạng đầu tiên: $S_n = \\frac{n(u_1 + u_n)}{2} = \\frac{n[2u_1 + (n-1)d]}{2}$."
  ],
  competency_goals: [
    "Năng lực tư duy và lập luận toán học: Phát hiện quy luật cộng dồn trong các dãy số thực tiễn.",
    "Năng lực mô hình hóa toán học: Thiết lập bài toán tính tổng số ghế trong rạp hát, bài toán tiền tiết kiệm.",
    "Năng lực giao tiếp toán học: Thảo luận nhóm, trình bày và giải thích lập luận trước tập thể lớp."
  ],
  skills_goals: [
    "Kỹ năng xác định công sai $d$ khi biết các số hạng liên tiếp.",
    "Kỹ năng tìm số hạng bất kỳ và tính tổng $n$ số hạng đầu tiên."
  ],
  character_goals: [
    "Chăm chỉ: Tích cực tham gia các hoạt động tìm tòi, xây dựng kiến thức mới.",
    "Trách nhiệm: Hợp tác nghiêm túc trong hoạt động nhóm, hoàn thành nhiệm vụ được giao."
  ],
  teaching_equipment: [
    "Giáo viên: Kế hoạch bài dạy, bài giảng điện tử PowerPoint trình chiếu, phiếu học tập số 1 & 2.",
    "Học sinh: Sách giáo khoa Toán 11, vở ghi chép, máy tính cầm tay (Casio FX-580VNX/880BTG)."
  ],
  activities: [
    {
      activity_number: 1,
      time_minutes: 7,
      goal: "Tạo hứng thú và gợi mở tình huống dãy số tăng đều qua bài toán xếp tầng gạch xây dựng.",
      expected_product: "Học sinh nêu được nhận xét: Số viên gạch ở mỗi tầng đều hơn tầng liền trước đúng 2 viên.",
      execution: {
        step_1_assign: "GV chiếu hình ảnh tháp gạch: Tầng 1 có 3 viên, tầng 2 có 5 viên, tầng 3 có 7 viên... Yêu cầu HS nhận xét quy luật.",
        step_2_excute: "HS quan sát hình ảnh, thảo luận cặp đôi trong 2 phút để tìm quy luật biến thiên của số viên gạch theo từng tầng.",
        step_3_report: "Đại diện 2 cặp HS xung phong phát biểu. Các nhóm khác lắng nghe, nhận xét và bổ sung ý kiến.",
        step_4_conclusion: "GV chuẩn hóa nhận định: Dãy số có tính chất mỗi số hạng sau bằng số hạng trước cộng thêm một hằng số được gọi là Cấp số cộng."
      }
    },
    {
      activity_number: 2,
      time_minutes: 20,
      goal: "Xây dựng định nghĩa chính xác về cấp số cộng, công thức số hạng tổng quát và tổng $n$ số hạng đầu tiên.",
      expected_product: "Phiếu học tập số 1 hoàn chỉnh với các công thức: $u_{n+1} = u_n + d$, $u_n = u_1 + (n-1)d$ và $S_n$.",
      execution: {
        step_1_assign: "GV phát Phiếu học tập số 1, yêu cầu các nhóm 4 học sinh giải quyết 3 câu hỏi dẫn dắt hình thành công thức.",
        step_2_excute: "Các nhóm thảo luận tích cực, suy luận công thức tổng quát dựa trên phương pháp quy nạp toán học.",
        step_3_report: "Đại diện Nhóm 1 và Nhóm 3 lên bảng trình bày kết quả. Nhóm 2 phản biện về điều kiện của công sai $d$.",
        step_4_conclusion: "GV chốt kiến thức trọng tâm, ghi bảng định nghĩa, công thức $u_n$ và công thức tổng $S_n$."
      }
    },
    {
      activity_number: 3,
      time_minutes: 12,
      goal: "Rèn luyện kỹ năng tìm công sai, tìm số hạng thứ $n$ và tính tổng $n$ số hạng đầu tiên qua các bài toán cụ thể.",
      expected_product: "Bài giải chính xác trong vở bài tập của học sinh cho 2 ví dụ luyện tập mức độ thông hiểu.",
      execution: {
        step_1_assign: "GV giao 2 bài toán luyện tập: Cho $(u_n)$ có $u_1 = 3, d = 4$. Tính $u_{15}$ và tính $S_{20}$.",
        step_2_excute: "Học sinh làm bài cá nhân vào vở trong 5 phút. GV đi quan sát và hỗ trợ các bạn còn lúng túng.",
        step_3_report: "Gọi 2 học sinh lên bảng giải chi tiết. Cả lớp cùng chấm chéo bài của bạn bên cạnh.",
        step_4_conclusion: "GV nhận xét bài làm trên bảng, lưu ý các lỗi sai thường gặp khi bấm máy tính hoặc nhầm dấu âm của $d$."
      }
    },
    {
      activity_number: 4,
      time_minutes: 6,
      goal: "Vận dụng cấp số cộng để giải quyết bài toán thực tế: Tính tổng số ghế ngồi trong một khán đài nhà hát vòng cung.",
      expected_product: "Bản mô hình toán học giải quyết bài toán rạp hát gồm 25 hàng ghế với đáp số chính xác.",
      execution: {
        step_1_assign: "GV giao bài toán thực tế khán đài nhà hát: Hàng đầu có 20 ghế, mỗi hàng sau nhiều hơn hàng trước 4 ghế. Tính tổng số ghế của 25 hàng.",
        step_2_excute: "Học sinh trao đổi nhanh theo bàn, xác định các đại lượng $u_1 = 20, d = 4, n = 25$ và áp dụng công thức $S_{25}$.",
        step_3_report: "Một học sinh đứng tại chỗ trình bày các bước giải quyết mô hình toán học.",
        step_4_conclusion: "GV tổng kết ứng dụng rộng rãi của cấp số cộng trong đời sống và giao bài tập về nhà trong SGK."
      }
    }
  ]
};

const DEMO_SAMPLE_DECK = {
  presentation_title: "Bài 3: Cấp số cộng",
  subject: "Toán học",
  grade: 11,
  theme: "math_academic",
  slides: [
    {
      slide_index: 1,
      type: "TITLE_SLIDE",
      layout: "TITLE_ONLY",
      title: "CẤP SỐ CỘNG",
      subtitle: "Chương II: Dãy số - Cấp số cộng và cấp số nhân | Toán học 11",
      bullet_points: [
        "Giáo viên giảng dạy: Tổ Toán học",
        "Bộ sách: Kết nối tri thức với cuộc sống"
      ],
      main_definition_latex: null,
      teacher_note: "Chào mừng các em học sinh đến với bài học Cấp số cộng. Nhắc nhở cả lớp chuẩn bị SGK và máy tính cầm tay."
    },
    {
      slide_index: 2,
      type: "WARM_UP_SLIDE",
      layout: "SINGLE_COLUMN",
      title: "KHỞI ĐỘNG: BÀI TOÁN THÁP GẠCH",
      subtitle: "Quan sát và phát hiện quy luật dãy số",
      bullet_points: [
        "Tầng 1 (đỉnh): Có 3 viên gạch",
        "Tầng 2: Có 5 viên gạch (+2)",
        "Tầng 3: Có 7 viên gạch (+2)",
        "Tầng 4: Có 9 viên gạch (+2)",
        "❓ Câu hỏi: Em có nhận xét gì về số lượng viên gạch ở mỗi tầng tiếp theo?"
      ],
      main_definition_latex: null,
      teacher_note: "Cho học sinh 1 phút quan sát, gọi 1 em nhận xét quy luật cộng thêm 2 viên gạch ở mỗi tầng."
    },
    {
      slide_index: 3,
      type: "CONCEPT_SLIDE",
      layout: "CONCEPT_HIGHLIGHT",
      title: "1. ĐỊNH NGHĨA CẤP SỐ CỘNG",
      subtitle: "Khái niệm và công sai d",
      bullet_points: [
        "Cấp số cộng là một dãy số mà mỗi số hạng (kể từ số hạng thứ hai) đều bằng số hạng đứng ngay trước nó cộng với một số không đổi $d$.",
        "Số $d$ được gọi là **công sai** của cấp số cộng.",
        "Đặc biệt khi $d = 0$, cấp số cộng là một dãy số không đổi."
      ],
      main_definition_latex: "u_{n+1} = u_n + d \\quad (n \\in \\mathbb{N}^*)",
      teacher_note: "Nhấn mạnh điều kiện n thuộc N* và công thức truy hồi u_{n+1} = u_n + d."
    },
    {
      slide_index: 4,
      type: "CONCEPT_SLIDE",
      layout: "TWO_COLUMN",
      title: "2. SỐ HẠNG TỔNG QUÁT",
      subtitle: "Biểu diễn u_n qua u_1 và d",
      bullet_points: [
        "Từ định nghĩa ta có: $u_2 = u_1 + d$, $u_3 = u_2 + d = u_1 + 2d$...",
        "Tổng quát với mọi $n \\ge 2$:",
        "Số hạng thứ $n$ được xác định theo số hạng đầu $u_1$ và công sai $d$."
      ],
      main_definition_latex: "u_n = u_1 + (n-1)d",
      teacher_note: "Hướng dẫn học sinh nhớ mẹo: vị trí thứ n thì chỉ có (n-1) khoảng công sai d."
    },
    {
      slide_index: 5,
      type: "CONCEPT_SLIDE",
      layout: "IMAGE_TEXT",
      title: "3. MINH HỌA HÌNH HỌC DÃY SỐ",
      subtitle: "Đồ thị cấp số cộng trên mặt phẳng tọa độ",
      bullet_points: [
        "Các điểm biểu diễn cấp số cộng $(n, u_n)$ luôn nằm trên một đường thẳng.",
        "Hệ số góc của đường thẳng chính bằng công sai $d$.",
        "Ví dụ với dãy số $u_n = 2n + 1$ (với $u_1 = 3, d = 2$):"
      ],
      chart_spec: {
        kind: "arithmetic_sequence",
        pedagogical_purpose: "Minh họa các điểm của cấp số cộng thẳng hàng như hàm số bậc nhất y = ax + b",
        expression: "2*x + 1",
        x_min: 1,
        x_max: 10,
        chart_title: "Biểu diễn cấp số cộng u_n = 2n + 1"
      },
      teacher_note: "Cho học sinh thấy mối liên hệ mật thiết giữa cấp số cộng và hàm số bậc nhất y = ax + b đã học ở lớp 10."
    },
    {
      slide_index: 6,
      type: "EXERCISE_SLIDE",
      layout: "SINGLE_COLUMN",
      title: "4. BÀI TẬP VẬN DỤNG NHANH",
      subtitle: "Củng cố công thức u_n và tính toán",
      bullet_points: [
        "📌 **Bài toán 1**: Cho cấp số cộng $(u_n)$ có $u_1 = -2$ và $d = 3$. Tìm số hạng thứ 10 ($u_{10}$)?",
        "💡 Hướng dẫn: Áp dụng $u_{10} = u_1 + 9d = -2 + 9 \\times 3 = 25$.",
        "📌 **Bài toán 2**: Dãy số $5, 9, 13, 17, \\dots$ có công sai $d$ bằng bao nhiêu? Số 101 là số hạng thứ mấy?"
      ],
      main_definition_latex: null,
      teacher_note: "Yêu cầu học sinh làm nháp nhanh trong 2 phút, bấm máy tính kiểm tra lại kết quả."
    },
    {
      slide_index: 7,
      type: "SUMMARY_SLIDE",
      layout: "TITLE_ONLY",
      title: "TỔNG KẾT BÀI HỌC",
      subtitle: "Ghi nhớ kiến thức trọng tâm & Bài tập về nhà",
      bullet_points: [
        "1. Định nghĩa công thức truy hồi: $u_{n+1} = u_n + d$",
        "2. Công thức số hạng tổng quát: $u_n = u_1 + (n-1)d$",
        "3. Công thức tính tổng $n$ số hạng: $S_n = \\frac{n(u_1 + u_n)}{2}$",
        "📝 Bài tập về nhà: Làm bài tập 2.8 đến 2.12 trong SGK trang 51."
      ],
      teacher_note: "Tổng kết lại các điểm mấu chốt, nhắc học sinh chuẩn bị bài mới 'Cấp số nhân'."
    }
  ]
};

// Initialization on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
  initApiBase();
  initTabs();
  initPresets();
  initEventListeners();
  loadHistoryFromStorage();
  checkServerHealth();
});

// Setup API Base URL
function initApiBase() {
  const savedApi = localStorage.getItem('lessonai_api_base');
  if (savedApi) {
    state.apiBase = savedApi;
  }
  const apiInput = document.getElementById('apiBaseInput');
  if (apiInput) {
    apiInput.value = state.apiBase;
  }
}

// Tab Switching
function initTabs() {
  const tabButtons = document.querySelectorAll('.tab-btn');
  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetTab = btn.getAttribute('data-tab');
      switchTab(targetTab);
    });
  });
}

function switchTab(tabId) {
  state.activeTab = tabId;
  
  // Update buttons
  document.querySelectorAll('.tab-btn').forEach(btn => {
    if (btn.getAttribute('data-tab') === tabId) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  // Update panels
  document.querySelectorAll('.tab-panel').forEach(panel => {
    if (panel.id === `tab-${tabId}`) {
      panel.classList.add('active');
    } else {
      panel.classList.remove('active');
    }
  });

  // Render specific tab content if needed
  if (tabId === 'plan' && state.currentPlan) {
    renderLessonPlan(state.currentPlan, state.currentValidation);
  } else if (tabId === 'slide' && state.currentDeck) {
    renderSlideDeck(state.currentDeck);
  } else if (tabId === 'json') {
    updateJsonViewer();
  }
}

// Preset Chips
function initPresets() {
  const container = document.getElementById('presetChipsList');
  if (!container) return;

  container.innerHTML = '';
  DEFAULT_PRESETS.forEach(preset => {
    const chip = document.createElement('button');
    chip.type = 'button';
    chip.className = 'preset-chip';
    chip.innerHTML = `<span>📚</span> ${preset.topic} (Lớp ${preset.grade})`;
    chip.addEventListener('click', () => {
      document.getElementById('inputTopic').value = preset.topic;
      document.getElementById('inputSubject').value = preset.subject;
      document.getElementById('inputGrade').value = preset.grade;
      showToast(`Đã nạp bài mẫu: ${preset.topic}`, 'info');
    });
    container.appendChild(chip);
  });
}

// Setup Event Listeners
function initEventListeners() {
  // Action Buttons
  const btnGenPlan = document.getElementById('btnGenPlan');
  if (btnGenPlan) btnGenPlan.addEventListener('click', () => generatePlanAction());

  const btnGenSlide = document.getElementById('btnGenSlide');
  if (btnGenSlide) btnGenSlide.addEventListener('click', () => generateSlideAction());

  const btnGenAll = document.getElementById('btnGenAll');
  if (btnGenAll) btnGenAll.addEventListener('click', () => generateAllAction());

  const btnLoadDemo = document.getElementById('btnLoadDemo');
  if (btnLoadDemo) btnLoadDemo.addEventListener('click', () => loadDemoSampleAction());

  // Export Buttons
  const btnExportDocx = document.getElementById('btnExportDocx');
  if (btnExportDocx) btnExportDocx.addEventListener('click', () => exportDocxAction());

  const btnExportPptx = document.getElementById('btnExportPptx');
  if (btnExportPptx) btnExportPptx.addEventListener('click', () => exportPptxAction());

  const btnGenSlideFromPlan = document.getElementById('btnGenSlideFromPlan');
  if (btnGenSlideFromPlan) btnGenSlideFromPlan.addEventListener('click', () => generateSlideFromCurrentPlan());

  // Slide Toolbar Controls
  const btnSlideGrid = document.getElementById('btnSlideGrid');
  const btnSlidePresent = document.getElementById('btnSlidePresent');
  if (btnSlideGrid && btnSlidePresent) {
    btnSlideGrid.addEventListener('click', () => setSlideViewMode('grid'));
    btnSlidePresent.addEventListener('click', () => setSlideViewMode('present'));
  }

  const btnPrevSlide = document.getElementById('btnPrevSlide');
  const btnNextSlide = document.getElementById('btnNextSlide');
  if (btnPrevSlide && btnNextSlide) {
    btnPrevSlide.addEventListener('click', () => prevSlide());
    btnNextSlide.addEventListener('click', () => nextSlide());
  }

  // Settings Modal
  const btnOpenSettings = document.getElementById('btnOpenSettings');
  const modalSettings = document.getElementById('modalSettings');
  const btnCloseSettings = document.getElementById('btnCloseSettings');
  const btnSaveSettings = document.getElementById('btnSaveSettings');

  if (btnOpenSettings && modalSettings) {
    btnOpenSettings.addEventListener('click', () => modalSettings.classList.add('active'));
    if (btnCloseSettings) btnCloseSettings.addEventListener('click', () => modalSettings.classList.remove('active'));
    if (btnSaveSettings) {
      btnSaveSettings.addEventListener('click', () => {
        const val = document.getElementById('apiBaseInput').value.trim();
        if (val) {
          state.apiBase = val.replace(/\/+$/, '');
          localStorage.setItem('lessonai_api_base', state.apiBase);
          modalSettings.classList.remove('active');
          checkServerHealth();
          showToast(`Đã lưu URL API: ${state.apiBase}`, 'success');
        }
      });
    }
  }

  // JSON Tab Subnav
  const btnJsonPlan = document.getElementById('btnJsonPlan');
  const btnJsonDeck = document.getElementById('btnJsonDeck');
  if (btnJsonPlan && btnJsonDeck) {
    btnJsonPlan.addEventListener('click', () => {
      state.activeJsonTab = 'plan';
      btnJsonPlan.classList.add('active');
      btnJsonDeck.classList.remove('active');
      updateJsonViewer();
    });
    btnJsonDeck.addEventListener('click', () => {
      state.activeJsonTab = 'deck';
      btnJsonDeck.classList.add('active');
      btnJsonPlan.classList.remove('active');
      updateJsonViewer();
    });
  }

  const btnCopyJson = document.getElementById('btnCopyJson');
  if (btnCopyJson) {
    btnCopyJson.addEventListener('click', () => {
      const textarea = document.getElementById('jsonEditor');
      if (textarea && textarea.value) {
        navigator.clipboard.writeText(textarea.value).then(() => {
          showToast("Đã sao chép JSON vào Clipboard!", "success");
        }).catch(() => {
          showToast("Không thể sao chép tự động", "warning");
        });
      }
    });
  }

  const btnExportCustomDocx = document.getElementById('btnExportCustomDocx');
  if (btnExportCustomDocx) {
    btnExportCustomDocx.addEventListener('click', () => exportFromCustomJson('docx'));
  }

  const btnExportCustomPptx = document.getElementById('btnExportCustomPptx');
  if (btnExportCustomPptx) {
    btnExportCustomPptx.addEventListener('click', () => exportFromCustomJson('pptx'));
  }
}

// Server Health Checker
async function checkServerHealth() {
  const badge = document.getElementById('serverStatusBadge');
  const text = document.getElementById('serverStatusText');
  
  try {
    const res = await fetch(`${state.apiBase}/api/v1/health`, { method: 'GET', signal: AbortSignal.timeout(3000) });
    if (res.ok) {
      const data = await res.json();
      badge.className = 'server-badge online';
      text.textContent = data.has_api_key ? 'Server Online (API Sẵn sàng)' : 'Server Online (Chưa có API Key)';
    } else {
      badge.className = 'server-badge offline';
      text.textContent = 'Server Lỗi (HTTP ' + res.status + ')';
    }
  } catch (err) {
    badge.className = 'server-badge offline';
    text.textContent = 'Mất kết nối Server';
  }
}

// Start Timer
function startTimer(message) {
  state.isGenerating = true;
  state.timerSeconds = 0;
  
  const card = document.getElementById('progressCard');
  const msgEl = document.getElementById('progressMsg');
  const timerEl = document.getElementById('progressTimer');
  
  if (card) card.classList.add('active');
  if (msgEl) msgEl.textContent = message || "Đang xử lý...";
  if (timerEl) timerEl.textContent = "00:00";

  // Disable buttons
  setButtonsState(true);

  if (state.timerInterval) clearInterval(state.timerInterval);
  state.timerInterval = setInterval(() => {
    state.timerSeconds++;
    const mins = String(Math.floor(state.timerSeconds / 60)).padStart(2, '0');
    const secs = String(state.timerSeconds % 60).padStart(2, '0');
    if (timerEl) timerEl.textContent = `${mins}:${secs}`;
  }, 1000);
}

// Stop Timer
function stopTimer() {
  state.isGenerating = false;
  if (state.timerInterval) clearInterval(state.timerInterval);
  
  const card = document.getElementById('progressCard');
  if (card) card.classList.remove('active');
  
  setButtonsState(false);
}

function setButtonsState(disabled) {
  const btnGenPlan = document.getElementById('btnGenPlan');
  const btnGenSlide = document.getElementById('btnGenSlide');
  const btnGenAll = document.getElementById('btnGenAll');
  if (btnGenPlan) btnGenPlan.disabled = disabled;
  if (btnGenSlide) btnGenSlide.disabled = disabled;
  if (btnGenAll) btnGenAll.disabled = disabled;
}

// Form Helpers
function getFormData() {
  const topic = document.getElementById('inputTopic').value.trim();
  const subject = document.getElementById('inputSubject').value.trim();
  const grade = parseInt(document.getElementById('inputGrade').value, 10) || 11;

  if (!topic) {
    showToast("Vui lòng nhập tên bài dạy / chủ đề!", "warning");
    document.getElementById('inputTopic').focus();
    return null;
  }

  return { topic, subject, grade };
}

// API Action: Generate Lesson Plan
async function generatePlanAction() {
  const form = getFormData();
  if (!form) return;

  startTimer(`Đang gọi Gemini AI sinh Kế hoạch bài dạy: "${form.topic}"...`);

  try {
    const res = await fetch(`${state.apiBase}/api/v1/lesson-plan/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form)
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `Lỗi server HTTP ${res.status}`);
    }

    const data = await res.json();
    state.currentPlan = data.plan;
    state.currentValidation = {
      is_valid: data.is_valid,
      errors: data.errors || [],
      warnings: data.warnings || []
    };

    saveToHistory(form.topic, 'plan', state.currentPlan);
    showToast("Đã sinh Giáo án 5512 thành công!", "success");
    renderLessonPlan(state.currentPlan, state.currentValidation);
    updateBadges();
    switchTab('plan');
  } catch (err) {
    showToast(`Lỗi: ${err.message}`, "error");
  } finally {
    stopTimer();
  }
}

// API Action: Generate Slide Deck
async function generateSlideAction() {
  const form = getFormData();
  if (!form) return;

  startTimer(`Đang gọi Gemini AI sinh Slide bài giảng: "${form.topic}"...`);

  try {
    const res = await fetch(`${state.apiBase}/api/v1/slide/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form)
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `Lỗi server HTTP ${res.status}`);
    }

    const deck = await res.json();
    state.currentDeck = deck;
    state.currentSlideIndex = 0;

    saveToHistory(form.topic, 'slide', state.currentDeck);
    showToast(`Đã sinh ${deck.slides?.length || 0} slide bài giảng!`, "success");
    renderSlideDeck(state.currentDeck);
    updateBadges();
    switchTab('slide');
  } catch (err) {
    showToast(`Lỗi: ${err.message}`, "error");
  } finally {
    stopTimer();
  }
}

// API Action: Generate Slide from Current Plan
async function generateSlideFromCurrentPlan() {
  if (!state.currentPlan) {
    showToast("Chưa có Giáo án để đồng bộ Slide!", "warning");
    return;
  }

  const payload = {
    topic: state.currentPlan.lesson_title,
    subject: state.currentPlan.subject,
    grade: state.currentPlan.grade,
    plan: state.currentPlan
  };

  startTimer(`Đang sinh Slide đồng bộ bám sát Giáo án "${payload.topic}"...`);

  try {
    const res = await fetch(`${state.apiBase}/api/v1/slide/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `Lỗi server HTTP ${res.status}`);
    }

    const deck = await res.json();
    state.currentDeck = deck;
    state.currentSlideIndex = 0;

    saveToHistory(payload.topic, 'slide', state.currentDeck);
    showToast(`Đã sinh ${deck.slides?.length || 0} slide đồng bộ từ Giáo án!`, "success");
    renderSlideDeck(state.currentDeck);
    updateBadges();
    switchTab('slide');
  } catch (err) {
    showToast(`Lỗi: ${err.message}`, "error");
  } finally {
    stopTimer();
  }
}

// API Action: Generate All (Synchronized)
async function generateAllAction() {
  const form = getFormData();
  if (!form) return;

  // Step 1: Lesson Plan
  startTimer(`Bước 1/2: Đang sinh Giáo án chuẩn 5512: "${form.topic}"...`);
  try {
    const resPlan = await fetch(`${state.apiBase}/api/v1/lesson-plan/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form)
    });

    if (!resPlan.ok) {
      const err = await resPlan.json().catch(() => ({ detail: resPlan.statusText }));
      throw new Error(err.detail || `Lỗi khi sinh Giáo án: HTTP ${resPlan.status}`);
    }

    const planData = await resPlan.json();
    state.currentPlan = planData.plan;
    state.currentValidation = {
      is_valid: planData.is_valid,
      errors: planData.errors || [],
      warnings: planData.warnings || []
    };

    // Step 2: Slide Deck synchronized with Lesson Plan
    const progressMsg = document.getElementById('progressMsg');
    if (progressMsg) progressMsg.textContent = `Bước 2/2: Đang sinh Slide bài giảng đồng bộ từ Giáo án...`;

    const slidePayload = {
      topic: form.topic,
      subject: form.subject,
      grade: form.grade,
      plan: state.currentPlan
    };

    const resSlide = await fetch(`${state.apiBase}/api/v1/slide/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(slidePayload)
    });

    if (!resSlide.ok) {
      const err = await resSlide.json().catch(() => ({ detail: resSlide.statusText }));
      throw new Error(err.detail || `Lỗi khi sinh Slide: HTTP ${resSlide.status}`);
    }

    const deckData = await resSlide.json();
    state.currentDeck = deckData;
    state.currentSlideIndex = 0;

    saveToHistory(form.topic, 'all', { plan: state.currentPlan, deck: state.currentDeck });
    showToast("Hoàn tất sinh trọn bộ Giáo án & Slide bài giảng!", "success");
    renderLessonPlan(state.currentPlan, state.currentValidation);
    renderSlideDeck(state.currentDeck);
    updateBadges();
    switchTab('plan');
  } catch (err) {
    showToast(`Lỗi: ${err.message}`, "error");
  } finally {
    stopTimer();
  }
}

// Action: Load Demo Sample Data
function loadDemoSampleAction() {
  state.currentPlan = DEMO_SAMPLE_PLAN;
  state.currentValidation = {
    is_valid: true,
    errors: [],
    warnings: []
  };
  state.currentDeck = DEMO_SAMPLE_DECK;
  state.currentSlideIndex = 0;

  // Fill form
  document.getElementById('inputTopic').value = DEMO_SAMPLE_PLAN.lesson_title;
  document.getElementById('inputSubject').value = DEMO_SAMPLE_PLAN.subject;
  document.getElementById('inputGrade').value = DEMO_SAMPLE_PLAN.grade;

  renderLessonPlan(state.currentPlan, state.currentValidation);
  renderSlideDeck(state.currentDeck);
  updateBadges();
  showToast("Đã nạp bộ dữ liệu mẫu (Demo Sample Data)!", "success");
  switchTab('plan');
}

// Action: Export Docx
async function exportDocxAction() {
  if (!state.currentPlan) {
    showToast("Chưa có dữ liệu Giáo án để xuất file Word!", "warning");
    return;
  }

  showToast("Đang chuẩn bị file Word (.docx)...", "info");

  try {
    const res = await fetch(`${state.apiBase}/api/v1/lesson-plan/export-docx`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(state.currentPlan)
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `Lỗi HTTP ${res.status}`);
    }

    const blob = await res.blob();
    const filename = `Giao_An_${(state.currentPlan.lesson_title || 'CV5512').replace(/\s+/g, '_')}.docx`;
    triggerDownload(blob, filename);
    showToast("Đã tải xuống file Word thành công!", "success");
  } catch (err) {
    showToast(`Xuất file Word thất bại: ${err.message}`, "error");
  }
}

// Action: Export PPTX
async function exportPptxAction() {
  if (!state.currentDeck) {
    showToast("Chưa có dữ liệu Slide để xuất file PowerPoint!", "warning");
    return;
  }

  showToast("Đang kết xuất file PowerPoint (.pptx)...", "info");

  try {
    const res = await fetch(`${state.apiBase}/api/v1/lesson-plan/export-slide`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(state.currentDeck)
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `Lỗi HTTP ${res.status}`);
    }

    const blob = await res.blob();
    const filename = `Slide_${(state.currentDeck.presentation_title || 'BaiGiang').replace(/\s+/g, '_')}.pptx`;
    triggerDownload(blob, filename);
    showToast("Đã tải xuống file Slide PPTX thành công!", "success");
  } catch (err) {
    showToast(`Xuất file Slide PPTX thất bại: ${err.message}`, "error");
  }
}

// Action: Export from Custom Edited JSON
async function exportFromCustomJson(type) {
  const textarea = document.getElementById('jsonEditor');
  if (!textarea || !textarea.value.trim()) {
    showToast("Không có nội dung JSON để xuất!", "warning");
    return;
  }

  let parsed;
  try {
    parsed = JSON.parse(textarea.value);
  } catch (err) {
    showToast(`Cú pháp JSON không hợp lệ: ${err.message}`, "error");
    return;
  }

  const endpoint = type === 'docx' 
    ? `${state.apiBase}/api/v1/lesson-plan/export-docx` 
    : `${state.apiBase}/api/v1/lesson-plan/export-slide`;

  showToast(`Đang xuất file ${type.toUpperCase()} từ JSON tùy chỉnh...`, "info");

  try {
    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(parsed)
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `Lỗi HTTP ${res.status}`);
    }

    const blob = await res.blob();
    const filename = `Export_Custom_${Date.now()}.${type}`;
    triggerDownload(blob, filename);
    showToast(`Tải xuống file ${type.toUpperCase()} thành công!`, "success");
  } catch (err) {
    showToast(`Lỗi xuất file: ${err.message}`, "error");
  }
}

// Trigger browser download
function triggerDownload(blob, filename) {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.style.display = 'none';
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  setTimeout(() => {
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  }, 100);
}

// Render Lesson Plan
function renderLessonPlan(plan, val) {
  const container = document.getElementById('planViewContainer');
  const emptyState = document.getElementById('planEmptyState');
  if (!container) return;

  if (!plan) {
    if (emptyState) emptyState.style.display = 'block';
    container.style.display = 'none';
    return;
  }

  if (emptyState) emptyState.style.display = 'none';
  container.style.display = 'block';

  // Validation Banner
  const valContainer = document.getElementById('planValidationBanner');
  if (valContainer) {
    if (val && val.is_valid) {
      valContainer.className = 'val-banner valid';
      valContainer.innerHTML = `
        <div class="val-icon">✅</div>
        <div>
          <div class="val-title">Đạt chuẩn Công văn 5512/BGDĐT</div>
          <div style="font-size: 0.85rem;">Giáo án đáp ứng đầy đủ mục tiêu, thiết bị dạy học và cấu trúc 4 hoạt động chuẩn.</div>
        </div>
      `;
    } else if (val) {
      valContainer.className = 'val-banner invalid';
      const errorsList = (val.errors || []).map(e => `<li>${escapeHtml(e)}</li>`).join('');
      valContainer.innerHTML = `
        <div class="val-icon">⚠️</div>
        <div>
          <div class="val-title">Chưa đạt đủ tiêu chí Công văn 5512 (${val.errors.length} lỗi)</div>
          <ul class="val-list">${errorsList}</ul>
        </div>
      `;
    } else {
      valContainer.innerHTML = '';
    }
  }

  // Document Content
  document.getElementById('docTitle').textContent = plan.lesson_title || 'KẾ HOẠCH BÀI DẠY';
  document.getElementById('docSubject').textContent = `Môn học: ${plan.subject || 'Toán học'}`;
  document.getElementById('docGrade').textContent = `Khối lớp: ${plan.grade || 11}`;

  // Goals
  renderList('docKnowledgeGoals', plan.knowledge_goals);
  renderList('docCompetencyGoals', plan.competency_goals);
  renderList('docCharacterGoals', plan.character_goals);
  renderList('docSkillsGoals', plan.skills_goals);
  renderList('docEquipment', plan.teaching_equipment);

  // Activities (4 Activities)
  const actContainer = document.getElementById('docActivitiesContainer');
  if (actContainer) {
    actContainer.innerHTML = '';
    (plan.activities || []).forEach(act => {
      const actEl = document.createElement('div');
      actEl.className = 'activity-box';
      
      const actNames = [
        "Hoạt động 1: Mở đầu / Khởi động",
        "Hoạt động 2: Hình thành kiến thức mới",
        "Hoạt động 3: Luyện tập",
        "Hoạt động 4: Vận dụng"
      ];
      const defaultName = actNames[act.activity_number - 1] || `Hoạt động ${act.activity_number}`;

      actEl.innerHTML = `
        <div class="activity-header">
          <div class="activity-title">${defaultName}</div>
          <span class="activity-time">⏱️ ${act.time_minutes || 10} phút</span>
        </div>
        <div class="activity-grid">
          <div>
            <strong>🎯 Mục tiêu hoạt động:</strong>
            <p style="margin-top: 0.25rem; color: #334155;">${renderMathString(act.goal || '')}</p>
          </div>
          <div>
            <strong>📦 Sản phẩm dự kiến của HS:</strong>
            <p style="margin-top: 0.25rem; color: #334155;">${renderMathString(act.expected_product || '')}</p>
          </div>
        </div>
        <div class="steps-container">
          <div class="step-card">
            <div class="step-title"><span>1️⃣</span> Bước 1: Chuyển giao nhiệm vụ (GV giao việc)</div>
            <div class="step-desc">${renderMathString(act.execution?.step_1_assign || '')}</div>
          </div>
          <div class="step-card">
            <div class="step-title"><span>2️⃣</span> Bước 2: Thực hiện nhiệm vụ (HS tiến hành)</div>
            <div class="step-desc">${renderMathString(act.execution?.step_2_excute || '')}</div>
          </div>
          <div class="step-card">
            <div class="step-title"><span>3️⃣</span> Bước 3: Báo cáo & Thảo luận (HS trình bày)</div>
            <div class="step-desc">${renderMathString(act.execution?.step_3_report || '')}</div>
          </div>
          <div class="step-card">
            <div class="step-title"><span>4️⃣</span> Bước 4: Kết luận & Nhận định (GV chốt kiến thức)</div>
            <div class="step-desc">${renderMathString(act.execution?.step_4_conclusion || '')}</div>
          </div>
        </div>
      `;
      actContainer.appendChild(actEl);
    });
  }
}

// Helper to render lists
function renderList(elementId, items) {
  const el = document.getElementById(elementId);
  if (!el) return;
  el.innerHTML = '';
  if (!items || items.length === 0) {
    el.innerHTML = '<li style="color: #94a3b8; font-style: italic;">(Chưa có nội dung)</li>';
    return;
  }
  items.forEach(item => {
    const li = document.createElement('li');
    li.innerHTML = renderMathString(item);
    el.appendChild(li);
  });
}

// Render Slide Deck (Đồng bộ 100% với giao diện file PowerPoint)
function renderSlideDeck(deck, triggerEnrich = true) {
  const gridContainer = document.getElementById('slideGridContainer');
  const emptyState = document.getElementById('slideEmptyState');
  const toolbar = document.getElementById('slideToolbar');
  if (!gridContainer) return;

  if (!deck || !deck.slides || deck.slides.length === 0) {
    if (emptyState) emptyState.style.display = 'block';
    gridContainer.style.display = 'none';
    if (toolbar) toolbar.style.display = 'none';
    return;
  }

  if (emptyState) emptyState.style.display = 'none';
  if (toolbar) toolbar.style.display = 'flex';

  // Toolbar Info
  document.getElementById('slideDeckTitle').textContent = deck.presentation_title || 'Slide bài giảng';
  document.getElementById('slideDeckCount').textContent = `${deck.slides.length} slide`;
  document.getElementById('slideDeckTheme').textContent = `Theme: ${deck.theme || 'math_academic'}`;

  // Tự động kiểm tra và làm giàu ảnh đồ thị từ backend nếu chưa có
  if (triggerEnrich) {
    ensureDeckEnriched(deck);
  }

  // Render Grid
  gridContainer.innerHTML = '';
  deck.slides.forEach((s, idx) => {
    const card = document.createElement('div');
    card.className = 'slide-card';
    
    const isTitleSlide = s.type === 'TITLE_SLIDE';
    const hasChart = Boolean(s.chart_image_base64 || (s.chart_spec && s.chart_spec.kind !== 'none' && s.chart_spec.expression));

    // 1. Header Bar
    const headerHtml = `
      <div class="slide-card-header">
        <span class="slide-number">Slide #${s.slide_index || (idx + 1)}</span>
        <span class="slide-type-badge">${s.type || 'SLIDE'}</span>
      </div>
    `;

    // 2. Body Nội dung
    let bodyHtml = '';

    if (isTitleSlide) {
      // Bố cục Slide Bìa (Trang nhã chuẩn Sư phạm)
      bodyHtml = `
        <div class="slide-body" style="padding: 0;">
          <div class="slide-hero-title-box">
            <span class="slide-hero-subject-tag">MÔN ${deck.subject || 'TOÁN HỌC'} - LỚP ${deck.grade || 11}</span>
            <h2 class="slide-hero-main-title">${renderMathString(s.title || '')}</h2>
            ${s.subtitle ? `<div class="slide-hero-subtitle">${renderMathString(s.subtitle)}</div>` : ''}
            <div style="margin-top: 1rem; font-size: 0.8rem; color: #64748b; font-weight: 600;">
              KẾ HOẠCH BÀI DẠY THEO CÔNG VĂN 5512
            </div>
          </div>
        </div>
      `;
    } else {
      // Formula markup
      let formulaHtml = '';
      if (s.formula_image_base64) {
        formulaHtml = `
          <div class="formula-box">
            <img src="${s.formula_image_base64}" class="formula-png-img" alt="Công thức trọng tâm">
          </div>
        `;
      } else if (s.main_definition_latex) {
        formulaHtml = `
          <div class="formula-box">
            ${renderMathString(`$$${s.main_definition_latex}$$`)}
          </div>
        `;
      }

      // Bullets
      const bulletsHtml = (s.bullet_points || []).map(b => `<li>${renderMathString(b)}</li>`).join('');

      if (hasChart) {
        // BỐ CỤC 2 CỘT: Cột Trái (chữ + công thức), Cột Phải (Ảnh Đồ thị Matplotlib thực tế)
        const plotImgHtml = s.chart_image_base64 
          ? `<img src="${s.chart_image_base64}" class="slide-plot-img" alt="Đồ thị hàm số">`
          : `<div style="padding: 1.5rem; text-align: center; color: #0284c7; font-size: 0.82rem;">📊 Đang tải đồ thị...</div>`;

        bodyHtml = `
          <div class="slide-body">
            <h3 class="slide-title">${renderMathString(s.title || '')}</h3>
            ${s.subtitle ? `<div class="slide-subtitle">${renderMathString(s.subtitle)}</div>` : ''}
            
            <div class="slide-content-split">
              <div class="slide-content-left">
                <ul class="slide-bullets">${bulletsHtml}</ul>
                ${formulaHtml}
              </div>

              <div class="slide-plot-container">
                ${plotImgHtml}
                <span class="slide-plot-badge">📊 Đồ thị Matplotlib Native</span>
                ${s.chart_spec?.chart_title ? `<div style="font-size: 0.74rem; color: #475569; margin-top: 0.2rem;">${escapeHtml(s.chart_spec.chart_title)}</div>` : ''}
              </div>
            </div>
          </div>
        `;
      } else {
        // BỐ CỤC 1 CỘT (Toàn chiều rộng)
        bodyHtml = `
          <div class="slide-body">
            <h3 class="slide-title">${renderMathString(s.title || '')}</h3>
            ${s.subtitle ? `<div class="slide-subtitle">${renderMathString(s.subtitle)}</div>` : ''}
            <ul class="slide-bullets">${bulletsHtml}</ul>
            ${formulaHtml}
          </div>
        `;
      }
    }

    // 3. Speaker Notes (Notes Pane)
    let noteHtml = '';
    if (s.teacher_note) {
      noteHtml = `
        <div class="teacher-note-box">
          <span class="teacher-note-label">🎙️ Speaker Notes:</span>
          <div style="flex: 1;">${renderMathString(s.teacher_note)}</div>
        </div>
      `;
    }

    card.innerHTML = `${headerHtml}${bodyHtml}${noteHtml}`;
    card.addEventListener('click', () => {
      state.currentSlideIndex = idx;
      setSlideViewMode('present');
    });

    gridContainer.appendChild(card);
  });

  // Render current slide in presentation mode
  renderCurrentPresentationSlide();

  // Đảm bảo hiển thị đúng container (Lưới hoặc Trình chiếu)
  setSlideViewMode(state.slideViewMode || 'grid');
}

// Chuyển đổi giữa chế độ xem Lưới (Grid) và Trình chiếu (Present)
function setSlideViewMode(mode) {
  state.slideViewMode = mode;
  const gridContainer = document.getElementById('slideGridContainer');
  const presentContainer = document.getElementById('slidePresentContainer');
  const btnGrid = document.getElementById('btnSlideGrid');
  const btnPresent = document.getElementById('btnSlidePresent');

  if (mode === 'grid') {
    if (gridContainer) gridContainer.style.display = 'grid';
    if (presentContainer) presentContainer.style.display = 'none';
    if (btnGrid) {
      btnGrid.className = 'btn btn-primary btn-sm';
    }
    if (btnPresent) {
      btnPresent.className = 'btn btn-secondary btn-sm';
    }
  } else {
    if (gridContainer) gridContainer.style.display = 'none';
    if (presentContainer) presentContainer.style.display = 'flex';
    if (btnGrid) {
      btnGrid.className = 'btn btn-secondary btn-sm';
    }
    if (btnPresent) {
      btnPresent.className = 'btn btn-primary btn-sm';
    }
    renderCurrentPresentationSlide();
  }
}

function prevSlide() {
  if (!state.currentDeck || !state.currentDeck.slides) return;
  if (state.currentSlideIndex > 0) {
    state.currentSlideIndex--;
    renderCurrentPresentationSlide();
  }
}

function nextSlide() {
  if (!state.currentDeck || !state.currentDeck.slides) return;
  if (state.currentSlideIndex < state.currentDeck.slides.length - 1) {
    state.currentSlideIndex++;
    renderCurrentPresentationSlide();
  }
}

// Hàm tự động gọi backend làm giàu ảnh đồ thị & công thức cho slide
async function ensureDeckEnriched(deck) {
  if (!deck || !deck.slides) return;
  const needsEnrich = deck.slides.some(s => s.chart_spec && s.chart_spec.kind !== 'none' && s.chart_spec.expression && !s.chart_image_base64);
  if (!needsEnrich) return;

  try {
    const res = await fetch(`${state.apiBase}/api/v1/slide/enrich`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(deck)
    });
    if (res.ok) {
      const enriched = await res.json();
      state.currentDeck = enriched;
      renderSlideDeck(state.currentDeck, false);
    }
  } catch (err) {
    console.warn("Không thể tải trước ảnh đồ thị:", err);
  }
}

// Render Slide ở chế độ Trình Chiếu (Màn chiếu 16:9 lớn)
function renderCurrentPresentationSlide() {
  if (!state.currentDeck || !state.currentDeck.slides) return;
  const slide = state.currentDeck.slides[state.currentSlideIndex];
  if (!slide) return;

  const total = state.currentDeck.slides.length;
  document.getElementById('presentSlideCounter').textContent = `Slide ${state.currentSlideIndex + 1} / ${total}`;

  const slideEl = document.getElementById('presentationSlideContent');
  if (!slideEl) return;

  const isTitleSlide = slide.type === 'TITLE_SLIDE';
  const hasChart = Boolean(slide.chart_image_base64 || (slide.chart_spec && slide.chart_spec.kind !== 'none' && slide.chart_spec.expression));

  if (isTitleSlide) {
    slideEl.innerHTML = `
      <div class="slide-hero-title-box" style="height: 100%;">
        <span class="slide-hero-subject-tag" style="font-size: 0.95rem;">MÔN ${state.currentDeck.subject || 'TOÁN HỌC'} - LỚP ${state.currentDeck.grade || 11}</span>
        <h1 class="slide-hero-main-title" style="font-size: 2.6rem; margin: 1rem 0 0.5rem 0;">${renderMathString(slide.title || '')}</h1>
        ${slide.subtitle ? `<div class="slide-hero-subtitle" style="font-size: 1.35rem;">${renderMathString(slide.subtitle)}</div>` : ''}
        <div style="margin-top: 2rem; font-size: 0.95rem; color: #64748b; font-weight: 600;">
          KẾ HOẠCH BÀI DẠY THEO CÔNG VĂN 5512 / BGDĐT
        </div>
      </div>
      ${slide.teacher_note ? `
        <div class="teacher-note-box">
          <span class="teacher-note-label">🎙️ Speaker Notes:</span>
          <div>${renderMathString(slide.teacher_note)}</div>
        </div>
      ` : ''}
    `;
    return;
  }

  // Formula
  let formulaHtml = '';
  if (slide.formula_image_base64) {
    formulaHtml = `
      <div class="formula-box" style="margin: 0.75rem 0;">
        <img src="${slide.formula_image_base64}" style="max-height: 60px;" alt="Công thức">
      </div>
    `;
  } else if (slide.main_definition_latex) {
    formulaHtml = `
      <div class="formula-box" style="margin: 0.75rem 0; font-size: 1.3rem;">
        ${renderMathString(`$$${slide.main_definition_latex}$$`)}
      </div>
    `;
  }

  const bulletsHtml = (slide.bullet_points || []).map(b => `<li style="margin-bottom: 0.75rem; font-size: 1.05rem;">${renderMathString(b)}</li>`).join('');

  if (hasChart) {
    const plotImgHtml = slide.chart_image_base64 
      ? `<img src="${slide.chart_image_base64}" style="width: 100%; max-height: 290px; object-fit: contain; border-radius: 8px;" alt="Đồ thị hàm số">`
      : `<div style="padding: 2rem; color: #0284c7;">📊 Đang nạp đồ thị...</div>`;

    slideEl.innerHTML = `
      <div style="flex: 1; display: flex; flex-direction: column;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
          <span class="slide-type-badge">${slide.type}</span>
          <span style="font-size: 0.85rem; color: #64748b;">${state.currentDeck.subject} - Lớp ${state.currentDeck.grade}</span>
        </div>
        
        <h2 style="font-family: 'Times New Roman', serif; font-size: 1.85rem; font-weight: 800; color: #0f2b5c; margin-bottom: 0.2rem;">
          ${renderMathString(slide.title)}
        </h2>
        ${slide.subtitle ? `<div style="font-size: 1.05rem; color: #475569; margin-bottom: 1rem; font-style: italic;">${renderMathString(slide.subtitle)}</div>` : ''}
        
        <div style="display: grid; grid-template-columns: 1.15fr 0.85fr; gap: 1.5rem; align-items: start; flex: 1;">
          <div>
            <ul class="slide-bullets">${bulletsHtml}</ul>
            ${formulaHtml}
          </div>
          <div class="slide-plot-container" style="padding: 0.6rem;">
            ${plotImgHtml}
            <span class="slide-plot-badge">📊 Đồ thị Matplotlib Native</span>
            ${slide.chart_spec?.chart_title ? `<div style="font-size: 0.8rem; color: #475569; margin-top: 0.3rem;">${escapeHtml(slide.chart_spec.chart_title)}</div>` : ''}
          </div>
        </div>
      </div>
      ${slide.teacher_note ? `
        <div class="teacher-note-box">
          <span class="teacher-note-label">🎙️ Speaker Notes:</span>
          <div>${renderMathString(slide.teacher_note)}</div>
        </div>
      ` : ''}
    `;
  } else {
    slideEl.innerHTML = `
      <div style="flex: 1; display: flex; flex-direction: column;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
          <span class="slide-type-badge">${slide.type}</span>
          <span style="font-size: 0.85rem; color: #64748b;">${state.currentDeck.subject} - Lớp ${state.currentDeck.grade}</span>
        </div>
        
        <h2 style="font-family: 'Times New Roman', serif; font-size: 2rem; font-weight: 800; color: #0f2b5c; margin-bottom: 0.25rem;">
          ${renderMathString(slide.title)}
        </h2>
        ${slide.subtitle ? `<div style="font-size: 1.1rem; color: #475569; margin-bottom: 1.25rem; font-style: italic;">${renderMathString(slide.subtitle)}</div>` : ''}
        
        <ul class="slide-bullets">${bulletsHtml}</ul>
        ${formulaHtml}
      </div>
      ${slide.teacher_note ? `
        <div class="teacher-note-box">
          <span class="teacher-note-label">🎙️ Speaker Notes:</span>
          <div>${renderMathString(slide.teacher_note)}</div>
        </div>
      ` : ''}
    `;
  }
}

// Update JSON View & Editor
function updateJsonViewer() {
  const textarea = document.getElementById('jsonEditor');
  if (!textarea) return;

  const targetData = state.activeJsonTab === 'plan' ? state.currentPlan : state.currentDeck;
  if (targetData) {
    textarea.value = JSON.stringify(targetData, null, 2);
  } else {
    textarea.value = `// Chưa có dữ liệu ${state.activeJsonTab === 'plan' ? 'Kế hoạch bài dạy' : 'Slide bài giảng'}.\n// Hãy sinh bài hoặc bấm 'Xem dữ liệu mẫu' để nạp.`;
  }
}

// Update Tab Badges
function updateBadges() {
  const planBadge = document.getElementById('badgePlan');
  const slideBadge = document.getElementById('badgeSlide');

  if (planBadge) {
    planBadge.textContent = state.currentPlan ? 'Đã có' : '0';
  }
  if (slideBadge) {
    slideBadge.textContent = state.currentDeck?.slides?.length ? `${state.currentDeck.slides.length}` : '0';
  }
}

// Math Rendering Helper (KaTeX + Fallback)
function renderMathString(text) {
  if (!text) return '';
  
  // If KaTeX is available
  if (window.katex && typeof window.katex.renderToString === 'function') {
    // Replace block math $$...$$
    let formatted = text.replace(/\$\$([\s\S]+?)\$\$/g, (match, formula) => {
      try {
        return window.katex.renderToString(formula.trim(), { displayMode: true, throwOnError: false });
      } catch (e) {
        return `<div class="formula-box">${escapeHtml(formula)}</div>`;
      }
    });

    // Replace inline math $...$
    formatted = formatted.replace(/\$([^\$\n]+?)\$/g, (match, formula) => {
      try {
        return window.katex.renderToString(formula.trim(), { displayMode: false, throwOnError: false });
      } catch (e) {
        return `<span style="font-style: italic; color: #1e40af;">${escapeHtml(formula)}</span>`;
      }
    });

    return formatted;
  }

  // Fallback if KaTeX is not loaded
  let simple = escapeHtml(text);
  simple = simple.replace(/\$\$([\s\S]+?)\$\$/g, '<div class="formula-box">$1</div>');
  simple = simple.replace(/\$([^\$\n]+?)\$/g, '<strong style="color: #1e40af; font-family: serif;">$1</strong>');
  return simple;
}

function escapeHtml(str) {
  if (typeof str !== 'string') return str;
  return str.replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
}

// History & LocalStorage
function saveToHistory(topic, type, data) {
  const item = {
    id: Date.now(),
    topic,
    type,
    time: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }),
    data
  };

  state.history.unshift(item);
  if (state.history.length > 10) state.history.pop();

  try {
    localStorage.setItem('lessonai_history', JSON.stringify(state.history));
  } catch (e) {
    console.warn("Storage full or unavailable");
  }
  renderHistoryTable();
}

function loadHistoryFromStorage() {
  try {
    const raw = localStorage.getItem('lessonai_history');
    if (raw) {
      state.history = JSON.parse(raw);
      renderHistoryTable();
    }
  } catch (e) {
    state.history = [];
  }
}

function renderHistoryTable() {
  const tbody = document.getElementById('historyTableBody');
  if (!tbody) return;

  if (state.history.length === 0) {
    tbody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: #94a3b8; padding: 1.5rem;">Chưa có lịch sử kiểm thử nào</td></tr>`;
    return;
  }

  tbody.innerHTML = '';
  state.history.forEach((h, idx) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><strong>${escapeHtml(h.topic)}</strong></td>
      <td><span class="slide-type-badge">${h.type.toUpperCase()}</span></td>
      <td style="color: #64748b;">${h.time}</td>
      <td>
        <button class="btn btn-secondary btn-sm" onclick="restoreHistoryItem(${idx})">Xem lại</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

window.restoreHistoryItem = function(index) {
  const item = state.history[index];
  if (!item) return;

  if (item.type === 'plan') {
    state.currentPlan = item.data;
    renderLessonPlan(state.currentPlan, { is_valid: true, errors: [], warnings: [] });
    switchTab('plan');
  } else if (item.type === 'slide') {
    state.currentDeck = item.data;
    renderSlideDeck(state.currentDeck);
    switchTab('slide');
  } else if (item.type === 'all') {
    state.currentPlan = item.data.plan;
    state.currentDeck = item.data.deck;
    renderLessonPlan(state.currentPlan, { is_valid: true, errors: [], warnings: [] });
    renderSlideDeck(state.currentDeck);
    switchTab('plan');
  }
  showToast(`Đã phục hồi lịch sử: ${item.topic}`, "info");
};

// Toast Notifications
function showToast(message, type = 'info') {
  let container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  
  const iconMap = {
    success: '✅',
    error: '❌',
    warning: '⚠️',
    info: 'ℹ️'
  };

  toast.innerHTML = `<span>${iconMap[type] || 'ℹ️'}</span> <div>${escapeHtml(message)}</div>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => {
      if (toast.parentNode) toast.parentNode.removeChild(toast);
    }, 300);
  }, 4000);
}
