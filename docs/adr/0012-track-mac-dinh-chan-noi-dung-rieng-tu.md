---
status: accepted
---

# Repo công khai: track mặc định, chỉ chặn artifact và nội dung riêng tư hoặc có bản quyền

Repo `nguyennhan18/lesson-plan-generator` là repo công khai. Git theo dõi mọi tệp, trừ năm nhóm: artifact sinh ra khi chạy (cache, build, log, `node_modules/`, `venv/`, `app/backend/output/`); bí mật và cấu hình cá nhân (`.env`, `.claude/settings.local.json`, `.vscode/`, `*.code-workspace`); tệp Office và PDF; học liệu SGK và corpus runtime (`data/raw/`, `data/processed/`, `app/backend/data/`); hồ sơ đồ án (`docs/requirements/`). Riêng `reports/` mặc định bị chặn, chỉ công bố thư mục bằng chứng được một ADR hoặc issue dẫn chiếu.

Lý do: trước đây `.gitignore` chặn cả `docs/`, `tests/`, `scripts/`, `.github/` rồi mở từng tệp bằng dòng `!`. Test hay tài liệu mới không có dòng `!` thì không vào Git, nên CI không chạy và người clone không thấy. `app/backend/tests/test_workbench_features.py` của #59 là một ca thật.

## Considered Options

- **Chặn mặc định, mở từng tệp bằng `!`** (cách cũ). Bị loại: mỗi test hay tài liệu mới cần thêm một dòng, quên là tệp mất khỏi Git và CI, và mỗi nhánh sửa cùng một vùng `.gitignore` nên xung đột khi gộp.
- **Chỉ track mã ứng dụng.** Bị loại: test, ADR và `AGENTS.md` không vào Git thì không review hay chạy CI được.

## Consequences

- Trước khi commit tệp mới, quét khoá API, token, ID Google Drive và thông tin cá nhân. Một tệp đã đẩy lên repo công khai coi như đã công bố, kể cả khi xoá sau đó.
- Muốn công bố một thư mục bằng chứng trong `reports/`, thêm một dòng `!` kèm ADR hoặc issue dẫn chiếu. Không ghi đè tệp bằng chứng đã có.
- Đổi quy tắc trong `.gitignore` vẫn cần chủ dự án duyệt trước (`AGENTS.md`, mục Boundaries).
