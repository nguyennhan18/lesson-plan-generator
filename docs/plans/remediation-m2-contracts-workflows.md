# Kế hoạch thực hiện M2 — Hợp đồng dữ liệu và thao tác tin cậy

> **Cập nhật 04/11/2026: CHƯA ĐỦ ĐIỀU KIỆN BÀN GIAO.** Các phần triển khai và kiểm thử cục bộ không đồng nghĩa đóng mốc M1–M4. Xem [review sau triển khai và điều kiện đóng mốc](remediation-acceptance-2026-11-03.md) cùng [báo cáo thực hiện](../../reports/remediation-implementation-2026-11-03.md). Những trạng thái bên dưới mô tả thời điểm lập kế hoạch nếu chưa có ghi chú cập nhật.


Ngày soạn: **03/11/2026**. Trạng thái: **kế hoạch, chưa triển khai/nghiệm thu M2**. Phạm vi: **R03/R05/R07/R13/R14/R16/R19/R21**, tương ứng PR03–PR08 trong [kế hoạch tổng thể](project-remediation-post-refactor.md). M0 đã có báo cáo nghiệm thu chặn tạm; M1 mới khởi động PR01-A theo [bàn giao ngày 03/11](../../reports/remediation-m1-pr01a-2026-11-03.md), chưa được coi là hoàn tất.

Mục tiêu M2: giáo viên sửa đúng bài, lưu và nạp lại đúng dữ liệu, xuất đúng snapshot; Copilot chỉ áp dụng đề xuất đúng slide/phiên bản và đúng chủ phiên; nhập tài liệu có giới hạn; thống kê API–UI thống nhất đơn vị. M2 giữ bố cục slide hiện tại. Block/layout mới và kiểm định đầy đủ chất lượng giảng dạy thuộc M3; phần trình chiếu/chú thích nâng cao thuộc M4.

**Bổ sung ngày 03/11/2026 — Loại bỏ nội dung mẫu khỏi frontend:** thực hiện inventory và cổng nghiệm thu trong [kế hoạch tổng thể](project-remediation-post-refactor.md). PR03 gỡ `sampleTemplates`, `textbookPresets`, `defaultInitialOutline`, chủ đề/lesson ID tự chọn và seed poll; bổ sung trạng thái dự án trống, bảo toàn dữ liệu đã lưu. PR06 gỡ chip gợi ý nội dung soạn sẵn, hội thoại giả và câu trả lời mẫu trong nhánh lỗi/response rỗng của TeacherChatDock. PR08 gỡ `DEFAULT_ANALYTICS_DATA`, số RAG giả và CSV có học sinh/điểm mẫu khỏi sản phẩm; fixture số liệu chỉ dùng trong kiểm thử. PR04 xác nhận chúng không lọt vào file xuất. Chưa có dữ liệu phải báo chưa có, không che bằng mẫu. Phạm vi này cần cập nhật dự toán sau inventory, chưa được coi là đã triển khai.

## 1. Kết quả cần bàn giao

| Nhóm | Hành vi sau M2 | Điều kiện đóng lỗi |
| --- | --- | --- |
| R05 | Thêm, sửa, xóa, đổi thứ tự và xuất qua API không lệch schema | Hành trình trình duyệt và nội dung tệp xuất khớp bản soạn |
| R16 — phần M2 | Project/deck/slide có ID bền vững; reload và chuyển bài giữ đúng dữ liệu, nét vẽ | Không trộn bài hoặc đổi đích sau reorder; phần nâng cao còn ở M4 |
| R19 — phần M2 | Migration và JSON round trip giữ metadata/nguồn/bảng/hình đã có | Không âm thầm bỏ trường hoặc slide; block schema đầy đủ còn ở M3 |
| R07 | Word/PPTX/ZIP cùng snapshot; lỗi trả JSON, không đổi bài | Kiểm tra nội dung và đủ thành phần ZIP, kể cả khi một exporter lỗi |
| R13 | Phiên do server cấp, kiểm tra sở hữu trên mọi thao tác | Hai chủ phiên không đọc/xóa/chat/áp dụng proposal của nhau |
| R03 | Trả lời và proposal cùng ngữ cảnh; preview rồi áp dụng qua backend | Sai ID/revision/hash, proposal hết hạn hoặc sai chủ đều không làm đổi deck |
| R21 | Upload/giải nén/parse có hạn mức và job dừng được | Vượt ngưỡng bị từ chối, timeout dừng worker; request sau còn hoạt động |
| R14 | Tỷ lệ và CV theo 0–1, UI hiển thị %, số đếm chính xác | Fixture biên khớp API–UI, tổng nhóm bằng số điểm hợp lệ |

