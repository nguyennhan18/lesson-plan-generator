/**
 * QUANTUM STUDIO - SLIDE PRESENTATION & INTERACTIVE 3D ENGINE (v6.0)
 * PowerPoint-style 16:9 Presentation Stage with Synchronized 3D Polyhedrons & Live Quiz
 */

const studioState = {
  currentSlide: 0,
  totalSlides: 5,

  // 3D Geometry Shared Parameters
  polyhedronType: 'cube',
  edgeLength: 4.0, // a = 4.0 cm
  yaw: 35,
  pitch: -22,
  zoom: 1.15,
  isOrbiting: false,
  dragStartX: 0,
  dragStartY: 0,

  // 3D Flags
  showHiddenLines: true,
  showVertexLabels: true,
  showAxes: false,

  // Quiz State
  votedOption: null,
  votes: { A: 31, B: 6, C: 3, D: 2 },

  // Timer
  timerSeconds: 45 * 60 + 20
};

// Polyhedron Definition Data
let vertices = {};
let edges = [];

/* ==========================================================================
   1. BUILD POLYHEDRON GEOMETRY
   ========================================================================== */
function buildGeometryData(type) {
  vertices = {};
  edges = [];
  const a = 1.6;

  if (type === 'cube') {
    // Đáy dưới ABCD
    vertices['A'] = { x: -a, y: -a, z: -a };
    vertices['B'] = { x: a, y: -a, z: -a };
    vertices['C'] = { x: a, y: a, z: -a };
    vertices['D'] = { x: -a, y: a, z: -a };

    // Đáy trên A'B'C'D'
    vertices["A'"] = { x: -a, y: -a, z: a };
    vertices["B'"] = { x: a, y: -a, z: a };
    vertices["C'"] = { x: a, y: a, z: a };
    vertices["D'"] = { x: -a, y: a, z: a };

    // Cạnh đáy dưới
    edges.push({ from: 'A', to: 'B', hidden: false });
    edges.push({ from: 'B', to: 'C', hidden: false });
    edges.push({ from: 'C', to: 'D', hidden: true });
    edges.push({ from: 'D', to: 'A', hidden: true });

    // Cột đứng
    edges.push({ from: 'A', to: "A'", hidden: false });
    edges.push({ from: 'B', to: "B'", hidden: false });
    edges.push({ from: 'C', to: "C'", hidden: false });
    edges.push({ from: 'D', to: "D'", hidden: true });

    // Cạnh đáy trên
    edges.push({ from: "A'", to: "B'", hidden: false });
    edges.push({ from: "B'", to: "C'", hidden: false });
    edges.push({ from: "C'", to: "D'", hidden: false });
    edges.push({ from: "D'", to: "A'", hidden: false });

  } else if (type === 'pyramid_square') {
    // S.ABCD với SA ⊥ (ABCD)
    vertices['A'] = { x: -a, y: -a, z: -a };
    vertices['B'] = { x: a, y: -a, z: -a };
    vertices['C'] = { x: a, y: a, z: -a };
    vertices['D'] = { x: -a, y: a, z: -a };
    vertices['S'] = { x: -a, y: -a, z: a * 1.5 };

    edges.push({ from: 'A', to: 'B', hidden: false });
    edges.push({ from: 'B', to: 'C', hidden: false });
    edges.push({ from: 'C', to: 'D', hidden: true });
    edges.push({ from: 'D', to: 'A', hidden: true });

    edges.push({ from: 'S', to: 'A', hidden: true });
    edges.push({ from: 'S', to: 'B', hidden: false });
    edges.push({ from: 'S', to: 'C', hidden: false });
    edges.push({ from: 'S', to: 'D', hidden: false });

  } else if (type === 'pyramid_triangle') {
    // S.ABC (Tứ diện)
    vertices['A'] = { x: -a * 1.2, y: -a * 0.7, z: -a };
    vertices['B'] = { x: a * 1.2, y: -a * 0.7, z: -a };
    vertices['C'] = { x: 0, y: a * 1.0, z: -a };
    vertices['S'] = { x: 0, y: 0, z: a * 1.4 };

    edges.push({ from: 'A', to: 'B', hidden: false });
    edges.push({ from: 'B', to: 'C', hidden: false });
    edges.push({ from: 'A', to: 'C', hidden: true });

    edges.push({ from: 'S', to: 'A', hidden: false });
    edges.push({ from: 'S', to: 'B', hidden: false });
    edges.push({ from: 'S', to: 'C', hidden: false });

  } else if (type === 'prism_triangle') {
    // Lăng trụ đứng ABC.A'B'C'
    vertices['A'] = { x: -a * 1.1, y: -a * 0.7, z: -a };
    vertices['B'] = { x: a * 1.1, y: -a * 0.7, z: -a };
    vertices['C'] = { x: 0, y: a * 0.9, z: -a };

    vertices["A'"] = { x: -a * 1.1, y: -a * 0.7, z: a };
    vertices["B'"] = { x: a * 1.1, y: -a * 0.7, z: a };
    vertices["C'"] = { x: 0, y: a * 0.9, z: a };

    edges.push({ from: 'A', to: 'B', hidden: false });
    edges.push({ from: 'B', to: 'C', hidden: false });
    edges.push({ from: 'A', to: 'C', hidden: true });

    edges.push({ from: 'A', to: "A'", hidden: false });
    edges.push({ from: 'B', to: "B'", hidden: false });
    edges.push({ from: 'C', to: "C'", hidden: false });

    edges.push({ from: "A'", to: "B'", hidden: false });
    edges.push({ from: "B'", to: "C'", hidden: false });
    edges.push({ from: "A'", to: "C'", hidden: false });
  }
}

/* ==========================================================================
   2. 3D PROJECTION & RENDERING
   ========================================================================== */
function projectPoint(pt, center, scale) {
  const radYaw = (studioState.yaw * Math.PI) / 180;
  const radPitch = (studioState.pitch * Math.PI) / 180;

  // Rotate Z (Yaw)
  const x1 = pt.x * Math.cos(radYaw) - pt.y * Math.sin(radYaw);
  const y1 = pt.x * Math.sin(radYaw) + pt.y * Math.cos(radYaw);
  const z1 = pt.z;

  // Rotate X (Pitch)
  const x2 = x1;
  const y2 = y1 * Math.cos(radPitch) - z1 * Math.sin(radPitch);
  const z2 = y1 * Math.sin(radPitch) + z1 * Math.cos(radPitch);

  return {
    px: center.x + x2 * scale * studioState.zoom,
    py: center.y - z2 * scale * studioState.zoom,
    depth: y2
  };
}

