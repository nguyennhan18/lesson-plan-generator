"""Bounded expression grammar producing data only, never executable Python/SymPy.

Parsing is not a mathematical proof or permission to render. Keep the original
tree (especially division and roots) so a worker can preserve excluded points.
No worker is started and no symbolic/numeric function is called in this module.
"""

from dataclasses import dataclass
from fractions import Fraction
import re


@dataclass(frozen=True)
class ExpressionBudget:
    max_source: int = 2048
    max_tokens: int = 512
    max_nodes: int = 256
    max_depth: int = 32
    max_digits: int = 32
    max_integer_power: int = 100
    max_constant_bits: int = 512


class ExpressionError(ValueError):
    def __init__(self, code: str, message: str, position: int = 0):
        super().__init__(message)
        self.code = code
        self.position = position

    def detail(self):
        return {"code": self.code, "message": str(self), "position": self.position}


@dataclass(frozen=True)
class ExpressionNode:
    kind: str
    value: str
    children: tuple["ExpressionNode", ...] = ()

    def to_dict(self):
        return {"kind": self.kind, "value": self.value,
                "children": [child.to_dict() for child in self.children]}


@dataclass(frozen=True)
class ParsedExpression:
    root: ExpressionNode
    symbols: tuple[str, ...]
    node_count: int
    depth: int


FUNCTIONS = frozenset({"sin", "cos", "tan", "log", "exp", "sqrt", "Abs"})
ALIASES = {"ln": "log", "abs": "Abs"}
CONSTANTS = frozenset({"pi", "E"})
_NUMBER = re.compile(r"(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", re.ASCII)
_NAME = re.compile(r"[A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)?", re.ASCII)


def _error(message, position=0, code="expression_invalid"):
    raise ExpressionError(code, message, position)


def _limit(message, position=0):
    _error(message, position, "expression_budget_exceeded")


class _Parser:
    def __init__(self, source, symbols, budget):
        self.budget = budget
        self.tokens = []
        self.index = 0
        self.count = 0
        self.used = set()
        position = 0
        while position < len(source):
            char = source[position]
            if char.isspace():
                position += 1
                continue
            match = _NUMBER.match(source, position)
            if match:
                number = match.group()
                mantissa, *exponent = re.split("[eE]", number)
                if sum(c.isdigit() for c in mantissa) > budget.max_digits:
                    _limit("Literal số quá dài", position)
                if exponent and (len(exponent[0].lstrip("+-")) > 3
                                 or abs(int(exponent[0])) > 100):
                    _limit("Số mũ thập phân vượt giới hạn", position)
                self.push("number", number, position)
                position = match.end()
                continue
            match = _NAME.match(source, position)
            if match:
                name = match.group()
                if name in FUNCTIONS or name in ALIASES:
                    self.push("function", ALIASES.get(name, name), position)
                elif name in CONSTANTS:
                    self.push("constant", name, position)
                elif name in symbols:
                    self.push("symbol", name, position)
                elif len(name) > 1 and all(c in symbols for c in name):
                    # Only split a run of explicitly declared one-letter symbols.
                    for offset, symbol in enumerate(name):
                        self.push("symbol", symbol, position + offset)
                else:
                    _error(f"Tên chưa được khai báo: {name}", position, "expression_forbidden")
                position = match.end()
                continue
            if source.startswith("**", position):
                self.push("op", "^", position)
                position += 2
                continue
            if char in "+-*/^()":
                self.push("op", char, position)
                position += 1
                continue
            _error("Ký tự không được phép trong biểu thức", position, "expression_forbidden")
        self.tokens.append(("end", "", len(source)))

    def push(self, kind, value, position):
        if len(self.tokens) >= self.budget.max_tokens:
            _limit("Quá nhiều token", position)
        self.tokens.append((kind, value, position))

    @property
    def token(self):
        return self.tokens[self.index]

    def take(self, value):
        if self.token[1] == value:
            self.index += 1
            return True
        return False

    def expect(self, value):
        if not self.take(value):
            _error(f"Thiếu ký hiệu {value}", self.token[2])

    def node(self, kind, value, *children):
        self.count += 1
        if self.count > self.budget.max_nodes:
            _limit("Quá nhiều node", self.token[2])
        return ExpressionNode(kind, value, children)

    def expression(self, minimum=0, nesting=1):
        if nesting > self.budget.max_depth:
            _limit("Biểu thức lồng quá sâu", self.token[2])
        kind, value, position = self.token
        self.index += 1
        if kind == "number":
            left = self.node("number", value)
        elif kind in {"symbol", "constant"}:
            left = self.node(kind, value)
            if kind == "symbol":
                self.used.add(value)
        elif kind == "function":
            self.expect("(")
            argument = self.expression(nesting=nesting + 1)
            self.expect(")")
            left = self.node("function", value, argument)
        elif value == "(":
            left = self.expression(nesting=nesting + 1)
            self.expect(")")
        elif value in {"+", "-"}:
            # Power binds more tightly than unary minus: -x^2 == -(x^2).
            left = self.node("unary", value, self.expression(25, nesting + 1))
        else:
            _error("Cần một toán hạng", position)
        while True:
            next_kind, operator, position = self.token
            implicit = next_kind in {"symbol", "constant", "function"} or operator == "("
            precedence = 20 if implicit else {"+": 10, "-": 10, "*": 20, "/": 20, "^": 30}.get(operator, -1)
            if precedence < minimum:
                break
            if not implicit:
                self.index += 1
            # Right-associative exponentiation: 2^3^2 == 2^(3^2).
            right = self.expression(precedence if operator == "^" and not implicit else precedence + 1,
                                    nesting + 1)
            left = self.node("binary", "*" if implicit else operator, left, right)
        return left