Đóng toàn bộ M2 không đồng nghĩa bài giảng đã đạt chuẩn giảng dạy. Không đóng R16/R19 toàn phần khi công việc ở M3/M4 chưa đạt. Sáu lỗi trọng yếu của dự án gồm cả lỗi ở M1; M2 chỉ đóng phần có bằng chứng tương ứng, không dùng kết quả M2 để tự đóng R01/R02/R12.

## 2. Điểm xuất phát đã đối chiếu mã nguồn

- `schemas/slide_schema.py` hiện dùng `slide_index`, chưa có bộ ID/revision/schema version; validator quiz đang gộp điều kiện nội dung với cấu trúc.
- `features/slide-editor/SlideEditorScreen.jsx` thêm slide bằng `slide_number`, trong khi backend yêu cầu `slide_index`. `App.jsx` còn đường áp dụng patch vào state trực tiếp theo chỉ số.
- `shared/storage/slideDeckStorage.js` lưu một deck vào key chung trong `sessionStorage`; lỗi đọc/ghi bị bỏ qua, nét vẽ mặc định theo deck `default` và vị trí slide. Chưa phải lưu toàn bộ project.
- `schemas/chat_schema.py` và `api/routes/chat.py` nhận deck/patch từ client, đích theo index; API history/delete chưa kiểm tra chủ sở hữu. `features/chat/TeacherChatDock.jsx` gửi session cố định `session_teacher_dock`.
- Theo M0, patch mẫu đã bị ngắt và fallback đổi bài khi xuất đã bị gỡ; M2 phải giữ các chặn này cho đến khi luồng thay thế đạt. Không coi trạng thái tạm ngắt là đã sửa chức năng.
- `exporters/dual_package_exporter.py` còn chuẩn hóa alias riêng. `features/exports/documentExportActions.js` còn đường lan snapshot hiện tại sang nhiều slide; phải hợp nhất với hợp đồng snapshot/fingerprint của M1, không tạo một chuẩn ảnh thứ hai.
- `api/routes/ingest.py` đang đọc toàn bộ upload rồi gọi parser đồng bộ trong endpoint async; kiểm tra phần mở rộng chưa đủ để giới hạn tài nguyên.
- `services/analytics.py` tính CV dưới dạng tỷ lệ; dữ liệu mẫu/UI ở `features/analytics/AnalyticsScreen.jsx` dùng CV như phần trăm. Cần kiểm kê toàn bộ caller trước khi thay hợp đồng.

Các đường dẫn trên tính từ `app/backend/src/lessonai` hoặc `app/frontend/src`. Đây là kết quả đọc mã để lập kế hoạch; chưa chạy lại baseline hay kiểm thử nghiệm thu M2.

## 3. Thứ tự và dự toán

Giả định một người làm backend, frontend và kiểm thử lần lượt: **24–34 ngày công**, thêm **4–6 ngày công dự phòng**. Chưa cam kết ngày hoàn thành; ngày 1 là ngày bắt đầu thực tế. Dự toán cần cập nhật sau PR03 và thử nghiệm worker/session. Xác thực dùng chung nhiều người là phạm vi mở rộng cần dự toán riêng; mặc định bàn giao local với biên sở hữu rõ ràng.

| Chặng | PR | Ngày công | Đầu ra và cổng chuyển chặng |
| --- | --- | --- | --- |
| 0. Baseline và hợp đồng | chuẩn bị | 1–2 | Inventory trường/caller, fixture cũ, quyết định revision/owner/hạn mức; lưu baseline mới |
| 1. ID, migration, editor, storage | 03 | 6–8 | Project envelope, adapter, reducer thao tác, phục hồi storage; migration không mất dữ liệu |
| 2. Snapshot và xuất file | 04 | 3–4 | Một đường normalize/validate, lỗi thống nhất, ZIP nguyên vẹn; nội dung tệp khớp snapshot |
| 3. Phiên và quyền | 05 | 3–4 | Server cấp phiên, owner/project scope, TTL/reset và test hai chủ phiên |
| 4. Copilot và proposal | 06 | 5–7 | Structured response, proposal store, preview/apply và xung đột; không có đường áp dụng tùy ý |
| 5. Upload và worker parse | 07 | 3–4 | Hạn mức trước/giữa parse, tiến trình có timeout/dừng/cleanup; test ngưỡng nhỏ |
| 6. Đơn vị thống kê | 08 | 1–2 | API–UI cùng đơn vị, số đếm và fixture biên; gỡ dữ liệu mẫu runtime, nghiệm thu trạng thái chưa có dữ liệu |
| 7. Nghiệm thu tích hợp | tổng hợp M2 | 2–3 | E2E API thật, audit M2, log/evidence và báo cáo đóng từng phần |