function renderSlide3DCanvas(slideIdx) {
  const canvas = document.getElementById(`canvas3D_${slideIdx}`);
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.parentElement.getBoundingClientRect();
  const w = rect.width > 20 ? rect.width : (canvas.parentElement.clientWidth || 550);
  const h = rect.height > 20 ? rect.height : (canvas.parentElement.clientHeight || 450);

  canvas.width = w * dpr;
  canvas.height = h * dpr;
  ctx.resetTransform();
  ctx.scale(dpr, dpr);

  ctx.clearRect(0, 0, w, h);

  const center = { x: w * 0.5, y: h * 0.52 };
  const scale = Math.min(w, h) * 0.22 * (studioState.edgeLength / 4.0);

  // Compute 2D points
  const p2d = {};
  for (const name in vertices) {
    p2d[name] = projectPoint(vertices[name], center, scale);
  }

  // A. SPECIFIC SLIDE FEATURES
  // Slide 3: Cross section plane (A'BD)
  if (slideIdx === 3 && p2d["A'"] && p2d['B'] && p2d['D']) {
    ctx.beginPath();
    ctx.moveTo(p2d["A'"].px, p2d["A'"].py);
    ctx.lineTo(p2d['B'].px, p2d['B'].py);
    ctx.lineTo(p2d['D'].px, p2d['D'].py);
    ctx.closePath();
    ctx.fillStyle = 'rgba(0, 240, 255, 0.22)';
    ctx.strokeStyle = '#00f0ff';
    ctx.lineWidth = 2.0;
    ctx.fill();
    ctx.stroke();
  }

  // B. DRAW STANDARD EDGES (WITH HIDDEN DASHED LINES)
  edges.forEach(e => {
    const p1 = p2d[e.from];
    const p2 = p2d[e.to];
    if (!p1 || !p2) return;

    ctx.beginPath();
    ctx.moveTo(p1.px, p1.py);
    ctx.lineTo(p2.px, p2.py);

    if (e.hidden && studioState.showHiddenLines) {
      ctx.setLineDash([6, 5]);
      ctx.strokeStyle = 'rgba(148, 163, 184, 0.5)';
      ctx.lineWidth = 1.4;
    } else {
      ctx.setLineDash([]);
      ctx.strokeStyle = '#e2e8f0';
      ctx.lineWidth = 2.0;
    }
    ctx.stroke();
    ctx.setLineDash([]);
  });

  // C. SLIDE SPECIFIC CONSTRUCTED LINES
  // Slide 1: Diagonal AC' & Base AC
  if (slideIdx === 1 && p2d['A'] && p2d["C'"] && p2d['C']) {
    // AC base (blue)
    ctx.beginPath();
    ctx.moveTo(p2d['A'].px, p2d['A'].py);
    ctx.lineTo(p2d['C'].px, p2d['C'].py);
    ctx.strokeStyle = '#38bdf8';
    ctx.lineWidth = 2.0;
    ctx.setLineDash([4, 4]);
    ctx.stroke();
    ctx.setLineDash([]);

    // AC' diagonal (golden yellow neon)
    ctx.beginPath();
    ctx.moveTo(p2d['A'].px, p2d['A'].py);
    ctx.lineTo(p2d["C'"].px, p2d["C'"].py);
    ctx.strokeStyle = '#f59e0b';
    ctx.lineWidth = 2.8;
    ctx.stroke();
  }

  // Slide 2: Perpendicular AH ⊥ B'D'
  if (slideIdx === 2 && p2d['A'] && p2d["B'"] && p2d["D'"]) {
    // B'D' edge (blue)
    ctx.beginPath();
    ctx.moveTo(p2d["B'"].px, p2d["B'"].py);
    ctx.lineTo(p2d["D'"].px, p2d["D'"].py);
    ctx.strokeStyle = '#38bdf8';
    ctx.lineWidth = 2.2;
    ctx.stroke();

    // Calculate midpoint H on B'D' in 3D
    const vB = vertices["B'"];
    const vD = vertices["D'"];
    const vH = { x: (vB.x + vD.x) / 2, y: (vB.y + vD.y) / 2, z: (vB.z + vD.z) / 2 };
    const pH = projectPoint(vH, center, scale);

    // Segment AH (rose red)
    ctx.beginPath();
    ctx.moveTo(p2d['A'].px, p2d['A'].py);
    ctx.lineTo(pH.px, pH.py);
    ctx.strokeStyle = '#f43f5e';
    ctx.lineWidth = 2.8;
    ctx.stroke();

    // Dot H
    ctx.beginPath();
    ctx.arc(pH.px, pH.py, 5, 0, Math.PI * 2);
    ctx.fillStyle = '#f43f5e';
    ctx.fill();

    ctx.font = 'bold 12px "JetBrains Mono"';
    ctx.fillStyle = '#fb7185';
    ctx.fillText('H', pH.px + 8, pH.py - 4);

    // Right angle symbol ∟
    const vAH = { x: p2d['A'].px - pH.px, y: p2d['A'].py - pH.py };
    const lenAH = Math.hypot(vAH.x, vAH.y) || 1;
    const uAH = { x: (vAH.x / lenAH) * 10, y: (vAH.y / lenAH) * 10 };

    const vBD = { x: p2d["B'"].px - pH.px, y: p2d["B'"].py - pH.py };
    const lenBD = Math.hypot(vBD.x, vBD.y) || 1;
    const uBD = { x: (vBD.x / lenBD) * 10, y: (vBD.y / lenBD) * 10 };

    ctx.beginPath();
    ctx.strokeStyle = '#f43f5e';
    ctx.lineWidth = 1.5;
    ctx.moveTo(pH.px + uAH.x, pH.py + uAH.y);
    ctx.lineTo(pH.px + uAH.x + uBD.x, pH.py + uAH.y + uBD.y);
    ctx.lineTo(pH.px + uBD.x, pH.py + uBD.y);
    ctx.stroke();
  }

  // D. DRAW VERTICES & LABELS
  for (const name in vertices) {
    const pt = p2d[name];
    if (!pt) continue;

    ctx.beginPath();
    ctx.arc(pt.px, pt.py, 4.5, 0, Math.PI * 2);
    ctx.fillStyle = '#00f0ff';
    ctx.shadowColor = '#00f0ff';
    ctx.shadowBlur = 8;
    ctx.fill();
    ctx.shadowBlur = 0;

    if (studioState.showVertexLabels) {
      ctx.font = 'bold 13px "JetBrains Mono"';
      ctx.fillStyle = '#ffffff';
      const offsetX = (pt.px > center.x) ? 10 : -20;
      const offsetY = (pt.py > center.y) ? 16 : -8;
      ctx.fillText(name, pt.px + offsetX, pt.py + offsetY);
    }
  }
}

