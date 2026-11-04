---
name: add-verified-visual-or-geometry-spec
description: Add or update mathematical graph plotting, discrete visuals, or 3D spatial geometry rendering across backend workers, visual confirmation tokens, PPTX export, and React studio components. Activate this skill WHENEVER modifying math_expression.py, math_worker.py, geometry_scene.py, visual_requirements.py, graph_generator.py, or frontend plotter/3D components.
---
# Add or Update a Verified Visual or Geometry Spec (`add-verified-visual-or-geometry-spec`)

## When to Use (Khi nào dùng)
Activate this skill whenever extending or fixing 2D function plots, discrete sequences/inequalities, or 3D polyhedron types across the backend verification/rendering pipeline and frontend canvas/export workflow.

## Prerequisites (Điều kiện tiên quyết)
- Understanding of the two-step teacher confirmation contract: visuals must first be confirmed via `POST /api/v1/visuals/confirm` (which issues an HMAC `requirement_token` bound to `deck_id`, `slide_id`, `source_fingerprint`, and normalized spec) before rendering or exporting.

## Steps (Các bước)
1. **Update parser or scene normalization:**
   - For algebraic/analytic expressions: update `app/backend/src/lessonai/services/math_expression.py` (pure AST parser, no SymPy/execution on import) and `app/backend/src/lessonai/services/math_worker.py` (executed inside `lessonai/core/jobs.py` `spawn` subprocess with deadline).
   - For 3D polyhedra: update `KINDS`, `normalize_spec()`, and `build_scene()` in `app/backend/src/lessonai/services/geometry_scene.py` so vertex coordinates, edge lengths, and volumes are computed from a single canonical coordinate set.
2. **Update requirement validation and token binding:**
   - Update `app/backend/src/lessonai/services/visual_requirements.py` (`confirm_requirement`, `checked_requirement`, `checked_slide_requirement`) so the spec is validated and cryptographically bound to `deck_id`, `slide_id`, and `source_fingerprint` (`fingerprint(visual_source(slide))`).
3. **Ensure thread/process-safe Matplotlib rendering:**
   - Wrap any Matplotlib figure rendering with `@serialized_render` from `app/backend/src/lessonai/core/render_runtime.py` (as done in `geometry_scene.py:_draw_scene` and `exporters/graph_generator.py`), and always close the task's own `fig` inside a `finally:` block.
4. **Wire into PPTX export:**
   - Update `app/backend/src/lessonai/services/rendering.py` and `app/backend/src/lessonai/exporters/slide_exporter.py` so confirmed visuals render per-slide without leaking cached images across slides or decks.
5. **Update frontend components and invalidation rules:**
   - Update `app/frontend/src/shared/math/FunctionPlotter.jsx`, `DataChartVisual.jsx`, or `app/frontend/src/features/geometry/GeometryVisual.jsx` / `ThreeCanvas.jsx`.
   - Ensure `mutateDeck()` in `app/frontend/src/shared/storage/projectStore.js` strips stale `requirement_token`, `chart_image_base64`, and `snapshot_3d_base64` whenever slide text or spec parameters change.

## Reference Examples (Ví dụ mẫu)
- Bounded AST grammar: `app/backend/src/lessonai/services/math_expression.py`.
- Subprocess worker execution: `app/backend/src/lessonai/core/jobs.py` and `app/backend/src/lessonai/services/math_worker.py`.
- Canonical 3D geometry & Matplotlib renderer: `app/backend/src/lessonai/services/geometry_scene.py`.
- Visual confirmation routes: `app/backend/src/lessonai/api/routes/visuals.py`.
- Client token invalidation on edit: `app/frontend/src/shared/storage/projectStore.js` (`mutateDeck`).

## Verification (Cách kiểm tra đã làm đúng)
```bash
GEMINI_API_KEY= GROQ_API_KEY= OPENROUTER_API_KEY= app/backend/venv/bin/python -m pytest -c app/backend/pyproject.toml app/backend/tests/test_remediation_runtime.py app/backend/tests/test_day11_3d_geometry.py app/backend/tests/test_day14_snapshot_to_pptx.py
node --test app/frontend/tests/critical-regressions.test.js
```

## Common Pitfalls (Lỗi thường gặp)
- **Using `eval()` or unguarded SymPy in the main process:** All symbolic/numeric evaluation must run through `math_expression.py` + `jobs.py` worker to prevent ReDoS/CPU exhaustion.
- **Calling `plt.close('all')` during concurrent requests:** Never close all Matplotlib figures globally inside a request handler; close only the local `fig` under `@serialized_render`.
- **Reusing legacy `/api/v1/geometry/*` endpoints:** Those routes in `app/backend/src/lessonai/api/routes/geometry.py` intentionally return HTTP `410 Gone`; always use `/api/v1/visuals/confirm` and `/api/v1/visuals/scene`.
