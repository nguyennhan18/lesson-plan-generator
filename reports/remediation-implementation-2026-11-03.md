# Báo cáo thực hiện sửa lỗi và nâng cấp — cập nhật 04/11/2026

**Trạng thái: đã triển khai và kiểm tra nhiều luồng kỹ thuật; M1–M4 CHƯA ĐỦ ĐIỀU KIỆN BÀN GIAO. M5 chưa đóng.** Tên file giữ ngày mở đợt thực hiện 03/11; số liệu dưới cập nhật ngày 04/11/2026 theo Asia/Ho_Chi_Minh. Đây là báo cáo tiến độ có bằng chứng, chưa phải biên bản nghiệm thu cuối.

- [Nội dung và mục đích của 124 file thay đổi](remediation-changed-files-2026-11-03.md).
- [Review lại kế hoạch, ma trận R01–R23 và điều kiện đóng mốc](../docs/plans/remediation-acceptance-2026-11-03.md).
- [Bằng chứng kiểm tra cục bộ](evidence-remediation-2026-11-04/README.md).

## 1. Những thay đổi đã đưa vào luồng sản phẩm

### M1 — Toán và hình theo dữ kiện

Biểu thức đi qua parser AST có giới hạn, worker riêng có thời hạn, miền xác định được tính từ biểu thức gốc trước rút gọn. Đồ thị tách nhánh theo miền, không nối qua lỗ xác định. Không dùng eval Python/JavaScript để thực thi chuỗi đầu vào ở các đường toán đang bật. Renderer khóa theo tác vụ và giữ figure riêng; cache giới hạn và có khóa theo spec/nguồn/deck/slide.

Đồ thị/hình phải có dữ kiện và bước giáo viên xác nhận. Token ký gắn dữ kiện, slide và nội dung đề tại thời điểm xác nhận; đổi đề/công thức/số đo làm xác nhận cũ mất hiệu lực. Frontend từ chối phản hồi muộn sau khi sửa đầu vào. Không dựng parabol hoặc đa diện mặc định khi yêu cầu thiếu/sai. Dãy số được tính từ u₁/d/số số hạng, miền nghiệm từ các nửa mặt phẳng, không dùng polygon do LLM tự điền.

Hình học hiện hỗ trợ ba loại: lập phương; chóp đều đáy vuông; chóp có SA vuông góc đáy vuông. Tọa độ, độ dài cạnh, chiều cao và thể tích cùng bộ dữ liệu. Web/xuất dùng cùng tọa độ; hình xuất có phân biệt cạnh khuất. Đây chưa phải hỗ trợ hình học tùy ý hoặc chứng minh mọi quan hệ hình học trong đề.

Qua render PPTX thực tế phát hiện 1/x bị auto-scale theo mẫu quá gần tiệm cận khiến đồ thị gần phẳng. Đã đổi cách chọn cửa sổ y theo khoảng giá trị điển hình, giữ nguyên đoạn đường cong và miền; giáo viên có thể nhập giới hạn y rõ. Phần vượt cửa sổ bị cắt theo viewport, không bị thay bằng hàm khác. Hình trước/sau được đối chiếu trong quá trình sửa; bằng chứng lưu là bản đã sửa.

### M2 — Soạn, lưu, sửa và xuất nhất quán

Project/deck/slide có ID ổn định và revision, dữ liệu giữ metadata và alias cũ có kiểm tra xung đột. IndexedDB lưu dự án; có chọn dự án và tải/phục hồi JSON. Lưu theo hàng đợi. Nếu khôi phục lỗi, tự lưu tạm dừng và vẫn có đường tạo/phục hồi, tránh âm thầm ghi đè trạng thái đang cần cứu. Khi form slide còn sửa chưa lưu, chuyển slide/màn hình/xuất bị chặn với thông báo; có cảnh báo đóng/tải lại trang khi còn bản sửa chưa lưu.

Copilot trả một kết quả có cấu trúc cho lời đáp và đề xuất; giáo viên xem before/after, xác nhận rồi áp dụng theo base revision/hash. Có cách ly owner/project/deck/session, kiểm tra xung đột và idempotence. Đây là cơ chế phiên cho ứng dụng cục bộ; chưa phải đăng nhập và lưu bền nhiều giáo viên trên máy chủ.

