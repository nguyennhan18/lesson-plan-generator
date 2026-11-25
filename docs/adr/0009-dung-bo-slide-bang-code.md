---
status: superseded by ADR-0002
---

> Bị thay bởi ADR 0002 (Dàn ý là nguồn chung) và spec #36, theo quyết định của chủ dự án ngày 2026-11-24. Bộ slide được dựng từ Dàn ý bằng một lượt gọi AI; Kế hoạch bài dạy chỉ sinh khi giáo viên bấm. Mối lo về quota mà ADR này nêu (prompt sinh slide khoảng 24.600 ký tự) được xử lý bằng ngân sách kích thước prompt trong ticket #40. ADR này ban đầu được tạo với số 0002 (trùng số), nay đánh lại thành 0009 và giữ nguyên nội dung bên dưới để truy vết.

# Bộ slide được dựng bằng code từ Kế hoạch bài dạy, không gọi AI

Bộ slide được dựng tất định từ nội dung có cấu trúc của Kế hoạch bài dạy. Mỗi Kiến thức trọng tâm thành một slide khái niệm. Mỗi Ví dụ thành một slide đề bài và một slide lời giải. Mỗi Bài luyện tập thành một slide câu hỏi. Lý do có hai. Lời gọi AI sinh slide (prompt khoảng 24.600 ký tự, kèm cả Kế hoạch bài dạy) là nguyên nhân chính làm vượt quota gói miễn phí. AI cũng hay làm Bộ slide lệch nội dung so với Kế hoạch bài dạy. Dựng bằng code thì mỗi Bài giảng chỉ còn 1–2 request, và hai sản phẩm luôn đồng bộ.

## Considered Options

- **Gọi AI sinh Bộ slide từ Kế hoạch bài dạy** (cách cũ). Bị loại: tốn request, dễ lệch nội dung.
- **Dựng bằng code, rồi gọi AI để "trình bày lại" cho hay hơn.** Bị loại trong giai đoạn này: lại tốn thêm request và mở lại khả năng lệch nội dung.

## Consequences

- Bộ slide chỉ hay bằng Kế hoạch bài dạy. Mọi cải thiện chất lượng phải làm ở Kế hoạch bài dạy.
- Hình minh họa (đồ thị, khối 3D) phải được khai báo ngay trong Kế hoạch bài dạy thì bộ dựng slide mới có để dùng.
