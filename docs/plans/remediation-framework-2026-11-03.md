# Khung kế hoạch sửa lỗi và nâng cấp Lesson-Plan-Generator

> **Cập nhật 04/11/2026: CHƯA ĐỦ ĐIỀU KIỆN BÀN GIAO.** Các phần triển khai và kiểm thử cục bộ không đồng nghĩa đóng mốc M1–M4. Xem [review sau triển khai và điều kiện đóng mốc](remediation-acceptance-2026-11-03.md) cùng [báo cáo thực hiện](../../reports/remediation-implementation-2026-11-03.md). Những trạng thái bên dưới mô tả thời điểm lập kế hoạch nếu chưa có ghi chú cập nhật.


Ngày lập: 03/11/2026. Căn cứ chính: [review toàn dự án R01–R23](../../reports/project-review-2026-11-02.md). Khung này tổng hợp để quản lý công việc; chi tiết kỹ thuật và thứ tự PR tiếp tục theo [kế hoạch sau tái cấu trúc](project-remediation-post-refactor.md) và [kế hoạch M1](remediation-m1-math-rendering.md).

## 1. Mục tiêu và điểm xuất phát

Mục tiêu là giáo viên có thể soạn, sửa, lưu, trình chiếu và xuất một bài giảng đúng nội dung; biết phần nào chưa được kiểm chứng; không mất công việc khi tác vụ lỗi. Thứ tự đầu tư: an toàn xử lý → dữ liệu nhất quán → chất lượng toán và học liệu → trình bày → canvas.

Theo các báo cáo đã có trong workspace:

| Hạng mục | Trạng thái được ghi nhận | Việc còn phải làm |
| --- | --- | --- |
| Tái cấu trúc | Đã tách backend package và frontend theo feature | Dùng cấu trúc hiện tại để sửa tiếp |
| M0 | Đã nghiệm thu chặn tạm; audit CLI được khôi phục | Giữ các chốt chặn cho tới khi giải pháp thay thế đạt |
| M1 / PR01-A | Đã có parser, fixture và bỏ parabol mặc định | Worker, nối runtime, render, frontend và kiểm tra hình đúng yêu cầu |
| M2–M5 | Chưa hoàn tất | Triển khai và nghiệm thu theo các mốc dưới đây |

Nguồn trạng thái: [review sau tái cấu trúc](../../reports/post-refactor-review-2026-11-02.md), [báo cáo M0](../../reports/remediation-m0-2026-11-02.md), [bàn giao PR01-A](../../reports/remediation-m1-pr01a-2026-11-03.md). Đây là tổng hợp tài liệu và cấu trúc dự án, chưa phải một lượt kiểm thử lại. Không dùng số liệu lỗi của review ban đầu làm trạng thái hiện tại nếu đã có bằng chứng mới hơn.

## 2. Lộ trình thực hiện

**Bổ sung bắt buộc ngày 03/11/2026: loại bỏ toàn bộ bài mẫu, bài gợi ý có sẵn và hình học mẫu khỏi luồng sản phẩm.** Khởi tạo bài/dàn ý/scene trống; gỡ preset và nội dung tự điền; thiếu dữ kiện hoặc API lỗi phải hiển thị trạng thái tương ứng. Gỡ cả điểm số, phiếu và trả lời chat giả lập. Kiểm tra cả backend fallback, storage và export để nội dung mẫu không quay lại từ đường khác. Giữ thuật toán dựng hình nhận dữ kiện thật và fixture kiểm thử tách khỏi bản production; bảo toàn bài giáo viên đã lưu.

Inventory, quy tắc và sáu ca nghiệm thu nằm trong mục **“Yêu cầu bổ sung ngày 03/11/2026 — Loại bỏ bài mẫu, bài gợi ý có sẵn và hình học mẫu khỏi sản phẩm”** của [kế hoạch tổng thể](project-remediation-post-refactor.md). Dọn hình mặc định ở M1; bài/dàn ý/preset/chat/thống kê ở M2; kiểm tra nguồn/fallback ở M3 và trạng thái tương tác ở M4; toàn bộ là điều kiện phát hành M5. Đây là yêu cầu mới trong kế hoạch, chưa phải đã gỡ nội dung khỏi mã ứng dụng.