Phụ thuộc: **PR03 → PR04/PR05; PR01 + PR03 + PR05 → PR06**. PR07/PR08 phụ thuộc M0 và có thể làm sớm khi cần giảm rủi ro, nhưng vẫn review riêng. PR04 kiểm tra lại với PR02 và hợp đồng scene/snapshot M1. Có thể bắt đầu PR03/05/07/08 khi M1 chưa xong; nghiệm thu tích hợp có toán/ảnh và bật patch toán phải đợi năng lực M1 tương ứng đạt. Không dùng parser cũ hoặc bỏ guard để vượt phụ thuộc.

Kiểm thử đi cùng từng PR. Runner trình duyệt được thiết lập từ PR03, không dồn tới chặng 7. Không tổ chức lại repo; đặt module theo [kiến trúc hiện hành](../architecture/repository.md). Worktree có nhiều thay đổi tái cấu trúc/M0/M1: ghi manifest tệp từng PR, không reset hoặc gom mọi thay đổi vào M2.

## 4. PR03 — Hợp đồng project, migration và editor

**Hợp đồng cần chốt trước khi code**

- Project envelope có `schema_version`, `project_id`, `deck_id`, revision nội dung, giáo án, dàn ý đã duyệt, cấu hình, slides, scenes và annotations. Mỗi slide có `slide_id` và revision. ID tạo khi sinh/nhập/thêm mới và giữ qua mọi lần lưu/xuất; nhân bản tạo ID mới.
- `slide_index` là thứ tự 1-based được tính lại sau thêm/xóa/reorder; index 0-based chỉ dùng cho điều khiển UI. Đích lưu trữ, proposal, annotation và ảnh dùng ID. Không suy ID từ tiêu đề hoặc chỉ số.
- Mỗi giao dịch thay đổi nội dung tăng deck revision một lần; slide bị thay đổi tăng slide revision. Reorder tăng deck revision nhưng không đổi slide ID/nội dung. Cache/ảnh render/trạng thái loading không tăng revision nội dung. Định nghĩa canonical JSON và hash dùng chung; loại trường cache/timestamp khỏi hash nội dung và có fixture đối chiếu JS–Python.
- Tách schema bản nháp lưu được khỏi đánh giá đủ nội dung. Quiz đang soạn dở được lưu là draft và có lỗi nội dung; không nới validator dùng cho xuất/ready mà thiếu tầng kiểm tra thay thế.
- Dữ liệu nguồn đã duyệt và trạng thái kiểm chứng kế thừa M1. Client/LLM không được tự gán trạng thái đã kiểm chứng; sửa nội dung phải vô hiệu hóa kết quả kiểm tra và cache liên quan.

**Migration và bảo toàn dữ liệu**