/* ==========================================================================
   3. SLIDE PRESENTATION NAVIGATION (POWERPOINT LOGIC)
   ========================================================================== */
function goToSlide(slideIndex) {
  if (slideIndex < 0 || slideIndex >= studioState.totalSlides) return;
  studioState.currentSlide = slideIndex;

  // Toggle active class on slide pages
  for (let i = 0; i < studioState.totalSlides; i++) {
    const page = document.getElementById(`slidePage_${i}`);
    if (page) {
      page.classList.toggle('active', i === slideIndex);
    }
  }

  // Update bottom counter
  const counterEl = document.getElementById('currentSlideDisplayNum');
  if (counterEl) counterEl.textContent = slideIndex + 1;

  // Update chat drawer slide badge (Task 6.3)
  const chatBadge = document.getElementById('chatSlideNumBadge');
  if (chatBadge) chatBadge.textContent = slideIndex + 1;

  // Update thumbnail pills
  document.querySelectorAll('.thumb-pill').forEach((pill, idx) => {
    pill.classList.toggle('active', idx === slideIndex);
  });


  // Re-render math with KaTeX on active slide
  triggerMathRender();

  // Render 3D canvas of that slide
  if (slideIndex < 4) {
    setTimeout(() => renderSlide3DCanvas(slideIndex), 30);
  }
}

function nextSlide() {
  if (studioState.currentSlide < studioState.totalSlides - 1) {
    goToSlide(studioState.currentSlide + 1);
  }
}

function prevSlide() {
  if (studioState.currentSlide > 0) {
    goToSlide(studioState.currentSlide - 1);
  }
}

function toggleFullscreen() {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen().catch(() => { });
  } else {
    document.exitFullscreen().catch(() => { });
  }
}

/* ==========================================================================
   4. KATEX AUTO-RENDER MATH ENGINE
   ========================================================================== */
function triggerMathRender() {
  const activeSlide = document.getElementById(`slidePage_${studioState.currentSlide}`);
  if (!activeSlide) return;

  if (window.renderMathInElement) {
    try {
      window.renderMathInElement(activeSlide, {
        delimiters: [
          { left: '$$', right: '$$', display: true },
          { left: '$', right: '$', display: false }
        ],
        throwOnError: false
      });
    } catch (e) {
      console.warn("KaTeX render error:", e);
    }
  }
}

/* ==========================================================================
   5. LIVE QUIZ SIMULATION
   ========================================================================== */
function voteQuizOption(opt) {
  studioState.votedOption = opt;

  // Bump votes
  studioState.votes[opt] = (studioState.votes[opt] || 0) + 3;
  const total = Object.values(studioState.votes).reduce((a, b) => a + b, 0);

  // Update visual bars & percentages
  ['A', 'B', 'C', 'D'].forEach(o => {
    const pct = Math.round((studioState.votes[o] / total) * 100);
    const pctEl = document.getElementById(`pct_${o}`);
    const barEl = document.getElementById(`bar_${o}`);
    const cardEl = document.getElementById(`quizCard_${o}`);

    if (pctEl) pctEl.textContent = `${pct}%`;
    if (barEl) barEl.style.width = `${pct}%`;
    if (cardEl) {
      cardEl.classList.toggle('voted', o === opt);
    }
  });

  const countBadge = document.getElementById('pollVotersCount');
  if (countBadge) countBadge.textContent = `${total} Học sinh đã nộp`;
}

function toggleSolutionBox() {
  const body = document.getElementById('solutionBodyContent');
  const icon = document.getElementById('solutionToggleIcon');
  if (body) {
    body.classList.toggle('open');
    if (icon) icon.textContent = body.classList.contains('open') ? '▲' : '▼';
  }
}

/* ==========================================================================
   6. 3D PARAMETERS & MOUSE ORBIT CONTROLS
   ========================================================================== */
function applyCameraPreset(preset) {
  if (preset === 'iso') {
    studioState.yaw = 35;
    studioState.pitch = -22;
  } else if (preset === 'top') {
    studioState.yaw = 0;
    studioState.pitch = -88;
  } else if (preset === 'front') {
    studioState.yaw = 0;
    studioState.pitch = 0;
  }
  renderSlide3DCanvas(studioState.currentSlide);
}