| Mốc | Công việc và sản phẩm bàn giao | Đối chiếu review | Điều kiện hoàn thành |
| --- | --- | --- | --- |
| M0 — Chặn tạm, giữ phép đo | Giữ tính năng chưa an toàn ở trạng thái tạm ngắt; không patch mẫu khác bài; không đổi bài khi xuất lỗi; audit có đầu ra riêng | RF01, R01/R02/R03/R07/R12 | Duy trì các test chặn tạm đã có. Mốc này đã được báo cáo đạt |
| M1 — Khôi phục toán và hình đáng tin | Parser → worker có deadline → render theo figure riêng → frontend gọi API; cache theo spec; kiểm tra công thức/hình khớp yêu cầu gốc | R01/R02/R12; phần giới hạn R11/R15 | Đầu vào nguy hiểm bị từ chối; tác vụ quá hạn dừng được; hàm đúng miền; không nhầm ảnh khi đồng thời; không thay hình thiếu dữ kiện bằng hình mẫu |
| M2 — Soạn, lưu và sửa nhất quán | ID/revision cho project/deck/slide; migration; thêm/xóa/sắp xếp/xuất; lỗi có cấu trúc; Copilot có diff và kiểm tra phiên bản; phiên riêng; upload có giới hạn; thống kê đúng đơn vị | R03/R05/R07/R13/R14/R16/R19/R21 | Thêm trang xuất được PPTX/ZIP; reload khôi phục công việc; patch cũ bị từ chối; lỗi giữ nguyên bài; không trộn phiên; phổ điểm 2,4,8,10 hiển thị đúng: dưới 5 là 2; từ 5 đến dưới 8 là 0; từ 8 trở lên là 2 |
| M3 — Nội dung đúng và đủ | Sinh bám dàn ý; nhận diện đúng bài; schema khối nội dung; kiểm định cả bước giải; RAG giữ giả thiết/bảng/hình/nguồn; ingest bảo toàn công thức và báo phần thiếu; hoàn thiện scene | R04/R08/R09/R10/R11/R15/R19/R20 | Bộ bài chuẩn giữ thứ tự dàn ý, đủ dữ kiện và lời giải; toán sai bị phát hiện trong phạm vi hỗ trợ; thiếu nguồn/hình có cảnh báo; không tự gắn nhãn sẵn sàng |
| M4 — Trình bày và xuất giữ nội dung | Layout web/PPTX theo khối; lời giải trên mặt slide; chia trang khi tràn; theme dễ đọc; chú thích và poll theo ID câu hỏi/slide | R06/R16/R17/R18 | Web/PPTX giữ nội dung thiết yếu; đọc được trên máy chiếu; đổi bài không trộn nét vẽ; poll ban đầu bằng 0, reset đúng |
| M5 — Nghiệm thu phát hành | E2E qua backend thật; clone sạch/CI; khóa và bundle dependency; tài liệu đúng khả năng; đo hiệu năng; giáo viên duyệt bộ bài chuẩn | R22/R23 và các lỗi còn mở | Các tính năng được bật vượt qua cổng kỹ thuật và chuyên môn; có bằng chứng đóng từng lỗi và danh sách giới hạn |

R11/R15 được kéo một phần lên M1 để tránh hình sai ngay khi khôi phục render; M3 vẫn phải nghiệm thu toàn phạm vi. R16/R19 trải nhiều mốc: chỉ đóng khi cả migration, lưu/khôi phục và các luồng sử dụng đều đạt.

## 3. Thứ tự chia gói công việc

Giữ mã PR đã có trong kế hoạch chi tiết để dễ theo dõi; đây là gói triển khai đề xuất, chưa phải PR đã mở.

