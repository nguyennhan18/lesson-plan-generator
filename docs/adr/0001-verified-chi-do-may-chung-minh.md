---
status: accepted
---

# `verified` chỉ do máy chứng minh; giáo viên duyệt không thay thế cho nhãn toán động của demo

Trong chuỗi tạo bài nhiều vai trò, một mệnh đề toán chỉ mang `verified` khi phép kiểm của máy chứng minh được nó, đúng trong phạm vi công bố của phép kiểm; thử vài giá trị mẫu hay parse thành công không đủ. Mệnh đề chưa chứng minh được là `unverified` và chuyển cho giáo viên duyệt, nhưng `teacher_approved` không đủ để hiển thị nhãn đạo hàm, nghiệm hoặc cực trị động của demo như kết quả chính xác (D1, D2, D12). Ứng dụng phục vụ giáo viên dạy học sinh, và một nhãn sai hiển thị trên màn chiếu khó bị phát hiện, nên chúng tôi chấp nhận phạm vi demo hẹp hơn thay vì để người duyệt gánh phần chứng minh mà máy chưa làm được.

## Considered Options

- **Cho `teacher_approved` thay thế kiểm chứng máy.** Mở rộng phạm vi nhanh hơn, nhưng nhãn động đổi theo tham số trong lúc chiếu mà giáo viên không thể duyệt từng giá trị trước đó. Bị loại.
- **Dùng LLM Phản biện để gắn `verified`.** Mức độ do LLM tự gắn không đủ làm bằng chứng (D9). Bị loại.

## Consequences

- Mỗi nhãn toán mới muốn hiện là chính xác phải có phép kiểm thuộc phạm vi công bố; thiếu phép kiểm thì cần ticket mở rộng, không có đường tắt bằng duyệt tay.
- Giáo viên vẫn duyệt diễn đạt và ý đồ sư phạm; đó là cổng khác (D12).
