# Dữ liệu LessonAI

- `raw/`: học liệu gốc và bản trích xuất đã nhập trước đây, được bỏ qua trong Git.
- `fixtures/`: Golden Set nhỏ dùng trong kiểm thử, được Git theo dõi.
- `processed/`: đầu ra thử nghiệm của pipeline chuẩn bị dữ liệu, được bỏ qua trong Git.

Dữ liệu chuẩn mà ứng dụng đọc nằm tại `app/backend/data/`. Không sửa song song
bản runtime và bản trong `raw/`. Báo cáo kiểm kê được lưu tại `reports/data/`.

Xem [quy trình dữ liệu](../docs/architecture/repository.md#dữ-liệu).