1. **PR01-B:** worker có thể kết thúc, hàng đợi giới hạn, lifecycle, miền xác định và nối parser vào các đường xử lý. PR01-A chỉ là nền tảng; chưa đủ mở lại tính năng.
2. **PR02:** ownership renderer/cache, kiểm tra khớp yêu cầu và hình học giới hạn theo kế hoạch M1; FunctionPlotter gọi API; kiểm thử race, timeout và ảnh đúng slide.
3. **PR03–04:** ID/revision/migration, editor và lưu dự án; snapshot xuất và hợp đồng lỗi. Ưu tiên giải quyết hành trình thêm slide → xuất đang hỏng.
4. **PR05–08:** cách ly phiên, Copilot có cấu trúc và kiểm tra xung đột, giới hạn upload, thống kê. R14 có thể sửa sớm do độc lập với renderer. Hoàn thành quyền sở hữu và giới hạn tài nguyên trước khi mở dịch vụ dùng chung.
5. **PR09–12:** dàn ý và nhận diện bài → schema khối/kiểm định → ingest/RAG và scene. Chốt schema trước khi tái xử lý toàn kho để tránh làm lại dữ liệu.
6. **PR13–14:** layout/xuất/lời giải/theme → chú thích và poll đúng vòng đời.
7. **PR15:** tổng hợp nghiệm thu, dependency, CI và tài liệu. Test, tài liệu và kiểm tra dependency vẫn đi cùng từng gói trước đó.

Chuỗi phụ thuộc chính: **M0 → M1 → M2 → M3 → M4 → M5**. Các việc độc lập như R14 và kiểm kê dependency có thể làm sớm, nhưng không dùng chúng để bỏ qua điều kiện qua mốc.

## 4. Quản lý backlog và nghiệm thu

Mỗi hạng mục dùng mẫu sau:

| Trường | Nội dung cần ghi |
| --- | --- |
| Mã và ưu tiên | Rxx / gói PR; P0, P1 hoặc P2; điều kiện triển khai áp dụng |
| Vấn đề | Thao tác cụ thể và kết quả sai đã quan sát |
| Hành vi mong muốn | Kết quả người dùng phải nhận được, kể cả khi lỗi |
| Phạm vi | Module, API/schema, migration và dữ liệu bị ảnh hưởng |
| Phụ thuộc | Hạng mục phải đạt trước; phần có thể làm độc lập |
| Phụ trách | Người thực hiện, người review kỹ thuật, giáo viên duyệt nếu liên quan nội dung |
| Nghiệm thu | Ca đúng, ca sai, ca lỗi và bằng chứng nội dung đầu ra |
| Bàn giao | Diff/PR, log test, fixture, ảnh hoặc file xuất, giới hạn còn lại |
| Trạng thái | Chưa làm / đang làm / chặn tạm / chờ nghiệm thu / đã đóng |

Phân biệt **chặn tạm** và **đã đóng**. Tắt đồ thị, trả patch null hoặc xuất bản nháp có cảnh báo là giảm rủi ro; đóng lỗi chức năng cần chứng minh hành vi đúng đã hoạt động trở lại.

Một hạng mục được đóng khi có đủ: test tái hiện lỗi cũ; kiểm tra hành vi mới qua luồng thật; nội dung giáo viên được giữ khi lỗi; migration nếu đổi hợp đồng; báo cáo bằng chứng và giới hạn. Build đạt hoặc HTTP 200 chỉ là một phần bằng chứng.

## 5. Bộ kiểm tra xuyên suốt