def _inspect_tree(node, budget, depth=1):
    """Check *tree* depth and bounded constant arithmetic without simplification.

    Fractions here only estimate/limit literal arithmetic; they never replace
    the AST. Check growth before power, including constant exponent towers.
    """
    if depth > budget.max_depth:
        _limit("Cây biểu thức quá sâu")
    children = [_inspect_tree(child, budget, depth + 1) for child in node.children]
    height = 1 + max((item[1] for item in children), default=0)
    values = [item[0] for item in children]
    constant = None
    if node.kind == "number":
        constant = Fraction(node.value)
    elif node.kind == "unary" and values[0] is not None:
        constant = values[0] if node.value == "+" else -values[0]
    elif node.kind == "binary":
        a, b = values
        if node.value == "^" and b is not None:
            if b.denominator == 1:
                if abs(b) > budget.max_integer_power:
                    _limit("Số mũ nguyên vượt giới hạn")
                if a is not None and a:
                    bits = max(abs(a.numerator).bit_length(), a.denominator.bit_length())
                    if bits * abs(int(b)) > budget.max_constant_bits:
                        _limit("Lũy thừa hằng quá lớn")
            elif abs(b) > budget.max_integer_power:
                _limit("Số mũ hằng vượt giới hạn")
        if a is not None and b is not None:
            if node.value == "+":
                constant = a + b
            elif node.value == "-":
                constant = a - b
            elif node.value == "*":
                constant = a * b
            elif node.value == "/" and b:
                constant = a / b
            elif node.value == "^" and b.denominator == 1 and (a or b > 0):
                constant = a ** int(b)
    if constant is not None and max(abs(constant.numerator).bit_length(),
                                    constant.denominator.bit_length()) > budget.max_constant_bits:
        _limit("Độ lớn hằng vượt giới hạn")
    return constant, height


