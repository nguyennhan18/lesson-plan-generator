import copy
import pytest
from lessonai.core.jobs import JobRunner, JobError
from lessonai.services.math_worker import verify_equality
from lessonai.services.visual_requirements import confirm_requirement, checked_requirement, VisualError
from lessonai.services.geometry_scene import build_scene
from lessonai.exporters.graph_generator import generate_math_plot
from lessonai.services.content_quality import evaluate_deck

pytestmark = pytest.mark.critical_regressions


def confirmed(expression="x^2", **kwargs):
    spec = {"kind": "function_plot", "expression": expression, "operation": "function",
            "x_min": -3., "x_max": 3., "deck_id": "deck-a", "slide_id": "slide-a", **kwargs}
    confirmation=confirm_requirement(spec)
    spec.update({**confirmation["requirement"]["spec"],"requirement_token": confirmation["requirement_token"]})
    return spec


def test_confirmation_cannot_be_forged_or_reused_after_formula_change():
    spec = confirmed()
    checked_requirement(spec)
    for change in ({"expression": "x^3"}, {"slide_id": "another"}, {"operation": "derivative"}, {"requirement_token": "verified"}):
        with pytest.raises(VisualError):
            checked_requirement({**spec, **change})


@pytest.mark.parametrize("expr", ["log(x)", "exp(x)", "Abs(x)", "1/x", "(x^2-1)/(x-1)", "tan(x)"])
def test_plot_domains_are_computed_from_original_expression(expr):
    runner = JobRunner()
    try:
        result = runner.run("math.plot", confirmed(expr), timeout=10)
        assert result["segments"]
        for segment in result["segments"]:
            xs = [p[0] for p in segment]
            if expr == "log(x)":
                assert min(xs) > 0
            if expr == "1/x":
                assert not min(xs) < 0 < max(xs)
            if expr.startswith("(x^2"):
                assert not min(xs) <= 1 <= max(xs)
    finally:
        runner.close()


def test_worker_timeout_reaps_process_and_next_job_succeeds():
    runner = JobRunner()
    with pytest.raises(JobError, match="thời hạn"):
        runner.run("math.plot", confirmed(), timeout=.001)
    assert not runner._processes
    assert runner.run("math.verify", {"lhs": "1+1", "rhs": "2"}, timeout=10)["status"] == "verified"
    runner.close()


def test_numeric_error_in_solution_is_blocking():
    report = evaluate_deck({"slides": [{"slide_id": "s", "title": "Kiểm tra", "worked_solution_steps": ["$1+1=3$"]}]})
    assert report["status"] == "blocked"
    assert any(c["status"] == "failed" and c["field"].startswith("worked_solution_steps") for c in report["checks"])


def test_rational_identity_does_not_erase_original_domain():
    assert verify_equality("(x^2-1)/(x-1)", "x+1")["status"] == "unverified"
    assert verify_equality("(x+1)^2", "x^2+2x+1")["status"] == "verified"
    assert verify_equality("sqrt(x^2)", "x")["status"] == "unverified"


def test_regular_pyramid_and_right_edge_pyramid_are_distinct():
    regular = build_scene({"polyhedron_type": "square_pyramid_regular", "base_edge": 4, "height": 3})
    right = build_scene({"polyhedron_type": "square_pyramid_at_a", "base_edge": 4, "height": 3})
    assert regular["vertices"]["S"] == [2, 2, 3]
    assert right["vertices"]["S"] == [0, 0, 3]
    lengths = regular["measurements"]["edge_lengths"]
    assert len({lengths[f"S-{name}"] for name in "ABCD"}) == 1
    with pytest.raises(ValueError):
        build_scene({"polyhedron_type": "unknown", "base_edge": 4, "height": 3})


def test_confirmed_plot_returns_png_and_missing_source_does_not():
    spec = confirmed()
    assert generate_math_plot(spec).startswith(b"\x89PNG")
    spec.pop("requirement_token")
    with pytest.raises(VisualError):
        generate_math_plot(spec)


