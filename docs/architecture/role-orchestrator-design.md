---
status: proposed (bản nháp, chờ chủ dự án duyệt)
date: 2026-11-25
base: feature/ban-lam-viec @ 3927e92
---

# Thiết kế bộ điều phối Vai trò (prompt chaining)

Bản nháp này mô tả cách hiện thực ADR 0010 (năm Vai trò, mỗi Vai trò một Model) trên hợp đồng API đã duyệt ở #19 (`POST /api/v1/orchestrator/run`). Chưa có dòng mã nào được viết. Các mục **[QĐ-n]** là quyết định chủ dự án cần chốt trước khi làm.

Code nền là nhánh `feature/ban-lam-viec` (đã có Dàn ý bản 3 #39, `math_spec/verify` #20, `jobs.py`, `math_worker.py`, gateway có hạn 45 s và `single_attempt`, đã bỏ `fallback.py`). Nhánh `main` ở `fc26ce2` cũ hơn và còn nội dung mẫu, không dùng làm nền.

## 1. Mâu thuẫn cần giải trước

ADR 0010 (2026-11-25) và ADR 0002 mới hơn một số mục trong `docs/architecture/multi-role-generation-decisions.md` và #19:

| Chỗ cũ | Nội dung cũ | ADR mới | Đề xuất |
|---|---|---|---|
| D13, O4.1 | Mọi Vai trò dùng chung một model; không chặn chuyển provider | ADR 0010: mỗi Vai trò một Model, cấm trùng Model với Vai trò thượng nguồn | Theo ADR 0010; sửa D13, O4.1 |
| O3.5, #19 mục 2 | Chuỗi `math → visual → giáo án → slide → phản biện`; slide dựng từ giáo án | ADR 0002: slide và giáo án cùng dựng từ Dàn ý. ADR 0010: bỏ Vai trò Thiết kế trực quan | Giai đoạn mới: `outline, math, slides, lesson_plan, review` |
| #39, #40 | "Một lượt gọi AI" mỗi API | ADR 0010 yêu cầu sửa các tiêu chí này | Sửa ticket |

- **[QĐ-1]** Đổi danh sách `stage` của `orchestrator/run` so với #19 (bỏ `visual`, thêm `outline`) là đổi hợp đồng đã duyệt, cần chủ dự án ghi nhận lại trên #19 hoặc một ticket mới.
- **[QĐ-2]** Lập Dàn ý: giữ endpoint hiện có của #39 và chỉ ghi `RoleRun` cho nó, hay chuyển hẳn vào `orchestrator/run` với `stage="outline"`? Đề xuất: **giữ endpoint #39**, cho nó trả thêm `role_run` (cũng là thay đổi hợp đồng, cần duyệt).

## 2. Đồ thị phụ thuộc

```
outline ──► math ──► slides
   │          │
   │          └────► lesson_plan   (khi giáo viên bấm)
   │
   └─(tất cả)──────► review        (khi giáo viên bấm)
```

| Stage | Vai trò | Đầu vào bắt buộc | Thượng nguồn (để loại Model) | Đầu ra |
|---|---|---|---|---|
| `outline` | Người lập Dàn ý | yêu cầu, bài SGK, trình độ, Nguồn đã duyệt | — | `WorkbenchOutline` (+ `math_intent` theo #19) |
| `math` | Chuyên gia toán | Dàn ý **đã duyệt** | outline | `MathClaimSet` qua Cổng toán |
| `slides` | Người dựng slide | Dàn ý đã duyệt, `MathClaimSet` | outline, math | Bộ slide canvas (#40) |
| `lesson_plan` | Người soạn KHBD | Dàn ý đã duyệt, `MathClaimSet` | outline, math | `LessonPlanSchema` |
| `review` | Phản biện | mọi kết quả đã có | outline, math, slides, lesson_plan (nếu có) | `ReviewReport` |

Quy tắc loại Model (ADR 0010): `excluded = {run.model_key for run in thượng_nguồn}`, dùng **Model thực tế đã chạy** (kể cả Model dự phòng), không dùng Model chính trên giấy. Dàn ý giáo viên đã sửa vẫn tính là đầu ra của Model đã lập nó.

## 3. Vỏ bàn giao `RoleRun` (theo D8, O3.4)

```python
class RoleRun(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1] = 1
    run_id: str                      # uuid4
    stage: Stage                     # Literal["outline","math","slides","lesson_plan","review"]
    supersedes: str | None           # run_id bị thay thế
    created_at: datetime
    input_hashes: dict[Stage, str]   # hash đầu ra của từng thượng nguồn đã dùng
    output_hash: str                 # canonical JSON + sha256 (O3.2)
    hash_version: int
    provider: str
    model: str
    is_primary_model: bool           # False -> cờ "model dự phòng"
    prompt_version: str              # vd "math_expert@1"
    round: int                       # 1..2 (D10)
    prompt_chars: int                # #40 ghi kích thước prompt
    doubts: list[Doubt]              # Nghi vấn; outline luôn []
    output: StageOutput              # union phân biệt theo stage
```

`Doubt = {target: Ref, text: str}`; `Ref` trỏ bằng ID ổn định + hash (O3.3): `item_id` của Mục dàn ý, `claim.id`, hoặc `slide_id` + tên trường.

Lưu ở trình duyệt trong `role_runs` (O3.1), không tăng `schema_version`. Server không giữ trạng thái; mỗi request mang theo các `RoleRun` thượng nguồn.

## 4. API `POST /api/v1/orchestrator/run`

```python
class OrchestratorRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    stage: Literal["math", "slides", "lesson_plan", "review"]
    outline: WorkbenchOutlineResponse          # bản đã duyệt, có thể đã sửa tay
    outline_run: RoleRun                        # để biết Model đã lập Dàn ý
    upstream: list[RoleRun] = []                # math, slides, ... tùy stage
    feedback: list[ReviewIssue] = []            # chỉ khi sửa theo Phản biện (D9)
    previous: RoleRun | None = None             # bản đang sửa -> supersedes, round+1

class OrchestratorRunResponse(BaseModel):
    status: Literal["done", "stopped"]
    run: RoleRun | None
    stop: StopReason | None                     # HTTP 200 khi dừng ở cổng (#19 mục 4)
    budget: BudgetView                          # đã dùng / còn lại
```

Lỗi hệ thống: HTTP 503 với `classify_generation_error`, giữ nguyên vỏ `{code, message, request_id}`. Thêm mã snake_case mới nếu cần, ví dụ `no_eligible_model`, `stale_input`, `budget_exhausted`. Không thêm trường vào `detail`.

## 5. Luồng xử lý một stage (`services/orchestration/run.py`)

```
1. check_prerequisites(stage, req)     # có đủ thượng nguồn; math không còn 'failed'
2. verify_hashes(req)                   # hash thượng nguồn khớp nội dung gửi kèm -> nếu không: stale_input
3. check_budget(req)                    # ≤12 lượt / Bài giảng, ≤~6 / nhà cung cấp
4. excluded = models_of(thượng nguồn)
5. routes = role_routes(stage, excluded, cooldowns)   # rỗng -> no_eligible_model, giữ Bản soạn
6. prompt = build_prompt(stage, req)    # JSON gọn, chỉ trường cần; đo prompt_chars
7. result, route = gateway.generate_structured(..., routes=routes)
8. validate(stage, result, req)         # kiểm bằng code, xem bảng dưới
   ├─ lỗi xác định & round < 2 -> gọi lại với danh sách lỗi (vòng tự sửa)
   └─ lỗi sau 2 vòng -> status="stopped"
9. return RoleRun(..., is_primary_model = route == routes_primary)
```

Kiểm tra sau mỗi stage, toàn bộ bằng code:

| Stage | Kiểm tra |
|---|---|
| `math` | Mỗi `MathClaim` qua `math_spec.verify` (Cổng toán, tiến trình con `spawn`). `failed` -> sửa tối đa 2 vòng. `unverified` -> dừng chờ giáo viên (#26), không tự sinh lại (D9). |
| `slides` | Mỗi slide thuộc đúng một Mục, số slide = `slide_count` đã duyệt (#40); công thức trích từ `MathClaimSet` phải trỏ đúng `claim.id` + hash (D7). |
| `lesson_plan` | `validate_5512_lesson_plan`; 4 Hoạt động khớp Dàn ý. |
| `review` | Mỗi `ReviewIssue` trỏ tới Ref có thật; `owner_stage` hợp lệ. Phản biện không sửa trực tiếp (D9). |
| mọi stage | Không có số liệu, định lý, trích dẫn ngoài Nguồn đã duyệt hoặc Mệnh đề toán: nguồn trích dẫn bằng số thứ tự trong ngữ cảnh, như `used_sources` ở `workbench_outline.py`. |

- **[QĐ-3]** Vòng tự sửa ở bước 8 dùng **cùng Model** (Model đó đã thấy lỗi của chính nó) hay **Model kế tiếp**? Đề xuất: cùng Model, vì lỗi là lỗi có phép kiểm xác định chứ không phải "suy luận lặp lại", và đỡ tốn quota nhà cung cấp khác. Mỗi vòng vẫn tính vào ngân sách.

## 6. Thay đổi ở `LLMGateway`

1. **Phân công model theo Vai trò** đọc từ cấu hình server, ví dụ `app/backend/data/role_models.json` hoặc biến môi trường. Giáo viên chỉ xem.
   ```json
   {"math": ["groq:<model-A>", "google:<model-B>", "openrouter:<model-C>"], "slides": ["..."]}
   ```
   Kiểm lúc khởi động: mỗi Vai trò có ≥ 3 Model trên ≥ 2 nhà cung cấp, và năm Model chính khác nhau. Sai thì ghi log rõ Model nào, vì sao (ADR 0010).
2. `generate_structured(..., routes: list[ProviderRoute] | None = None)` nhận danh sách tuyến do bộ điều phối tính, thay cho `get_active_routes(task_type)`. Trả thêm tuyến đã thắng, ví dụ `GenerationResult(value, route, attempts)`, vì hiện hàm chỉ trả `value` nên không biết Model nào đã chạy.
3. **Tạm nghỉ**: 503/504 hai lần liên tiếp thì Model nghỉ 5 phút với mọi Vai trò. Lưu trong bộ nhớ, mất khi khởi động lại (đúng ADR 0010). Dùng chung với `_dead_models`.
4. Giữ hạn 45 s mỗi lượt gọi; đặt thêm hạn cho cả stage (**[QĐ-5]**).

- **[QĐ-4]** Tên Model cụ thể cho từng Vai trò và thứ tự dự phòng. ADR 0010 để mở. Ràng buộc từ memory: demo chỉ dùng gói miễn phí; các model OpenRouter đang cấu hình là model trả phí, không phải `:free`.

## 7. Ngân sách lượt gọi

Server không giữ trạng thái, nên ngân sách được đếm từ `role_runs` client gửi lên, cộng các vòng sửa (`round`). Client có thể gửi thiếu. Với ứng dụng cục bộ một người dùng, đây là rào chắn chống lỗi chứ không phải chống gian lận.

- **[QĐ-6]** Chấp nhận đếm ngân sách phía client như trên, hay giữ bộ đếm trong bộ nhớ server theo `lesson_id`? (Bộ đếm server mất khi khởi động lại.)

## 8. Prompt cho từng Vai trò

Mỗi Vai trò một module `prompts/roles/<stage>.py` với `PROMPT_VERSION`. Quy tắc chung:

- Đầu vào là JSON gọn, chỉ có trường Vai trò cần; không đưa cả `RoleRun`. Ngân sách 12.000 ký tự cho Bộ slide (#40); vượt thì cắt ngữ cảnh thừa, không thay bằng nội dung mẫu.
- Mệnh đề toán đi vào prompt kèm `claim.id`; Vai trò sau trích lại bằng ID, không chép lại công thức tự do.
- Mỗi prompt (trừ Dàn ý) yêu cầu `doubts`: chỉ ra chỗ đầu vào có vẻ sai hoặc thiếu, không tự sửa.
- Câu cấm chung: không đưa số liệu, định lý, trích dẫn ngoài Nguồn đã duyệt và Mệnh đề toán.

## 9. Phía frontend

- `lessonGenerationActions.js` gọi `postJson('/api/v1/orchestrator/run', ...)` theo thứ tự `math → slides`; KHBD và Phản biện gắn vào nút bấm.
- Lưu `RoleRun` vào `role_runs` qua state trong `App.jsx` (không tạo store mới). O3.1 cảnh báo phải đưa trường này vào `currentProject` và danh sách phụ thuộc của effect lưu, kèm test lưu rồi nạp lại.
- Khi `output_hash` của Dàn ý đổi: slide của Mục bị sửa được đánh dấu "Cần xem lại"; KHBD bị đánh dấu "lệch Dàn ý" (ADR 0002). Chỉ sinh lại khi giáo viên đồng ý.
- Hiện cờ "model dự phòng" và tên Model trên từng kết quả (chỉ xem).

## 10. Kiểm thử (LLM giả, không gọi API thật)

- Quy tắc loại Model: `slides` không bao giờ chọn Model đã chạy `outline` hoặc `math`, kể cả khi đó là Model dự phòng.
- Hết Model hợp lệ -> 503 `no_eligible_model`, không có nội dung mẫu, Bản soạn giữ nguyên.
- Model không phải Model chính -> `is_primary_model = false`.
- Hash thượng nguồn sai -> `stale_input`.
- Vòng sửa dừng sau 2 vòng -> `status="stopped"`, HTTP 200.
- `unverified` dừng chờ giáo viên, không tự gọi lại.
- Tạm nghỉ sau hai lần 503 liên tiếp; hết 5 phút thì dùng lại được.
- Vượt ngân sách -> `budget_exhausted`.
- Contract test cập nhật `api_contract.json` đúng phạm vi đã duyệt.

## 11. Chia ticket đề xuất

1. Gateway: nhận `routes`, trả tuyến đã thắng, Tạm nghỉ (không đổi hành vi hiện có). Tách được, làm trước.
2. Cấu hình Phân công model + kiểm lúc khởi động (cần [QĐ-4]).
3. `RoleRun`, hàm băm chung, `orchestrator/run` khung với stage `math` (nối #20–#24).
4. Stage `slides` từ Dàn ý + `MathClaimSet` (sửa #40).
5. Stage `lesson_plan` từ Dàn ý (sửa #50, #31).
6. Stage `review` và vòng giao lỗi (#32, #9).
7. Frontend: `role_runs`, đánh dấu "Cần xem lại", hiện Model.

## 12. Tóm tắt quyết định cần chủ dự án chốt

| Mã | Câu hỏi | Đề xuất |
|---|---|---|
| QĐ-1 | Đổi danh sách `stage` của #19 (bỏ `visual`, KHBD và slide cùng từ Dàn ý) | Duyệt lại trên #19 |
| QĐ-2 | Dàn ý: endpoint #39 hay `stage="outline"` | Giữ #39, trả thêm `role_run` |
| QĐ-3 | Vòng tự sửa: cùng Model hay Model kế tiếp | Cùng Model |
| QĐ-4 | Phân công model cụ thể, chỉ gói miễn phí | Cần đo trước (#34) |
| QĐ-5 | Hạn thời gian cho cả stage và cả chuỗi | Đo trước (#34, O7.1) |
| QĐ-6 | Đếm ngân sách ở client hay server | Client |
| QĐ-7 | Cập nhật D13, O3.5, O4.1 trong tài liệu quyết định cho khớp ADR 0010 | Có, cùng PR với ticket 3 |
