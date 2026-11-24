---
status: accepted
---

# Đồ thị tương tác: server tính toán, trình duyệt chỉ vẽ

Đồ thị hàm số được vẽ trong trình duyệt, để khi Trình chiếu giáo viên phóng to, kéo khung nhìn, đọc tọa độ và bật các điểm đặc biệt. Tuy vậy, mọi phép phân tích và tính biểu thức vẫn chạy ở server, trong tiến trình con có giới hạn: server lấy mẫu điểm và dùng SymPy tính chính xác cực trị, giao điểm với trục, tiệm cận. Mỗi lần giáo viên phóng hay kéo, trình duyệt xin lại điểm cho khung nhìn mới. Lý do: chỉ có một bộ phân tích biểu thức làm nguồn sự thật, không chạy biểu thức trong JavaScript, và không thêm dependency.

## Considered Options

- **Thư viện vẽ đồ thị JavaScript tự tính biểu thức.** Bị loại: thêm dependency, và hai bộ phân tích (server dùng khi xuất file, trình duyệt dùng khi Trình chiếu) có thể cho kết quả khác nhau trên cùng một biểu thức.
- **Giữ ảnh PNG vẽ sẵn ở server** (cách cũ). Bị loại: không tương tác được.

## Consequences

- Mỗi lần phóng hay kéo, đồ thị cần backend đang chạy trên máy giáo viên. Độ trễ phải đủ thấp để thao tác trên lớp không bị giật.