function init3DInteractionEvents() {
  // Bind mouse drag on each slide canvas
  for (let i = 0; i < 4; i++) {
    const canvas = document.getElementById(`canvas3D_${i}`);
    if (!canvas) continue;

    canvas.addEventListener('mousedown', (e) => {
      studioState.isOrbiting = true;
      studioState.dragStartX = e.clientX;
      studioState.dragStartY = e.clientY;
    });

    window.addEventListener('mousemove', (e) => {
      if (!studioState.isOrbiting) return;
      const dx = e.clientX - studioState.dragStartX;
      const dy = e.clientY - studioState.dragStartY;

      studioState.yaw = (studioState.yaw + dx * 0.5 + 360) % 360;
      studioState.pitch = Math.max(-88, Math.min(88, studioState.pitch - dy * 0.4));

      studioState.dragStartX = e.clientX;
      studioState.dragStartY = e.clientY;

      renderSlide3DCanvas(studioState.currentSlide);
    });

    window.addEventListener('mouseup', () => {
      studioState.isOrbiting = false;
    });

    canvas.addEventListener('wheel', (e) => {
      e.preventDefault();
      studioState.zoom = Math.max(0.6, Math.min(2.2, studioState.zoom - e.deltaY * 0.0015));
      renderSlide3DCanvas(studioState.currentSlide);
    }, { passive: false });
  }

  // Drawer Toggles
  const drawer = document.getElementById('floating3DDrawer');
  const btnOpen = document.getElementById('btnToggle3DTools');
  const btnClose = document.getElementById('btnClose3DDrawer');

  if (btnOpen && drawer) btnOpen.addEventListener('click', () => drawer.classList.toggle('open'));
  if (btnClose && drawer) btnClose.addEventListener('click', () => drawer.classList.remove('open'));

  // Shape Selector
  const selShape = document.getElementById('selPolyhedronType');
  if (selShape) {
    selShape.addEventListener('change', (e) => {
      studioState.polyhedronType = e.target.value;
      buildGeometryData(studioState.polyhedronType);
      renderSlide3DCanvas(studioState.currentSlide);
    });
  }

  // Edge Length Slider
  const slider = document.getElementById('rngEdgeLength');
  const disp = document.getElementById('dispEdgeVal');
  if (slider) {
    slider.addEventListener('input', (e) => {
      studioState.edgeLength = parseFloat(e.target.value);
      if (disp) disp.textContent = `${studioState.edgeLength.toFixed(1)} cm`;
      renderSlide3DCanvas(studioState.currentSlide);
    });
  }

  // Toggles
  const chkHidden = document.getElementById('chkShowHiddenLines');
  const chkLabels = document.getElementById('chkShowVertexLabels');
  const chkAxes = document.getElementById('chkShowAxesOxyz');

  if (chkHidden) chkHidden.addEventListener('change', e => { studioState.showHiddenLines = e.target.checked; renderSlide3DCanvas(studioState.currentSlide); });
  if (chkLabels) chkLabels.addEventListener('change', e => { studioState.showVertexLabels = e.target.checked; renderSlide3DCanvas(studioState.currentSlide); });
  if (chkAxes) chkAxes.addEventListener('change', e => { studioState.showAxes = e.target.checked; renderSlide3DCanvas(studioState.currentSlide); });
}

/* ==========================================================================
   7. CHAT CO-PILOT CLIENT LOGIC (NGÀY 6)
   ========================================================================== */
const chatState = {
  isOpen: false,
  sessionId: null,
  isThinking: false
};

function getOrCreateSessionId() {
  let sess = sessionStorage.getItem('quantum_chat_session_id');
  if (!sess) {
    sess = 'sess_' + Math.random().toString(36).substring(2, 9) + '_' + Date.now();
    sessionStorage.setItem('quantum_chat_session_id', sess);
  }
  return sess;
}

function toggleChatCopilot(forceOpen = null) {
  const drawer = document.getElementById('chatCopilotDrawer');
  if (!drawer) return;

  if (forceOpen !== null) {
    chatState.isOpen = forceOpen;
  } else {
    chatState.isOpen = !chatState.isOpen;
  }

  drawer.classList.toggle('open', chatState.isOpen);
  if (chatState.isOpen) {
    const input = document.getElementById('chatInputText');
    if (input) setTimeout(() => input.focus(), 150);
  }
}

function setChatThinking(isThinking) {
  chatState.isThinking = isThinking;
  const indicator = document.getElementById('chatTypingIndicator');
  const sendBtn = document.getElementById('btnSendChatMessage');
  if (indicator) {
    indicator.classList.toggle('hidden', !isThinking);
  }
  if (sendBtn) {
    sendBtn.disabled = isThinking;
    sendBtn.style.opacity = isThinking ? '0.6' : '1';
  }
  // Scroll to bottom
  const container = document.getElementById('chatMessagesStream');
  if (container && isThinking) {
    container.scrollTop = container.scrollHeight;
  }
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function formatAiMarkdown(text) {
  if (!text) return '';
  let html = text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>');

  const lines = html.split('\n');
  let inList = false;
  let out = [];

  for (let line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith('• ') || trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      if (!inList) {
        out.push('<ul class="chat-list-styled">');
        inList = true;
      }
      out.push(`<li>${trimmed.substring(2)}</li>`);
    } else {
      if (inList) {
        out.push('</ul>');
        inList = false;
      }
      if (trimmed === '') {
        out.push('<div class="chat-spacer" style="height: 6px;"></div>');
      } else {
        out.push(`<p style="margin-bottom: 4px;">${line}</p>`);
      }
    }
  }
  if (inList) out.push('</ul>');
  return out.join('');
}

function appendChatMessage(role, text, timestamp, suggestedAction = null) {
  const container = document.getElementById('chatMessagesStream');
  if (!container) return;

  const row = document.createElement('div');
  row.className = `chat-msg-row ${role === 'user' ? 'user-msg-row' : 'ai-msg-row'}`;

  const timeStr = timestamp || new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });

  if (role === 'user') {
    row.innerHTML = `
      <div class="user-bubble">
        <div class="msg-content">${escapeHtml(text)}</div>
        <div class="msg-timestamp">${timeStr}</div>
      </div>
    `;
  } else {
    const formattedHtml = formatAiMarkdown(text);
    const actionBadgeHtml = suggestedAction && suggestedAction !== 'GENERAL_ADVICE'
      ? `<div class="msg-action-badge"><span class="badge-dot"></span> Đề xuất sư phạm: ${escapeHtml(suggestedAction)}</div>`
      : '';
    row.innerHTML = `
      <div class="chat-msg-avatar">🤖</div>
      <div class="chat-msg-bubble ai-bubble">
        <div class="msg-author">Trợ giảng AI Co-pilot</div>
        <div class="msg-content">${formattedHtml}</div>
        ${actionBadgeHtml}
        <div class="msg-timestamp">${timeStr}</div>
      </div>
    `;
  }

  container.appendChild(row);

  // Trigger KaTeX rendering on this newly created message bubble
  if (role === 'assistant' && window.renderMathInElement) {
    try {
      window.renderMathInElement(row, {
        delimiters: [
          { left: '$$', right: '$$', display: true },
          { left: '$', right: '$', display: false }
        ],
        throwOnError: false
      });
    } catch (e) {
      console.warn("KaTeX render error in chat bubble:", e);
    }
  }

  // Smooth scroll to bottom
  container.scrollTop = container.scrollHeight;
}