1. Lập bảng trường: prompt → response → state/storage → Word/PPTX/ZIP; gồm `teacher_note`, lời giải, quiz, nguồn, bảng, scene, ảnh và metadata công thức. Mỗi trường có nơi lưu, quy tắc migration và test.
2. Backend có adapter versioned ở biên API; frontend có adapter tương ứng cho storage, cùng dùng bộ fixture hợp đồng. Lõi editor/export chỉ nhận dữ liệu chuẩn; bỏ normalize riêng trong exporter.
3. Dữ liệu chưa có version/ID được nâng cấp một lần, lưu ID đã tạo để lần reload sau không cấp lại. Chuyển `slide_number` sang `slide_index`; nếu cả hai khác nhau trả lỗi có đường dẫn trường. ID trùng, phiên bản tương lai hoặc cấu trúc không biết không được sửa đoán.
4. `{source, slide_id}` cũ chuyển sang `SourceRef.source_type/id` và giữ phần metadata hợp lệ. Không nhầm ID nguồn với ID slide nội bộ. Bảng/block chưa mô hình hóa phải được giữ trong vùng extension có version hoặc từ chối rõ trước khi lưu/xuất; không dựa vào hành vi mặc định bỏ extra của Pydantic.
5. Backup raw cũ trước khi chuyển; ghi dữ liệu mới hoàn tất rồi mới chuyển con trỏ/key hiện hành. Migration thất bại giữ nguyên raw, thông báo và cho tải bản phục hồi; không thay bằng bài mẫu. Có test tính lặp lại của migration, ID ổn định và JSON round trip.
6. Thay key chung bằng kho project có danh sách/chọn project. Ưu tiên IndexedDB cho dữ liệu project và asset, chuyển từ `sessionStorage` cũ khi còn truy cập được; session cũ đã mất không thể phục hồi. Kiểm tra quota/lỗi giao dịch, báo trạng thái chưa lưu và cho tải JSON. Reload/đóng mở trình duyệt giữ project đã lưu, không chỉ giữ trong một tab.
7. Annotation keyed theo project/deck/slide ID, scene theo fingerprint M1. Với nét vẽ cũ chỉ có index, chỉ gắn khi chứng minh được deck/order gốc; dữ liệu mơ hồ được giữ để phục hồi, không tự gán vào bài mới.

**Tích hợp editor:** một đường mutation cho text/MathLive/thêm/xóa/reorder/nhân bản/patch; đồng bộ selection theo slide ID. Xóa slide đang chọn chọn trang hợp lệ kế tiếp; draft rỗng không crash. Khi đổi project, flush giao dịch lưu và reset/load chat, scene, annotation đúng scope. Phản hồi bất đồng bộ của project cũ không ghi vào project mới.

Cổng PR03: fixture migration đạt; thêm/sửa/xóa/reorder rồi reload giữ đúng ID/nội dung/nguồn/nét vẽ; lỗi quota/JSON/migration không thay bài hoặc mất raw.

## 5. PR04 — Xuất một snapshot, lỗi có hợp đồng

- Chụp immutable snapshot project/deck revision tại thời điểm bấm xuất. Mọi thành phần Word/PPTX/ZIP nhận cùng snapshot; chỉnh sửa trong lúc xuất không trộn hai phiên bản. Chuẩn hóa một lần ở API và không tự chọn bài khác trong exporter đồng bộ.
- Thống nhất JSON lỗi gồm `code`, `message`, `request_id`, có thể thêm `field_errors`. Thiếu dữ liệu 400; sai schema 422; xung đột 409; quá dung lượng 413; định dạng không hỗ trợ 415; lỗi chuyển đổi 500. Giữ nguyên HTTPException; không trả traceback hoặc bí mật provider.
- Frontend chỉ tải tệp khi status/content type/chữ ký định dạng đúng. Đọc JSON lỗi kể cả khi request dùng blob; giữ nội dung, selection và trạng thái lưu. Không hiển thị tải thành công khi nhận JSON 200 sai loại.
- ZIP tạo trong thư mục job riêng; manifest ghi project/deck/revision và thành phần yêu cầu. Chỉ trả thành công khi mọi thành phần bắt buộc đã tạo và mở được; lỗi giữa chừng không trả ZIP thiếu. Dọn theo job và không xóa output của request khác.
- Hình dùng đúng slide ID/spec fingerprint theo M1; không phát ảnh cấp deck cho slide thiếu ảnh. Giữ nhãn nháp/lý do khi chưa render/kiểm chứng được. `ready` từ client không có quyền bỏ kiểm định backend; M2 không cấp nhãn sẵn sàng giảng dạy thay M3.

Cổng PR04: mở/đọc Word/PPTX và ZIP bằng thư viện, so nội dung duy nhất của hai bài và thứ tự sau sửa; lỗi chủ đích ở từng exporter trả đúng JSON, không file dự phòng; xuất trong lúc sửa vẫn thuộc snapshot ban đầu. Kiểm tra hình từng slide và nhìn bản xuất đại diện khi M1 đã cung cấp snapshot đúng chuẩn.

## 6. PR05 — Biên chủ phiên và vòng đời chat

