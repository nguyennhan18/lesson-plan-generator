"""Bounded math rendering from confirmed requirements and isolated computation."""
import io
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from lessonai.core.render_runtime import serialized_render
from lessonai.core.jobs import get_runner
from lessonai.services.math_expression import parse_expression
from lessonai.services.visual_requirements import checked_requirement, VisualError


def _plain_value(value):
    return getattr(value, "value", value)


def expression_chart_is_disabled(config):
    return False


def safe_eval_expression(expr_str):
    return parse_expression(expr_str)


def is_plottable(config):
    if not isinstance(config, dict):
        return False
    kind = _plain_value(config.get("kind") or config.get("plot_type"))
    if kind in {"arithmetic_sequence","inequality_system"}:
        try:
            from lessonai.services.discrete_visuals import normalize
            normalize(config);checked_requirement(config)
            return True
        except (ValueError,KeyError,TypeError):return False
    if kind in {"function_plot", "function"}:
        try:
            parse_expression(config.get("expression"))
            checked_requirement(config)
            return True
        except ValueError:
            return False
    return kind == "chart" and bool(config.get("labels")) and bool(config.get("values"))


def function_y_limits(config, points):
    """Keep asymptote samples from flattening the visible graph.

    Only the viewport is cropped; every segment and domain exclusion is kept.
    An explicit teacher viewport takes precedence over the robust automatic one.
    """
    lo, hi = config.get("y_min"), config.get("y_max")
    if lo is not None or hi is not None:
        if lo is None or hi is None:
            raise ValueError("Cần cả hai giới hạn trục y")
        lo, hi = float(lo), float(hi)
        if not math.isfinite(lo) or not math.isfinite(hi) or lo >= hi:
            raise ValueError("Giới hạn trục y không hợp lệ")
        return lo, hi
    import numpy as np
    values=[p[1] for segment in points["segments"] for p in segment if math.isfinite(p[1])]
    lo, hi = map(float, np.percentile(values, [5, 95]))
    span=hi-lo
    padding=max(span*.1, abs(lo)*.05, 1e-6) if span else max(abs(lo)*.1, 1.)
    return lo-padding, hi+padding


@serialized_render
def _draw(config, points, figsize):
    if len(figsize) != 2 or any(not math.isfinite(v) or not 0 < v <= 12 for v in figsize):
        raise ValueError("Kích thước ảnh không hợp lệ")
    fig, ax = plt.subplots(figsize=figsize)
    try:
        if points is not None and "points" in points:
            ax.scatter([point[0] for point in points["points"]],[point[1] for point in points["points"]],color="#2563eb")
            ax.set_xlabel("n");ax.set_ylabel("u(n)");ax.grid(alpha=.2)
        elif points is not None and "polygon" in points:
            polygon=points['polygon']
            if len(polygon)>=3:ax.fill([p[0] for p in polygon],[p[1] for p in polygon],color='#93c5fd',alpha=.4)
            for row in points['constraints']:
                style='--' if row['relation'] in ('<','>') else '-'
                if row['b']:
                    xs=[config['x_min'],config['x_max']];ys=[(row['c']-row['a']*x)/row['b'] for x in xs];ax.plot(xs,ys,linestyle=style)
                else:ax.axvline(row['c']/row['a'],linestyle=style)
            ax.set_xlim(config['x_min'],config['x_max']);ax.set_ylim(config['y_min'],config['y_max'])
            ax.set_title('Miền nghiệm trong cửa sổ hiển thị');ax.grid(alpha=.2)
        elif points is not None:
            for segment in points["segments"]:
                ax.plot([p[0] for p in segment], [p[1] for p in segment], color="#2563eb")
            ax.axhline(0, color="#777", linewidth=.6)
            ax.axvline(0, color="#777", linewidth=.6)
            ax.set_xlim(float(config["x_min"]), float(config["x_max"]))
            ax.set_ylim(*function_y_limits(config, points))
            ax.set_title("y = " + points["expression"][:180])
            ax.grid(alpha=.2)
        else:
            labels, values = config.get("labels"), config.get("values")
            if not isinstance(labels, list) or not isinstance(values, list) or not 0 < len(values) <= 100 or len(labels) != len(values):
                raise ValueError("Dữ liệu biểu đồ thiếu hoặc vượt giới hạn")
            if any(not isinstance(v, (int, float)) or not math.isfinite(v) for v in values):
                raise ValueError("Giá trị biểu đồ không hợp lệ")
            kind = config.get("chart_kind", "bar")
            if kind == "bar":
                ax.bar([str(v)[:80] for v in labels], values)
            elif kind == "pie" and all(v >= 0 for v in values) and sum(values) > 0:
                ax.pie(values, labels=[str(v)[:80] for v in labels], autopct="%1.1f%%")
            else:
                raise ValueError("Biểu đồ không được hỗ trợ")
            ax.set_title(str(config.get("chart_title") or config.get("title") or "")[:180])
        fig.tight_layout()
        with io.BytesIO() as buffer:
            fig.savefig(buffer, format="png", dpi=120, transparent=True)
            return buffer.getvalue()
    finally:
        plt.close(fig)


from functools import lru_cache
from lessonai.services.visual_requirements import canonical


@lru_cache(maxsize=32)
def _cached_render(signature):
    import json
    descriptor=json.loads(signature)
    config=descriptor["spec"];kind=config["kind"];points=None
    if kind in {"function_plot","function"}:
        points=get_runner().run("math.plot",config)
    elif kind in {"arithmetic_sequence","inequality_system"}:
        from lessonai.services.discrete_visuals import construct
        points=construct(config)
    return _draw(config,points,descriptor["figsize"])


def generate_math_plot(config,figsize=(6,4)):
    if not isinstance(config,dict):raise ValueError("chart_spec không hợp lệ")
    kind=_plain_value(config.get("kind") or config.get("plot_type"))
    if kind in {"function_plot","function"}:
        parse_expression(config.get("expression"));checked_requirement(config)
    elif kind in {"arithmetic_sequence","inequality_system"}:
        checked_requirement(config)
    elif kind!="chart":raise VisualError("Loại đồ thị chưa được hỗ trợ; không tạo hình thay thế")
    fields=("expression","operation","x_min","x_max","y_min","y_max","first_term","common_difference","count","constraints","labels","values","chart_kind","chart_title","title","source_fingerprint","deck_id","slide_id")
    spec={key:config[key] for key in fields if key in config};spec["kind"]=kind
    return _cached_render(canonical({"renderer":"confirmed-math-v2","spec":spec,"figsize":list(figsize)}))
