# Tài liệu Đặc tả Yêu cầu Phần mềm (SRS)

**Tên hệ thống:** LessonAI-5512  
**Phiên bản:** 0.1  
**Tác giả:** Manus AI

## 1. Mục đích và phạm vi

LessonAI-5512 hỗ trợ giáo viên Toán THCS/THPT tạo bản nháp kế hoạch bài dạy theo khung Công văn 5512, sinh hình học từ tham số và tạo slide bài giảng có thể chỉnh sửa. Hệ thống không tự động phê duyệt tính đúng đắn sư phạm; mọi tài liệu trước khi tải xuống phải qua bước xem trước và xác nhận của giáo viên.

Phạm vi PoC gồm bài học một tiết hoặc một chủ đề ngắn, đầu ra DOCX và PPTX, tiếng Việt, các dạng hình cơ bản như điểm, đoạn thẳng, tam giác, đường tròn, góc và đồ thị đơn giản. Ngoài phạm vi gồm chấm điểm học sinh tự động, quản lý điểm chính thức, đồng bộ LMS và sinh video.

## 2. Người dùng và giả định

| Actor | Nhu cầu |
|---|---|
| Giáo viên | Nhập chủ đề, lớp, thời lượng; chỉnh sửa; duyệt; xuất file |
| Tổ trưởng/chuyên môn | Xem, nhận xét, tái sử dụng mẫu |
| Quản trị viên | Quản lý mẫu, người dùng, quota, log và quyền |
| LLM Gateway | Sinh JSON theo schema; không truy cập trực tiếp cơ sở dữ liệu |
| MCP_Geometry | Nhận tham số hình học, trả SVG/metadata và lỗi |

Giả định đầu vào do giáo viên cung cấp là hợp pháp, không chứa dữ liệu nhạy cảm không cần thiết và có thể được xử lý bởi nhà cung cấp LLM đã cấu hình.

## 3. Yêu cầu chức năng

| ID | Yêu cầu | Ưu tiên | Tiêu chí nghiệm thu |
|---|---|---:|---|
| FR-01 | Tạo dự án bài học | Must | Lưu được môn, lớp, chủ đề, thời lượng, mục tiêu |
| FR-02 | Sinh cấu trúc kế hoạch bài dạy | Must | Kết quả có mục tiêu và đủ 4 hoạt động theo schema |
| FR-03 | Kiểm tra khung 5512 | Must | Validator báo thiếu/sai trường, không chỉ dựa vào LLM |
| FR-04 | Chỉnh sửa từng trường | Must | Người dùng sửa nội dung mà không mất lịch sử |
| FR-05 | Gọi MCP_Geometry | Must | Tạo hình từ JSON tham số, trả preview và metadata |
| FR-06 | Sinh DOCX | Must | Giữ template, heading, bảng, công thức/hình và metadata |
| FR-07 | Sinh PPTX | Must | Tạo slide theo layout, chữ/hình/bảng, có notes |
| FR-08 | Xem trước và duyệt | Must | Trạng thái draft → reviewed → approved |
| FR-09 | Tái sinh có kiểm soát | Should | Chọn phạm vi tái sinh, giữ phần đã khóa |
| FR-10 | Nhật ký audit | Must | Ghi ai, khi nào, prompt/model/template/version |
| FR-11 | Quản lý mẫu | Should | Tạo, phiên bản hóa, kích hoạt mẫu |
| FR-12 | Tải xuống artifact | Must | Chỉ cho phép tải artifact của người có quyền |

## 4. Quy tắc nghiệp vụ 5512

Trong PoC, hệ thống biểu diễn bài dạy bằng bốn hoạt động bắt buộc: **Mở đầu**, **Hình thành kiến thức mới**, **Luyện tập**, **Vận dụng**. Mỗi hoạt động có mục tiêu, nội dung/nhiệm vụ, sản phẩm và cách tổ chức thực hiện. Validator phải kiểm tra tên hoạt động, mục tiêu có thể quan sát, sản phẩm đầu ra và chỉ dẫn tổ chức; cho phép giáo viên cấu hình biến thể nhưng không cho phép thiếu hoạt động khi đánh dấu “chuẩn 5512”. Căn cứ văn bản và các phụ lục được lưu trong [1].

## 5. Yêu cầu phi chức năng

| Nhóm | Mức mục tiêu |
|---|---|
| Hiệu năng | P95 tạo bản nháp dưới 60 giây với bài học chuẩn; preview dưới 5 giây |
| Độ tin cậy | Retry tối đa 2 lần; job có trạng thái và idempotency key |
| Bảo mật | RBAC, TLS, secret server-side, audit log, giới hạn upload |
| Khả dụng | Giao diện responsive; lỗi có thể sửa; không mất bản nháp |
| Tương thích | DOCX/PPTX mở được trong Microsoft Office và LibreOffice ở mức PoC |
| Khả năng truy vết | Mọi nội dung sinh tự động gắn source, model, prompt version |
| Khả năng bảo trì | Module hóa validator, renderer, LLM gateway, MCP client |

## 6. Tiêu chí nghiệm thu PoC

PoC đạt khi 30/30 ca kiểm thử tạo được schema hợp lệ và 30/30 ca có đủ bốn hoạt động; ít nhất 90% trường nội dung đạt rubric chuyên môn do hai giáo viên chấm độc lập; 95% hình hình học không có lỗi tọa độ nghiêm trọng; 100% artifact mẫu mở được và không mất các vùng bắt buộc. Các con số này là **mục tiêu nghiệm thu đề xuất**, không phải kết quả đã đo.

## Tài liệu tham chiếu

[1]: https://boiduonghanoi.edu.vn/mod/folder/view.php?id=175 "Công văn 5512 và các phụ lục"  
[2]: https://json-schema.org/specification "JSON Schema Specification"