Upload có chặn body, kích thước file, cấu trúc ZIP, số phần, tổng giải nén, đường dẫn nguy hiểm, số dòng và thời hạn xử lý. Các lỗi route, Origin và chặn body có request ID. Phân tích bảng điểm dùng file thật, sửa nhóm điểm/tỷ lệ/CV; không khởi tạo bằng bảng điểm mẫu.

### M3 — Chốt nội dung và nguồn

Dàn ý được duyệt đi vào sinh bài; kiểm tra ID/thứ tự/tiêu đề và các ý bắt buộc. Provider/model truyền qua tác vụ. Lỗi provider hoặc vi phạm hợp đồng không trả bài mẫu thay thế. Bài không xác định trong danh mục không tự rơi về bài đầu.

Bộ kiểm tra quét cả lời giải, đáp án, giải thích, blocks và bảng. Sai số học trong phạm vi hỗ trợ có thể chặn; đẳng thức có biến chưa rõ vai trò/điều kiện được đánh dấu chưa xác minh. Có các kiểm tra identity giới hạn khi khai báo đúng vai trò. Bộ kiểm tra này chưa thay thế kiểm định đầy đủ nội dung toán.

Nguồn RAG phải có bản ghi duyệt gắn reviewer/thời điểm/hash; chỉ lấy nguyên đơn vị nguồn trong ngân sách ngữ cảnh. Citation được đối chiếu với nguồn thật cung cấp, hash sai bị từ chối; hash thiếu được gắn phiên bản nguồn thực. Kho đã kiểm kê **2.741 đơn vị: 1.847 slide, 894 câu hỏi; 0 đơn vị được tự phê duyệt**. Kho chưa duyệt được cách ly. [Tóm tắt inventory](evidence-remediation-2026-11-04/source-inventory-summary.json). Inventory đầy đủ ở `reports/data/source-review-inventory-2026-11-03.json` trên workspace, chưa đưa vào bundle sản phẩm.

Nhập Office giữ OMML gốc và media/OLE kèm cảnh báo. **Chưa chuyển đổi và tái tạo đầy đủ OMML/MathType thành nội dung toán có thể sửa.**

### M4 — Trình chiếu và file xuất

Trình chiếu dùng nội dung thật, công thức, lời giải từng bước, blocks, bảng và nguồn. Nét vẽ/bảng phụ/poll theo ID, có undo/redo; lượt chọn bắt đầu 0 và đặt lại đúng câu hỏi. Chức năng này ghi nhận tại máy giáo viên, chưa là dịch vụ bỏ phiếu học sinh trực tuyến.

PPTX giữ lời giải trên mặt slide, bổ sung trang nối tiếp cho nội dung dài, không chỉ lưu trong notes. Ảnh dựng lại theo đúng slide/spec đã xác nhận. Chia trang dài đã được gộp để tránh mỗi bullet thành một trang thưa. Footer thống nhất và đánh số theo số trang xuất thực. Thiếu xác nhận/nội dung còn lỗi được gắn bản nháp; không lấy ảnh 3D toàn cục. Word giữ giáo án thật và vẫn là bản nháp. ZIP có manifest và checksum của tài liệu thực sự được xuất.

Công thức không render được bằng mathtext được giữ bằng LaTeX gốc; nếu cả việc chèn công thức thất bại thì xuất trả lỗi, không dùng pixel trong suốt để giấu mất nội dung. Một số công thức/bảng phức tạp vẫn chưa đạt trình bày cần thiết để đóng M4. Web và PPTX cùng dữ kiện nhưng chưa bảo đảm giống từng điểm ảnh hay cùng góc camera.

### Yêu cầu bỏ bài mẫu

Đã gỡ bài/preset/dàn ý/hình/poll/bảng điểm mẫu ở luồng sản phẩm. Rà bổ sung ngày 04/11 tìm thấy và gỡ cửa sổ “Slide Mẫu KNTT”, nhãn “Nguồn RAG: KNTT 12” gắn sẵn và mô tả tự nhận dùng toàn kho. Endpoint xem bài mẫu cũ trả 410; bộ đếm chỉ tính học liệu đã duyệt. Các fixture trong thư mục kiểm thử không đi vào bài người dùng.

