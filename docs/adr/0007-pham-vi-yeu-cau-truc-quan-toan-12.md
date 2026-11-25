---
status: accepted
---

# Phạm vi Yêu cầu trực quan cho Toán 12

Yêu cầu trực quan chỉ gồm ba loại, chọn theo nội dung Toán 12 (GDPT 2018):

- đồ thị hàm số;
- hình không gian: ba khối sẵn có (hình lập phương, chóp tứ giác đều, chóp đáy vuông có SA vuông góc đáy) và Hình Oxyz (điểm, vectơ, đường thẳng, mặt phẳng, mặt cầu);
- Bảng biến thiên cho ba dạng hàm: bậc ba, phân thức bậc nhất trên bậc nhất, phân thức bậc hai trên bậc nhất.

Quyết định này thay mục 1 của ADR-008 trong `project-management/decisions/DECISIONS.md`, vốn giới hạn hình 3D ở ba khối. Lý do: hình học không gian ở Toán 12 chủ yếu diễn ra trong hệ trục Oxyz, còn thể tích khối chóp và khối lăng trụ thuộc Toán 11.

## Considered Options

- **Chỉ giữ ba khối** (ADR-008). Bị loại: không phục vụ được các chương về hệ trục tọa độ Oxyz, vốn là phần hình không gian chính của Toán 12.
- **Thêm luôn khối tròn xoay sinh từ đồ thị trong bản đầu.** Để sau, cho bản đầu tập trung vào Hình Oxyz.

## Consequences

- Bỏ hai loại hình của lớp khác đang có trong hệ thống: dãy số cộng (Toán 11) và miền nghiệm hệ bất phương trình (Toán 10).
- Để sau, chưa làm: khối tròn xoay, đối tượng suy ra trong Hình Oxyz (giao điểm, hình chiếu, khoảng cách), thanh trượt tham số, vẽ đạo hàm hay tiếp tuyến, sơ đồ cây xác suất, biểu đồ thống kê.
