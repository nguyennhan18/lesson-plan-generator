# Review kế hoạch sau triển khai — cập nhật 04/11/2026

**Kết luận: M1–M4 chưa đủ điều kiện bàn giao; M5 chưa đóng.** Tên file giữ ngày mở đợt sửa 03/11; review này cập nhật ngày 04/11/2026 (Asia/Ho_Chi_Minh). Đây là đánh giá kỹ thuật cục bộ, chưa thay thế nghiệm thu chuyên môn.

## 1. Quy tắc nghiệm thu đã điều chỉnh

Một hạng mục chỉ được đóng khi có: (1) hành vi chạy được qua đường sản phẩm thực; (2) ca đúng, ca sai, ca thiếu dữ kiện và ca thay đổi phiên bản; (3) bằng chứng kiểm thử gắn phiên bản; (4) kiểm tra file xuất khi liên quan; (5) xác nhận chuyên môn khi liên quan nội dung toán hoặc tiến trình bài dạy. Không tính việc có module, API hoặc test xanh là đủ để đóng cả mốc.

“Đúng nội dung” gồm: đúng chủ đề và dàn ý đã duyệt; giữ đủ giả thiết/điều kiện/đơn vị; công thức và từng bước giải phù hợp; hình thỏa các ràng buộc của đề; trích dẫn đúng nguồn và phiên bản; trình chiếu/file xuất giữ nội dung thiết yếu. Mọi phần không kiểm được phải hiện trạng thái cần đối chiếu, không sinh dữ kiện để lấp chỗ trống.

`ready` hiện có nghĩa **giáo viên đã xác nhận đúng phiên bản và bộ kiểm tra hỗ trợ chưa phát hiện lỗi chặn**. Nó không phải chứng minh toán học toàn bộ bài, không phải phê duyệt tự động của LLM. Token xác nhận có thời hạn, mất hiệu lực khi nội dung thay đổi hoặc backend khởi động lại. Word vẫn được xuất dưới nhãn bản nháp vì chưa có luồng duyệt giáo án độc lập.

## 2. Review lại các mốc

| Mốc | Kết quả triển khai | Điều kiện còn thiếu để đóng |
|---|---|---|
| M0 | Giữ chốt lỗi và đầu ra audit riêng | Duy trì trong các lượt sửa tiếp theo |
| M1 | Parser nối runtime, worker có deadline/hủy tiến trình, renderer riêng, cache theo spec/nguồn/slide, đồ thị không tự thay công thức, hình xác nhận dữ kiện | Bộ đề chuẩn được giáo viên duyệt; nghiệm thu đầy đủ miền/điểm gián đoạn, bố cục và quy ước hình trong phạm vi phát hành; không suy rộng ba loại hình thành hỗ trợ toàn bộ hình học |
| M2 | ID/revision, IndexedDB và JSON, Copilot có diff/CAS, ownership cục bộ, lỗi upload/xuất, sửa đơn vị thống kê; chặn xuất khi form chưa lưu | Nghiệm thu toàn bộ migration dữ liệu cũ thực tế, lỗi quota/đóng tab/xung đột nhiều tab; nếu dùng chung dịch vụ phải bổ sung đăng nhập và lưu bền phía máy chủ |
| M3 | Bám dàn ý, nhận diện bài cụ thể, kiểm tra lời giải trong phạm vi hỗ trợ, xác nhận nội dung theo phiên bản; cách ly nguồn chưa duyệt; giữ OMML/media gốc | Duyệt và sửa kho nguồn; chuyển đổi OMML/MathType đủ ngữ nghĩa; bộ chuẩn bài đầy đủ và bộ phản ví dụ; kiểm tra các dạng toán ngoài phạm vi hiện có |
| M4 | Lời giải lên mặt slide, trang nối tiếp, ảnh theo đúng slide, footer; nét vẽ/poll theo ID; đã render PPTX bằng LibreOffice để rà cục bộ | Bảng xuất có cấu trúc, công thức phức tạp, văn bản cực dài; nghiệm thu trực quan đủ layout/theme và máy chiếu; đồng bộ góc nhìn 3D nếu yêu cầu giống trình chiếu |
| M5 | Khóa dependency, bỏ CDN, kiểm thử API/trình duyệt, cấu hình CI; kiểm tra cài trong bản sao sạch cục bộ | CI hosted thực chạy; bộ đề chuẩn được giáo viên ký duyệt; đo hiệu năng theo tải đại diện; đóng các điều kiện M1–M4 |

## 3. Đối chiếu R01–R23

“Đạt kiểm tra cục bộ” chỉ áp dụng hành vi được mô tả, không tương đương bàn giao toàn dự án.

