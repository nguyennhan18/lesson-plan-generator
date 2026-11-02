"""PR01-A: grammar/security fixtures; no renderer or symbolic worker is enabled."""

from dataclasses import replace
import json
from pathlib import Path

import pytest

from lessonai.services.math_expression import (
    ExpressionBudget, ExpressionError, parse_expression,
)

pytestmark = pytest.mark.critical_regressions
CASES = json.loads((Path(__file__).parent / "fixtures/m1_expression_cases.json").read_text())


def shape(node):
    return [node.value, *(shape(child) for child in node.children)] if node.children else node.value


@pytest.mark.parametrize("case", CASES["valid"], ids=lambda case: case["source"])
def test_supported_grammar_preserves_meaning(case):
    parsed = parse_expression(case["source"], symbols=case["symbols"],
                              syntax=case.get("syntax", "expression"))
    assert shape(parsed.root) == case["tree"]
    assert set(parsed.symbols) <= set(case["symbols"])
    assert 1 <= parsed.node_count <= 256
    assert 1 <= parsed.depth <= 32
    # The worker contract is JSON data, never a callable or symbolic object.
    assert json.loads(json.dumps(parsed.root.to_dict())) == parsed.root.to_dict()


@pytest.mark.parametrize("case", CASES["rejected"], ids=lambda case: case["source"])
def test_rejected_grammar_has_a_typed_error(case):
    with pytest.raises(ExpressionError) as caught:
        parse_expression(case["source"], syntax=case.get("syntax", "expression"))
    assert caught.value.code == case["code"]
    assert caught.value.position >= 0
    assert caught.value.detail()["message"]


def test_marker_is_never_executed_even_with_latex_or_declared_symbols(tmp_path):
    marker = tmp_path / "must-not-exist"
    payload = f"__import__('pathlib').Path({str(marker)!r}).touch()"
    for syntax in ("expression", "latex"):
        with pytest.raises(ExpressionError):
            parse_expression(payload, syntax=syntax, symbols=("x", "Path"))
    assert not marker.exists()


@pytest.mark.parametrize(("field", "value", "source"), [
    ("max_source", 4, "x + 1"),
    ("max_tokens", 2, "x+1"),
    ("max_nodes", 2, "x+1"),
    ("max_depth", 3, "((((x))))"),
    ("max_depth", 3, "x+x+x+x"),
    ("max_depth", 3, "----x"),
    ("max_digits", 3, "1234"),
    ("max_integer_power", 3, "x^4"),
    ("max_constant_bits", 16, "100^10"),
    ("max_constant_bits", 16, "65535*65535"),
])
def test_independent_budget_limits(field, value, source):
    with pytest.raises(ExpressionError, match=".") as caught:
        parse_expression(source, budget=replace(ExpressionBudget(), **{field: value}))
    assert caught.value.code == "expression_budget_exceeded"


def test_limits_accept_boundary_values_and_reject_next_value():
    assert parse_expression("x^100").root.value == "^"
    assert parse_expression("x^-100").root.value == "^"
    assert parse_expression("1" * 32).root.kind == "number"
    for source in ("1" * 33, "(" * 1000 + "x" + ")" * 1000,
                   "+".join(["x"] * 600), "1e-999999999", "x^(50+51)"):
        with pytest.raises(ExpressionError) as caught:
            parse_expression(source)
        assert caught.value.code == "expression_budget_exceeded"


def test_latex_depth_is_checked_before_recursive_conversion():
    with pytest.raises(ExpressionError) as caught:
        parse_expression(r"\sqrt{" * 100 + "x" + "}" * 100, syntax="latex")
    assert caught.value.code == "expression_budget_exceeded"


@pytest.mark.parametrize("symbols", [("__builtins__",), ("x.a",), ("sin",), ("pi",),
                                    ("ln",), ("x", 2), ("x" * 33,), "xyz"])
def test_symbol_declarations_cannot_create_executable_names(symbols):
    with pytest.raises(ExpressionError) as caught:
        parse_expression("x", symbols=symbols)
    assert caught.value.code == "expression_forbidden"


def test_exact_declared_name_wins_over_implicit_single_letter_product():
    assert parse_expression("ac", symbols=("a", "c", "ac")).root.value == "ac"
    assert parse_expression("ac", symbols=("a", "c", "ac")).root.kind == "symbol"
    assert parse_expression("a c", symbols=("a", "c", "ac")).root.value == "*"


@pytest.mark.parametrize("source", [None, 12, "", "  "])
def test_empty_or_non_string_source_has_an_explicit_error(source):
    with pytest.raises(ExpressionError) as caught:
        parse_expression(source)
    assert caught.value.code == "expression_invalid"


def test_parse_does_not_remove_singularities_or_certify_identities():
    parsed = parse_expression("(x^2-1)/(x-1)")
    assert parsed.root.value == "/"
    assert shape(parsed.root.children[1]) == ["-", "x", "1"]
    assert shape(parse_expression("sqrt(x^2)").root) == ["sqrt", ["^", "x", "2"]]
    # Even an undefined constant remains syntax data for the worker's domain check.
    assert shape(parse_expression("1/0").root) == ["/", "1", "0"]
    assert not hasattr(parsed, "verified")