- Server cấp session riêng gắn `owner_id`, `project_id`, `deck_id`, TTL và thời điểm hoạt động. Định danh chủ phiên lấy từ ngữ cảnh server xác nhận; không tin `owner_id` do body gửi. Session ID khó đoán chỉ là định danh.
- Chế độ local: chỉ bind loopback; server cấp credential chủ phiên ngẫu nhiên, lưu an toàn phía browser và kiểm tra ở mọi API liên quan. Chốt cơ chế cookie/token và kiểm tra origin/CSRF tương ứng; CORS không thay kiểm tra quyền. Thiếu/sai credential bị từ chối.
- History, interact, reset/delete, tạo/đọc/apply proposal đều kiểm tra owner và project/deck. Thống nhất 401 khi thiếu chủ phiên; 404 cho tài nguyên không thuộc chủ để tránh tiết lộ tồn tại. Proposal không được tiếp tục dùng sau reset/xóa phiên/hết hạn.
- Local một process có store TTL giới hạn kích thước; restart làm phiên/proposal cũ hết hiệu lực và UI xin phiên mới, không phát lại patch cũ. Nếu dùng nhiều worker phải dùng store chia sẻ có thao tác nguyên tử; không bật chế độ dùng chung khi chưa có xác thực, quyền bảo trì và giới hạn tương ứng.
- Nút làm mới chat gọi xóa đúng phiên backend rồi tạo phiên mới; đổi project tải lịch sử đúng scope. Giới hạn số phiên/tin nhắn/proposal và độ dài nội dung; kiểm thử hết hạn với clock được inject.

Cổng PR05: hai chủ A/B, mỗi chủ có hai project; thử ID bị lộ ở mọi endpoint vẫn không đọc/xóa/áp dụng chéo; reset không xóa project khác; phản hồi tới muộn không hiện trong chat mới.

## 7. PR06 — Copilot có proposal và kiểm tra xung đột

1. Một lần sinh có cấu trúc trả `ai_response` và patch tùy chọn trên cùng snapshot yêu cầu. Bỏ nhánh chọn patch theo số slide và nhánh nghiệp vụ theo môi trường pytest nếu còn; inject gateway ở test, dùng cùng handler runtime.
2. Kiểm tra response schema, project/deck/slide ID và allowlist trường thay đổi; cấm patch ID/revision/nguồn đã duyệt/quyền/trạng thái kiểm chứng/cache. Giới hạn kích thước, validate toàn bộ slide sau merge. JSON hợp lệ chưa chứng minh đúng chủ đề hoặc toán.
3. Proposal server lưu phần thay đổi đã kiểm tra, `proposal_id`, owner/session/project/deck/slide ID, base revisions, base content hash, TTL và trạng thái kiểm chứng/cần rà soát. UI preview diff theo ID; không gửi patch tùy ý để apply.
4. Apply API tra proposal, kiểm tra quyền/TTL/base rồi merge nguyên tử. Không còn đường App tự merge patch bỏ qua API. Hai request apply đồng thời chỉ một request commit; retry cùng request ID trả cùng kết quả, không tăng revision hai lần. Nếu store local thì khóa thao tác tại store, không chỉ khóa frontend.
5. Khi revision/hash khác trả 409, giữ sửa tay và đề xuất cũ để xem; người dùng yêu cầu sinh lại từ snapshot mới. Không tự rebase patch lên nội dung đã đổi. Frontend kiểm tra lại active project/deck/revision cả khi nhận proposal lẫn khi nhận kết quả apply.
6. Vì nội dung editor còn ở client, apply phải nhận snapshot hiện hành có schema/hash hợp lệ để so base và trả snapshot mới; frontend chỉ commit nếu state vẫn là base đã gửi. Server chỉ bảo đảm sở hữu/vòng đời proposal và apply một lần, không tuyên bố giải quyết cộng tác nhiều người với revision client cung cấp. Nếu mở cộng tác, cần kho nội dung/revision có thẩm quyền ở server và compare-and-swap tại đó.
7. Apply thành công giữ trường không liên quan, tăng revision theo PR03 và xóa cache/kết quả kiểm chứng phụ thuộc. LLM lỗi/JSON sai/đích sai: patch null, deck nguyên vẹn; thông báo rõ đề xuất chưa kiểm chứng. Patch toán chỉ bật trong khả năng M1 đã đạt; phần không đối chiếu được phải giữ cần rà soát/chặn theo cổng M1.