class _LatexAdapter:
    """A small structural adapter; never drops conditions or unknown commands."""
    def __init__(self, source, budget):
        self.source = source
        self.budget = budget
        self.index = 0

    def whitespace(self):
        while self.index < len(self.source) and self.source[self.index].isspace():
            self.index += 1

    def group(self, depth):
        self.whitespace()
        if self.index >= len(self.source) or self.source[self.index] != "{":
            _error("Lệnh LaTeX cần đối số trong ngoặc nhọn", self.index)
        self.index += 1
        return self.sequence(depth + 1, grouped=True)

    def sequence(self, depth=1, grouped=False):
        if depth > self.budget.max_depth:
            _limit("LaTeX lồng quá sâu", self.index)
        output = []
        while self.index < len(self.source):
            char = self.source[self.index]
            self.index += 1
            if char == "}":
                if not grouped:
                    _error("Ngoặc LaTeX đóng không khớp", self.index - 1)
                return "".join(output)
            if char == "{":
                output.append("(" + self.sequence(depth + 1, grouped=True) + ")")
            elif char == "\\":
                start = self.index - 1
                match = re.match(r"[A-Za-z]+", self.source[self.index:])
                if not match:
                    _error("Lệnh LaTeX chưa hỗ trợ", start, "expression_unsupported")
                command = match.group()
                self.index += len(command)
                if command in {"frac", "dfrac", "tfrac"}:
                    numerator = self.group(depth)
                    denominator = self.group(depth)
                    output.append(f"(({numerator})/({denominator}))")
                elif command == "sqrt":
                    output.append("sqrt(" + self.group(depth) + ")")
                elif command in {"cdot", "times"}:
                    output.append("*")
                elif command == "pi":
                    output.append(" pi ")
                elif command in {"sin", "cos", "tan", "log", "ln", "exp"}:
                    # Require explicit parentheses; do not guess the extent of an argument.
                    output.append(" " + command + " ")
                elif command in {"left", "right"}:
                    self.whitespace()
                    expected = "(" if command == "left" else ")"
                    if self.index >= len(self.source) or self.source[self.index] != expected:
                        _error("Chỉ hỗ trợ cặp ngoặc tròn left/right", start, "expression_unsupported")
                    output.append(expected)
                    self.index += 1
                else:
                    _error(f"Lệnh LaTeX chưa hỗ trợ: {command}", start, "expression_unsupported")
            elif char == "_" and self.index < len(self.source) and self.source[self.index] == "{":
                self.index += 1
                subscript = self.sequence(depth + 1, grouped=True)
                if not re.fullmatch(r"[A-Za-z0-9]+", subscript, re.ASCII):
                    _error("Chỉ số ký hiệu chưa hỗ trợ", self.index, "expression_unsupported")
                output.append("_" + subscript)
            else:
                output.append(char)
        if grouped:
            _error("Thiếu ngoặc LaTeX đóng", self.index)
        return "".join(output)


def parse_expression(source: str, *, symbols=("x",), syntax="expression",
                     budget: ExpressionBudget | None = None) -> ParsedExpression:
    """Parse an allowlisted language; callers must explicitly declare symbols.

    Error offsets refer to source for plain expressions; for LaTeX, adapter
    errors refer to source and grammar errors to the converted expression.
    The caller must not claim these are all original LaTeX offsets.
    """
    budget = budget or ExpressionBudget()
    if not isinstance(source, str) or not source.strip():
        _error("Biểu thức phải là chuỗi không rỗng")
    if len(source) > budget.max_source:
        _limit("Biểu thức quá dài")
    if syntax not in {"expression", "latex"}:
        _error("Cú pháp chưa hỗ trợ", code="expression_unsupported")
    if (not isinstance(symbols, (tuple, list, frozenset, set)) or len(symbols) > 16
            or any(not isinstance(name, str) or len(name) > 32
                   or not _NAME.fullmatch(name) or name in FUNCTIONS | CONSTANTS
                   or name in ALIASES for name in symbols)):
        _error("Tập ký hiệu khai báo không hợp lệ", code="expression_forbidden")
    if syntax == "latex":
        # Only remove a complete outer math delimiter; never remove conditions.
        source = source.strip()
        for delimiter in ("$$", "$"):
            if source.startswith(delimiter) and source.endswith(delimiter) and len(source) > 2 * len(delimiter):
                source = source[len(delimiter):-len(delimiter)]
                break
        source = _LatexAdapter(source, budget).sequence()
        if len(source) > budget.max_source:
            _limit("Biểu thức sau chuyển LaTeX quá dài")
    parser = _Parser(source, frozenset(symbols), budget)
    root = parser.expression()
    if parser.token[0] != "end":
        _error("Token thừa hoặc phép nhân ngầm không hợp lệ", parser.token[2])
    _, depth = _inspect_tree(root, budget)
    return ParsedExpression(root, tuple(sorted(parser.used)), parser.count, depth)
