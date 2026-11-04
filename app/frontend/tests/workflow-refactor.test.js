import assert from 'node:assert/strict';
import { beforeEach, afterEach, test } from 'node:test';
import { runInNewContext } from 'node:vm';
import { buildSync } from 'esbuild';
import { createDocumentExportActions } from '../src/features/exports/documentExportActions.js';
import { createLessonGenerationActions } from '../src/features/generation/lessonGenerationActions.js';

let calls, downloads, alerts, revoked, restore;
beforeEach(() => {
  calls = [];
  downloads = [];
  alerts = [];
  revoked = [];
  const replacements = {
    fetch: async (url, options) => {
      calls.push({ url, payload: JSON.parse(options.body) });
      const contentType = url.endsWith('export-docx')
        ? 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        : url.endsWith('export-slide')
          ? 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
          : 'application/zip';
      return { ok: true, headers: { get: () => contentType }, blob: async () => new Blob([new Uint8Array([80,75,3,4]),'office file']) };
    },
    alert: message => alerts.push(message),
    window: {
      URL: { createObjectURL: () => 'blob:export', revokeObjectURL: url => revoked.push(url) }
    },
    document: {
      createElement: () => ({ click() { downloads.push({ name: this.download, url: this.href }); } })
    }
  };
  const previous = Object.fromEntries(Object.keys(replacements).map(key => [key, Object.getOwnPropertyDescriptor(globalThis, key)]));
  Object.assign(globalThis, replacements);
  restore = () => {
    for (const [key, descriptor] of Object.entries(previous)) {
      if (descriptor) Object.defineProperty(globalThis, key, descriptor);
      else delete globalThis[key];
    }
  };
});
afterEach(() => restore());

const plan = { lesson_title: 'Bài học thử' };
function makeDeck() {
  return {
    presentation_title: 'Slide thử',
    slides: [
      { title: 'Hình trước', has_3d: true, snapshot_3d_base64: 'old' },
      { title: 'Hình hiện tại', has_3d: true },
      { title: 'Văn bản' }
    ]
  };
}
function exportActions(options = {}) {
  return createDocumentExportActions({
    lessonPlan: plan, slideDeck: makeDeck(), currentSlide: 1,
    threeCanvasCaptureRef: { current: null }, ...options
  });
}

test('Word sends lesson and slides together, downloads DOCX and releases the URL', async () => {
  const deck = makeDeck();
  await exportActions({ slideDeck: deck }).handleExportDocx();
  assert.deepEqual(calls, [{ url: '/api/v1/lesson-plan/export-docx', payload: { plan, slide_deck: deck } }]);
  assert.equal(downloads[0].name, 'Giao_An_5512_Bài học thử.docx');
  assert.deepEqual(revoked, ['blob:export']);
});

test('Word supports a lesson without slides', async () => {
  await exportActions({ slideDeck: null }).handleExportDocx();
  assert.deepEqual(calls[0].payload, plan);
});

test('PowerPoint sends an immutable deck and never propagates the current view', async () => {
  const deck = makeDeck();
  const before = structuredClone(deck);
  await exportActions({ slideDeck: deck, threeCanvasCaptureRef: { current: () => 'new-image' } }).handleExportPptx();
  assert.equal(calls[0].url, '/api/v1/lesson-plan/export-slide');
  assert.equal(calls[0].payload.snapshot_3d_base64, undefined);
  assert.equal(calls[0].payload.slides[0].snapshot_3d_base64, 'old');
  assert.equal(calls[0].payload.slides[1].snapshot_3d_base64, undefined);
  assert.equal(calls[0].payload.slides[2].snapshot_3d_base64, undefined);
  assert.deepEqual(deck, before);
  assert.equal(downloads[0].name, 'Slide_Slide thử.pptx');
});

test('PowerPoint ignores the deprecated global browser capture', async () => {
  window.__threeCanvasCaptureSnapshot = () => 'browser-image';
  await exportActions().handleExportPptx();
  assert.equal(calls[0].payload.slides[1].snapshot_3d_base64, undefined);
});

test('ZIP sends both documents and preserves existing snapshots without a capture', async () => {
  const deck = { ...makeDeck(), snapshot_3d_base64: 'existing-image' };
  await exportActions({ slideDeck: deck }).handleExportDualPackage();
  assert.equal(calls[0].url, '/api/v1/lesson-plan/export-dual-package');
  assert.deepEqual(calls[0].payload, { plan, slide_deck: deck });
  assert.equal(downloads[0].name, 'Tron_Bo_Giao_An_Va_Slide_Bài_học_thử.zip');
});

test('ZIP supports a lesson without slides', async () => {
  await exportActions({ slideDeck: null }).handleExportDualPackage();
  assert.deepEqual(calls[0].payload, { plan, slide_deck: null });
});