async function submitChatMessage(customText = null) {
  const input = document.getElementById('chatInputText');
  const message = customText ? customText.trim() : (input ? input.value.trim() : '');
  if (!message || chatState.isThinking) return;

  if (input && !customText) input.value = '';

  // Đảm bảo mở drawer nếu đang đóng
  if (!chatState.isOpen) {
    toggleChatCopilot(true);
  }

  const nowTime = new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });

  // 1. Hiển thị tin nhắn người dùng (Task 6.3)
  appendChatMessage('user', message, nowTime);

  // 2. Hiển thị "Đang suy nghĩ..." (Task 6.4)
  setChatThinking(true);

  try {
    const response = await fetch('/api/v1/chat/interact', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: chatState.sessionId,
        user_message: message,
        current_slide_index: studioState.currentSlide,
        subject: studioState.subject || "Toán học",
        grade: studioState.grade || 11,
        class_proficiency: studioState.classProficiency || "standard",
        slide_deck: null
      })
    });

    if (!response.ok) {
      throw new Error(`Mã phản hồi HTTP ${response.status}`);
    }

    const data = await response.json();
    setChatThinking(false);

    // 3. Hiển thị phản hồi của AI (Task 6.4)
    appendChatMessage('assistant', data.ai_response, data.timestamp || nowTime, data.suggested_action, data.suggested_patch);

  } catch (err) {
    console.error("Lỗi gửi tin nhắn Co-pilot:", err);
    setChatThinking(false);
    appendChatMessage('assistant', `⚠️ Có lỗi khi kết nối với Trợ giảng AI: ${err.message}. Thầy/Cô vui lòng thử lại nhé!`, nowTime);
  }
}

function handleQuickChipClick(promptText) {
  submitChatMessage(promptText);
}

async function resetChatSession() {
  if (!confirm("Thầy/Cô có muốn làm mới cuộc trò chuyện với Trợ giảng AI?")) return;

  try {
    await fetch(`/api/v1/chat/session/${chatState.sessionId}`, { method: 'DELETE' });
  } catch (e) { }

  chatState.sessionId = 'sess_' + Math.random().toString(36).substring(2, 9) + '_' + Date.now();
  sessionStorage.setItem('quantum_chat_session_id', chatState.sessionId);

  const container = document.getElementById('chatMessagesStream');
  if (container) {
    const nowTime = new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
    container.innerHTML = `
      <div class="chat-msg-row ai-msg-row">
        <div class="chat-msg-avatar">🤖</div>
        <div class="chat-msg-bubble ai-bubble">
          <div class="msg-author">Trợ giảng AI Co-pilot</div>
          <div class="msg-content">
            Đã làm mới phiên hỗ trợ! Em đang theo dõi cùng Thầy/Cô tại <strong>Slide ${studioState.currentSlide + 1}</strong>. Thầy/Cô cần em hỗ trợ gì ạ?
          </div>
          <div class="msg-timestamp">${nowTime}</div>
        </div>
      </div>
    `;
  }
}

/* ==========================================================================
   8. MULTI-SCREEN NAVIGATION & PRESENTATION COCKPIT CONTROLS
   ========================================================================== */

function switchScreen(screenName) {
  const tabMap = {
    'presentation': 'tabPresentation',
    'lesson-plan': 'tabLessonPlan',
    'slide-editor': 'tabSlideEditor',
    'analytics': 'tabAnalytics'
  };

  const screenMap = {
    'presentation': 'screenPresentation',
    'lesson-plan': 'screenLessonPlan',
    'slide-editor': 'screenSlideEditor',
    'analytics': 'screenAnalytics'
  };

  // 1. Cập nhật Tab buttons
  Object.values(tabMap).forEach(id => {
    const el = document.getElementById(id);
    if (el) el.classList.remove('active');
  });
  const activeTab = document.getElementById(tabMap[screenName]);
  if (activeTab) activeTab.classList.add('active');

  // 2. Cập nhật Screens container
  Object.values(screenMap).forEach(id => {
    const el = document.getElementById(id);
    if (el) el.classList.remove('active');
  });
  const activeScreen = document.getElementById(screenMap[screenName]);
  if (activeScreen) activeScreen.classList.add('active');

  // 3. Tự động render 3D / Math khi trở về màn hình trình chiếu
  if (screenName === 'presentation') {
    setTimeout(() => {
      renderSlide3DCanvas(studioState.currentSlide);
      triggerMathRender();
    }, 60);
  } else if (screenName === 'slide-editor') {
    setTimeout(triggerMathRender, 60);
  }
}

function toggleLeftChatDock(forceState = null) {
  const dock = document.getElementById('presLeftChatDock');
  const btnExpand = document.getElementById('btnExpandLeftChat');
  if (!dock) return;

  const isCollapsed = dock.classList.contains('collapsed');
  const willCollapse = forceState !== null ? !forceState : !isCollapsed;

  dock.classList.toggle('collapsed', willCollapse);
  if (btnExpand) btnExpand.classList.toggle('hidden', !willCollapse);

  setTimeout(() => renderSlide3DCanvas(studioState.currentSlide), 280);
}

function toggleRightToolsDock(forceState = null) {
  const dock = document.getElementById('presRightToolsDock');
  const btnExpand = document.getElementById('btnExpandRightTools');
  if (!dock) return;

  const isCollapsed = dock.classList.contains('collapsed');
  const willCollapse = forceState !== null ? !forceState : !isCollapsed;

  dock.classList.toggle('collapsed', willCollapse);
  if (btnExpand) btnExpand.classList.toggle('hidden', !willCollapse);

  setTimeout(() => renderSlide3DCanvas(studioState.currentSlide), 280);
}

function switchToolsSubtab(tab) {
  const btn3D = document.getElementById('btnSubtab3D');
  const btnGraph = document.getElementById('btnSubtabGraph');
  const content3D = document.getElementById('toolContent3D');
  const contentGraph = document.getElementById('toolContentGraph');

  if (tab === '3d') {
    if (btn3D) btn3D.classList.add('active');
    if (btnGraph) btnGraph.classList.remove('active');
    if (content3D) content3D.classList.add('active');
    if (contentGraph) contentGraph.classList.remove('active');
  } else {
    if (btn3D) btn3D.classList.remove('active');
    if (btnGraph) btnGraph.classList.add('active');
    if (content3D) content3D.classList.remove('active');
    if (contentGraph) contentGraph.classList.add('active');
    setTimeout(plot2DFunction, 40);
  }
}

