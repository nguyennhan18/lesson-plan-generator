---
status: accepted
---

# Xác nhận không hết hạn theo thời gian

Cả hai loại xác nhận của giáo viên đều được ký bằng một khóa lưu trên máy của giáo viên, và khóa này không bao giờ được đưa vào git:

- xác nhận dữ kiện của một Yêu cầu trực quan;
- Xác nhận chuyên môn của một phiên bản Bộ slide hoặc Kế hoạch bài dạy.

Xác nhận không hết hạn theo thời gian và vẫn còn sau khi khởi động lại máy hay backend. Nó chỉ mất hiệu lực khi thứ được xác nhận thay đổi: với hình là dữ kiện của hình, hoặc đề bài hay công thức trên slide chứa hình đó; với Xác nhận chuyên môn là nội dung của phiên bản đã duyệt. Lý do: giáo viên thường soạn bài trước vài ngày. Với khóa nằm trong bộ nhớ và hạn 24 giờ như trước, mọi Hình tương tác sẽ biến mất và bài đã duyệt lại thành Bản nháp đúng lúc lên lớp.

## Considered Options

- **Giữ hạn 24 giờ và khóa trong bộ nhớ** (cách cũ). Bị loại: giáo viên buộc phải xác nhận lại mọi hình và duyệt lại bài ngay trước tiết dạy, hoặc chiếu bài không có hình.
- **Bỏ chữ ký, chỉ lưu một cờ "đã xác nhận" trong dự án.** Bị loại: khi đó nội dung do AI sinh hoặc dữ liệu nhập từ ngoài có thể tự gắn cờ đã xác nhận.

## Consequences

- Trước khi vào Trình chiếu, hệ thống cảnh báo nếu còn hình chưa xác nhận hoặc Bộ slide chưa có Xác nhận chuyên môn. Hình chưa xác nhận bị ẩn hẳn khỏi slide, không để khung trống và không dùng ảnh thay thế (ADR 0001).
- Nếu mất tệp khóa, mọi xác nhận cũ mất hiệu lực và giáo viên phải xác nhận lại.
- Quyết định này thay phần hạn 24 giờ và khóa trong bộ nhớ của cả token xác nhận hình lẫn token duyệt bài trong ADR-008 của `project-management/decisions/DECISIONS.md`.
