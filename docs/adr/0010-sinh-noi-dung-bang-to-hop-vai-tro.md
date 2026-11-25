---
status: accepted
confirmed: 2026-11-25
---

# Sinh nội dung bằng năm Vai trò, mỗi Vai trò có Phân công model riêng

Bài giảng được sinh bởi năm Vai trò, mỗi Vai trò có nhiệm vụ, đầu vào và đầu ra riêng:

- **Người lập Dàn ý**
- **Chuyên gia toán** (kết quả đi qua Cổng toán)
- **Người dựng slide**
- **Người soạn Kế hoạch bài dạy**, chỉ chạy khi giáo viên bấm
- **Phản biện**, chỉ chạy khi giáo viên bấm

Chủ dự án xác nhận tiếp tục phương án năm Vai trò với năm Model chính khác nhau và Phản biện theo yêu cầu trong phiên thiết kế ngày 2026-11-25. Bộ slide được ưu tiên trong luồng chính; Kế hoạch bài dạy dùng cùng Dàn ý đã duyệt và các Mệnh đề toán, được tạo khi giáo viên yêu cầu theo ADR 0002.

Mỗi Vai trò chạy bằng Model do chủ dự án phân công trong cấu hình server; giáo viên chỉ xem được phân công này. Một Vai trò không được chạy cùng Model với bất kỳ Vai trò nào đã góp vào đầu vào của nó, kể cả gián tiếp. Vì vậy Phản biện phải khác Model với cả bốn Vai trò tạo nội dung. Nhờ vậy mỗi bước nhìn đầu vào bằng một cách suy luận khác, giảm việc lặp lại chỗ bịa và sự tự tin thái quá của bước trước. Khác Model là đủ, không bắt buộc khác hãng. Mỗi Vai trò, trừ Người lập Dàn ý, trả kèm Nghi vấn về đầu vào. Không Vai trò nào được đưa ra số liệu, định lý hay trích dẫn không có trong Nguồn đã duyệt hoặc Mệnh đề toán.

Lý do chính là chất lượng: phần toán cần model suy luận mạnh, phần dựng slide cần model nhanh. Lợi ích phụ là các lượt gọi được rải ra nhiều nhà cung cấp miễn phí. Quyết định này giữ giao diện và luồng của spec #36, chỉ thay động cơ sinh nội dung phía sau. Nó cũng đảo ngược quyết định "mọi vai trò dùng chung một model" của spec #18.

## Considered Options

- **Một model cho mọi bước, chọn trong Cài đặt** (spec #36 ban đầu). Bị loại: một model khó vừa giỏi toán vừa nhanh, mọi lượt gọi dồn vào một gói quota, và bước sau dễ tin theo chỗ sai của chính nó ở bước trước.
- **Chuỗi sáu vai trò của #18, có Thiết kế trực quan.** Bị loại: hình chỉ sinh từ Yêu cầu trực quan đã xác nhận, và đồ thị do server tính (ADR 0003, 0006), nên phần trực quan không cần AI.
- **Cho giáo viên tự chọn model cho từng Vai trò.** Bị loại: giáo viên không có thông tin để biết model nào hợp với Vai trò nào.
- **Bắt buộc các Vai trò liên tiếp khác hãng model** (ví dụ Gemini rồi GPT). Bị loại theo quyết định của chủ dự án ngày 2026-11-24: chỉ cần khác Model, cùng hãng vẫn được.

## Consequences

- Ngân sách tăng lên 12 lượt cho mỗi Bài giảng, mỗi nhà cung cấp tối đa khoảng 6 lượt. Chuỗi chính tốn khoảng 3 lượt, tối đa khoảng 9 lượt khi có sửa và Phản biện.
- Mỗi Vai trò có một Danh sách dự phòng do chủ dự án đặt, ít nhất 3 Model trên ít nhất 2 nhà cung cấp. Một Model chỉ được vào danh sách khi hạn mức của nó chứa được một lượt gọi của Vai trò đó; quy tắc 2 nhà cung cấp chỉ tính các Model này. Model chính của năm Vai trò là năm Model khác nhau.
- Khi Model đang dùng hỏng (khóa hết hạn, model bị gỡ, hết quota, quá tải), Vai trò chuyển sang Model kế tiếp trong danh sách. Model đó phải còn dùng được và khác Model của mọi Vai trò đã góp vào đầu vào. Nó được phép trùng với Model của một Vai trò không liên quan.
- Kết quả chạy bằng Model không phải Model chính mang cờ "model dự phòng". Không còn Model nào thỏa thì hệ thống dừng và giữ nguyên Bản soạn (ADR 0001).
- Model trả lỗi quá tải (503/504) hai lần liên tiếp bị Tạm nghỉ 5 phút với mọi Vai trò. Trạng thái này mất khi khởi động lại server.
- Chủ dự án thấy được Model nào không dùng được và vì sao, qua phép kiểm lúc khởi động và lúc chạy.
- Các ticket của #36 có tiêu chí "một lượt gọi AI" và có Cài đặt chọn model (#39, #40, #46, #50) phải được sửa lại cho khớp.

## Các quyết định còn mở

- Model cụ thể và nhà cung cấp cho từng Vai trò, cùng thứ tự Danh sách dự phòng, cần được đối chiếu với khả năng truy cập và hạn mức thực tế. Tên model trong các đề xuất trước đây chưa phải Phân công model đã chốt.
- Cần chốt thời gian chờ mục tiêu cho chuỗi tạo Bộ slide, cho Kế hoạch bài dạy và cho Phản biện; phân biệt mục tiêu đo lường với thời hạn dừng một lần chạy.
- Cần chốt phạm vi sử dụng dịch vụ miễn phí hoặc có phí trước khi chọn danh sách ứng viên và chạy phép đo có chi phí.
- Cần chốt bộ bài đối chiếu và tiêu chí chọn Model theo từng Vai trò, gồm chất lượng nội dung, lỗi toán, tuân thủ cấu trúc đầu ra, thời gian và lượng token.

Các xác nhận trên ghi nhận thiết kế. Việc phân công năm Model và điều phối các Vai trò còn cần triển khai và kiểm thử.
