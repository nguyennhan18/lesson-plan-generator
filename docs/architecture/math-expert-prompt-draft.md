---
status: proposed (bản nháp, chờ chủ dự án duyệt)
date: 2026-11-25
base: feature/ban-lam-viec @ 3927e92
related: role-orchestrator-design.md, ADR 0008, ADR 0010, D1/D2/D4/D5/D11, O3.7, #19–#24, #27
---

# Prompt Vai trò Chuyên gia toán (bản nháp)

Chưa có mã. Tệp đích dự kiến: `app/backend/src/lessonai/prompts/roles/math_expert.py` (system prompt + `PROMPT_VERSION`), schema ở `app/backend/src/lessonai/schemas/role_math.py`, hàm dựng prompt ở `app/backend/src/lessonai/services/orchestration/math_stage.py`.

## 1. Vị trí trong chuỗi

```
Dàn ý đã duyệt (có math_intent)  ──►  Chuyên gia toán  ──►  kiểm bằng code  ──►  POST math-spec/verify (Cổng toán)
                                         ▲                                              │
                                         └────── vòng sửa (≤ 2) với mệnh đề 'failed' ───┘
```

- Đầu vào: các Mục dàn ý đã duyệt, `math_intent` (họ hàm, tham số, khoảng tương tác, hiện tượng cần quan sát), Nguồn đã duyệt.
- Đầu ra: công thức cụ thể và các Mệnh đề toán **nguyên tử** để Cổng toán kiểm từng cái một.
- LLM **không bao giờ** gắn trạng thái. `verified`, `unverified`, `failed` chỉ do Cổng toán trả (ADR 0008).

## 2. Schema đầu ra

```python
ClaimKind = Literal[
    "derivative",          # có phép kiểm: derivative_polynomial_identity v1 (#20)
    "real_roots",          # #21, hiện -> unverified
    "critical_points",     # #22
    "extremum_max", "extremum_min",
    "monotonic_interval",
    "parameter_range",     # #23
    "exclusion",           # #23
    "solution_step",       # #24
]

class ParamInterval(BaseModel):            # O3.7
    model_config = ConfigDict(extra="forbid")
    parameter: str                          # phải thuộc function.parameters
    lower: str | None                       # biểu thức hằng, None = -∞
    upper: str | None                       # None = +∞
    lower_closed: bool
    upper_closed: bool

class ExpertClaim(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(pattern=r"^[a-z0-9_]{1,60}$")     # ổn định qua các vòng sửa
    kind: ClaimKind
    expression: str = Field(max_length=500)           # ngôn ngữ biểu thức, KHÔNG LaTeX
    applies_when: list[ParamInterval] = []            # rỗng = mọi giá trị tham số
    used_in: list[str] = Field(min_length=1)          # item_id của Mục dàn ý
    statement_vi: str = Field(max_length=300)         # câu tiếng Việt để giáo viên đọc

class MathExpertOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    function: MathFunction                  # dùng lại từ math_spec_schema.py
    claims: list[ExpertClaim] = Field(min_length=1, max_length=50)
    doubts: list[Doubt] = []                # Nghi vấn về Dàn ý / math_intent
```

Khi gửi sang Cổng toán, mỗi `ExpertClaim` được rút gọn về `MathClaim(id, kind, expression)`. **Lưu ý:** hash của bằng chứng hiện chỉ gồm `function`, `kind`, `expression` (`statement()` trong `services/math_spec.py`), chưa gồm `applies_when`. Với `derivative` thì không sao, vì đạo hàm đúng với mọi `a`. Với mệnh đề có điều kiện như cực trị khi `a > 0`, phép kiểm ở #21–#22 phải đưa `applies_when` vào `statement` và vào hash. Chưa có phép kiểm thì mệnh đề vẫn là `unverified`.

## 3. System prompt (bản nháp)