- **An toàn và tài nguyên:** marker vô hại không chạy; timeout dừng worker; cleanup không ảnh hưởng request khác; upload vượt giới hạn bị từ chối có kiểm soát.
- **Hành trình giáo viên:** sửa dàn ý → sinh → thêm/sửa/xóa/sắp xếp → lưu/reload → xuất Word/PPTX/ZIP. Kiểm tra bằng trình duyệt và backend thật; có thể mock provider bên ngoài để ca lỗi tái lập được.
- **Copilot:** câu trả lời và patch cùng bài; xem trước/sau; thay đổi revision trong khi chờ; áp dụng patch cũ không ghi đè nội dung mới.
- **Độ đúng nội dung:** kiểm tra cả lời giải, điều kiện, bảng, hình và nguồn. Tách trạng thái `draft`, `needs_review`, `ready`; phần ngoài phạm vi kiểm chứng phải ghi chưa kiểm tra. `ready` cần tiêu chí chuyên môn đã thống nhất và xác nhận của giáo viên trong phạm vi phát hành.
- **File xuất:** đọc lại text/media để kiểm tra bảo toàn nội dung, rồi render kiểm tra khả năng đọc và tràn trang. Lời giải chỉ có trong notes chưa đạt yêu cầu R06.
- **Khả năng tái lập:** fixture nhỏ đi cùng repo; test raw data tách rõ; CI trên checkout sạch; test trọng yếu không skip. Thử provider thật và duyệt chuyên môn có bằng chứng riêng.

Bộ bài nghiệm thu ban đầu nên phủ hàm số, nguyên hàm/tích phân, hình học không gian/tọa độ, thống kê và xác suất. Với mỗi nhóm, có ca đủ dữ kiện, thiếu dữ kiện và nội dung sai có chủ ý. Chốt quy mô sau khi giáo viên xác nhận bài đại diện; tỷ lệ lint sạch không được diễn giải thành tỷ lệ đúng toán.

## 6. Nâng cấp sau khi nền tảng ổn định

| Nâng cấp | Thời điểm và điều kiện bắt đầu | Kết quả cần đo |
| --- | --- | --- |
| Hiệu năng | Đo sớm; tách tải phần 3D/editor khi đã có luồng ổn định | Thời gian mở bài/chuyển trang/render/xuất, bộ nhớ trên thiết bị lớp học mục tiêu; đặt ngưỡng từ baseline |
| Gateway AI | Hoàn thiện cùng generation và nghiệm thu M3–M5 | Metadata provider/model, phân loại lỗi, deadline toàn tác vụ, độ trễ/chi phí, fallback giữ đúng bài |
| Canvas theo khối | Sau khi schema khối, ID/revision, lưu dự án và Web/PPTX đạt; triển khai thử một layout trước | Chỉnh vị trí/kích thước/nhóm mà giữ nguyên công thức, lời giải, nguồn và nội dung khi xuất |
| Bình chọn từ học sinh | Sau poll cục bộ đúng trạng thái và nền tảng phiên/quyền đã đạt | Thu phiếu thật, tách câu hỏi/lớp/phiên; chưa có phiếu thì hiển thị 0/chưa thu, dữ liệu mô phỏng chỉ ở môi trường kiểm thử |

Ưu tiên hoàn tất hành trình soạn → lưu → xuất và độ đúng toán trước khi mở rộng canvas hoặc tương tác lớp học.

## 7. Ước lượng và nhịp triển khai

M1 đã có dự toán trong kế hoạch riêng: **18–25 ngày công, cộng 3–5 ngày dự phòng**, cho tổng phạm vi M1 mở rộng với một người thực hiện. Đây là dự toán toàn mốc; chưa có số ngày công thực tế để suy ra chính xác phần còn lại sau PR01-A.

M2–M5 chưa nên chốt lịch từ số lượng lỗi. Trước mỗi mốc, chia thành gói như mục 3, xác định fixture/migration/tiêu chí và ước lượng riêng phát triển, kiểm thử, duyệt chuyên môn. Chốt lại phạm vi sau M1 vì worker, schema và dữ liệu nguồn ảnh hưởng các mốc sau.

Mỗi tuần cập nhật một bảng ngắn: gói đã đạt; lỗi còn mở; bằng chứng; điểm nghẽn; dự báo mốc tiếp theo. Không chuyển trạng thái sang đã đóng chỉ vì đã có mã hoặc tổng số test tăng.

**Việc bắt đầu ngay:** triển khai PR01-B theo kế hoạch M1 hiện có, giữ nguyên chốt chặn M0; sau đó nghiệm thu runtime/render trước khi mở lại đồ thị và kiểm định đại số. Khung này chỉ bổ sung tài liệu kế hoạch, chưa thực hiện thay đổi ứng dụng.