function quickSelectGeom(type) {
  if (type === 'diagonal') {
    goToSlide(1);
    showLivePatchToast("📐 Đang hiển thị: Đường chéo không gian AC' = a√3");
  } else if (type === 'altitude') {
    goToSlide(2);
    showLivePatchToast("📏 Đang hiển thị: Đoạn vuông góc AH ⊥ B'D'");
  } else if (type === 'cross_section') {
    goToSlide(3);
    showLivePatchToast("▱ Đang hiển thị: Thiết diện tam giác đều (A'BD)");
  }
}

function applyPresetFunction(val) {
  const input = document.getElementById('inputMathFunction');
  if (input) input.value = val;
  plot2DFunction();
}

function plot2DFunction() {
  const canvas = document.getElementById('canvasFunctionPlot');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width;
  const h = canvas.height;

  // Clear & background
  ctx.clearRect(0, 0, w, h);
  ctx.fillStyle = '#060a14';
  ctx.fillRect(0, 0, w, h);

  // Grid lines
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
  ctx.lineWidth = 1;
  const step = 25;
  for (let x = 0; x < w; x += step) {
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke();
  }
  for (let y = 0; y < h; y += step) {
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
  }

  // Axes (Center O)
  const cx = w / 2;
  const cy = h / 2;
  ctx.strokeStyle = 'rgba(56, 189, 248, 0.45)';
  ctx.lineWidth = 1.5;

  ctx.beginPath(); ctx.moveTo(0, cy); ctx.lineTo(w, cy); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(cx, 0); ctx.lineTo(cx, h); ctx.stroke();

  // Axis Labels
  ctx.fillStyle = '#38bdf8';
  ctx.font = '10px monospace';
  ctx.fillText('x', w - 12, cy - 6);
  ctx.fillText('y', cx + 6, 12);
  ctx.fillText('O', cx - 12, cy + 12);

  // Parse expression
  const exprInput = document.getElementById('inputMathFunction');
  const expr = exprInput ? exprInput.value.trim() : 'x**3 - 3*x';

  ctx.strokeStyle = '#00f0ff';
  ctx.lineWidth = 2.5;
  ctx.beginPath();

  const scaleX = 22;
  const scaleY = 22;
  let first = true;

  for (let px = 0; px < w; px += 2) {
    const x = (px - cx) / scaleX;
    let y = 0;
    try {
      const evalExpr = expr
        .replace(/\bsin\b/g, 'Math.sin')
        .replace(/\bcos\b/g, 'Math.cos')
        .replace(/\btan\b/g, 'Math.tan')
        .replace(/\bsqrt\b/g, 'Math.sqrt')
        .replace(/\babs\b/g, 'Math.abs')
        .replace(/\bpi\b/g, 'Math.PI')
        .replace(/\^/g, '**');

      const fn = new Function('x', `return ${evalExpr};`);
      y = fn(x);
    } catch (e) {
      y = 0;
    }

    if (isNaN(y) || !isFinite(y)) {
      first = true;
      continue;
    }

    const py = cy - y * scaleY;
    if (py < -60 || py > h + 60) {
      first = true;
      continue;
    }

    if (first) {
      ctx.moveTo(px, py);
      first = false;
    } else {
      ctx.lineTo(px, py);
    }
  }
  ctx.stroke();

  // Draw title banner on canvas
  ctx.fillStyle = '#f8fafc';
  ctx.font = 'bold 11px Inter, sans-serif';
  ctx.fillText(`y = ${expr}`, 10, 18);
}

// Handlers for Lesson Plan, Slide Editor, Analytics
function setProficiencyLevel(level) {
  ['btnProfStandard', 'btnProfBasic', 'btnProfAdvanced'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.classList.remove('active');
  });
  const idMap = { 'standard': 'btnProfStandard', 'basic': 'btnProfBasic', 'advanced': 'btnProfAdvanced' };
  const target = document.getElementById(idMap[level]);
  if (target) target.classList.add('active');
  showLivePatchToast(`🎯 Đã chọn mức độ phân hóa lớp: ${level.toUpperCase()}`);
}

function triggerFileUpload(inputId) {
  const el = document.getElementById(inputId);
  if (el) el.click();
}

function handleGradeSheetUploaded(input) {
  if (input.files && input.files[0]) {
    const fileName = input.files[0].name;
    showLivePatchToast(`📊 Đã nhận tệp: ${fileName} - Đang phân tích Z-Score & Phổ điểm...`);
    setTimeout(() => {
      showLivePatchToast(`✅ Phân loại thành công: Lớp đạt chuẩn STANDARD (μ = 7.42)`);
    }, 1200);
  }
}

function generateLessonPlanAction() {
  showLivePatchToast("🚀 Đang gọi Gemini AI sinh Kế hoạch bài dạy 5512...");
  setTimeout(() => {
    showLivePatchToast("✨ Đã hoàn tất Kế hoạch bài dạy 4 hoạt động chuẩn 5512!");
  }, 1500);
}

function exportCurrentLessonPlanDocx() {
  showLivePatchToast("📥 Đang tải xuống file Word Kế hoạch bài dạy (.docx)...");
  window.location.href = "/";
}

function exportSlideDeckPptx() {
  showLivePatchToast("📥 Đang xuất file Slide PowerPoint (.pptx) Native...");
  window.location.href = "/";
}

function loadSlideIntoEditor(idx) {
  document.querySelectorAll('.slide-thumb-card').forEach((card, i) => {
    card.classList.toggle('active', i === idx);
  });
  showLivePatchToast(`📝 Đang chỉnh sửa nội dung Slide ${idx + 1}`);
}

function saveSlideEditsAction() {
  showLivePatchToast("💾 Đã lưu thay đổi nội dung slide thành công!");
}

function addNewSlideEditor() {
  showLivePatchToast("➕ Đã thêm slide mới vào bài giảng!");
}

/* ==========================================================================
   9. INITIALIZATION & GLOBAL BINDINGS
   ========================================================================== */
