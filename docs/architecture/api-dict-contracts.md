# Untyped `dict` Endpoint Payload & Error Contracts (`LessonAI-5512`)

Runtime inspection of `lessonai.main.app.routes` (`_IncludedRouter.original_router.routes` + `inspect.signature`) shows **42 mounted routes** (`4` built-in FastAPI docs routes and **38** application endpoints). Among the **38** application endpoints, **22** have parameters that are not pure Pydantic `BaseModel` subclasses:
- **11 non-JSON-dict endpoints** where non-Pydantic parameters are standard FastAPI constructs (not contract defects): `Request`/`Response` (`core/ownership.py:21`), `Depends(require_owner)` (`quality.py:40, 73, 78`, `system.py:43, 55`), query primitives (`system.py:21`), path strings (`chat.py:27, 31`), and multipart `UploadFile` (`ingest.py:25, 29`).
- **11 JSON body endpoints** typed as `dict` / `Dict[str, Any]` (`10` pure `dict`/`Dict[str, Any]` + `1` `Union[Dict[str, Any], LessonPlanSchema]` at `exports.py:16`), grouped by validation mechanism:
  1. **Partially typed on route (`1/11`):** `POST /api/v1/lesson-plan/export-docx` (`exports.py:16`, `Union[Dict[str, Any], LessonPlanSchema]`), which validates `LessonPlanSchema` and `SlideDeckSchema` inside `exports.py:29, 32`.
  2. **Request model exists in `schemas.py` but is unbound on route (`2/11`):** `POST /api/v1/chat/interact` (`chat.py:16`, `ChatInteractRequest` in `schemas.py:362` unused) and `POST /api/v1/chat/apply-patch` (`chat.py:36`, `ApplyPatchRequest` in `schemas.py:398` unused); both validate inner `slide_deck` via `SlideDeckSchema.model_validate` in `copilot.py:70, 114` and check outer keys manually.
  3. **No top-level request wrapper in `lessonai/schemas/*`, but inner payload validated via `BaseModel` (`3/11`):** `POST /api/v1/quality/approve` (`quality.py:45`, calls `SlideDeckSchema.model_validate(payload["deck"])` at line `50`), `POST /api/v1/chat/sessions` (`chat.py:8`, calls `SlideDeckSchema.model_validate` at `copilot.py:36`), and `POST /api/v1/lesson-plan/export-dual-package` (`exports.py:92`, validates `LessonPlanSchema`/`SlideDeckSchema` at `dual_package_exporter.py:187, 200`).
  4. **No request wrapper in `lessonai/schemas/*`; validated via custom service functions (`5/11`):** `POST /api/v1/visuals/confirm` (`visuals.py:10`), `POST /api/v1/visuals/scene` (`visuals.py:18`), `POST /api/v1/chart/render` (`slides.py:49`), `POST /api/v1/slide/enrich` (`slides.py:40`), and `POST /api/v1/validation/audit-deck` (`validation.py:7`).

All errors pass through the global exception handlers in `app/backend/src/lessonai/main.py:55-70`, which wrap responses as `{"detail": {..., "request_id": "<uuid>"}}` with header `X-Request-ID`.

---

## 1. Content Quality & Approval (`app/backend/src/lessonai/api/routes/quality.py`)

### `POST /api/v1/quality/approve`
- **Auth:** Requires `lessonai_owner` cookie (`Depends(require_owner)` in `app/backend/src/lessonai/api/routes/quality.py:46`).
- **Request Payload (`payload: dict`, `quality.py:46-59`):**
  ```json
  {
    "acknowledged": true,
    "deck": { "...SlideDeckSchema fields..." },
    "reviewed_issue_ids": ["<warning_issue_id_1>", "..."],
    "content_fingerprint": "<sha256_from_evaluate_deck>"
  }
  ```
  - `acknowledged` (`bool`, required): Must be strictly `true` (`payload.get("acknowledged") is not True` -> `422`, `quality.py:47-48`).
  - `deck` (`dict`, required): Validated via `SlideDeckSchema.model_validate(payload["deck"])` (`quality.py:50`).
  - `reviewed_issue_ids` (`list[str]`, required): Must match `sorted(issue["issue_id"] for issue in report["issues"] if issue["severity"] == "warning")` (`quality.py:56-59`).
  - `content_fingerprint` (`str`, required): Must match `report["content_fingerprint"]` (`quality.py:58`).
- **Response (`200 OK`, `quality.py:65`):**
  ```json
  {
    "review_token": "<base64url_payload>.<hmac_sha256_hex>",
    "report": {
      "status": "ready",
      "review_method": "teacher_confirmation_for_this_revision",
      "review_record": {
        "method": "issue_review_v1",
        "reviewed_issue_ids": ["..."],
        "content_fingerprint": "<sha256>",
        "reviewer": "<16_hex_chars>",
        "confirmed_at": 1793817600
      },
      "issues": [],
      "checks": [],
      "content_fingerprint": "<sha256>",
      "scope": "Đẳng thức số học; hình có xác nhận dữ kiện. Văn xuôi và sư phạm cần giáo viên duyệt."
    }
  }
  ```