## 2. Kết quả kiểm tra có bằng chứng

| Kiểm tra | Kết quả | Bằng chứng |
|---|---|---|
| `make test` | **352 backend đạt, 1 bỏ qua; 32 frontend đạt** | [Log đầy đủ](evidence-remediation-2026-11-04/backend-and-frontend.txt) |
| `make test-critical` | **138 backend đạt; 8 frontend đạt** | [Log critical](evidence-remediation-2026-11-04/critical.txt) |
| E2E qua backend thật, Chrome | **11 luồng đạt**, 16,5 giây | [Log trình duyệt](evidence-remediation-2026-11-04/browser-e2e.txt) |
| Bản sao sạch cục bộ: Python mới, pip từ lock, package editable; không corpus/venv/node_modules/dist cũ | Cài được; **342 portable đạt, 1 bỏ qua, 10 loại khỏi phạm vi** | [Cài Python](evidence-remediation-2026-11-04/clean-python-install.txt), [cài package](evidence-remediation-2026-11-04/clean-package-install.txt), [test](evidence-remediation-2026-11-04/clean-backend-portable.txt) |
| Bản sao sạch: `npm ci`, Node test, production build | **32 test đạt; build thành công** | [Cài npm](evidence-remediation-2026-11-04/clean-npm-install.txt), [test](evidence-remediation-2026-11-04/clean-frontend.txt), [build](evidence-remediation-2026-11-04/clean-build.txt) |
| Audit acceptance riêng | **9 probe backend + 3 probe frontend đạt**; probe Node không được tính là E2E | [JSON](evidence-remediation-2026-11-04/acceptance-probes.json) |
| Dependency audit ngày 03/11 | **Không thấy lỗ hổng đã biết** trong kết quả npm/pip tại thời điểm quét | [npm](evidence-remediation-2026-11-04/npm-audit-20261103.json), [Python](evidence-remediation-2026-11-04/python-audit-20261103.json) |
| Render PPTX bằng LibreOffice | Đã rà cục bộ công thức/đồ thị 1/x, chóp SA vuông góc đáy và trang nối; bản fixture xuất 16 trang | [Đồ thị](evidence-remediation-2026-11-04/pptx-function.png), [hình học](evidence-remediation-2026-11-04/pptx-geometry.png) |
| Sửa bổ sung request ID ở lớp chặn body/Origin sau bộ đầy đủ | Chạy lại 2 ca liên quan; xem log riêng | [Log](evidence-remediation-2026-11-04/request-id-followup.txt) |
| Hosted CI | **Chưa chạy/xác nhận** | Workflow đã cấu hình; bản sao sạch cục bộ chưa thay thế hosted CI |
| Provider LLM thật, giáo viên nghiệm thu | **Chưa thực hiện trong lượt kiểm tra này** | Test dùng mock phản hồi AI và tắt API key; không có kết quả tỷ lệ hallucination thực tế |

Một test bỏ qua cần provider thật/API key. Mười ca loại ở bản portable cần corpus/báo cáo nội bộ; không được tính là đã đạt trong bản sạch. Không gọi provider bằng key thật để ghi nhận các số liệu trên.

Bản sao sạch được tạo từ tệp đang theo dõi và tệp mới không bị ignore, bỏ các tệp đã bị xóa, không mang theo `.env`, corpus, venv hay node_modules cũ. Đây là kiểm tra cài nguồn workspace sạch cục bộ trên macOS, **chưa phải clone một commit đã phát hành và chạy CI Linux**. Lượt npm ci đầu dùng đường dẫn `/tmp` qua prefix bị lỗi phân giải; chạy trực tiếp trong đường dẫn `/private/tmp/.../app/frontend` cài thành công. MathLive vẫn tạo cảnh báo chunk lớn; chưa có chứng cứ tối ưu hiệu năng máy chiếu/máy cấu hình thấp.

Sửa request ID là thay đổi sau lượt đầy đủ/E2E. Hai ca API ảnh hưởng đã được kiểm tra lại riêng; báo cáo không giả định đã chạy lại toàn bộ bộ test sau sửa nhỏ này. Fingerprint mã nguồn lưu tại [workspace-fingerprints.json](evidence-remediation-2026-11-04/workspace-fingerprints.json).