def test_discrete_sequence_is_computed_and_not_a_continuous_curve():
    from lessonai.services.discrete_visuals import construct
    result=construct({'kind':'arithmetic_sequence','first_term':3,'common_difference':-2,'count':4})
    assert result['points']==[[1,3],[2,1],[3,-1],[4,-3]]
    with pytest.raises(ValueError):construct({'kind':'arithmetic_sequence','first_term':3,'common_difference':2,'count':10000})


def test_inequality_polygon_comes_from_constraints_not_model_vertices():
    from lessonai.services.discrete_visuals import construct
    rows=[{'a':1,'b':0,'c':0,'relation':'>='},{'a':0,'b':1,'c':0,'relation':'>='},{'a':1,'b':1,'c':2,'relation':'<='}]
    spec={'kind':'inequality_system','constraints':rows,'x_min':-1,'x_max':4,'y_min':-1,'y_max':4,'vertices':[[99,99]]}
    result=construct(spec)
    assert {tuple(point) for point in result['polygon']}=={(0,0),(2,0),(0,2)}
    spec['constraints'].append({'a':1,'b':0,'c':-1,'relation':'<='})
    assert construct(spec)['polygon']==[]


@pytest.mark.parametrize('fields',[{'kind':'arithmetic_sequence','first_term':1,'common_difference':2,'count':8},{'kind':'inequality_system','constraints':[{'a':1,'b':1,'c':1,'relation':'<'}],'x_min':-2,'x_max':2,'y_min':-2,'y_max':2}])
def test_data_visuals_require_confirmation_and_render(fields):
    fields={**fields,'deck_id':'d','slide_id':'s'}
    with pytest.raises(VisualError):generate_math_plot(fields)
    signed=confirm_requirement(fields)
    fields.update(signed['requirement']['spec']);fields['requirement_token']=signed['requirement_token']
    assert generate_math_plot(fields).startswith(b'\x89PNG')


def test_visual_cache_does_not_bypass_confirmation(monkeypatch):
    from lessonai.exporters.graph_generator import _cached_render
    _cached_render.cache_clear()
    spec=confirmed('x+17')
    first=generate_math_plot(spec);before=_cached_render.cache_info()
    assert generate_math_plot(spec)==first
    assert _cached_render.cache_info().hits==before.hits+1
    with pytest.raises(VisualError):generate_math_plot({**spec,'requirement_token':'forged'})
    assert _cached_render.cache_info().hits==before.hits+1


def test_formula_rendering_failure_never_returns_an_invisible_placeholder(monkeypatch):
    from lessonai.exporters import slide_exporter
    monkeypatch.setattr(slide_exporter.plt.Figure,'savefig',lambda *args,**kwargs: (_ for _ in ()).throw(RuntimeError('disk/render failure')))
    with pytest.raises(ValueError,match='Không thể render'):
        slide_exporter.render_latex_to_bytes(r'\frac{1}{2}')
    with pytest.raises(ValueError,match='Không có công thức'):
        slide_exporter.render_latex_to_bytes(' ')


def test_asymptote_does_not_flatten_automatic_viewport_and_manual_limits_are_signed():
    from lessonai.exporters.graph_generator import function_y_limits
    points={'segments':[[[i/10,y] for i,y in enumerate(list(range(-10,11))*10+[1e9,-1e9])]]}
    lo,hi=function_y_limits({},points)
    assert -100<lo<0<hi<100
    assert function_y_limits({'y_min':-5,'y_max':5},points)==(-5.,5.)
    spec=confirmed('1/x',y_min=-5,y_max=5)
    checked_requirement(spec)
    with pytest.raises(VisualError):checked_requirement({**spec,'y_max':10})
    with pytest.raises(VisualError):confirmed('1/x',y_min=-5)