```text
PROMPT_VERSION = "math_expert@0.1"

Bạn là Chuyên gia toán trong nhóm soạn bài giảng Toán 12 (GDPT 2018, sách Kết nối tri thức).
Đầu ra của bạn KHÔNG đến thẳng giáo viên: mỗi mệnh đề sẽ được máy kiểm chứng bằng ký hiệu.
Một mệnh đề sai sẽ bị trả lại; một mệnh đề máy không kiểm được sẽ chuyển giáo viên duyệt tay.
Vì vậy hãy viết ít mệnh đề, mỗi mệnh đề đúng một sự kiện, và chính xác tuyệt đối.

# ĐẦU VÀO
Bạn nhận JSON gồm:
- "dàn ý": các Mục đã được giáo viên duyệt (item_id, hoạt động, loại mục, tiêu đề, các ý).
- "ý đồ toán": họ hàm, tham số (tên, vai trò, khoảng tương tác), hiện tượng cần học sinh quan sát.
  Giáo viên ĐÃ DUYỆT ý đồ này.
- "nguồn đã duyệt": các đơn vị nguồn SGK được đánh số.
- "loại mệnh đề": danh sách kind được phép dùng.

# NHIỆM VỤ
1. Chọn MỘT công thức cụ thể thuộc đúng họ hàm trong "ý đồ toán", dùng đúng tên biến và tham số đã cho.
   Không đổi họ hàm, không thêm hay bớt tham số.
2. Viết các mệnh đề toán mà bài giảng cần để làm rõ "hiện tượng cần quan sát":
   đạo hàm, nghiệm, điểm dừng, cực trị, khoảng đơn điệu, điều kiện của tham số, các bước giải.
3. Với mỗi mệnh đề phụ thuộc tham số, chia đủ mọi trường hợp của tham số trong khoảng tương tác,
   kể cả giá trị biên (ví dụ a < 0, a = 0, a > 0). Mỗi trường hợp là một mệnh đề riêng, có applies_when.
   Các applies_when của cùng một loại mệnh đề phải phủ kín khoảng tương tác và không chồng nhau.
4. Ghi used_in là item_id của các Mục dàn ý sẽ dùng mệnh đề đó.

# CÁCH VIẾT expression
- Chỉ dùng: số, biến, tham số, + - * / ^ ( ), sqrt, sin, cos, tan, log, exp, Abs, pi, E.
  Viết rõ phép nhân: 3*a*x, không viết 3ax.
- KHÔNG dùng LaTeX, không dùng ký hiệu ≤ ≥ ∈ ±, không viết chữ trong expression.
- derivative: expression là đạo hàm theo biến, ví dụ "3*x^2 - 3*a".
- real_roots, critical_points: liệt kê giá trị cách nhau bằng dấu phẩy, ví dụ "0, sqrt(3*a), -sqrt(3*a)".
- extremum_max, extremum_min: một điểm dạng "(hoành độ, tung độ)".
- monotonic_interval: "(đầu, cuối): tăng" hoặc "(đầu, cuối): giảm"; dùng -oo, oo cho vô cực.
- Không viết giá trị gần đúng (1.732...) thay cho giá trị đúng (sqrt(3)).
- statement_vi: một câu tiếng Việt ngắn cho giáo viên đọc; có thể dùng LaTeX trong $...$.
  statement_vi phải nói ĐÚNG điều expression nói, không thêm ý.

# KHÔNG ĐƯỢC
- Không gắn hay nhắc tới trạng thái kiểm chứng ("đã kiểm", "chắc chắn đúng").
- Không đưa số liệu, định lý, ví dụ hay trích dẫn không có trong "nguồn đã duyệt"
  hoặc không suy ra trực tiếp từ công thức bạn chọn.
- Không viết lời giảng, không viết slide; chỉ viết mệnh đề.
- Không tự sửa Dàn ý hay ý đồ toán.

# NGHI VẤN (doubts)
Nếu Dàn ý hoặc ý đồ toán có chỗ sai, thiếu hoặc mâu thuẫn (ví dụ khoảng tương tác làm hàm không
còn hiện tượng cần quan sát, hoặc một Mục cần kiến thức ngoài họ hàm đã duyệt), ghi vào doubts
với target là item_id hoặc "math_intent", và VẪN làm theo ý đồ đã duyệt. Không có nghi vấn thì để [].

# VÒNG SỬA
Nếu đầu vào có "kết quả cổng toán vòng trước", chỉ sửa các mệnh đề có status "failed" theo reason.
Giữ nguyên id và nội dung của mọi mệnh đề khác. Không xóa mệnh đề "unverified".

Trả về đúng một đối tượng JSON theo schema.
```

## 4. User prompt (code tự dựng)

```python
def build_math_prompt(outline, intent, sources, gate_feedback=None) -> str:
    payload = {
        "dàn ý": [
            {"item_id": i.item_id, "hoạt động": i.activity, "loại mục": i.kind,
             "tiêu đề": i.title, "các ý": i.points}
            for i in outline.items
        ],
        "ý đồ toán": intent.model_dump(mode="json"),
        "nguồn đã duyệt": [{"number": n, **unit} for n, unit in enumerate(sources, 1)],
        "loại mệnh đề": list(get_args(ClaimKind)),
    }
    if gate_feedback:  # vòng 2: chỉ mệnh đề failed + reason, kèm bản trước
        payload["bản trước"] = gate_feedback.previous.model_dump(mode="json")
        payload["kết quả cổng toán vòng trước"] = [
            {"id": c.id, "status": c.status, "reason": c.reason}
            for c in gate_feedback.results
        ]
    return json.dumps(payload, ensure_ascii=False)
```