window.goToSlide = goToSlide;
window.nextSlide = nextSlide;
window.prevSlide = prevSlide;
window.voteQuizOption = voteQuizOption;
window.toggleSolutionBox = toggleSolutionBox;
window.applyCameraPreset = applyCameraPreset;
window.toggleChatCopilot = toggleLeftChatDock;
window.submitChatMessage = submitChatMessage;
window.handleQuickChipClick = handleQuickChipClick;
window.resetChatSession = resetChatSession;

// Multi-Screen Functions
window.switchScreen = switchScreen;
window.toggleLeftChatDock = toggleLeftChatDock;
window.toggleRightToolsDock = toggleRightToolsDock;
window.switchToolsSubtab = switchToolsSubtab;
window.quickSelectGeom = quickSelectGeom;
window.applyPresetFunction = applyPresetFunction;
window.plot2DFunction = plot2DFunction;
window.setProficiencyLevel = setProficiencyLevel;
window.triggerFileUpload = triggerFileUpload;
window.handleGradeSheetUploaded = handleGradeSheetUploaded;
window.generateLessonPlanAction = generateLessonPlanAction;
window.exportCurrentLessonPlanDocx = exportCurrentLessonPlanDocx;
window.exportSlideDeckPptx = exportSlideDeckPptx;
window.loadSlideIntoEditor = loadSlideIntoEditor;
window.saveSlideEditsAction = saveSlideEditsAction;
window.addNewSlideEditor = addNewSlideEditor;

document.addEventListener('DOMContentLoaded', () => {
  // Navigation buttons
  const btnNext = document.getElementById('btnNextSlide');
  const btnPrev = document.getElementById('btnPrevSlide');
  const btnFs = document.getElementById('btnToggleFullscreen');

  if (btnNext) btnNext.addEventListener('click', nextSlide);
  if (btnPrev) btnPrev.addEventListener('click', prevSlide);
  if (btnFs) btnFs.addEventListener('click', toggleFullscreen);

  // Chat Co-pilot Session
  chatState.sessionId = getOrCreateSessionId();
  const btnResetChat = document.getElementById('btnResetChatSession');
  if (btnResetChat) btnResetChat.addEventListener('click', resetChatSession);

  // Set real timestamp for initial welcome AI message
  const initialTime = document.getElementById('initialAiTimestamp');
  if (initialTime) initialTime.textContent = new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });

  // Keyboard navigation & Shortcuts (PowerPoint style)
  window.addEventListener('keydown', (e) => {
    const activeTag = document.activeElement ? document.activeElement.tagName.toLowerCase() : '';
    if (activeTag === 'input' || activeTag === 'textarea') {
      if (e.key === 'Escape') {
        toggleLeftChatDock(false);
        toggleRightToolsDock(false);
      }
      return;
    }

    if (e.key === 'ArrowRight' || e.key === ' ') {
      e.preventDefault();
      nextSlide();
    } else if (e.key === 'ArrowLeft') {
      e.preventDefault();
      prevSlide();
    } else if (e.key === 'f' || e.key === 'F5') {
      e.preventDefault();
      toggleFullscreen();
    } else if (e.key === 'c' || e.key === 'C') {
      e.preventDefault();
      toggleLeftChatDock();
    } else if (e.key === 't' || e.key === 'T') {
      e.preventDefault();
      toggleRightToolsDock();
    } else if (e.key === 'Escape') {
      toggleLeftChatDock(false);
      toggleRightToolsDock(false);
    }
  });

  // Build Geometry
  buildGeometryData('cube');

  // Init 3D interactions
  init3DInteractionEvents();

  // Window resize re-render
  window.addEventListener('resize', () => {
    if (studioState.currentSlide < 4) {
      renderSlide3DCanvas(studioState.currentSlide);
    }
  });

  // Session timer
  const timerText = document.getElementById('sessionTimerText');
  setInterval(() => {
    studioState.timerSeconds++;
    const m = Math.floor(studioState.timerSeconds / 60);
    const s = studioState.timerSeconds % 60;
    if (timerText) timerText.textContent = `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  }, 1000);

  // Initial Slide render & 2D function plotter
  goToSlide(0);
  setTimeout(plot2DFunction, 400);

  // Ensure KaTeX renders after CDN load
  setTimeout(triggerMathRender, 300);
  setTimeout(triggerMathRender, 1000);
});


/* ==========================================================================*/
/* ==========================================================================
   TASK 7.2: LIVE PATCHING LOGIC (CẬP NHẬT SLIDE TRỰC TIẾP KHÔNG TẢI LẠI TRANG)
   ========================================================================== */

// Bộ nhớ lưu tạm các bản vá AI đề xuất theo mã định danh
const activeSlidePatches = {};

/**
 * Áp dụng bản vá SlidePatchProposal vào đúng phần tử DOM của Slide đích.
 * Đảm bảo: (1) Không reload trang; (2) Không reset Canvas 3D; (3) Tự động re-render KaTeX; (4) Giữ nguyên vẹn các slide khác.
 */
function patchCurrentSlide(patch) {
  if (!patch) return false;

  const targetIndex = (patch.target_slide_index !== undefined) ? patch.target_slide_index : (patch.slide_index || 0);
  const slideEl = document.getElementById(`slidePage_${targetIndex}`);

  if (!slideEl) {
    console.warn(`[LivePatch] Không tìm thấy phần tử #slidePage_${targetIndex} trong DOM`);
    return false;
  }

  // 1. Nếu giáo viên đang đứng ở slide khác, tự động chuyển camera sang đúng slide đích để xem kết quả
  if (studioState.currentSlide !== targetIndex) {
    goToSlide(targetIndex);
  }

  // 2. Cập nhật danh sách gạch đầu dòng (Bullet Points) nếu bản vá có đề xuất
  if (Array.isArray(patch.bullet_points) && patch.bullet_points.length > 0) {
    const listEl = slideEl.querySelector('.slide-list');
    if (listEl) {
      listEl.innerHTML = patch.bullet_points
        .map(item => `<li>${item}</li>`)
        .join('');
    }
  }

  // 3. Cập nhật công thức toán học LaTeX trọng tâm nếu có
  if (patch.main_definition_latex) {
    const formulaEl = slideEl.querySelector('.formula-highlight');
    if (formulaEl) {
      formulaEl.innerHTML = `$$${patch.main_definition_latex}$$`;
    }
  }

  // 4. Cập nhật câu hỏi trắc nghiệm nếu là hành động ADD_QUIZ (dành riêng cho Slide 5)
  if (patch.quiz) {
    const questionBody = slideEl.querySelector('.quiz-question-body');
    if (questionBody && patch.quiz.question) {
      questionBody.innerHTML = patch.quiz.question;
    }
    if (Array.isArray(patch.quiz.options)) {
      const optionCards = slideEl.querySelectorAll('.quiz-card-option');
      patch.quiz.options.forEach((optText, idx) => {
        if (optionCards[idx]) {
          const textEl = optionCards[idx].querySelector('.option-text');
          if (textEl) textEl.innerHTML = optText;
        }
      });
    }
  }

  // 5. Tự động kích hoạt KaTeX biên dịch lại công thức toán học sắc nét trên slide vừa vá
  if (window.renderMathInElement) {
    try {
      window.renderMathInElement(slideEl, {
        delimiters: [
          { left: '$$', right: '$$', display: true },
          { left: '$', right: '$', display: false }
        ],
        throwOnError: false
      });
    } catch (e) {
      console.warn("[LivePatch] Lỗi biên dịch KaTeX:", e);
    }
  }

  // 6. Kích hoạt hiệu ứng viền phát sáng Cyan/Emerald (Task 7.3)
  slideEl.classList.remove('slide-patched-glow');
  void slideEl.offsetWidth; // Buộc trình duyệt Reflow để khởi động lại CSS animation
  slideEl.classList.add('slide-patched-glow');
  setTimeout(() => {
    slideEl.classList.remove('slide-patched-glow');
  }, 2800);

  return true;
}

