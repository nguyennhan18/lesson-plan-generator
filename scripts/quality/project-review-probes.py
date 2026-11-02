"""Local, non-destructive probes for the project review of 2026-11-02.

Run with app/backend/venv/bin/python scripts/quality/project-review-probes.py --output /tmp/review.json.
No real LLM requests are made. Evaluation probes set only an in-process marker.
"""

import argparse
import builtins
import contextlib
import io
import json
import math
import os
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from unittest.mock import patch

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, required=True, help="New JSON evidence file; existing files are never overwritten")
parser.add_argument("--mode", choices=("baseline", "acceptance"), default="baseline")
args = parser.parse_args()
if args.output.exists():
    parser.error(f"Evidence already exists: {args.output}")

ROOT = Path(__file__).resolve().parents[2]
for key in ("GEMINI_API_KEY", "GROQ_API_KEY", "OPENROUTER_API_KEY"):
    os.environ[key] = ""
os.environ.setdefault("MPLCONFIGDIR", "/tmp/lesson-review-mpl")

output = {}
with contextlib.redirect_stdout(io.StringIO()):
    from fastapi.testclient import TestClient
    from lessonai.main import app
    from docx import Document
    from docx.oxml import OxmlElement
    from pptx import Presentation
    from lessonai.parsers.docx_parser import parse_docx
    from lessonai.exporters.slide_exporter import export_slide_deck_to_pptx
    from lessonai.rag.curriculum_registry import infer_lesson_id
    from lessonai.services.chat import handle_copilot_chat, session_manager
    from lessonai.services.geometry import calculate_parametric_geometry
    from lessonai.services.validation import audit_slide_deck, latex_to_sympy_expr
    from lessonai.schemas.slide_schema import SlideSchema, SlideDeckSchema

    client = TestClient(app)
    marker_expression = (
        "(__import__('builtins').setattr(__import__('builtins'), "
        "'lessonReviewMarker', 731), x)[1]"
    )
    response = client.post(
        "/api/v1/chart/render",
        json={"kind": "function_plot", "expression": marker_expression},
    )
    output["backend_expression_evaluation"] = {
        "status": response.status_code,
        "error": response.json() if response.headers.get("content-type", "").startswith("application/json") else None,
        "in_process_marker_set": getattr(builtins, "lessonReviewMarker", None) == 731,
    }
    if hasattr(builtins, "lessonReviewMarker"):
        delattr(builtins, "lessonReviewMarker")
    latex_to_sympy_expr(marker_expression)
    output["validator_expression_evaluation"] = {
        "in_process_marker_set": getattr(builtins, "lessonReviewMarker", None) == 731,
    }
    if hasattr(builtins, "lessonReviewMarker"):
        delattr(builtins, "lessonReviewMarker")

    deck = {
        "presentation_title": "Nguyên hàm",
        "subject": "Toán học",
        "grade": 12,
        "slides": [
            {"slide_index": 1, "title": "Mở đầu", "bullet_points": []},
            {"slide_index": 2, "title": "Họ nguyên hàm", "bullet_points": ["Tìm nguyên hàm của $2x$."]},
        ],
    }
    sid = "project-review-isolated-731"
    with patch("lessonai.llm.gateway.llm_gateway.generate_text", return_value="Nguyên hàm của 2x là x^2 + C."):
        reply = handle_copilot_chat(
            sid, "Giải thích slide này đơn giản hơn", current_slide_index=1, slide_deck=deck, grade=12
        )
    output["copilot_patch"] = {
        "response": reply.ai_response,
        "patch": reply.suggested_patch.model_dump() if reply.suggested_patch else None,
    }
    history = client.get("/api/v1/chat/history/" + sid)
    output["unauthenticated_history"] = {
        "status": history.status_code,
        "message_count": len(history.json()["history"]),
    }
    session_manager.clear_session(sid)

    new_slide = {
        "slide_number": 3,
        "title": "3. Nội dung bổ sung mới",
        "activity_type": "LUYỆN TẬP & CỦNG CỐ",
        "layout": "IMAGE_TEXT",
        "bullet_points": ["Nhập các ý chính trọng tâm tại đây."],
        "main_definition_latex": "",
        "teacher_note": "Ghi chú dành riêng cho giáo viên.",
        "has_3d": False,
    }
    edited_deck = {**deck, "slides": [*deck["slides"], new_slide]}
    response = client.post("/api/v1/lesson-plan/export-slide", json=edited_deck)
    output["editor_add_slide_export"] = {
        "status": response.status_code,
        "detail": response.json().get("detail") if response.headers.get("content-type", "").startswith("application/json") else None,
    }

    response = client.post("/api/v1/lesson-plan/export-docx", json={"plan": None})
    is_word = response.headers.get("content-type", "").startswith("application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    exported_text = ""
    if is_word:
        exported = Document(io.BytesIO(response.content))
        exported_text = " ".join(p.text for p in exported.paragraphs)
    output["invalid_word_export"] = {
        "status": response.status_code,
        "filename": response.headers.get("content-disposition"),
        "error": None if is_word else response.json(),
        "contains_grade10": "LỚP 10" in exported_text,
        "contains_unrequested_inequality_lesson": "HỆ BẤT PHƯƠNG TRÌNH" in exported_text,
    }

    marker = "SOLUTIONMARKERXYZ"
    ppt = Presentation(export_slide_deck_to_pptx({**deck, "slides": [{
        "slide_index": 1, "type": "EXERCISE_SLIDE", "layout": "TWO_COLUMN",
        "title": "Ví dụ", "bullet_points": ["Đề bài"], "worked_solution_steps": [marker],
    }]}))
    visible_text = " ".join(s.text for s in ppt.slides[0].shapes if s.has_text_frame)
    notes_text = ppt.slides[0].notes_slide.notes_text_frame.text
    output["pptx_solution_preservation"] = {
        "solution_visible": marker in visible_text,
        "solution_in_notes": marker in notes_text,
    }

    output["lesson_inference"] = {
        topic: infer_lesson_id(topic)
        for topic in ("Ứng dụng hình học của tích phân", "Ứng dụng tích phân tính diện tích hình phẳng")
    }
    geometry = calculate_parametric_geometry("pyramid_square", 4, 4)
    apex = geometry.vertices["S"]
    edges = {
        key: round(math.dist(apex.to_tuple(), geometry.vertices[key].to_tuple()), 4)
        for key in ("A", "B", "C", "D")
    }
    output["regular_pyramid_geometry"] = {
        "apex": apex.model_dump(), "lateral_edges": edges,
        "all_lateral_edges_equal": len(set(edges.values())) == 1,
    }

    output["worked_solution_audit"] = audit_slide_deck({"slides": [{
        "slide_index": 1, "title": "Bài giải", "worked_solution_steps": ["$1+1=3$"],
    }]}).model_dump()
    parsed = SlideSchema.model_validate({
        "slide_index": 1, "title": "Probe", "layout": "TWO_COLUMN",
        "stage": "knowledge_formation", "key_message": "marker", "table_data": {"rows": [["x", "0"]]},
        "source_refs": [{"source": "slides_kntt12", "slide_id": "M12-C1-B1-S05"}],
    })
    quiz = SlideSchema.model_validate({
        "slide_index": 1, "title": "Quiz", "layout": "QUIZ_OPTION",
        "quiz_options": [{"label": "A", "text": "A", "is_correct": True}],
    })
    output["schema_acceptance"] = {
        "empty_solution_accepted": not parsed.worked_solution_steps,
        "empty_deck_accepted": len(SlideDeckSchema(presentation_title="Probe", subject="Toán học", grade=12, slides=[]).slides) == 0,
        "one_option_quiz_accepted": len(quiz.quiz_options) == 1,
        "discarded_fields": [key for key in ("stage", "key_message", "table_data") if key not in parsed.model_dump()],
        "legacy_source_ref_after_parse": parsed.source_refs[0].model_dump(),
    }

    document = Document()
    paragraph = document.add_paragraph("Công thức: ")
    equation = OxmlElement("m:oMath")
    run = OxmlElement("m:r")
    text = OxmlElement("m:t")
    text.text = "x+1"
    run.append(text)
    equation.append(run)
    paragraph._p.append(equation)
    stream = io.BytesIO()
    document.save(stream)
    parsed_doc = parse_docx(stream.getvalue())
    output["docx_formula_ingestion"] = {
        "omml_exists_in_source": "x+1" in document.element.xml,
        "formula_in_parsed_raw_text": "x+1" in parsed_doc["raw_text"],
        "parsed_text": parsed_doc["raw_text"],
    }

    grades = "STT,Ho ten,Diem\n1,A,2\n2,B,4\n3,C,8\n4,D,10\n"
    response = client.post(
        "/api/v1/ingest/classify-grades", files={"file": ("review.csv", grades.encode(), "text/csv")}
    )
    output["analytics_api_response"] = response.json()

    # Start jobs together. Instrument the full figure lifetime without placing a
    # barrier inside the render lock (which would deadlock a correct renderer).
    import time
    from matplotlib.figure import Figure
    import lessonai.exporters.graph_generator as graph_module
    pyplot = graph_module.plt
    original_subplots = pyplot.subplots
    original_savefig = Figure.savefig
    original_close = pyplot.close
    barrier = threading.Barrier(2)
    observation_lock = threading.Lock()
    thread_state = threading.local()
    active_figures = set()
    max_active = [0]
    observations = []

    def tracked_subplots(*args, **kwargs):
        with observation_lock:
            figure, axes = original_subplots(*args, **kwargs)
            thread_state.expected_figure = id(figure)
            active_figures.add(id(figure))
            max_active[0] = max(max_active[0], len(active_figures))
        time.sleep(0.03)
        return figure, axes

    def tracked_savefig(figure, *args, **kwargs):
        with observation_lock:
            observations.append({
                "expected_figure": thread_state.expected_figure,
                "actual_saved_figure": id(figure),
                "matches": thread_state.expected_figure == id(figure),
            })
        return original_savefig(figure, *args, **kwargs)

    def tracked_close(figure=None):
        try:
            return original_close(figure)
        finally:
            with observation_lock:
                active_figures.discard(id(figure))

    def render_worker(index):
        barrier.wait(timeout=10)
        try:
            content = graph_module.generate_math_plot({
                "kind": "chart", "labels": ["A", "B"], "values": [index, 3 * index],
                "chart_title": f"review-{index}",
            }, figsize=(2, 2))
            return {"bytes": len(content), "png": content.startswith(b"\x89PNG")}
        except Exception as error:
            return {"error": type(error).__name__, "message": str(error)}

    with patch.object(pyplot, "subplots", tracked_subplots), patch.object(Figure, "savefig", tracked_savefig), patch.object(pyplot, "close", tracked_close):
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(render_worker, (1, 2)))
    from lessonai.utils.temp_file_cleaner import cleanup_memory_and_figures
    held_figure = pyplot.figure()
    try:
        cleanup_memory_and_figures()
        cleanup_preserves_other_job = pyplot.fignum_exists(held_figure.number)
    finally:
        pyplot.close(held_figure)
    output["concurrent_matplotlib"] = {
        "observations": observations, "results": results,
        "max_active_figures": max_active[0],
        "unreleased_job_figures": len(active_figures),
        "cleanup_preserves_other_job": cleanup_preserves_other_job,
        "wrong_figure_observed": any(not item["matches"] for item in observations),
    }

