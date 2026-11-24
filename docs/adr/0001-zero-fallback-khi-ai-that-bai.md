---
status: accepted
---

# Không thay nội dung mẫu khi AI thất bại (zero-fallback)

Khi AI, bộ phân tích hay bộ xuất thất bại, hệ thống trả lỗi có mã rõ ràng và giữ nguyên Bản soạn của giáo viên. Hệ thống không bao giờ tự chèn một Kế hoạch bài dạy hay Bộ slide mẫu thay cho kết quả của AI. Lý do: nội dung mẫu (khung dựng sẵn, chỉ thay tên bài vào chỗ trống) trông giống kết quả thật. Giáo viên dễ dùng nhầm, và đó là nguồn lớn nhất của các bài "sơ sài" quan sát được trên nhánh `main` cũ.

## Considered Options

- **Trả giáo án mẫu và để cảnh báo trong `warnings`** (cách cũ). Bị loại: giáo viên không đọc cảnh báo, và nội dung sai chủ đề vẫn đi tới DOCX/PPTX.
- **Giữ giáo án mẫu nhưng dán nhãn "Mẫu, không phải AI tạo", giáo viên phải tự chọn mới được dùng.** Bị loại: vẫn phải bảo trì hàng nghìn dòng nội dung mẫu cho từng bài, và nội dung mẫu chưa qua người duyệt thật (xem Nguồn đã duyệt).

## Consequences

- Khi nhà cung cấp AI hết quota hoặc lỗi, giáo viên thấy thông báo lỗi và nút thử lại, không thấy bài. Vì vậy phải giảm số request cho mỗi Bài giảng để lỗi quota hiếm khi xảy ra.