- Không gửi `minutes`, `slide_count`, `source_refs.sha256`: Vai trò này không cần.
- Gọi với `temperature` thấp (đề xuất 0.2) và `response_schema=MathExpertOutput`.

## 5. Kiểm bằng code trước khi gọi Cổng toán

Lỗi ở đây cũng tính là một vòng sửa (D10). Mỗi lỗi có lý do tiếng Việt để đưa vào vòng sau.

| Kiểm tra | Vì sao |
|---|---|
| `function.variable` và `function.parameters` khớp `math_intent` | D4: không đổi ý đồ đã duyệt |
| Họ hàm khớp `math_intent` (cách kiểm: xem QĐ-M2) | D4 |
| `function.expression` và mọi `expression` parse được bằng `math_expression.py` | Lỗi cú pháp, không phải lỗi toán |
| `id` không trùng; giữ nguyên `id` ở vòng sửa | O3.3, D7 trỏ bằng ID |
| Mỗi `used_in` là `item_id` có thật | D7 |
| `applies_when.parameter` thuộc `parameters`; khoảng nằm trong khoảng tương tác | O3.7 |
| Cùng `kind` thì các `applies_when` phủ kín khoảng tương tác và không chồng nhau | Không bỏ sót trường hợp `a = 0` |
| Có ít nhất một `derivative` khi họ hàm là đa thức | Ca demo D11 cần nhãn đạo hàm |

Sau đó mỗi mệnh đề đi qua `verify_claim`:
- `failed` → vòng sửa;
- `unverified` → dừng, chờ giáo viên (#26);
- tất cả `verified` → sang Người dựng slide.

## 6. Không dùng ví dụ mẫu với ca `f_a(x) = x^3 - 3*a*x`

Các kết quả ở D11 là oracle cho test và E2E. Đưa chúng vào prompt làm ví dụ thì benchmark chỉ đo việc chép lại. Nếu cần một ví dụ định dạng, dùng họ hàm khác không có trong bộ 15 ca benchmark (**QĐ-M4**).

## 7. Test (LLM giả)

- JSON đầu vào có đủ khóa; không có `minutes`, `slide_count`.
- Vòng 2 chỉ chứa mệnh đề `failed` kèm reason và bản trước; `id` các mệnh đề khác không đổi.
- Mỗi kiểm tra ở mục 5 có một test từ chối.
- Thiếu trường hợp `a = 0` thì bị từ chối trước khi tới Cổng toán.
- Không có trường trạng thái nào trong `MathExpertOutput` (`extra="forbid"`).
- `RoleRun.prompt_version == "math_expert@0.1"`.

Đo thật (cần QĐ-4): chạy prompt trên bộ benchmark Toán 12 với từng Model ứng viên. Ghi tỷ lệ `failed`, `unverified`, lỗi schema và số token.

## 8. Quyết định cần chủ dự án

| Mã | Câu hỏi | Đề xuất |
|---|---|---|
| QĐ-M1 | `math_intent` chưa có (#27). Khi Dàn ý thiếu nó thì dừng, hay cho Chuyên gia toán đề xuất họ hàm rồi bắt giáo viên duyệt lại Dàn ý (D4)? | Dừng với `stop_reason="missing_math_intent"` |
| QĐ-M2 | Kiểm "đúng họ hàm" bằng gì? `math_intent` cần mẫu công thức có cấu trúc (ví dụ `"x^3 - 3*a*x"` với hệ số tự do) hay chỉ tên họ hàm? | Mẫu công thức, so bằng ký hiệu trong worker |
| QĐ-M3 | Một Bài giảng một hàm (như demo D11), hay nhiều hàm? | Một hàm cho demo; mở rộng sau |
| QĐ-M4 | Có đưa ví dụ định dạng vào prompt không, và dùng hàm nào | Có, một ví dụ ngắn ngoài bộ benchmark |
| QĐ-M5 | `applies_when` đưa vào hash bằng chứng từ #21 trở đi | Có; cần sửa `statement()` cùng phép kiểm đầu tiên có điều kiện |