output["scope"] = "Local API and data-contract probes; no live LLM, no external data access, no destructive system API calls."
output["measured_at"] = datetime.now(timezone.utc).isoformat()
output["date"] = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).date().isoformat()
output["mode"] = args.mode
output["acceptance_scope"] = "M0 containment only; not closure of R01/R02/R03/R05/R07/R12"
output["m0_checks"] = {
    "backend_marker_rejected": not output["backend_expression_evaluation"]["in_process_marker_set"] and output["backend_expression_evaluation"]["status"] in (400, 422, 503),
    "validator_marker_rejected": not output["validator_expression_evaluation"]["in_process_marker_set"],
    "no_sample_patch": output["copilot_patch"]["patch"] is None,
    "no_substitute_word": output["invalid_word_export"]["status"] in (400, 422) and output["invalid_word_export"]["filename"] is None,
    "render_serialized": max_active[0] == 1 and len(observations) == 2 and all(item["matches"] for item in observations) and all(item.get("png") for item in results) and not active_figures,
    "cleanup_preserves_other_job": cleanup_preserves_other_job,
}
args.output.parent.mkdir(parents=True, exist_ok=True)
with args.output.open("x", encoding="utf-8") as destination:
    json.dump(output, destination, ensure_ascii=False, indent=2)
print(json.dumps({k: v for k, v in output.items() if k != "analytics_api_response"}, ensure_ascii=False, indent=2))

if args.mode == "acceptance" and not all(output["m0_checks"].values()):
    raise SystemExit(1)