- **Error Statuses & Codes (`quality.py:47-59`):**
  - `401` (`session_expired`): Missing or expired `lessonai_owner` cookie (`app/backend/src/lessonai/core/ownership.py:16`).
  - `422` (`http_422`): `acknowledged` is not `true` or `deck` fails `SlideDeckSchema` validation (`quality.py:48, 52`).
  - `409` (`content_blocked`): `evaluate_deck(deck)["status"] == "blocked"` (`quality.py:55`).
  - `409` (`review_incomplete`): `reviewed_issue_ids` does not match warning issue IDs or `content_fingerprint` mismatches (`quality.py:59`).

---

## 2. Visual Requirement Confirmation & 3D Scene (`app/backend/src/lessonai/api/routes/visuals.py`)

### `POST /api/v1/visuals/confirm`
- **Auth:** Requires `lessonai_owner` cookie (`Depends(require_owner)` in `app/backend/src/lessonai/api/routes/visuals.py:11`).
- **Request Payload (`data: dict`, validated in `app/backend/src/lessonai/services/visual_requirements.py:36-76`):**
  - Common required keys (`visual_requirements.py:38-43`):
    - `deck_id` (`str`, non-empty)
    - `slide_id` (`str`, non-empty)
    - `source` (`dict`): Slide fields used to compute `source_fingerprint` over `SOURCE_FIELDS` (`title`, `subtitle`, `bullet_points`, `question`, `main_definition_latex`, `math_formulas`, `worked_solution_steps`, `blocks`, `table_data`, `source_refs` — `visual_requirements.py:25-33`).
    - `kind` (`str`): One of `"function_plot"`, `"arithmetic_sequence"`, `"inequality_system"`, `"geometry"`.
  - Kind-specific keys:
    1. `kind == "function_plot"` (`visual_requirements.py:44-61`):
       - `expression` (`str`): Must parse under `parse_expression()` (`app/backend/src/lessonai/services/math_expression.py`).
       - `operation` (`str`, default `"function"`): `"function"` or `"derivative"`.
       - `x_min`, `x_max` (`float`): `-1e6 <= x_min < x_max <= 1e6`.
       - `y_min`, `y_max` (`float`, optional): If either is provided, both must be provided and `-1e6 <= y_min < y_max <= 1e6`.
    2. `kind == "arithmetic_sequence"` (`app/backend/src/lessonai/services/discrete_visuals.py:13-16`):
       - `first_term` (`float`, `|v| <= 1e6`), `common_difference` (`float`, `|v| <= 1e6`), `count` (`int`, `1 <= count <= 200`).
    3. `kind == "inequality_system"` (`app/backend/src/lessonai/services/discrete_visuals.py:17-30`):
       - `constraints` (`list[dict]`, length `1..12`): Each item requires `a`, `b`, `c` (`float`, `a != 0` or `b != 0`) and `relation` in `("<=", ">=", "<", ">")`.
       - `x_min`, `x_max`, `y_min`, `y_max` (`float`, `x_min < x_max` and `y_min < y_max`).
    4. `kind == "geometry"` (`app/backend/src/lessonai/services/geometry_scene.py:8-21`):
       - `polyhedron_type` (`str`): Must be in `KINDS = {"cube", "square_pyramid_regular", "square_pyramid_at_a"}` (`geometry_scene.py:5`).
       - `base_edge` (`float`, `0 < a <= 1e6`).
       - `height` (`float`, `0 < h <= 1e6`; optional for `"cube"`, but if provided must equal `base_edge`).
- **Response (`200 OK`, `visual_requirements.py:75-76`):**
  - `{"requirement_token": "<base64url>.<hmac_hex>", "requirement": {...}, "spec_fingerprint": "<sha256>"}`.
- **Error Statuses & Codes (`visuals.py:14-15`):**
  - `422` (`visual_invalid`): Missing/invalid parameters or unsupported `kind` / `polyhedron_type`.

### `POST /api/v1/visuals/scene`
- **Auth:** None (validates HMAC `requirement_token` instead; `app/backend/src/lessonai/api/routes/visuals.py:18-24`).
- **Request Payload (`spec: dict`):**
  - Must include `deck_id`, `slide_id`, `polyhedron_type`, `base_edge`, `height`, `source_fingerprint`, and a valid, non-expired `requirement_token` matching those exact fields (`visual_requirements.py:79-100`).
- **Response (`200 OK`, `geometry_scene.py:49-51`):**
  - `{"spec": ..., "vertices": ..., "edges": ..., "faces": ..., "measurements": ..., "altitude_foot": ..., "scene_fingerprint": ..., "status": "constraints_checked"}`.