| Mã | Kết quả hiện tại | Bằng chứng/phần còn mở |
|---|---|---|
| R01 | Đạt chốt kỹ thuật trong phạm vi parser | Biểu thức qua AST và worker; từ chối đầu vào nguy hiểm, timeout thu hồi tiến trình; test runtime/critical |
| R02 | Đạt luồng đồ thị cục bộ | Frontend gọi API, không eval; không có ảnh thay thế khi lỗi; ca phản hồi muộn và đổi công thức qua trình duyệt |
| R03 | Đạt cơ chế sửa cục bộ | Một phản hồi có cấu trúc cho lời đáp và thay đổi; xác nhận trước áp dụng; xung đột/idempotence và cách ly phiên có test; chất lượng đề xuất AI cần giáo viên đọc |
| R04 | Đạt hợp đồng dàn ý | Giữ ID/thứ tự/tiêu đề/nội dung bắt buộc; sai hợp đồng bị từ chối, không trả bài mẫu |
| R05 | Đạt thêm slide → xuất cục bộ | Backend tự chuẩn hóa chỉ số, frontend tạo ID; kiểm thử API và tải PPTX từ trình duyệt |
| R06 | Đã đưa lời giải lên mặt slide | Test đọc lại PPTX và render; còn kiểm tra đủ công thức phức tạp và khả năng đọc |
| R07 | Đạt chốt không đổi bài khi xuất lỗi | Thiếu dữ liệu trả lỗi; ZIP chỉ chứa tài liệu thật; lỗi chèn công thức không trả file thành công bị mất nội dung |
| R08 | Mở | Nguồn chưa duyệt được cách ly, lấy nguyên đơn vị thay cắt đoạn; chưa sửa và duyệt toàn kho |
| R09 | Một phần | Quét cả lời giải/đáp án/khối/bảng; chặn lỗi số học hỗ trợ, không tự chứng nhận đẳng thức có biến; còn phạm vi kiểm định toán rộng |
| R10 | Đạt các ca nhận diện đã kiểm tra | Ưu tiên cụm cụ thể, bài không biết trả None; không đảm bảo bao phủ mọi cách diễn đạt |
| R11 | Một phần | Ba loại: lập phương, chóp đều đáy vuông, chóp SA vuông góc đáy; tọa độ và số đo chung; không hỗ trợ hình tùy ý |
| R12 | Đạt chốt render cục bộ | Khóa figure, cleanup, cache giới hạn; test đồng thời và không dùng nhầm ảnh |
| R13 | Đạt cách ly phiên ở chế độ cục bộ | Cookie owner/session/CAS; chưa là hệ thống xác thực nhiều giáo viên trên dịch vụ dùng chung |
| R14 | Đạt bộ số liệu chuẩn | Điểm 2,4,8,10: dưới 5 = 2, từ 5 đến dưới 8 = 0, từ 8 trở lên = 2; tỷ lệ dùng đúng đơn vị |
| R15 | Đạt chốt ảnh theo slide | Token gắn deck/slide/spec/dữ kiện nguồn; thay giả thiết hủy xác nhận; không lấy ảnh toàn cục |
| R16 | Một phần | ID, lưu/khôi phục, nét vẽ, poll; chặn tự lưu khi restore lỗi; còn migration thực tế, nhiều tab và quota |
| R17 | Đã sửa CSS và bundle font | Còn nghiệm thu trực quan toàn theme và trên máy chiếu |
| R18 | Đã bỏ phiếu mẫu | Số lượt bắt đầu 0/reset theo câu hỏi; chỉ ghi nhận tại máy giáo viên, chưa phải dịch vụ bỏ phiếu trực tuyến |
| R19 | Đạt các ca hợp đồng đã kiểm tra | Version/alias/metadata, API fixture; còn kiểm kê dữ liệu cũ thực tế |
| R20 | Mở một phần | Giữ OMML/media/OLE và cảnh báo; chưa tái tạo đầy đủ công thức native/MathType vào bài có thể sửa |
| R21 | Đạt giới hạn ứng dụng đã kiểm tra | Body/upload/ZIP/số dòng/deadline/worker; chưa có benchmark tải dùng chung |
| R22 | Đạt khóa và audit ở thời điểm chạy | Không CDN runtime; npm/pip audit có log; chưa thay thế kiểm tra dependency định kỳ |
| R23 | Một phần | Bản sao sạch cục bộ và E2E; CI đã cấu hình nhưng chưa có kết quả hosted; tài liệu công bố giới hạn |

Yêu cầu gỡ bài mẫu: đã gỡ bài/dàn ý/hình/poll/thống kê giả ở luồng sản phẩm, gỡ cửa sổ xem slide mẫu và nhãn nguồn KNTT gắn sẵn; endpoint xem mẫu cũ trả 410. Dữ liệu kiểm thử chỉ nằm trong tests/e2e. Các nút chèn ký hiệu/cấu trúc công thức trống là công cụ nhập, không phải bài giảng điền sẵn.

## 4. Công việc tiếp theo và kết quả nghiệm thu bắt buộc

1. **Hoàn thiện M3:** tạo bộ đề và đáp án chuẩn có người duyệt, gồm đúng/sai/thiếu điều kiện/mâu thuẫn và bài ngoài phạm vi. Từng ca phải xác định được kết quả chặn/cần duyệt/hình mong đợi, không chỉ kiểm tra HTTP 200.
2. **Đóng R08/R20:** chuyển đổi công thức native và đối chiếu với tài liệu gốc; quy trình duyệt nguồn có reviewer/thời điểm/hash. Chỉ đưa đơn vị đã duyệt vào RAG. Không phê duyệt hàng loạt bằng một cờ mặc định.
3. **Hoàn thiện M4:** bảng có cấu trúc, công thức phức tạp và dài, chia trang theo layout; render đủ bộ fixture để đọc lại, kiểm tra tràn/cắt/độ tương phản; giáo viên nghiệm thu trên thiết bị trình chiếu.
4. **Đóng M2 theo môi trường sử dụng:** kiểm tra quota, phục hồi dữ liệu cũ và nhiều tab. Chọn chế độ cục bộ hay dịch vụ dùng chung trước khi chốt yêu cầu đăng nhập/lưu máy chủ.
5. **Đóng M5:** CI chạy trên đúng commit; lưu artifact bằng chứng; đo độ trễ và giới hạn tải; ký nghiệm thu chuyên môn từng bài chuẩn. Chỉ sau đó mới lập biên bản bàn giao cuối.

Không dùng tỷ lệ hoàn thành phần trăm vì các điều kiện còn mở có trọng số và rủi ro khác nhau. [Báo cáo thực hiện](../../reports/remediation-implementation-2026-11-03.md) ghi các lệnh và số liệu; [danh sách file](../../reports/remediation-changed-files-2026-11-03.md) ghi thay đổi/mục đích từng file.