Cổng PR06: chat → preview → apply qua API thật; reorder/xóa slide/sửa tay khi LLM chậm; phản hồi đảo thứ tự; proposal sai chủ/hết hạn/replay; apply hai lần đồng thời; sửa trong khi chờ apply. Dùng mock gateway qua runtime để tái lập; một lượt provider thật cấu hình riêng chỉ đánh giá tích hợp, không thay các test xác định hay bằng chứng toán độc lập.

## 8. PR07 — Upload có giới hạn và parser dừng được

- Kiểm kê cả parse-document và classify-grades. Đọc theo chunk, đếm bytes thực tế, kiểm tra Content-Length sớm nếu có nhưng không tin nó. Áp hạn mức ở HTTP ingress/multipart để framework không spool file quá lớn trước khi handler được gọi; bảo vệ spool/temp disk bên cạnh phần đọc của ứng dụng.
- Kiểm tra signature/container và cấu trúc DOCX/PPTX/XLSX/XLSM, không chỉ extension/MIME. ZIP có giới hạn entry, tổng bytes giải nén, từng entry và tỷ lệ nén; đo bytes thực khi đọc, không chỉ metadata. Chặn archive mã hóa/đường dẫn vượt thư mục/liên kết không hợp lệ. Không thực thi macro hoặc tải liên kết ngoài.
- Hạn mức riêng cho slide/trang hoặc đoạn/shape, bảng/hàng/cột/ô, độ dài text, CSV rows/columns và ảnh giải mã. Đặt mặc định/cấu hình trong `core/config.py`; chốt số cụ thể và fixture tại chặng 0, không đưa con số chưa đo thành SLA.
- Parse chạy trong tiến trình có deadline, giới hạn concurrency/hàng đợi và khả năng terminate/reap; timeout không chỉ hủy coroutine hoặc chuyển sang thread. Tài liệu nhỏ vẫn có thể gây parse nặng nên kiểm tra cấu trúc trong worker. Có mã lỗi riêng cho timeout/quá tải, quy định status trong hợp đồng trước khi triển khai.
- Worker/job sở hữu temp dir, đóng upload trong mọi nhánh; timeout/crash/client ngắt không để job chạy vô hạn. Giới hạn thời gian dọn và không đụng tài nguyên job khác. Có thể dùng chung primitive quản lý tiến trình M1 nếu phù hợp, nhưng parser và math job có budget riêng.

Cổng PR07: test file nhỏ với ngưỡng cấu hình thấp cho từng giới hạn, giả timeout/crash, kiểm tra tiến trình đã dừng và request sau chạy được; health/chat còn đáp ứng khi parse chậm. Không tạo zip bomb hoặc thử tải làm cạn máy.

## 9. PR08 — Thống kê đúng đơn vị và số đếm

- API tỷ lệ nhóm và `cv` là số 0–1 đối với tỷ lệ nhóm; CV là hệ số không âm, có thể lớn hơn 1. UI nhân 100 khi hiển thị %, so phân hóa cao với `0.28`, không với `28`. Không ép CV vào miền 0–1.
- Trả số đếm nhóm từ backend; UI không suy số học sinh bằng tỷ lệ đã làm tròn. Nhóm `<5`, `5≤điểm<8`, `≥8` phủ đủ dữ liệu hợp lệ và không giao nhau; tổng count bằng cỡ mẫu.
- Gỡ dữ liệu mẫu runtime và CSV điểm mẫu; sửa biểu đồ, prompt và mọi caller theo dữ liệu thật. Fixture số liệu được giữ riêng để kiểm thử. Quy định dữ liệu rỗng/không hợp lệ và trung bình 0; ưu tiên CV null kèm lý do khi mean=0, thay vì hiển thị 0% như đo được. Chốt hợp đồng này bằng fixture trước khi đổi API.
- Fixture: `2,4,8,10` cho count `2/0/2`, tỷ lệ `0.5/0/0.5`; tập đúng ngưỡng 5/8; 0%, 50%, 100%; một học sinh, toàn 0, dữ liệu thiếu và điểm ngoài 0–10 theo chính sách lọc/từ chối đã ghi rõ. Đối chiếu mean/std/CV với phép tính tham chiếu, không chỉ snapshot UI.

## 10. Nghiệm thu, bằng chứng và bàn giao