- **Error Statuses & Codes (`visuals.py:23-24`):**
  - `409` (`visual_needs_review`): Missing, expired, or mismatched `requirement_token` / spec.

---

## 3. AI Copilot Chat & Live Slide Patching (`app/backend/src/lessonai/api/routes/chat.py`, `services/copilot.py`)

All `/api/v1/chat/*` routes require `Depends(require_owner)` (`chat.py:9, 17, 28, 32, 37`).

| Endpoint | Request `dict` Keys | Validation & Limits (`copilot.py`) | Error Statuses |
|---|---|---|---|
| `POST /api/v1/chat/sessions` (`chat.py:8-14`) | `slide_deck` (`SlideDeckSchema` dict) | Max 64 active sessions in memory (`copilot.py:35`); 1h TTL (`expires = now + 3600`, `copilot.py:39`). | `401` (`session_expired`), `422` (`http_422`), `503` (`http_503` when `>= 64` sessions) |
| `POST /api/v1/chat/interact` (`chat.py:16-25`) | `session_id` (`str`), `slide_deck` (`dict`), `slide_id` (`str`), `user_message` (`str`, `1..8000` chars) | Serialized `slide_deck` must be `<= 1 MiB` (`copilot.py:67`); `(deck_id, project_id)` must match session (`copilot.py:71`); LLM `changes` keys must be a subset of `ALLOWED = {"title", "subtitle", "bullet_points", "worked_solution_steps", "main_definition_latex", "math_formulas", "teacher_note", "quiz_options", "layout"}` (`copilot.py:17, 86`). | `404` (session/project mismatch), `413` (deck `> 1 MiB`), `422` (invalid message/slide/patch), `503` (`chat_unavailable` on LLM error) |
| `POST /api/v1/chat/apply-patch` (`chat.py:36-43`) | `proposal_id` (`str`), `slide_deck` (`dict`), `acknowledged` (`bool`, must be `true`) | Compare-and-swap (CAS): `fingerprint(content_snapshot(deck)) == proposal["base_hash"]` and `deck["revision"] == proposal["base_revision"]` (`copilot.py:121`). Idempotent if already applied to the same state (`copilot.py:117-120`). Strips `chart_image_base64`, `formula_image_base64`, `snapshot_3d_base64`, `requirement_token`, and `review_token` (`copilot.py:129-135`). | `404` (missing/expired proposal), `409` (CAS revision/hash conflict), `422` (`acknowledged != True`) |

---

## 4. Slide Enrichment, Chart Render, Deck Audit & Package Exports (`slides.py`, `validation.py`, `exports.py`)

- **`POST /api/v1/slide/enrich` (`app/backend/src/lessonai/api/routes/slides.py:40-46`):**
  - Accepts `deck: dict` (`SlideDeckSchema`-compatible dict), clears stale cached images (`chart_image_base64`, `formula_image_base64`, `chart_render_status`, `chart_render_error`), and populates fresh renders via `enrich_slide_deck_with_renders(deck)` (`app/backend/src/lessonai/services/rendering.py`).
- **`POST /api/v1/chart/render` (`app/backend/src/lessonai/api/routes/slides.py:49-66`):**
  - Accepts `spec: dict` containing a confirmed `requirement_token` (`checked_requirement(spec)` in `app/backend/src/lessonai/exporters/graph_generator.py:32, 38`). Returns `image/png` bytes or `409` (`visual_needs_review`), `422` (`expression_invalid` / `chart_invalid`), `503` (`job_busy`), `504` (`job_timeout`).
- **`POST /api/v1/validation/audit-deck` (`app/backend/src/lessonai/api/routes/validation.py:7-20`, `app/backend/src/lessonai/services/validation.py:1001-1048`):**
  - Accepts `deck_payload: dict` containing either `{slides: [...]}` directly or `{slide_deck: {slides: [...]}}` plus optional `"use_ai_proofreader": bool` (`default: False`, `validation.py:1011-1020`). Returns `DeckAuditResponse` (`is_clean`, `total_warnings`, `warnings: List[SlideWarningItem]`).
- **`POST /api/v1/lesson-plan/export-docx` (`app/backend/src/lessonai/api/routes/exports.py:16-60`):**
  - Accepts `payload: Union[Dict[str, Any], LessonPlanSchema]` — either a direct `LessonPlanSchema` payload or a wrapper `dict` `{"plan": <LessonPlanSchema>, "slide_deck": <optional SlideDeckSchema>}` (also accepts alias `"lesson_plan"`).
- **`POST /api/v1/lesson-plan/export-dual-package` (`app/backend/src/lessonai/api/routes/exports.py:92-130`):**
  - Accepts `payload: Dict[str, Any]` with `"plan"` (or `"lesson_plan"`) and/or `"slide_deck"` (or `"deck"`). Returns `application/zip` with headers `X-Dual-Package-Docs-Count`, `X-Dual-Package-SHA256`, `X-Docx-SHA256`, and `X-Pptx-SHA256`.