for (const action of ['handleExportDocx', 'handleExportPptx', 'handleExportDualPackage']) {
  test(`${action} stops when required data is missing`, async () => {
    await exportActions({ lessonPlan: null, slideDeck: null })[action]();
    assert.equal(calls.length, 0);
    assert.equal(alerts.length, 1);
    assert.equal(downloads.length, 0);
  });

  test(`${action} reports HTTP errors without downloading`, async () => {
    globalThis.fetch = async () => ({ ok: false, status: 500 });
    await exportActions()[action]();
    assert.match(alerts[0], /HTTP 500/);
    assert.equal(downloads.length, 0);
  });
}

// Bundle the real hook and fullscreen helper; substitute only React's effect
// scheduler so browser event behavior can be checked without a DOM dependency.
const presentationBundle = buildSync({
  entryPoints: [new URL('../src/features/presentation/usePresentationControls.js', import.meta.url).pathname],
  bundle: true, write: false, platform: 'node', format: 'cjs', external: ['react']
}).outputFiles[0].text;

function mountPresentation(initial = {}) {
  const state = { currentSlide: 0, activeScreen: 'presentation', isPresentationMode: false, isBlackout: false, isLeftOpen: false, isRightOpen: false, ...initial };
  const windowEvents = new Map();
  const documentEvents = new Map();
  window.addEventListener = (name, handler) => windowEvents.set(name, handler);
  window.removeEventListener = (name, handler) => {
    if (windowEvents.get(name) === handler) windowEvents.delete(name);
  };
  document.addEventListener = (name, handler) => documentEvents.set(name, handler);
  document.removeEventListener = (name, handler) => {
    if (documentEvents.get(name) === handler) documentEvents.delete(name);
  };
  document.documentElement = { requestFullscreen: async () => { document.fullscreenElement = document.documentElement; } };
  document.exitFullscreen = async () => { document.fullscreenElement = null; };
  const effects = [];
  const module = { exports: {} };
  runInNewContext(presentationBundle, {
    module, exports: module.exports, window, document, console,
    require: name => {
      assert.equal(name, 'react');
      return { useEffect: callback => effects.push(callback) };
    }
  });
  const options = { ...state, slideDeck: makeDeck() };
  for (const key of Object.keys(state)) {
    options[`set${key[0].toUpperCase()}${key.slice(1)}`] = value => {
      state[key] = typeof value === 'function' ? value(state[key]) : value;
    };
  }
  const actions = module.exports.usePresentationControls(options);
  const cleanups = effects.map(callback => callback());
  return {
    state, actions, windowEvents, documentEvents,
    press(key, tagName = 'DIV') {
      const event = { key, code: key === ' ' ? 'Space' : key, target: { tagName }, preventDefault() { this.prevented = true; } };
      windowEvents.get('keydown')(event);
      return event;
    },
    cleanup: () => cleanups.forEach(cleanup => cleanup?.())
  };
}

test('presentation navigation stays within slide bounds and ignores editable fields', () => {
  const ui = mountPresentation();
  ui.press('ArrowLeft');
  assert.equal(ui.state.currentSlide, 0);
  ui.press('End');
  ui.press('ArrowRight');
  assert.equal(ui.state.currentSlide, 2);
  for (const tag of ['INPUT', 'TEXTAREA', 'SELECT', 'MATH-FIELD']) {
    assert.equal(ui.press('Home', tag).prevented, undefined);
    assert.equal(ui.state.currentSlide, 2);
  }
  ui.press('Home');
  ui.press(' ');
  assert.equal(ui.state.currentSlide, 1);
  ui.cleanup();
});

test('presentation synchronizes fullscreen state and removes browser listeners', async () => {
  const ui = mountPresentation();
  await ui.actions.handleStartPresentation();
  assert.equal(ui.state.isPresentationMode, true);
  assert.equal(ui.state.activeScreen, 'presentation');
  await ui.actions.handleExitPresentation();
  assert.equal(document.fullscreenElement, null);
  ui.state.isBlackout = true;
  ui.documentEvents.get('fullscreenchange')();
  assert.equal(ui.state.isPresentationMode, false);
  assert.equal(ui.state.isBlackout, false);
  ui.cleanup();
  assert.equal(ui.windowEvents.size, 0);
  assert.equal(ui.documentEvents.size, 0);
});

test('blackout Escape clears blackout before leaving presentation', () => {
  const ui = mountPresentation({ isPresentationMode: true, isBlackout: true });
  ui.press('Escape');
  assert.equal(ui.state.isBlackout, false);
  assert.equal(ui.state.isPresentationMode, true);
  ui.cleanup();
});

test('presentation shortcut toggles blackout and tool docks', () => {
  const ui = mountPresentation();
  ui.press('b');
  ui.press('c');
  ui.press('t');
  assert.equal(ui.state.isBlackout, true);
  assert.equal(ui.state.isLeftOpen, true);
  assert.equal(ui.state.isRightOpen, true);
  ui.cleanup();
});

