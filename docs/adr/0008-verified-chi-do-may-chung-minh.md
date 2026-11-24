---
status: accepted
---

# `verified` chỉ do máy chứng minh; giáo viên duyệt không thay thế cho nhãn toán do hệ thống tính

Một Mệnh đề toán chỉ mang `verified` khi phép kiểm của máy chứng minh được nó, đúng trong Phạm vi công bố của phép kiểm; thử vài giá trị mẫu hay parse thành công không đủ. Mệnh đề chưa chứng minh được là `unverified`. `teacher_approved` không đủ để hiển thị các nhãn toán do hệ thống tính (điểm cực trị, giao điểm với trục, tiệm cận, các dòng của Bảng biến thiên) như kết quả chính xác. Ứng dụng phục vụ giáo viên dạy học sinh, và một nhãn sai trên màn chiếu khó bị phát hiện kịp, nên chúng tôi chấp nhận phạm vi hẹp hơn thay vì để người duyệt gánh phần chứng minh mà máy chưa làm được.

ADR này trước là ADR 0001 trên nhánh `feat/multi-role-orchestrator`; được đánh số lại khi gộp tài liệu domain (2026-11-24). Quyết định giữ nguyên, chỉ bỏ phần gắn với chuỗi nhiều vai trò mà spec thiết kế lại giao diện đã thay.

## Considered Options

- **Cho `teacher_approved` thay thế kiểm chứng máy.** Mở rộng phạm vi nhanh hơn, nhưng các nhãn này hiện ra trong lúc chiếu theo thao tác của giáo viên, và giáo viên không thể duyệt trước từng nhãn. Bị loại.
- **Dùng LLM để gắn `verified`.** Mức độ chắc chắn do LLM tự gắn không đủ làm bằng chứng. Bị loại.

## Consequences

- Mỗi nhãn toán mới muốn hiện là chính xác phải có phép kiểm thuộc Phạm vi công bố. Thiếu phép kiểm thì báo "chưa hỗ trợ" và mở ticket mở rộng; không có đường tắt bằng duyệt tay.
- Giáo viên vẫn duyệt diễn đạt và cách dạy qua Xác nhận chuyên môn; đó là cổng khác.