Cổng bổ sung: app mới/storage sạch không có bài/dàn ý/scene mẫu, preset bài gợi ý, điểm số/phiếu hay lịch sử chat giả; API lỗi hoặc rỗng không trả lời/thay bài mẫu; chuyển dự án và reload không làm rò nội dung cũ. Kiểm tra cả UI, payload và Word/PPTX/ZIP; bản soạn có sẵn được bảo toàn. Hoàn thành các ca tương ứng trong mục yêu cầu loại bỏ mẫu của kế hoạch tổng thể trước khi đóng M2.

Các lệnh **đang có** chạy từ repo root khi triển khai:

```bash
make test-critical
make test
make build
make audit-baseline REVIEW_OUTPUT=/tmp/lessonai-m2-baseline-<run-id>
```

`make audit-acceptance` hiện chỉ là cổng chặn tạm M0, không chứng minh M2 đạt. Cần bổ sung profile audit M2, fixture contract/migration và runner trình duyệt/API thật trong các PR tương ứng; cập nhật CI rồi mới ghi lệnh chính thức vào báo cáo. Không sửa kỳ vọng M0 sang M2 một cách âm thầm hoặc ghi các target chưa tồn tại là đã chạy.

| Luồng bắt buộc | Bằng chứng |
| --- | --- |
| Thêm → sửa text/MathLive → xóa/reorder → lưu/reload → xuất Word/PPTX/ZIP | ID/revision, dữ liệu trước/sau, đọc nội dung tệp và thứ tự; ảnh đúng từng slide |
| Project A → B → A, có nét vẽ/chat/scene riêng | Không rò dữ liệu hoặc nhận response cũ vào project mới |
| Chat → preview → apply; sửa tay/reorder/xóa khi đang chờ | Đúng ID hoặc 409; sửa tay không bị ghi đè; deck không đổi khi lỗi |
| Hai chủ phiên, thao tác chéo mọi endpoint liên quan | Bị từ chối cả với ID đã biết; TTL/reset/restart đúng hợp đồng |
| Export lỗi schema/converter/ZIP và edit trong lúc xuất | JSON đúng status/code/request_id; không file khác bài hoặc ZIP thiếu |
| Upload quá ngưỡng/timeout/crash và thống kê biên | Worker được thu hồi; dịch vụ còn đáp ứng; count/đơn vị khớp UI–API |

Checklist đóng M2:

- [ ] Có inventory và fixture versioned cho hợp đồng, migration, hash/revision; không mất trường nghiệp vụ hay slide.
- [ ] PR03–PR08 đạt cổng riêng; các phụ thuộc M1 dùng trong tích hợp đã nghiệm thu, guard còn lại được ghi rõ.
- [ ] Hành trình trên chạy qua frontend và backend thật, không chỉ test chuỗi mã hoặc API mock. Không có test M2 trọng yếu skip/xfail.
- [ ] `make test-critical`, `make test`, `make build`, audit M2 và CI đạt trên môi trường ghi rõ. Test provider thiếu khóa được báo riêng, không tính là bằng chứng tích hợp provider.
- [ ] Có log/evidence prefix mới mỗi lượt; lưu output lỗi và manifest tệp xuất, không ghi đè bằng chứng M0/M1 hoặc lộ dữ liệu nhạy cảm.
- [ ] Báo cáo `reports/remediation-m2-<ngày-nghiệm-thu>.md` ghi commit hoặc manifest diff chưa commit, môi trường, kết quả, giới hạn local/shared, dữ liệu migration và trạng thái từng R-code.
- [ ] README/kế hoạch tổng thể cập nhật theo kết quả đã đo; R16/R19 còn phần M3/M4 được giữ mở. Có hướng dẫn backup/khôi phục JSON và lỗi hết phiên/chưa lưu.

Khi lỗi, tắt riêng chức năng bằng capability/guard, giữ draft và raw backup; không hạ dữ liệu mới xuống schema cũ gây mất trường, không quay lại patch mẫu, parser nguy hiểm hoặc fallback đổi bài. Rủi ro lịch chính là migration dữ liệu mơ hồ, xung đột bất đồng bộ, quota lưu asset và quản lý tiến trình đa nền tảng; xử lý bằng fixture/thử nghiệm từ đầu và cập nhật dự toán, không giảm cổng nghiệm thu.
