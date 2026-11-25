---
status: accepted
---

# Luật tầng do máy cưỡng chế, và `services/` chia theo việc

Backend có một thứ tự tầng duy nhất, `import-linter` cưỡng chế trên CI:

```text
api | tooling  →  exporters  →  services  →  llm | rag | parsers | prompts  →  schemas  →  core | utils
```

Mũi tên nghĩa là "được phép import". Hợp đồng nằm trong `[tool.importlinter]` của
`app/backend/pyproject.toml`; `make lint` chạy nó, và mọi import đi ngược chiều làm
CI đỏ. Bên trong tầng `services`, mã chia thành năm nhóm theo việc nó làm —
`generation/`, `quality/`, `visuals/`, `math/`, `assistant/` — cộng ba tệp đứng
riêng vì không thuộc nhóm nào: `jobs.py`, `uploads.py`, `analytics.py`.

Hai chỗ đặt nghịch trực giác, nên chốt ở đây để không ai "sửa lại":

- `exporters` nằm **trên** `services`, vì một bộ xuất phải chạy cổng chất lượng và
  vẽ hình trước khi ghi tệp. Nó dùng `services`, không phải ngược lại.
- `jobs.py` nằm ở `services/`, không ở `core/`, vì nó nạp worker của `services`.
  `core` chỉ chứa phần không phụ thuộc nghiệp vụ.

Lý do cần máy cưỡng chế: luật tầng đã được viết trong `AGENTS.md` từ trước, nhưng
không có gì kiểm. Khi dựng cổng lint lần đầu, đo được **12 import vi phạm** mà
không ai biết, gồm `core` nạp `services`, ba bộ xuất nạp `api.routes` và `parsers`
nạp `services`. Một luật chỉ có trong tài liệu thì mỗi tuần lại lệch thêm một ít.

Lý do gom `services/`: nó từng là 19 tệp phẳng với tên như `workbench_quality.py`,
`content_quality.py`, `lesson_quality.py`, `visual_requirements.py`,
`expert_confirmation.py` nằm cạnh `math_worker.py` và `geometry_scene.py`. Muốn
biết "chỗ nào chặn bài này" phải đọc tên từng tệp rồi mở thử. Nhóm theo việc thì
mỗi `__init__.py` nói được nhóm đó chịu trách nhiệm gì, và chỗ cần tìm thu hẹp
ngay từ tên thư mục.

## Considered Options

- **Giữ luật tầng chỉ trong tài liệu.** Bị loại: đã thử rồi, và kết quả đo được là
  12 vi phạm tích tụ không ai thấy.
- **Chia `services/` theo lớp kỹ thuật** (`handlers/`, `helpers/`, `models/`). Bị
  loại: tên như vậy không trả lời được câu hỏi người sửa đang hỏi. "Cổng chất lượng
  ở đâu" là câu hỏi theo việc, không theo lớp.
- **Chia theo ticket hoặc theo giao diện** (`workbench/`, `studio/`). Bị loại: giao
  diện cũ đã bị bỏ ở `#59`, và nếu chia theo giao diện thì `content_quality.py`
  phải nằm ở cả hai chỗ.
- **Đổi tên tệp khi gom** (ví dụ `services/math/expression.py` thay cho
  `math/math_expression.py`). Hoãn, không loại: gom và đổi tên cùng lúc thì
  `git log --follow` của từng tệp khó theo, và một đợt đổi tên riêng sau này rẻ hơn
  một đợt gom bị trộn hai việc.
- **Dựng cổng lint rồi sửa hết vi phạm trong một commit.** Bị loại: 12 vi phạm cần
  bốn lần chuyển mã xuyên tầng; làm chung một commit thì không còn cách nào kiểm
  chứng từng phần. Thay vào đó, mỗi vi phạm được ghi một dòng `ignore_imports` kèm
  cách xử lý đã chốt, rồi xoá dần — từ 10 dòng xuống 1.

## Consequences

- Thêm một dòng vào `ignore_imports` là nới luật, nên cần chủ dự án duyệt trước
  (`AGENTS.md`, mục Boundaries). Dòng duy nhất còn lại là
  `schemas.schemas -> rag.curriculum_registry`.
- **Việc còn mở — `schemas` nạp `rag`:** validator của `LessonRequest` và
  `OutlineRequest` gọi `infer_lesson_id` của registry. Bỏ cạnh này là đổi hành vi
  phân tích request, nên nó là một ticket riêng, không phải việc kèm theo của một
  đợt tái cấu trúc.
- **Việc còn mở — tiền tố `workbench_`:** giao diện cũ đã bị bỏ ở `#59`, nên
  `workbench_` không còn phân biệt được gì. Tám tệp còn mang tiền tố này
  (`workbench_quality`, `workbench_visuals`, `workbench_assistant`,
  `workbench_outline`, `workbench_slides`, `workbench_lesson_plan` và hai schema).
  Bỏ tiền tố là một đợt đổi tên riêng; làm chung với đợt gom thì mất khả năng
  truy vết từng tệp.
- **Việc còn mở — chữ "provenance" đang mang ba nghĩa:**
  `schemas/provenance.py` là metadata của lần sinh nội dung,
  `services/quality/artifact_provenance.py` là phần XML nhúng trong tệp Office, và
  `rag/` từng có `provenance.py` nói về nguồn học liệu (đã xoá ở `1f519b6`). Cần
  chốt từ vựng trong `GLOSSARY.md` trước khi thêm nghĩa thứ tư.
- Khi thêm module mới, đặt nó vào nhóm trả lời đúng câu hỏi "ai sẽ đi tìm tệp này,
  và họ đang hỏi gì". Nếu không nhóm nào vừa, để phẳng trong `services/` và nói lý
  do trong docstring — đó là trường hợp của `jobs.py`, `uploads.py`, `analytics.py`.
- Cổng lint phải gọi bằng console script `lint-imports`. Gọi
  `python -m importlinter.cli` chỉ nạp module rồi thoát 0, tức cổng luôn xanh —
  đã thử và xác nhận.
