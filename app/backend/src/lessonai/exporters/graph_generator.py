"""Chart rendering. String expressions are temporarily unavailable during M0."""

import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from lessonai.core.feature_availability import ExpressionProcessingUnavailable
from lessonai.core.render_runtime import serialized_render


def _plain_value(value):
    return getattr(value, "value", value)


def expression_chart_is_disabled(config) -> bool:
    if not isinstance(config, dict):
        return False
    kind = _plain_value(config.get("plot_type") or config.get("kind") or "function")
    return kind in {"function", "function_plot", "arithmetic_sequence", "inequality_system", "linear_programming"}


def safe_eval_expression(expr_str: str):
    """Compatibility entry point; never parse an untrusted string during M0."""
    raise ExpressionProcessingUnavailable()


def is_plottable(config) -> bool:
    """Capability check without evaluating strings, including boundary lines."""
    if not isinstance(config, dict) or expression_chart_is_disabled(config):
        return False
    return (_plain_value(config.get("plot_type") or config.get("kind")) == "chart"
            and bool(config.get("labels")) and bool(config.get("values")))


@serialized_render
def generate_math_plot(config: dict, figsize: tuple = (6, 4)) -> bytes:
    if not isinstance(config, dict):
        raise ValueError("chart_spec không hợp lệ (không phải dict)")
    if expression_chart_is_disabled(config):
        raise ExpressionProcessingUnavailable()
    if not is_plottable(config):
        raise ValueError("Loại đồ thị không hỗ trợ hoặc thiếu labels/values")
    fig, ax = plt.subplots(figsize=figsize)
    try:
        kind = config.get("chart_kind", "bar")
        if kind == "bar":
            ax.bar(config["labels"], config["values"], color="#1f77b4")
        elif kind == "pie":
            ax.pie(config["values"], labels=config["labels"], autopct="%1.1f%%")
        else:
            raise ValueError("Chỉ hỗ trợ biểu đồ cột và tròn trong M0")
        title = config.get("chart_title") or config.get("title")
        if title:
            ax.set_title(str(title))
        fig.tight_layout()
        with io.BytesIO() as buffer:
            fig.savefig(buffer, format="png", dpi=300, transparent=True)
            return buffer.getvalue()
    finally:
        plt.close(fig)