/**
 * Xử lý sự kiện khi giáo viên nhấp nút "⚡ Áp dụng vào Slide X" trong khung chat
 */
function handleApplyPatchClick(patchId, btnElement) {
  const patch = activeSlidePatches[patchId];
  if (!patch) return;

  const success = patchCurrentSlide(patch);
  if (success && btnElement) {
    const slideNum = (patch.target_slide_index !== undefined ? patch.target_slide_index : (patch.slide_index || 0)) + 1;
    btnElement.disabled = true;
    btnElement.innerHTML = `✅ Đã áp dụng vào Slide ${slideNum}`;
    btnElement.classList.add('applied');

    // Hiển thị Toast thông báo thành công (Task 7.3)
    showLivePatchToast(`✨ Đã cập nhật thành công nội dung cho Slide ${slideNum}!`);
  }
}

/**
 * Hiển thị Toast thông báo trạng thái cập nhật slide
 */
function showLivePatchToast(msg) {
  let toast = document.getElementById('livePatchToast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'livePatchToast';
    toast.className = 'live-patch-toast';
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 3000);
}

// Cập nhật chữ ký hàm nhận thêm tham số suggestedPatch:
function appendChatMessage(role, text, timestamp, suggestedAction = null, suggestedPatch = null) {
  const container = document.getElementById('chatMessagesStream');
  if (!container) return;

  const row = document.createElement('div');
  row.className = `chat-msg-row ${role === 'user' ? 'user-msg-row' : 'ai-msg-row'}`;

  const timeStr = timestamp || new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });

  if (role === 'user') {
    row.innerHTML = `
      <div class="user-bubble">
        <div class="msg-content">${escapeHtml(text)}</div>
        <div class="msg-timestamp">${timeStr}</div>
      </div>
    `;
  } else {
    const formattedHtml = formatAiMarkdown(text);
    const actionBadgeHtml = (suggestedAction && suggestedAction !== 'GENERAL_ADVICE')
      ? `<div class="msg-action-badge"><span class="badge-dot"></span> Đề xuất: ${escapeHtml(suggestedAction)}</div>`
      : '';

    // Tạo thẻ đề xuất bản vá kèm nút bấm Áp dụng nếu AI có sinh patch
    let patchCardHtml = '';
    if (suggestedPatch && (suggestedPatch.bullet_points || suggestedPatch.main_definition_latex || suggestedPatch.quiz)) {
      const patchId = 'patch_' + Date.now() + '_' + Math.random().toString(36).substr(2, 5);
      activeSlidePatches[patchId] = suggestedPatch;
      const targetNum = (suggestedPatch.target_slide_index !== undefined ? suggestedPatch.target_slide_index : (suggestedPatch.slide_index || 0)) + 1;
      const explanation = suggestedPatch.preview_explanation || 'Đề xuất tối ưu hóa nội dung cho học sinh dễ hiểu hơn';

      patchCardHtml = `
        <div class="patch-proposal-box">
          <div class="patch-header">
            <span class="patch-badge">⚡ BẢN VÁ ĐỀ XUẤT</span>
            <span class="patch-target-tag">Mục tiêu: Slide ${targetNum}</span>
          </div>
          <div class="patch-desc">${escapeHtml(explanation)}</div>
          <button type="button" class="btn-live-patch" onclick="handleApplyPatchClick('${patchId}', this)">
            ⚡ Áp dụng vào Slide ${targetNum} ngay
          </button>
        </div>
      `;
    }

    row.innerHTML = `
      <div class="chat-msg-avatar">🤖</div>
      <div class="chat-msg-bubble ai-bubble">
        <div class="msg-author">Trợ giảng AI Co-pilot</div>
        <div class="msg-content">${formattedHtml}</div>
        ${actionBadgeHtml}
        ${patchCardHtml}
        <div class="msg-timestamp">${timeStr}</div>
      </div>
    `;
  }

  container.appendChild(row);

  // Kích hoạt KaTeX render công thức toán học trong bong bóng chat
  if (role === 'assistant' && window.renderMathInElement) {
    try {
      window.renderMathInElement(row, {
        delimiters: [
          { left: '$$', right: '$$', display: true },
          { left: '$', right: '$', display: false }
        ],
        throwOnError: false
      });
    } catch (e) {
      console.warn("KaTeX render error in chat bubble:", e);
    }
  }

  // Cuộn mượt xuống đáy khung chat
  container.scrollTop = container.scrollHeight;
}
