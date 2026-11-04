---
name: add-or-update-api-endpoint
description: Add a new FastAPI route or add/modify fields on an existing request/response schema, service call, frontend client, and OpenAPI contract fixture in LessonAI-5512. Activate this skill WHENEVER creating a new endpoint under /api/v1/*, adding a field X to an existing API Y (such as LessonRequest, OutlineRequest, SlideSchema, or SlideDeckSchema), or updating app/backend/tests/fixtures/api_contract.json.
---
# Add or Update an API Endpoint (`add-or-update-api-endpoint`)

## When to Use (Khi nào dùng)
Activate this skill whenever you need to:
- Add a new HTTP endpoint under `app/backend/src/lessonai/api/routes/`.
- Add or modify a field `X` on an existing API `Y` (e.g., `LessonRequest`, `OutlineRequest`, `SlideSchema`, `SlideDeckSchema`, or `dict`-typed route payloads).
- Wire a backend route into `app/frontend/src/features/` or `app/frontend/src/shared/api/client.js`.

## Prerequisites (Điều kiện tiên quyết)
- Editable backend package installed in `app/backend/venv` (`app/backend/venv/bin/python -m pip install --no-deps -e app/backend`).
- Explicit confirmation from the user before updating `app/backend/tests/fixtures/api_contract.json` (`AGENTS.md` Boundary).

## Steps (Các bước)
1. **Check whether the target endpoint uses a Pydantic schema or raw `dict`:**
   - **Typed Pydantic endpoints** (e.g., `/api/v1/lesson-plan/generate` -> `LessonRequest`, `/api/v1/presentation/outline` -> `OutlineRequest`, `/api/v1/slide/generate` -> `LessonRequest`, `/api/v1/quality/check` -> `SlideDeckSchema`, `/api/v1/lesson-plan/export-slide` -> `SlideDeckSchema`): Edit the model in `app/backend/src/lessonai/schemas/schemas.py`, `slide_schema.py`, or `chat_schema.py`. This **changes `app.openapi()`** and requires regenerating `app/backend/tests/fixtures/api_contract.json` in Step 6.
   - **Raw `dict` endpoints** (e.g., `/api/v1/quality/approve`, `/api/v1/visuals/confirm`, `/api/v1/visuals/scene`, `/api/v1/chat/sessions`, `/api/v1/chat/interact`, `/api/v1/chat/apply-patch`, `/api/v1/slide/enrich`, `/api/v1/chart/render`): Extract and validate the field inside the service function (`lessonai/services/visual_requirements.py`, `lessonai/services/copilot.py`, `lessonai/api/routes/quality.py`) and update `docs/architecture/api-dict-contracts.md`; `app.openapi()` schema components will not change unless you replace `dict` with a Pydantic model.
2. **Forward the field explicitly through the route handler (Critical — no `**req.model_dump()` forwarding):**
   - Route handlers in `app/backend/src/lessonai/api/routes/lesson_plan.py`, `presentation.py`, and `slides.py` unpack request attributes **by explicit keyword argument** (e.g., `topic=req.topic, subject=req.subject, ...`).
   - You MUST add `new_field=req.new_field` both in the route call (`api/routes/*.py`) and in the target service signature (`app/backend/src/lessonai/services/generation/{lesson_plan,outline,slides}.py`).
3. **Register Slide/Deck fields in fingerprinting, CAS revision, and math/visual scanners (when editing `SlideSchema` or `SlideDeckSchema`):**
   - **If the new field is derived/ephemeral** (e.g., render status, cached base64 image, transient UI state):
     - Add its key name to `ignored` in `app/backend/src/lessonai/services/content_quality.py:content_snapshot()` (lines 118–119).
     - Add its key name to the ignored array in `app/frontend/src/shared/storage/projectStore.js:mutateDeck()` (line 26) and the cleanup loop (line 36) so it does not falsely increment `revision` or invalidate `review_token`.
   - **If the new field is authored math/problem text on a slide:**
     - Add its key name to `math_fields(slide)` in `app/backend/src/lessonai/services/content_quality.py` (line 13) so `evaluate_deck()` verifies its formulas.
     - Add its key name to `SOURCE_FIELDS` in `app/backend/src/lessonai/services/visual_requirements.py` (line 25) so editing the field invalidates stale visual `requirement_token` signatures.
4. **Enforce session ownership and structured error contract:**
   - If the endpoint accesses or mutates local session state, add `owner=Depends(require_owner)` from `lessonai.core.ownership`.
   - Raise `HTTPException(status_code, detail={"code": "<snake_case>", "message": "<Vietnamese message>"})`; `main.py` automatically attaches `request_id` and `X-Request-ID`.
   - If adding a new route module, include `routes.router` in `create_app()` in `app/backend/src/lessonai/main.py`.
5. **Wire the frontend payload and owner cookie helper:**
   - Pass the new field in the frontend action module (e.g., `app/frontend/src/features/generation/lessonGenerationActions.js` or `app/frontend/src/features/exports/documentExportActions.js`).
   - Use `postJson(url, payload)` from `app/frontend/src/shared/api/client.js`. If introducing a new route prefix that requires `require_owner`, add that prefix to the regex `/^\/api\/v1\/(chat|quality|visuals)/` in `app/frontend/src/shared/api/client.js`.
6. **Regenerate the OpenAPI contract fixture (when Pydantic schemas or route paths change):**
   ```bash
   app/backend/venv/bin/python -c 'import json; from pathlib import Path; from lessonai.main import app; p = Path("app/backend/tests/fixtures/api_contract.json"); spec = app.openapi(); p.write_text(json.dumps({"paths": spec["paths"], "components": spec["components"]}, ensure_ascii=False, indent=2) + "\n")'
   ```

## Reference Examples (Ví dụ mẫu)
- Explicit keyword unpacking in route handlers: `app/backend/src/lessonai/api/routes/slides.py` (`generate_slide_endpoint`) and `app/backend/src/lessonai/api/routes/lesson_plan.py` (`generate_lesson_plan_endpoint`).
- Session-protected route with structured errors: `app/backend/src/lessonai/api/routes/quality.py` (`/api/v1/quality/check`, `/api/v1/quality/approve`).
- Content snapshot & math field scanning: `app/backend/src/lessonai/services/content_quality.py` (`math_fields`, `content_snapshot`).
- Visual source fingerprinting: `app/backend/src/lessonai/services/visual_requirements.py` (`SOURCE_FIELDS`, `visual_source`).
- Frontend CAS revision & token stripping: `app/frontend/src/shared/storage/projectStore.js` (`normalizeDeck`, `mutateDeck`).
- OpenAPI contract test: `app/backend/tests/test_package_contract.py` (`test_public_api_matches_versioned_runtime_contract`).

## Verification (Cách kiểm tra đã làm đúng)
```bash
GEMINI_API_KEY= GROQ_API_KEY= OPENROUTER_API_KEY= app/backend/venv/bin/python -m pytest -c app/backend/pyproject.toml app/backend/tests/test_package_contract.py app/backend/tests/test_schema.py
node --test app/frontend/tests/project-contracts.test.js
make test-critical
```

## Common Pitfalls (Lỗi thường gặp)
- **Silent field drop at the route layer:** Adding a field to `LessonRequest` in `schemas.py` and `generate_slide_deck()` in `services/generation/slides.py` without passing `field=req.field` in `api/routes/slides.py` causes the route to silently ignore the client's value.
- **Breaking `review_token` on render/enrichment:** Adding a transient render field to `SlideSchema` without adding it to `ignored` in `content_quality.py:content_snapshot()` and `projectStore.js:mutateDeck()` causes `enrich_slide_deck_with_renders()` to change `content_fingerprint` and invalidate teacher approval tokens.
- **Forgetting `api_contract.json`:** Any Pydantic field addition on a typed route fails `test_public_api_matches_versioned_runtime_contract` until `app/backend/tests/fixtures/api_contract.json` is updated.
