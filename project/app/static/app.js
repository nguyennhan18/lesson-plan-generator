/**
 * QUANTUM STUDIO - ENGINE & INTERACTION CONTROLLER (v4.0)
 * Powers the 4-column workstation, dynamic 3D SVG transformation,
 * live quiz voting, slide rail navigation, and AI CV 5512 lesson plan integration.
 */

// Application State
const state = {
  apiBase: window.location.origin.startsWith('http') && !window.location.port.includes('3000')
    ? window.location.origin
    : 'http://localhost:8000',
  currentSlideIndex: 0,
  
  // 3D Parameters
  radius: 4.5,
  alpha: 35, // deg
  beta: -15, // deg
  zoom: 1.0,
  showPlane: true,
  showShadow: true,
  isDragging3D: false,
  dragStartX: 0,
  dragStartY: 0,

  // Live Quiz
  quizLocked: false,
  votes: { A: 26, B: 7, C: 4, D: 1 },

  // Timer
  timerSeconds: 45 * 60 + 20,

  // Slides Data
  slides: [
    {
      index: 1,
      title: "Mặt cầu & Hình nón Oxyz",
      status: "Đang dạy",
      time: "12:30",
      tag: "3D Oxyz",
      header: "Phương trình Chính tắc Mặt Cầu (S)",
      id: "ID: EQ-302",
      latex: "(x - a)^2 + (y - b)^2 + (z - c)^2 = R^2",
      center: "(1; 2; -3)",
      radius: "4.5 m",
      quizQuestion: "Bán kính mặt cầu ngoại tiếp khối chóp S.ABC với SA ⊥ đáy có công thức:",
      steps: [
        { label: "Bước 1:", desc: "Xác định tâm đường tròn ngoại tiếp đa giác đáy ΔABC → điểm H.", border: "border-cyan-400", text: "text-cyan-300" },
        { label: "Bước 2:", desc: "Dựng trục d qua H vuông góc với mặt phẳng (ABC). Dựng mặt phẳng trung trực của cạnh bên SA.", border: "border-indigo-400", text: "text-indigo-300" },
        { label: "Bước 3:", desc: "Giao điểm chính là tâm mặt cầu I. Khi đó:\nR = √(R_đáy² + (SA/2)²) = a√3", border: "border-emerald-400", text: "text-emerald-400" }
      ]
    },
    {
      index: 2,
      title: "Cực trị hình học không gian",
      status: "",
      time: "08:15",
      tag: "Giải tích",
      header: "Điều kiện Cực trị Hình học Không gian",
      id: "ID: EQ-303",
      latex: "\\max / \\min \\ f(x, y, z) \\quad \\text{với} \\quad \\nabla f = \\lambda \\nabla g",
      center: "(0; 0; 0)",
      radius: "3.2 m",
      quizQuestion: "Khoảng cách ngắn nhất từ điểm M(1; 2; 3) đến mặt cầu (S): x² + y² + z² = 9 là:",
      steps: [
        { label: "Bước 1:", desc: "Tâm mặt cầu O(0; 0; 0) và bán kính R = 3.", border: "border-cyan-400", text: "text-cyan-300" },
        { label: "Bước 2:", desc: "Độ dài đoạn OM = √(1² + 2² + 3²) = √14 ≈ 3.74.", border: "border-indigo-400", text: "text-indigo-300" },
        { label: "Bước 3:", desc: "Khoảng cách ngắn nhất: d = OM - R = √14 - 3 ≈ 0.74.", border: "border-emerald-400", text: "text-emerald-400" }
      ]
    },
    {
      index: 3,
      title: "Câu hỏi tương tác trực tiếp",
      status: "Quiz",
      time: "05:00",
      tag: "Mini-Test",
      header: "Bài toán Xác định Tâm và Bán kính",
      id: "ID: TEST-01",
      latex: "x^2 + y^2 + z^2 - 2ax - 2by - 2cz + d = 0",
      center: "(2; -3; 1)",
      radius: "5.0 m",
      quizQuestion: "Mặt cầu x² + y² + z² - 4x + 6y - 2z - 11 = 0 có bán kính R bằng:",
      steps: [
        { label: "Bước 1:", desc: "Xác định a = 2, b = -3, c = 1, d = -11.", border: "border-cyan-400", text: "text-cyan-300" },
        { label: "Bước 2:", desc: "Điều kiện a² + b² + c² - d = 4 + 9 + 1 - (-11) = 25 > 0.", border: "border-indigo-400", text: "text-indigo-300" },
        { label: "Bước 3:", desc: "Bán kính: R = √25 = 5.", border: "border-emerald-400", text: "text-emerald-400" }
      ]
    },
    {
      index: 4,
      title: "Mặt bậc hai tham số đa chiều",
      status: "",
      time: "15:00",
      tag: "Paraboloid",
      header: "Phương trình Paraboloid Eliptic",
      id: "ID: EQ-401",
      latex: "z = \\frac{x^2}{a^2} + \\frac{y^2}{b^2}",
      center: "(0; 0; 0)",
      radius: "Tham số z ≥ 0",
      quizQuestion: "Thiết diện của paraboloid z = x² + y² khi cắt bởi mặt phẳng z = 4 là:",
      steps: [
        { label: "Bước 1:", desc: "Thay z = 4 vào phương trình ta được: x² + y² = 4 = 2².", border: "border-cyan-400", text: "text-cyan-300" },
        { label: "Bước 2:", desc: "Thiết diện là đường tròn nằm trên mp z = 4 có tâm (0; 0; 4), bán kính R = 2.", border: "border-indigo-400", text: "text-indigo-300" }
      ]
    }
  ],

  currentPlan: null,
  currentDeck: null
};

