import base64
from lessonai.exporters.graph_generator import generate_math_plot, is_plottable, expression_chart_is_disabled
from lessonai.core.feature_availability import EXPRESSION_UNAVAILABLE_MESSAGE
from lessonai.exporters.slide_exporter import render_latex_to_bytes


def enrich_slide_deck_with_renders(deck_dict: dict) -> dict:
    """
    Sinh trước ảnh đồ thị Matplotlib và ảnh công thức LaTeX (dưới dạng Base64 Data URL)
    cho từng slide để Front-end hiển thị CHÍNH XÁC 1:1 như khi tải file PowerPoint về.
    """
    slides = deck_dict.get("slides", [])
    for slide in slides:
        # 1. Đồ thị Matplotlib
        chart_spec = slide.get("chart_spec")
        slide.pop("chart_image_base64", None)
        slide.pop("chart_render_error", None)
        slide["chart_render_status"] = "not_requested"
        if expression_chart_is_disabled(chart_spec):
            slide["chart_render_status"] = "temporarily_unavailable"
            slide["chart_render_error"] = EXPRESSION_UNAVAILABLE_MESSAGE
        if chart_spec and is_plottable(chart_spec):
            try:
                png_bytes = generate_math_plot(chart_spec, figsize=(4.6, 3.6))
                b64 = base64.b64encode(png_bytes).decode("utf-8")
                slide["chart_image_base64"] = f"data:image/png;base64,{b64}"
                slide["has_chart"] = True
                slide["chart_render_status"] = "rendered"
            except Exception as e:
                print(f"Lỗi render đồ thị cho slide preview: {e}")
                slide["has_chart"] = False
                slide["chart_render_status"] = "error"
        else:
            slide["has_chart"] = False

        # 2. Công thức toán LaTeX
        main_latex = slide.get("main_definition_latex")
        slide.pop("formula_image_base64", None)
        if main_latex:
            try:
                formula_png = render_latex_to_bytes(main_latex)
                b64_f = base64.b64encode(formula_png).decode("utf-8")
                slide["formula_image_base64"] = f"data:image/png;base64,{b64_f}"
            except Exception as e:
                print(f"Lỗi render công thức LaTeX cho slide preview: {e}")

    return deck_dict

