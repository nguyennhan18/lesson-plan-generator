# SKILL.md — Modular Skill Index (`LessonAI-5512`)

All recurring agent workflows are packaged as standalone modular skills under `.claude/skills/<skill-name>/SKILL.md` (with no duplicated content in this root index):

| Skill Name | Path | When to Activate |
|---|---|---|
| `add-or-update-api-endpoint` | `.claude/skills/add-or-update-api-endpoint/SKILL.md` | Activate WHENEVER creating a new endpoint under `/api/v1/*`, adding/modifying a field `X` on an existing API `Y` (`LessonRequest`, `OutlineRequest`, `SlideSchema`, `SlideDeckSchema`, or `dict` routes; see `docs/architecture/api-dict-contracts.md`), or updating `app/backend/tests/fixtures/api_contract.json`. |
| `prepare-and-approve-rag-sources` | `.claude/skills/prepare-and-approve-rag-sources/SKILL.md` | Activate WHENEVER inspecting or updating curriculum files in `app/backend/data/`, running `deck_lint.py`, staging packaged data (`scripts/data/build_packaged_data.py`), or preparing/approving hash-locked source manifests (`scripts/quality/prepare-source-review.py`, `app/backend/data/reviewed_sources.json`). |
| `add-verified-visual-or-geometry-spec` | `.claude/skills/add-verified-visual-or-geometry-spec/SKILL.md` | Activate WHENEVER modifying `math_expression.py`, `math_worker.py`, `geometry_scene.py`, `visual_requirements.py`, `graph_generator.py`, or frontend 2D plotter / 3D Three.js visual components. |
| `run-remediation-acceptance-and-e2e-audit` | `.claude/skills/run-remediation-acceptance-and-e2e-audit/SKILL.md` | Activate WHENEVER running verification suites (`make test-critical`, `make test-portable`, `make audit-acceptance`, `make test-e2e`) before a commit/PR or collecting append-only remediation evidence. |