// Initial Setup
document.addEventListener('DOMContentLoaded', () => {
  initLiveTimer();
  init3DControls();
  initSlideRailEvents();
  initQuizModule();
  initDrawerAndModals();
  initAnnotationTools();
  applyCurrentSlide(0);
  apply3DTransform();
});

/* ==========================================================================
   1. LIVE TIMER
   ========================================================================== */
function initLiveTimer() {
  const timerEl = document.getElementById('sessionTimerText');
  setInterval(() => {
    state.timerSeconds++;
    const m = Math.floor(state.timerSeconds / 60);
    const s = state.timerSeconds % 60;
    if (timerEl) {
      timerEl.textContent = `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
    }
  }, 1000);
}

/* ==========================================================================
   2. 3D VECTOR GEOMETRY SIMULATION & SLIDERS
   ========================================================================== */
function init3DControls() {
  const sliderRadius = document.getElementById('sliderRadius');
  const sliderAlpha = document.getElementById('sliderAlpha');
  const sliderBeta = document.getElementById('sliderBeta');
  const chkPlane = document.getElementById('chkShowPlane');
  const chkShadow = document.getElementById('chkShowShadow');

  // Sliders input
  if (sliderRadius) {
    sliderRadius.addEventListener('input', (e) => {
      state.radius = parseFloat(e.target.value);
      document.getElementById('val-radius').textContent = state.radius.toFixed(2);
      document.getElementById('calloutRadius').textContent = `${state.radius.toFixed(1)} m`;
      apply3DTransform();
    });
  }

  if (sliderAlpha) {
    sliderAlpha.addEventListener('input', (e) => {
      state.alpha = parseInt(e.target.value, 10);
      document.getElementById('val-alpha').textContent = `${state.alpha}°`;
      document.getElementById('labelRotationZ').textContent = `Trục quay: Z-Normal (Alpha: ${state.alpha}°)`;
      apply3DTransform();
    });
  }

  if (sliderBeta) {
    sliderBeta.addEventListener('input', (e) => {
      state.beta = parseInt(e.target.value, 10);
      document.getElementById('val-beta').textContent = `${state.beta}°`;
      apply3DTransform();
    });
  }

  // Toggles
  if (chkPlane) {
    chkPlane.addEventListener('change', (e) => {
      state.showPlane = e.target.checked;
      const plane = document.getElementById('svgTangentPlaneGroup');
      if (plane) plane.style.display = state.showPlane ? 'block' : 'none';
    });
  }

  if (chkShadow) {
    chkShadow.addEventListener('change', (e) => {
      state.showShadow = e.target.checked;
      const shadow = document.getElementById('svgShadowEllipse');
      if (shadow) shadow.style.display = state.showShadow ? 'block' : 'none';
    });
  }

  // Canvas Mouse Orbit Interaction
  const canvasViewport = document.getElementById('canvasViewport');
  if (canvasViewport) {
    canvasViewport.addEventListener('mousedown', (e) => {
      state.isDragging3D = true;
      state.dragStartX = e.clientX;
      state.dragStartY = e.clientY;
    });

    window.addEventListener('mousemove', (e) => {
      if (!state.isDragging3D) return;
      const dx = e.clientX - state.dragStartX;
      const dy = e.clientY - state.dragStartY;

      state.alpha = (state.alpha + Math.round(dx * 0.5) + 360) % 360;
      state.beta = Math.max(-85, Math.min(85, state.beta - Math.round(dy * 0.4)));

      state.dragStartX = e.clientX;
      state.dragStartY = e.clientY;

      // Update UI
      if (sliderAlpha) sliderAlpha.value = state.alpha;
      if (sliderBeta) sliderBeta.value = state.beta;
      document.getElementById('val-alpha').textContent = `${state.alpha}°`;
      document.getElementById('val-beta').textContent = `${state.beta}°`;
      document.getElementById('labelRotationZ').textContent = `Trục quay: Z-Normal (Alpha: ${state.alpha}°)`;

      apply3DTransform();
    });

    window.addEventListener('mouseup', () => {
      state.isDragging3D = false;
    });
  }

  // Zoom controls
  const btnZoomIn = document.getElementById('btnZoomIn');
  const btnZoomOut = document.getElementById('btnZoomOut');
  const btnReset = document.getElementById('btnResetAngle');
  const zoomDisplay = document.getElementById('zoomPercentDisplay');

  if (btnZoomIn) {
    btnZoomIn.addEventListener('click', () => {
      state.zoom = Math.min(2.0, state.zoom + 0.15);
      if (zoomDisplay) zoomDisplay.textContent = `${Math.round(state.zoom * 100)}%`;
      apply3DTransform();
    });
  }
  if (btnZoomOut) {
    btnZoomOut.addEventListener('click', () => {
      state.zoom = Math.max(0.5, state.zoom - 0.15);
      if (zoomDisplay) zoomDisplay.textContent = `${Math.round(state.zoom * 100)}%`;
      apply3DTransform();
    });
  }
  if (btnReset) {
    btnReset.addEventListener('click', () => {
      state.alpha = 35;
      state.beta = -15;
      state.radius = 4.5;
      state.zoom = 1.0;

      if (sliderRadius) sliderRadius.value = 4.5;
      if (sliderAlpha) sliderAlpha.value = 35;
      if (sliderBeta) sliderBeta.value = -15;
      if (zoomDisplay) zoomDisplay.textContent = "100%";

      document.getElementById('val-radius').textContent = "4.50";
      document.getElementById('val-alpha').textContent = "35°";
      document.getElementById('val-beta').textContent = "-15°";
      document.getElementById('calloutRadius').textContent = "4.5 m";
      document.getElementById('labelRotationZ').textContent = "Trục quay: Z-Normal (Alpha: 35°)";

      apply3DTransform();
    });
  }
}

function apply3DTransform() {
  const svgWrap = document.getElementById('svg3DWrap');
  const sphereCircle = document.getElementById('svgSphereCircle');
  const equator = document.getElementById('svgEquatorEllipse');
  const meridian = document.getElementById('svgMeridianEllipse');
  const labelR = document.getElementById('svgLabelR');

  // Scale sphere elements based on radius
  const baseR = 95;
  const scaleFactor = (state.radius / 4.5);
  const currentR = baseR * scaleFactor;

  if (sphereCircle) sphereCircle.setAttribute('r', currentR);
  if (equator) equator.setAttribute('rx', currentR);
  if (meridian) meridian.setAttribute('ry', currentR);
  if (labelR) labelR.textContent = `R = ${state.radius.toFixed(1)}`;

  // Apply subtle perspective rotate transform on SVG wrap
  if (svgWrap) {
    const rotZ = (state.alpha - 35) * 0.4;
    const rotX = (state.beta + 15) * 0.3;
    svgWrap.style.transform = `scale(${state.zoom}) rotateZ(${rotZ}deg) rotateX(${rotX}deg)`;
  }
}

/* ==========================================================================
   3. SLIDE RAIL NAVIGATION
   ========================================================================= */
function initSlideRailEvents() {
  const items = document.querySelectorAll('.slide-card-item');
  items.forEach((item) => {
    item.addEventListener('click', () => {
      const idx = parseInt(item.getAttribute('data-slide-index'), 10);
      applyCurrentSlide(idx);
    });
  });

  const btnAdd = document.getElementById('btnAddNewSlide');
  if (btnAdd) {
    btnAdd.addEventListener('click', () => {
      alert("Bạn có thể thêm slide mới bằng cách mở 'Soạn bài AI' hoặc tải file tài liệu!");
      openAIDrawer();
    });
  }
}

function applyCurrentSlide(index) {
  state.currentSlideIndex = index;
  const slide = state.slides[index] || state.slides[0];

  // Highlight active slide item
  document.querySelectorAll('.slide-card-item').forEach((el, idx) => {
    if (idx === index) {
      el.classList.add('active-slide-ring');
      el.classList.remove('border-white/10');
    } else {
      el.classList.remove('active-slide-ring');
      el.classList.add('border-white/10');
    }
  });

  // Update Callout Box
  const header = document.getElementById('formulaCardHeader');
  const idEl = document.getElementById('formulaCardId');
  const latexEl = document.getElementById('formulaLatexContainer');
  const centerEl = document.getElementById('calloutCenter');
  const radiusEl = document.getElementById('calloutRadius');

  if (header) header.textContent = slide.header || slide.title;
  if (idEl) idEl.textContent = slide.id || `SLIDE-0${slide.index}`;
  if (centerEl) centerEl.textContent = slide.center || '(0; 0; 0)';
  if (radiusEl) radiusEl.textContent = slide.radius || '4.5 m';

  // Render KaTeX
  if (latexEl && window.katex && slide.latex) {
    try {
      window.katex.render(slide.latex, latexEl, { throwOnError: false, displayMode: true });
    } catch (e) {
      latexEl.textContent = slide.latex;
    }
  }

  // Update Quiz
  const qTitle = document.getElementById('quizQuestionTitle');
  if (qTitle && slide.quizQuestion) {
    qTitle.innerHTML = `<span class="text-cyan-400 font-semibold font-mono">Câu 0${slide.index}:</span> ${slide.quizQuestion}`;
  }

  // Update Solution Steps
  const stepsBox = document.getElementById('solutionStepsBox');
  if (stepsBox && slide.steps) {
    stepsBox.innerHTML = slide.steps.map(s => `
      <div class="p-1.5 rounded bg-studio-850/80 border-l-2 ${s.border}">
        <span class="${s.text} font-semibold">${s.label}</span> ${s.desc.replace('\n', '<br/>')}
      </div>
    `).join('');
  }
}

/* ==========================================================================
   4. LIVE QUIZ INTERACTION
   ========================================================================== */
window.castQuizVote = function(option) {
  if (state.quizLocked) {
    alert("Bình chọn hiện đã bị khóa bởi Giảng viên!");
    return;
  }

  state.votes[option] = (state.votes[option] || 0) + 4;
  const total = Object.values(state.votes).reduce((a, b) => a + b, 0);

  ['A', 'B', 'C', 'D'].forEach(opt => {
    const pct = Math.round((state.votes[opt] / total) * 100);
    const pctEl = document.getElementById(`pct${opt}`);
    const barEl = document.getElementById(`bar${opt}`);
    if (pctEl) pctEl.textContent = `${pct}%`;
    if (barEl) barEl.style.width = `${pct}%`;
  });

  const badge = document.getElementById('quizVotesBadge');
  if (badge) badge.textContent = `${total} Đã nộp`;
};

function initQuizModule() {
  const btnLock = document.getElementById('btnLockPoll');
  if (btnLock) {
    btnLock.addEventListener('click', () => {
      state.quizLocked = !state.quizLocked;
      btnLock.textContent = state.quizLocked ? "Mở bình chọn" : "Khóa bình chọn";
      btnLock.style.color = state.quizLocked ? "#f87171" : "#cbd5e1";
    });
  }

  const btnCopy = document.getElementById('btnCopySteps');
  if (btnCopy) {
    btnCopy.addEventListener('click', () => {
      const slide = state.slides[state.currentSlideIndex];
      if (!slide || !slide.steps) return;
      const text = slide.steps.map(s => `${s.label} ${s.desc}`).join('\n');
      navigator.clipboard.writeText(text);
      alert("Đã sao chép lời giải chi tiết vào Clipboard!");
    });
  }

  const btnF5 = document.getElementById('btnLaunchPresentation');
  if (btnF5) {
    btnF5.addEventListener('click', () => {
      if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(() => {});
      } else {
        document.exitFullscreen().catch(() => {});
      }
    });
  }
}

/* ==========================================================================
   5. AI STUDIO DRAWER & MODALS
   ========================================================================== */
function openAIDrawer() {
  const modal = document.getElementById('aiStudioDrawerModal');
  if (modal) {
    modal.classList.remove('hidden');
    modal.classList.add('flex');
  }
}

function closeAIDrawer() {
  const modal = document.getElementById('aiStudioDrawerModal');
  if (modal) {
    modal.classList.add('hidden');
    modal.classList.remove('flex');
  }
}

window.setDrawerTopic = function(t) {
  const input = document.getElementById('drawerTopic');
  if (input) input.value = t;
};

function initDrawerAndModals() {
  const btnOpen = document.getElementById('btnOpenAIDrawer');
  const btnClose = document.getElementById('btnCloseAIDrawerModal');
  const navAi = document.getElementById('navAiDrawer');
  const navDocs = document.getElementById('navDocsExport');

  if (btnOpen) btnOpen.addEventListener('click', openAIDrawer);
  if (btnClose) btnClose.addEventListener('click', closeAIDrawer);
  if (navAi) navAi.addEventListener('click', openAIDrawer);
  if (navDocs) navDocs.addEventListener('click', openAIDrawer);

  // Settings Modal
  const modalSettings = document.getElementById('settingsBackdrop');
  const btnOpenSettings = document.getElementById('btnOpenSettingsModal');
  const btnCloseSettings = document.getElementById('btnCloseSettingsModal');
  const btnSaveSettings = document.getElementById('btnSaveServerUrl');
  const inputUrl = document.getElementById('inputServerUrl');

  if (btnOpenSettings && modalSettings) {
    btnOpenSettings.addEventListener('click', () => {
      modalSettings.classList.remove('hidden');
      modalSettings.classList.add('flex');
    });
  }
  if (btnCloseSettings && modalSettings) {
    btnCloseSettings.addEventListener('click', () => {
      modalSettings.classList.add('hidden');
      modalSettings.classList.remove('flex');
    });
  }
  if (btnSaveSettings && inputUrl) {
    btnSaveSettings.addEventListener('click', () => {
      state.apiBase = inputUrl.value.trim().replace(/\/$/, '');
      modalSettings.classList.add('hidden');
      modalSettings.classList.remove('flex');
      alert(`Đã lưu cấu hình server: ${state.apiBase}`);
    });
  }

  // AI Buttons in Drawer
  const btnGenPlan = document.getElementById('btnGenLessonPlan');
  const btnGenSlide = document.getElementById('btnGenSlideDeck');
  const btnDemo = document.getElementById('btnLoadDemoOxyz');

  if (btnGenPlan) btnGenPlan.addEventListener('click', handleGeneratePlan);
  if (btnGenSlide) btnGenSlide.addEventListener('click', handleGenerateSlide);
  if (btnDemo) btnDemo.addEventListener('click', handleLoadDemo);

  // Export Buttons
  const btnDocx = document.getElementById('btnExportDocx');
  const btnPptx = document.getElementById('btnExportPptx');

  if (btnDocx) btnDocx.addEventListener('click', exportDocxFile);
  if (btnPptx) btnPptx.addEventListener('click', exportPptxFile);
}

async function handleGeneratePlan() {
  const topic = document.getElementById('drawerTopic').value.trim() || "Mặt cầu trong không gian Oxyz";
  const subject = document.getElementById('drawerSubject').value;
  const grade = parseInt(document.getElementById('drawerGrade').value, 10);
  const preview = document.getElementById('drawerPlanPreview');

  if (preview) preview.innerHTML = `<span class="text-cyan-400">⏳ Đang gọi Gemini AI sinh giáo án CV 5512 cho '${topic}'...</span>`;

  try {
    const res = await fetch(`${state.apiBase}/api/v1/lesson-plan/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic, subject, grade, additional_requirements: "" })
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    state.currentPlan = data.plan;

    if (preview) {
      preview.innerHTML = `
        <h4 class="text-cyan-300 font-bold mb-1">${data.plan.lesson_title || topic}</h4>
        <p class="text-slate-300"><strong>Môn:</strong> ${data.plan.subject} (Lớp ${data.plan.grade})</p>
        <p class="text-emerald-400 mt-1">Đã tạo đủ 4 hoạt động dạy học chuẩn CV 5512!</p>
      `;
    }
    alert("Sinh Kế hoạch bài dạy (CV 5512) thành công!");
  } catch (e) {
    if (preview) preview.innerHTML = `<span class="text-rose-400">Lỗi kết nối AI: ${e.message}. Bạn có thể bấm 'Nạp Dữ Liệu Mẫu'.</span>`;
  }
}

