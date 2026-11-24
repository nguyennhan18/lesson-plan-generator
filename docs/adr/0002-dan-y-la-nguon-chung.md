---
status: accepted
---

# Dàn ý là nguồn chung của Bộ slide và Kế hoạch bài dạy

Trước đây Bộ slide được dựng từ Kế hoạch bài dạy, nên mỗi Bài giảng phải đi qua chuỗi Dàn ý → Kế hoạch bài dạy → Bộ slide. Nay cả Bộ slide và Kế hoạch bài dạy đều dựng trực tiếp từ Dàn ý đã duyệt. Luồng chính (prompt → Dàn ý → Bộ slide → Trình chiếu) chỉ sinh Bộ slide; Kế hoạch bài dạy chỉ được sinh khi giáo viên yêu cầu. Lý do: giáo viên chuẩn bị tiết dạy theo đúng thứ tự này, luồng chính bớt một lượt gọi AI (xem hệ quả về quota trong ADR 0001), và hai sản phẩm đồng bộ qua cùng một nguồn đã duyệt thay vì để sai sót của Kế hoạch bài dạy lan sang slide.

## Considered Options

- **Giữ chuỗi Dàn ý → Kế hoạch bài dạy → Bộ slide** (cách cũ). Bị loại: ba lượt gọi AI cho mỗi Bài giảng, giáo viên phải chờ một văn bản chưa cần dùng ngay, và lỗi ở Kế hoạch bài dạy lan sang slide.
- **Bỏ Kế hoạch bài dạy.** Bị loại: Kế hoạch bài dạy theo Công văn 5512 là hồ sơ nhà trường yêu cầu, và là lý do sản phẩm tồn tại.

## Consequences

- Dàn ý phải mang đủ cấu trúc để dựng được một Kế hoạch bài dạy 5512 mà không cần đến Bộ slide.
- Kiểm tra độ trung thành đối chiếu Bộ slide với Dàn ý, không đối chiếu với Kế hoạch bài dạy.
- Dữ liệu chỉ chảy một chiều, từ Dàn ý sang Bộ slide và Kế hoạch bài dạy. Sửa trên Slide không làm đổi Dàn ý. Sửa một Mục dàn ý chỉ sinh lại slide của Mục đó, sau khi giáo viên đồng ý. Kế hoạch bài dạy đã soạn trước khi Dàn ý đổi bị đánh dấu lệch Dàn ý.