## 3. Di trú kiểm thử và giới hạn của số đếm

Có **38 kiểm tra chuỗi mã nguồn** và **31 kiểm tra hợp đồng/hành vi cũ** được thay/bỏ trong đợt di trú. Chúng từng yêu cầu CDN, preset, fallback bài mẫu, ảnh chụp toàn cục hoặc cấu trúc component cũ. Danh sách lưu trong [source assertions](evidence-remediation-2026-11-04/migrated-source-assertions.json) và [contract tests](evidence-remediation-2026-11-04/migrated-contract-tests.json). Các assert còn lại được cập nhật theo hợp đồng mới; một assert gắn callback fullscreen theo chuỗi chính xác được bỏ khi callback có chốt bản sửa chưa lưu.

Thay thế bằng test runtime worker/parser/domain/cache; API ownership/CAS/quality/generation/export/ingest; Node contract ID/revision; 11 ca trình duyệt qua backend thật. **Không dùng số test nhỏ hơn/lớn hơn baseline để suy luận độ bao phủ hoặc độ đúng tăng bao nhiêu.** Chưa có báo cáo coverage ngữ nghĩa hay bộ chuẩn sư phạm đầy đủ. Riêng test model routing có sẵn trong workspace ngày tiếp tục được chạy tích hợp cùng; không quy toàn bộ thay đổi chưa commit là do một người/phiên viết.

## 4. Vì sao chưa bàn giao

1. **Độ đúng chuyên môn:** kiểm tra số học và hình có giới hạn. Token hình xác nhận rằng giáo viên đã duyệt spec theo đề; chưa tự chứng minh spec do LLM đề xuất khớp mọi câu chữ, giả thiết và mục tiêu của bài. Chưa có bộ đề chuẩn được người có chuyên môn ký duyệt và bộ phản ví dụ đủ rộng.
2. **Nguồn và Office:** cách ly được nguồn chưa duyệt nhưng chưa sửa/duyệt toàn kho, chưa tái tạo đầy đủ OMML/MathType. Bảo toàn XML gốc là bước chống mất dữ liệu, chưa đạt mục tiêu nội dung có thể sửa đầy đủ.
3. **Trình bày/xuất:** còn bảng dạng text, công thức phức tạp/raw LaTeX, độ dài và bố cục/theme cần nghiệm thu đủ. Chưa kiểm tra trên máy chiếu và PowerPoint/Word thực tế của giáo viên.
4. **Vòng đời/vận hành:** còn migration dữ liệu thật, quota/nhiều tab, phiên máy chủ nếu triển khai dùng chung, hosted CI và benchmark tải đại diện. Chưa có luồng duyệt độc lập giáo án Word.

`ready` chỉ là xác nhận của giáo viên với phiên bản hiện tại cộng kiểm tra hỗ trợ chưa phát hiện lỗi chặn. Không có bước LLM tự đánh giá rồi tự chứng nhận “đúng nội dung”. Khi sửa nội dung, xác nhận cũ bị hủy. Quy trình này giảm nguy cơ chèn nội dung cho đủ chỗ, nhưng chưa chứng nhận đầu ra AI tự động luôn đúng.

## 5. Kết quả review kế hoạch và việc cần làm tiếp

Giữ nguyên mục tiêu giáo viên soạn–sửa–lưu–trình chiếu–xuất bài đúng nội dung. Điều chỉnh cách đóng mốc: cần bằng chứng hành vi, phản ví dụ, file xuất và kiểm duyệt chuyên môn; không đóng mốc theo số file/module/test xanh. [Review kế hoạch](../docs/plans/remediation-acceptance-2026-11-03.md) phân rõ R01–R23 đã chặn lỗi nào và còn thiếu gì.

Ưu tiên tiếp theo: (1) bộ bài chuẩn/đáp án/ràng buộc hình và phản ví dụ được duyệt; (2) R08/R20 về nguồn/công thức Office; (3) bảng/công thức/layout M4 và kiểm tra thiết bị thực; (4) migration/quota/nhiều tab phù hợp môi trường dùng; (5) CI theo commit, benchmark và ký nghiệm thu. Chỉ lập biên bản bàn giao cuối khi các điều kiện này đạt. Không có commit/push/deploy nào được thực hiện trong lượt này.