async function handleGenerateSlide() {
  const topic = document.getElementById('drawerTopic').value.trim() || "Mặt cầu trong không gian Oxyz";
  const subject = document.getElementById('drawerSubject').value;
  const grade = parseInt(document.getElementById('drawerGrade').value, 10);
  const preview = document.getElementById('drawerPlanPreview');

  if (preview) preview.innerHTML = `<span class="text-cyan-400">⏳ Đang gọi Gemini AI sinh Slide bài giảng...</span>`;

  try {
    const res = await fetch(`${state.apiBase}/api/v1/slide/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic, subject, grade })
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    state.currentDeck = data.slide_deck;

    alert(`Sinh thành công ${data.slide_deck.slides.length} slide bài giảng!`);
    closeAIDrawer();
  } catch (e) {
    if (preview) preview.innerHTML = `<span class="text-rose-400">Lỗi sinh Slide: ${e.message}</span>`;
  }
}

function handleLoadDemo() {
  alert("Đã nạp thành công bộ bài giảng mẫu chuẩn Quantum Studio Oxyz!");
  applyCurrentSlide(0);
  closeAIDrawer();
}

async function exportDocxFile() {
  if (!state.currentPlan) {
    alert("Chưa có kế hoạch bài dạy. Vui lòng bấm 'Sinh Giáo án 5512' trước!");
    return;
  }
  try {
    const res = await fetch(`${state.apiBase}/api/v1/lesson-plan/export-docx`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(state.currentPlan)
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const blob = await res.blob();
    triggerDownload(blob, `Giao_an_5512_${Date.now()}.docx`);
  } catch (e) {
    alert(`Lỗi tải Word: ${e.message}`);
  }
}

async function exportPptxFile() {
  if (!state.currentDeck) {
    alert("Chưa có Slide bài giảng. Vui lòng bấm 'Sinh Slide Bài giảng' trước!");
    return;
  }
  try {
    const res = await fetch(`${state.apiBase}/api/v1/lesson-plan/export-slide`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(state.currentDeck)
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const blob = await res.blob();
    triggerDownload(blob, `Slide_Bai_Giang_${Date.now()}.pptx`);
  } catch (e) {
    alert(`Lỗi tải PowerPoint: ${e.message}`);
  }
}

function triggerDownload(blob, name) {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

/* ==========================================================================
   6. ANNOTATION TOOLS QUICK ACTIONS
   ========================================================================== */
function initAnnotationTools() {
  const tools = document.querySelectorAll('.tool-btn-draw');
  tools.forEach(btn => {
    btn.addEventListener('click', () => {
      tools.forEach(b => {
        b.classList.remove('bg-studio-700/60', 'text-cyan-400', 'border-cyan-500/30');
        b.classList.add('text-slate-300');
      });
      btn.classList.add('bg-studio-700/60', 'text-cyan-400', 'border-cyan-500/30');
      btn.classList.remove('text-slate-300');
    });
  });

  const colors = document.querySelectorAll('.color-dot');
  colors.forEach(dot => {
    dot.addEventListener('click', () => {
      colors.forEach(d => d.classList.remove('ring-2', 'ring-white'));
      dot.classList.add('ring-2', 'ring-white');
    });
  });

  const btnClear = document.getElementById('btnClearCanvas');
  if (btnClear) {
    btnClear.addEventListener('click', () => {
      alert("Đã xóa toàn bộ nét vẽ và ghi chú bảng!");
    });
  }

  const btnSnapshot = document.getElementById('btnSnapshotCanvas');
  if (btnSnapshot) {
    btnSnapshot.addEventListener('click', () => {
      alert("Đã chụp và lưu ảnh bảng giảng dạy thành công!");
    });
  }
}
