---
status: accepted
---

# Hình tương tác chỉ sinh từ Yêu cầu trực quan đã xác nhận ở Dàn ý

Một đồ thị hàm số hay hình không gian chỉ xuất hiện trên Slide khi Mục dàn ý chứa nó có một Yêu cầu trực quan mà giáo viên đã xác nhận dữ kiện ngay lúc duyệt Dàn ý. AI chỉ được đề xuất Yêu cầu trực quan khi Mục có đối tượng toán cụ thể (một biểu thức hàm số, hoặc một hình có đủ giả thiết và số đo); giáo viên tự thêm được vào bất kỳ Mục nào; bước sinh slide không được thêm, bỏ hay đổi Hình tương tác. Lý do: AI hay chèn hình không khớp đề bài, và một hình sai chiếu trước lớp gây hại nhiều hơn là không có hình.

## Considered Options

- **Xác nhận trên từng slide sau khi sinh** (cách cũ). Bị loại: giáo viên phải xác nhận nhiều lần, và AI đã dựng slide quanh một hình có thể sai trước khi giáo viên kịp kiểm tra.
- **Để AI tự thêm hình khi slide có công thức.** Bị loại: đây chính là kiểu tạo hình bừa bãi cần chặn.

## Consequences

- Xác nhận gắn với Mục dàn ý chứ không gắn với Slide, vì lúc xác nhận chưa có slide nào.
- Mỗi Yêu cầu trực quan hiện trên ít nhất một Slide của Mục chứa nó, và không hiện ngoài Mục đó.
- Khi giáo viên thêm hình ngay trong màn Bộ slide, thao tác đó tạo một Yêu cầu trực quan mới cho Mục của slide, và vẫn phải xác nhận dữ kiện. Trợ giảng AI cũng không được thêm hay đổi Hình tương tác.
- Bảng biến thiên (kể cả bảng xét dấu) theo cùng luật: hệ thống tính từ biểu thức đã xác nhận, AI không được tự viết.
- Quyết định này thay phần xác nhận hình theo từng slide trong ADR-008 của `project-management/decisions/DECISIONS.md`.