function generationActions(initial = {}) {
  const state = {
    outline: { outline_slides:[{id:'o1',title:'Đề',bullet_points:[]}], topic: 'Hình lập phương', subject: 'Toán học', grade: 12, lesson_id: 'M12-CD-B1' },
    presentationConfig: { use_rag: true, class_proficiency: 'advanced' },
    classProficiency: 'standard', recommendedOutcome: 'Vận dụng',
    isGeneratingOutline: false, activeScreen: 'outline', isAiGenerating: false,
    generationStep: '', lessonPlan: null, slideDeck: null, currentSlide: 2, polyhedronType: 'cube',
    ...initial
  };
  const options = { ...state };
  const changes = [];
  for (const key of Object.keys(state)) {
    options[`set${key[0].toUpperCase()}${key.slice(1)}`] = value => {
      state[key] = value;
      changes.push({ key, value });
    };
  }
  return { state, changes, ...createLessonGenerationActions(options) };
}

test('generation calls lesson then slides with the returned plan and updates App state', async () => {
  const deck = makeDeck();
  globalThis.fetch = async (url, options) => {
    calls.push({ url, payload: JSON.parse(options.body) });
    return { ok: true, json: async () => url.endsWith('/lesson-plan/generate') ? { plan } : deck };
  };
  const ui = generationActions();
  await ui.handleGenerateFromOutline();
  assert.deepEqual(calls.map(call => call.url), ['/api/v1/lesson-plan/generate', '/api/v1/slide/generate']);
  assert.equal(calls[0].payload.class_proficiency, 'advanced');
  assert.equal(calls[0].payload.target_outcome, 'Vận dụng');
  assert.equal(calls[0].payload.lesson_id, 'M12-CD-B1');
  assert.deepEqual(calls[1].payload.plan, plan);
  assert.deepEqual(ui.state.lessonPlan, plan);
  assert.deepEqual(ui.state.slideDeck, {...deck,project_id:undefined});
  assert.equal(ui.state.currentSlide, 0);
  assert.equal(ui.state.activeScreen, 'presentation');
  assert.equal(ui.state.isAiGenerating, false);
  assert.equal(ui.state.generationStep, '');
  assert.ok(ui.changes.some(change => change.key === 'isAiGenerating' && change.value === true));
});

for (const failureAt of ['lesson', 'slides']) {
  test(`generation restores loading state after ${failureAt} HTTP failure`, async t => {
    t.mock.method(console, 'error', () => {});
    globalThis.fetch = async (url, options) => {
      calls.push({ url, payload: JSON.parse(options.body) });
      if (failureAt === 'lesson' || url.endsWith('/slide/generate')) return { ok: false, status: 503 };
      return { ok: true, json: async () => ({ plan }) };
    };
    const ui = generationActions();
    await ui.handleGenerateFromAi({ topic: 'Hình lập phương', subject: 'Toán học', grade: '12' });
    assert.equal(calls.length, failureAt === 'lesson' ? 1 : 2);
    assert.equal(ui.state.isAiGenerating, false);
    assert.equal(ui.state.generationStep, '');
    assert.equal(ui.state.activeScreen, 'outline');
    assert.equal(ui.state.slideDeck, null);
    assert.equal(ui.state.lessonPlan, null);
    assert.match(alerts[0], /HTTP 503/);
  });
}

test('outline request preserves configuration and normalizes response fields', async () => {
  const config = { topic: 'Đồ thị hàm số', grade: '12', num_slides: '8', use_rag: false, model_provider: 'groq', model_id: 'chosen-model' };
  globalThis.fetch = async (url, options) => {
    calls.push({ url, payload: JSON.parse(options.body) });
    return { ok: true, json: async () => ({ outline_slides: [{ title: 'Mở đầu', key_points: ['Ý chính'] }] }) };
  };
  const ui = generationActions();
  await ui.handleGenerateOutline(config);
  assert.equal(calls[0].url, '/api/v1/presentation/outline');
  assert.equal(calls[0].payload.use_rag, false);
  assert.equal(calls[0].payload.model_id, 'chosen-model');
  assert.equal(calls[0].payload.grade, 12);
  assert.equal(ui.state.outline.outline_slides[0].id, 'outline-slide-1');
  assert.deepEqual(ui.state.outline.outline_slides[0].bullet_points, ['Ý chính']);
  assert.equal(ui.state.presentationConfig, config);
  assert.equal(ui.state.isGeneratingOutline, false);
  assert.equal(ui.state.activeScreen, 'outline');
});

test('outline preserves the draft and clears loading on network failure', async t => {
  t.mock.method(console, 'warn', () => {});
  globalThis.fetch = async () => { throw new Error('offline'); };
  const ui = generationActions();
  await ui.handleGenerateOutline({ topic: 'Đồ thị hàm số' });
  assert.equal(ui.state.outline.outline_slides.length, 1);
  assert.equal(ui.state.outline.topic, 'Hình lập phương');
  assert.match(alerts[0], /offline/);
  assert.equal(ui.state.isGeneratingOutline, false);
  assert.equal(ui.state.activeScreen, 'outline');
});
