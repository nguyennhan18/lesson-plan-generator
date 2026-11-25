# DECISIONS.md — Nhật ký quyết định kiến trúc (`LessonAI-5512`)

- **ADR-008 (Trạng thái: Đã được thay thế / Superseded tại `#59`, 2026-11-26):**
  - ADR-008 của giao diện Studio bản 2 cũ đã được thay thế bởi các quyết định kiến trúc của Bàn làm việc bản 3 (`docs/adr/`):
    - **ADR 0003** (`docs/adr/0003-khung-ban-lam-viec.md`): Khung Bàn làm việc ba cột, Canvas 16:9 (`1600 × 900`), Dải slide và chế độ Trình chiếu toàn màn hình là giao diện mặc định và duy nhất của ứng dụng.
    - **ADR 0005** (`docs/adr/0005-xac-nhan-khong-het-han.md`): Xác nhận dữ kiện hình và Xác nhận chuyên môn dùng khóa ký lâu dài `signing.key` trong thư mục cấu hình theo người dùng, không hết hạn theo thời gian và chỉ mất hiệu lực khi nội dung nguồn thay đổi hoặc khóa ký bị thay.
    - **ADR 0007** (`docs/adr/0007-yeu-cau-truc-quan-toan-12.md`): Bốn loại Yêu cầu trực quan Toán 12 trong Bàn làm việc (`graph` có tô miền diện tích và điểm đặc biệt qua Cổng toán, `bbt` Bảng biến thiên 3 bước hiện dần cho 3 họ hàm, `solid` Khối đa diện có khai triển, `oxyz` Hình Oxyz), bỏ hai hình cũ ngoài phạm vi Toán 12 (`arithmetic_sequence`, `inequality_system`).
