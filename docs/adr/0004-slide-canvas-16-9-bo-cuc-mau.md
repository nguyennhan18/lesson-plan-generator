---
status: accepted
---

# Slide là khung 16:9 có phần tử đặt vị trí; AI chỉ chọn bố cục mẫu

Mỗi Slide là một khung 16:9 cố định, tự co giãn theo màn hình hay máy chiếu, chứa các phần tử (chữ, công thức, ảnh, Hình tương tác) đặt ở vị trí cụ thể; giáo viên kéo thả và đổi kích thước được. AI không sinh tọa độ: nó chọn một bố cục mẫu, và bố cục mẫu quyết định vị trí ban đầu của các phần tử. Lý do: giáo viên cần chỉnh bố cục như trên PowerPoint, còn tọa độ do AI tự sinh dễ chồng lấn và khó kiểm tra.

## Considered Options

- **Chỉ đổi giữa các bố cục mẫu, không kéo thả.** Bị loại: giáo viên không chỉnh được bố cục khi nội dung không vừa mẫu.
- **Bảng vô hạn (mọi slide nằm trên một mặt phẳng, chiếu bằng cách phóng và lướt).** Bị loại: khó xuất sang PPTX và khó dùng với máy chiếu trong lớp.
