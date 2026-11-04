import assert from 'node:assert/strict';
import { test } from 'node:test';
import { runInNewContext } from 'node:vm';
import { createRequire } from 'node:module';
import { buildSync } from 'esbuild';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { createDocumentExportActions } from '../src/features/exports/documentExportActions.js';

const require = createRequire(import.meta.url);
const plotterBundle = buildSync({
  entryPoints: [new URL('../src/shared/math/FunctionPlotter.jsx', import.meta.url).pathname],
  bundle: true, write: false, platform: 'node', format: 'cjs', external: ['react']
}).outputFiles[0].text;

test('plotter keeps untrusted input as text and never evaluates it locally', () => {
  const module = { exports: {} };
  const sandbox = { module, exports: module.exports, require };
  runInNewContext(plotterBundle, sandbox, { timeout: 1000, contextCodeGeneration: { strings: false, wasm: false } });
  const expression = '(globalThis.lessonReviewMarker = 731, x)';
  const markup = renderToStaticMarkup(React.createElement(module.exports.default, { defaultExpr: expression }));
  assert.equal(sandbox.lessonReviewMarker, undefined);
  assert.match(markup, /Đối chiếu công thức/);
  assert.ok(markup.includes(expression));
  assert.match(markup, /disabled/);
  assert.doesNotMatch(markup, /<canvas|<img/);
});

test('M1 missing expression never invents a default polynomial or a graph', () => {
  const module = { exports: {} };
  runInNewContext(plotterBundle, { module, exports: module.exports, require }, { timeout: 1000 });
  for (const props of [{}, { defaultExpr: '' }]) {
    const markup = renderToStaticMarkup(React.createElement(module.exports.default, props));
    assert.match(markup, /Chưa có công thức để vẽ/);
    assert.doesNotMatch(markup, /x\*\*2|Parabol|<canvas|<img|<code/);
  }
});

for (const action of ['handleExportDocx', 'handleExportPptx', 'handleExportDualPackage']) {
  for (const responseStatus of [503, 200]) {
    test(`M0 ${action} reads JSON errors at HTTP ${responseStatus} and preserves the draft`, async () => {
      const deck = { presentation_title: 'Nguyên hàm', slides: [{ slide_index: 1, title: 'Giữ nguyên', bullet_points: ['2x'] }] };
      const original = structuredClone(deck);
      const alerts = [];
      let downloads = 0;
      const replacements = {
        fetch: async () => ({
          ok: responseStatus === 200, status: responseStatus,
          headers: { get: () => 'application/json; charset=utf-8' },
          json: async () => ({ detail: { code: 'expression_processing_temporarily_unavailable', message: 'Đồ thị đang tạm ngắt' } }),
          blob: async () => { throw new Error('JSON must not be read as an Office file'); }
        }),
        alert: message => alerts.push(message),
        document: { createElement: () => { downloads++; throw new Error('Unexpected download'); } },
        window: { URL: { createObjectURL: () => { downloads++; throw new Error('Unexpected URL'); } } }
      };
      const previous = Object.fromEntries(Object.keys(replacements).map(key => [key, Object.getOwnPropertyDescriptor(globalThis, key)]));
      Object.assign(globalThis, replacements);
      try {
        const actions = createDocumentExportActions({
          lessonPlan: { lesson_title: 'Nguyên hàm' }, slideDeck: deck, currentSlide: 0,
          threeCanvasCaptureRef: { current: null }
        });
        await actions[action]();
        assert.equal(downloads, 0);
        assert.equal(alerts.length, 1);
        assert.match(alerts[0], /Đồ thị đang tạm ngắt/);
        assert.deepEqual(deck, original);
      } finally {
        for (const [key, descriptor] of Object.entries(previous)) {
          if (descriptor) Object.defineProperty(globalThis, key, descriptor);
          else delete globalThis[key];
        }
      }
    });
  }
}
