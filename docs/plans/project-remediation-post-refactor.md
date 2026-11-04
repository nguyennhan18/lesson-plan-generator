**Kế hoạch sửa lỗi dự án sau tái cấu trúc — 02/11/2026**

> **Cập nhật 04/11/2026: CHƯA ĐỦ ĐIỀU KIỆN BÀN GIAO.** Các phần triển khai và kiểm thử cục bộ không đồng nghĩa đóng mốc M1–M4. Xem [review sau triển khai và điều kiện đóng mốc](remediation-acceptance-2026-11-03.md) cùng [báo cáo thực hiện](../../reports/remediation-implementation-2026-11-03.md). Những trạng thái bên dưới mô tả thời điểm lập kế hoạch nếu chưa có ghi chú cập nhật.


Trạng thái: **M0 / PR00 đã triển khai và qua nghiệm thu chặn tạm ngày 02/11/2026**. M1–M5 chưa hoàn thành. Chi tiết thay đổi, kiểm thử và giới hạn: [báo cáo M0](../../reports/remediation-m0-2026-11-02.md).

- RF01 đã sửa: hai CLI audit chạy được, có smoke test, đầu ra riêng và kiểm tra điểm neo.
- R01/R02/R03 đang được chặn tạm: đồ thị từ biểu thức, kiểm định đại số và proposal tự sửa slide chưa bật lại. Đây chưa phải điều kiện đóng các lỗi chức năng.
- Đã bỏ fallback đổi bài khi xuất Word/PPTX, dùng khóa chung cho Matplotlib và ngừng cleanup đóng figure của request khác. R07/R12 còn cần nghiệm thu đầy đủ tại M1/M2.
- `make test`: backend **301 passed, 1 skipped** (test provider thiếu khóa); frontend **28 passed**. **22** test backend thuộc `critical_regressions` và **7** test frontend trọng yếu đạt, không skip. Build, audit nghiệm thu M0 và kiểm tra dependency sau vá đạt.
- Đã đưa các bản vá dependency phát hiện ở M0 vào đợt này; Python tối thiểu tăng lên **3.11** theo yêu cầu Pillow 13. R22 vẫn còn phần MathLive bundle và nghiệm thu M5.
- Bước kế tiếp theo thứ tự PR: **01 — parser an toàn và toàn bộ đường parse (M1/R01)**. Không bật lại parser cũ để khôi phục tính năng.

Kế hoạch này thay thế kế hoạch sáu lỗi trước tái cấu trúc về thứ tự triển khai và vị trí mã. Phạm vi gồm R01–R23 của review toàn dự án và RF01: hai công cụ audit bị hỏng sau di chuyển tệp. Các chi tiết bố cục trong plan v3 được dùng lại khi phù hợp, nhưng phụ thuộc vào các bước an toàn và hợp đồng dữ liệu dưới đây.

Căn cứ: [review sau tái cấu trúc](/Users/nguyennhan18/Documents/Lesson-Plan-Generator/reports/post-refactor-review-2026-11-02.md), [bằng chứng tái hiện](/Users/nguyennhan18/Documents/Lesson-Plan-Generator/reports/post-refactor-review-evidence.json), [review R01–R23](/Users/nguyennhan18/Documents/Lesson-Plan-Generator/reports/project-review-2026-11-02.md), [kiến trúc hiện hành](/Users/nguyennhan18/Documents/Lesson-Plan-Generator/docs/architecture/repository.md).

**Kết quả cần đạt**

1. Biểu thức toán không thực thi mã; render đồng thời không lấy nhầm ảnh.
2. Giáo viên thêm/sửa/xóa trang, dùng Copilot, tải lại dự án và xuất file mà giữ đúng nội dung, định danh và phiên bản.
3. Bài sinh ra bám dàn ý đã duyệt, có định nghĩa/điều kiện/ví dụ/lời giải hoàn chỉnh và hình đúng dữ kiện.
4. Nội dung chưa kiểm chứng có trạng thái rõ; nội dung đã xác định sai bị chặn trước khi được dùng như bài hoàn chỉnh.
5. Bản web và Word/PPTX giữ cùng ý nghĩa toán học; từng lỗi đã sửa có test hành vi và bằng chứng nghiệm thu.

Baseline đã đo: backend 279 test đạt, 1 bỏ qua; frontend 21 test đạt; build thành công. Sáu lỗi R01/R02/R03/R05/R07/R12 vẫn tái hiện. Lint báo lỗi trên 21/64 slide của 8 deck dự phòng được kiểm tra. Đây là baseline lịch sử, không thay thế việc đo lại khi bắt đầu triển khai và không phải tỷ lệ đúng toán học.

**Lộ trình và điều kiện qua mốc**

**Yêu cầu bổ sung ngày 03/11/2026 — Loại bỏ bài mẫu, bài gợi ý có sẵn và hình học mẫu khỏi sản phẩm**

Theo yêu cầu của người dùng, đây là điều kiện bắt buộc xuyên M1–M5, chưa được triển khai/nghiệm thu chỉ bằng việc bổ sung kế hoạch. Frontend chỉ hiển thị nội dung của dự án giáo viên đã tạo/nhập/lưu, nguồn giáo viên chủ động chọn, hoặc kết quả sinh theo yêu cầu hiện hành với trạng thái kiểm định rõ ràng. Bỏ nội dung soạn sẵn dùng để lấp màn hình, tự điền đề hoặc che lỗi. Gắn nhãn demo hay đổi tên bài mẫu thành bài gợi ý không đáp ứng yêu cầu loại bỏ.

Phạm vi kiểm kê ban đầu qua đọc mã (đường dẫn dưới `app/frontend/src`):

| Nơi hiện có | Việc phải thực hiện | Mốc |
| --- | --- | --- |
| `features/dashboard/PresentationDashboard.jsx`: `sampleTemplates`, chọn bài mẫu, placeholder liệt kê đề cụ thể | Gỡ danh sách/thẻ bài mẫu, handler và lời mời chọn mẫu; dùng hướng dẫn nhập yêu cầu trung tính | M2 / PR03 |
| `features/lesson-plan/LessonPlanScreen.jsx`: `textbookPresets`, topic/lesson ID chọn sẵn, số RAG cố định | Gỡ preset bài/mục tiêu; yêu cầu chọn/nhập bài thực; thống kê lấy từ dữ liệu thật, chưa tải được thì chưa có dữ liệu | M2 / PR03, PR08 |
| `features/generation/lessonGenerationActions.js`: `defaultInitialOutline`; `App.jsx`: dàn ý/chủ đề Oxyz ban đầu | Khởi tạo dự án trống; chỉ nạp dàn ý của đúng dự án hoặc kết quả request hiện hành. Chặn sinh từ outline chưa có | M2 / PR03; M3 / PR09 |
| `App.jsx`, `OutlineWorkspace.jsx`, `ThreeCanvas.jsx`, `RightToolsDock.jsx`, `UnfoldedNetViewer.jsx`: loại khối/tham số mặc định | Gỡ hình và số đo tự điền; thiếu scene hoặc tham số cần thiết thì báo thiếu, không chuyển sang cube/chóp. Chỉ dựng scene có dữ kiện và thao tác chọn/tạo rõ ràng | M1 / PR02; M3 / PR12 |
| `features/chat/TeacherChatDock.jsx`: quick chips nội dung, lời chào như lịch sử ở giờ cố định, câu trả lời mẫu trong `catch` hoặc khi response thiếu | Gỡ gợi ý nội dung có sẵn và hội thoại giả; hướng dẫn thao tác trung tính nằm ngoài lịch sử. API lỗi/response rỗng trả trạng thái lỗi, không đóng vai AI đã trả lời | M2 / PR06 |
| `features/analytics/AnalyticsScreen.jsx`: `DEFAULT_ANALYTICS_DATA`, CSV học sinh/điểm mẫu | Gỡ dữ liệu và tải CSV mẫu có số liệu; chỉ hiện thống kê sau khi nhập thành công. Nếu cần hướng dẫn định dạng thì dùng cấu trúc cột trống, không tạo học sinh/điểm | M2 / PR08 |
| `features/presentation/PresentationStage.jsx`: số phiếu `28/7/4/3` | Xóa số phiếu giả ngay trong đợt dọn dữ liệu; hiển thị chưa thu phiếu hoặc 0. Nghiệm thu reset/cách ly theo câu hỏi tại M4 | M2 / PR03; M4 / PR14 |
| `features/exports/documentExportActions.js` và exporter backend: ảnh hiện tại/ảnh cấp deck thay ảnh còn thiếu | Không xuất hình khác để lấp chỗ trống; ràng buộc ảnh với slide/spec/revision, thiếu thì dựng từ spec hợp lệ hoặc báo thiếu | M1 / PR02; M2 / PR04 |

Đây là inventory khởi đầu, không phải danh sách đầy đủ. Khi triển khai phải lần theo cả caller, nhánh lỗi, storage, API, backend fallback và export; không chỉ xóa các khối giao diện nhìn thấy. Bộ sinh/fallback backend không được đưa bài hoặc hình mẫu trở lại frontend. RAG chỉ cung cấp đơn vị học liệu phù hợp yêu cầu, đủ dữ kiện và có nguồn; dữ liệu không đạt trả lỗi hoặc nháp với phần thiếu, không báo hoàn tất bằng bài dự phòng khác. Áp dụng cùng validator cho nhánh LLM và nhánh truy xuất.

Quy tắc thực hiện:

- Chưa nhập yêu cầu: chưa có bài/dàn ý/scene; thao tác cần dữ liệu bị vô hiệu hóa kèm lý do. Đang tải, lỗi, chưa hỗ trợ và chưa có dữ liệu có trạng thái riêng.
- Chỉ giữ mặc định về giao diện như theme, tỷ lệ slide, camera; các lựa chọn cấu hình phải hiển thị rõ. Mặc định không được tạo thêm dữ kiện toán, chọn bài/scene hoặc kết quả học tập.
- Danh mục chương trình có nguồn có thể dùng làm bộ chọn bài do giáo viên thao tác; không tự chọn bài đầu tiên thay yêu cầu còn thiếu. Preview tài liệu do giáo viên chủ động mở phải thể hiện đúng nguồn và không tự nhập vào dự án.
- Giữ các thuật toán dựng đường thẳng, khối lập phương, hình chóp có tham số để phục vụ đề thật; chúng chỉ chạy khi nhận spec hợp lệ và kiểm tra theo yêu cầu. Việc chọn màu/góc nhìn không được làm thay đổi dữ kiện. Không tự chọn hình gần giống cho loại chưa hỗ trợ.
- Bài tập và ví dụ do giáo viên yêu cầu sinh theo ngữ cảnh vẫn là nội dung của bài thật và phải kiểm định. Các fixture/golden set phục vụ test được đặt riêng, không được frontend runtime import, đóng gói vào production hoặc hiện thành kho bài mẫu. Không xóa chúng chỉ vì có chữ “mẫu”.
- Dữ liệu dự án cũ của giáo viên được bảo toàn. Chỉ cách ly seed/demo cũ khi nhận diện được bằng nguồn/phiên bản; dữ liệu chưa rõ nguồn giữ để xem xét, không tự xóa theo tiêu đề hoặc từ khóa và không tự coi là đã kiểm chứng.
- Gỡ code/data/asset mẫu không còn sử dụng khỏi đường chạy production, không chỉ ẩn bằng CSS hoặc một cờ UI. Sửa cả test đang mặc định phải có mẫu để phản ánh hành vi trống; vẫn giữ ca test có dữ liệu thực và test mất dữ liệu.

Nghiệm thu bổ sung bắt buộc:

1. Mở app với storage sạch, đi qua dashboard/dàn ý/editor/giáo án/analytics/trình chiếu/3D/chat: không có bài mẫu, bài gợi ý cố định, hình mẫu, số điểm/phiếu hoặc lịch sử hội thoại giả. Không tự gửi yêu cầu sinh bài khi chưa có yêu cầu người dùng.
2. Lỗi mạng, API trả rỗng, provider lỗi, RAG không tìm thấy và dạng hình chưa hỗ trợ: giữ bản soạn, hiển thị đúng trạng thái; không có nội dung/ảnh/trả lời mẫu xuất hiện và không báo tạo thành công.
3. Tạo bài A, chuyển sang dự án B trống và reload: không hiện dàn ý/scene/thống kê/ảnh của A tại B. Storage lỗi hoặc dữ liệu cũ không xác định được nguồn không kích hoạt seed/demo.
4. Đề không có công thức/scene hoặc thiếu dữ kiện cần thiết: không tự thêm biểu thức, loại khối hay số đo. Đề đủ dữ kiện vẫn dựng được hình đúng sau kiểm định; loại bỏ mẫu không được vô hiệu hóa toàn bộ chức năng hợp lệ để làm xanh test.
5. PPTX/Word/ZIP chỉ chứa nội dung thuộc dự án đang xuất. Không có ảnh mặc định, dòng placeholder nhập liệu hoặc bài dự phòng lọt vào file. Không có dự án/dữ liệu bắt buộc thì không xuất một tài liệu mẫu.
6. Kiểm tra import và output build production để xác nhận fixture/seed/demo đã tách khỏi sản phẩm; kết hợp E2E cho các ca trên. Tìm chuỗi “sample” hoặc đổi tên biến không đủ chứng minh đạt.

Bàn giao inventory trước/sau, test hành vi, ảnh trạng thái trống/lỗi và nội dung file xuất. Đây là cổng phát hành M5; các phần hình bắt buộc đạt trước khi mở renderer M1, các phần khởi tạo/chat/thống kê đạt trong M2. Cập nhật dự toán tại inventory, không mặc định phạm vi bổ sung đã nằm trọn trong số ngày công cũ. Bổ sung này ưu tiên áp dụng khi kế hoạch cũ có cách diễn đạt “sửa dữ liệu mẫu” ở runtime.

| Mốc | Công việc chính | Lỗi liên quan | Điều kiện qua mốc |
| --- | --- | --- | --- |
| M0 — Khôi phục phép đo, chặn tạm | Sửa công cụ audit; ngắt thực thi biểu thức chưa bảo vệ, patch mẫu khác bài và fallback đổi bài | RF01; chặn tạm R01/R02/R03/R07/R12 | Công cụ chạy được; các tính năng chưa an toàn bị từ chối rõ; dữ liệu đang soạn được giữ |
| M1 — Toán và render an toàn | Parser chung, giới hạn tài nguyên, figure riêng, frontend dùng render backend | R01/R02/R12 | Payload marker bị từ chối; hàm hợp lệ vẽ đúng; test xen kẽ hai tác vụ đạt |
| M2 — Hợp đồng và thao tác tin cậy | ID/version/migration; editor/export; Copilot; cách ly phiên; upload; đơn vị thống kê | R03/R05/R07/R13/R14/R16/R19/R21 | Sáu lỗi trọng yếu có test chặn; hành trình sửa → xuất và chat → áp dụng/xung đột chạy thật qua API |
| M3 — Chất lượng toán và học liệu | Dàn ý xuyên suốt, định tuyến bài, khối nội dung, kiểm định, RAG/ingest, scene hình học | R04/R08/R09/R10/R11/R15/R19/R20 | Các bài đại diện có đủ dữ kiện/lời giải/nguồn; bài sai không được đánh dấu sẵn sàng |
| M4 — Trình bày và xuất tương đương | Layout theo khối, lời giải trên mặt PPTX, theme, chú thích và poll đúng trạng thái | R06/R16/R17/R18 | Bài đại diện đọc được trên web/PPTX; không mất bước giải/hình; đổi bài không trộn trạng thái |
| M5 — Nghiệm thu và phát hành có giới hạn | E2E, bộ bài chuẩn, dependency, clone sạch, tài liệu và báo cáo đóng lỗi | R22/R23 và toàn bộ đợt | Không còn lỗi chặn phát hành trong phạm vi bật; có xác nhận chuyên môn cho bài được công bố sẵn sàng giảng dạy |

M0 là biện pháp giảm rủi ro tạm thời, không phải điều kiện đóng sáu lỗi. Chỉ bật lại tính năng đầy đủ sau mốc sửa tương ứng. Các thay đổi được chia thành PR ở cuối tài liệu; không cần tổ chức lại thư mục thêm một lần nữa.

**M0 — Khôi phục công cụ và chặn hành vi nguy hiểm**

Tệp thực hiện: [probe Python](/Users/nguyennhan18/Documents/Lesson-Plan-Generator/scripts/quality/project-review-probes.py), [probe frontend](/Users/nguyennhan18/Documents/Lesson-Plan-Generator/scripts/quality/project-review-frontend-probes.mjs), [Makefile](/Users/nguyennhan18/Documents/Lesson-Plan-Generator/Makefile), [CI](/Users/nguyennhan18/Documents/Lesson-Plan-Generator/.github/workflows/ci.yml).

- Cập nhật import `lessonai`, đường dẫn schema và nơi kiểm tra action sinh bài. Phép đọc nguồn phải báo lỗi nếu không tìm thấy điểm neo, tránh kết luận từ một chuỗi rỗng.
- Cho phép chỉ định tệp đầu ra, tách đo baseline khỏi kiểm tra nghiệm thu; bảo toàn bằng chứng lịch sử. Cập nhật probe để đọc lỗi JSON khi API từ chối thay vì luôn giả định response là Word/ảnh. Kiểm tra hồi quy kiểm chứng hành vi qua hàm/API, giảm phụ thuộc tìm chuỗi mã nguồn.
- Bổ sung smoke test CLI và nhóm test `critical_regressions`. Test hành vi mong muốn được đưa vào cùng PR sửa lỗi; không dùng `xfail`/skip để coi lỗi nghiêm trọng là đã hết.
- Gỡ fallback đổi sang bài lớp 10 trước khi chặn render, để lỗi trong giai đoạn chuyển đổi không biến thành tài liệu khác bài.
- Từ chối biểu thức chưa có parser an toàn trước mọi lệnh parse, kể cả `is_plottable`, validator, enrich và export; frontend tạm bỏ nhánh đánh giá chuỗi. Phần không hỗ trợ hiển thị trạng thái và giữ bản nháp.
- Trả `suggested_patch: null` cho các nhánh sửa nội dung mẫu; ngừng đóng mọi figure từ cleanup request. Bọc các đường Matplotlib hiện có bằng khóa chung trong lúc chuyển đổi M1.

Nghiệm thu M0: không đặt được marker Python/JavaScript bằng probe; không có patch khác bài và file dự phòng khác bài; công cụ audit chạy hết trên fixture. Nếu tính năng bị ngắt để đạt an toàn, ghi rõ là đang tạm ngắt, chưa đóng lỗi chức năng.

**M1 — Một đường xử lý biểu thức và render**

Kế hoạch triển khai chi tiết, cập nhật theo trạng thái M0 đã hoàn thành: [M1 — khôi phục toán và render an toàn](/Users/nguyennhan18/Documents/Lesson-Plan-Generator/docs/plans/remediation-m1-math-rendering.md). M1 giữ bố cục slide hiện tại; phạm vi này không bao gồm đổi sang engine canvas.

Tệp chính: [graph_generator.py](/Users/nguyennhan18/Documents/Lesson-Plan-Generator/app/backend/src/lessonai/exporters/graph_generator.py), [validation.py](/Users/nguyennhan18/Documents/Lesson-Plan-Generator/app/backend/src/lessonai/services/validation.py), [rendering.py](/Users/nguyennhan18/Documents/Lesson-Plan-Generator/app/backend/src/lessonai/services/rendering.py), [slide_exporter.py](/Users/nguyennhan18/Documents/Lesson-Plan-Generator/app/backend/src/lessonai/exporters/slide_exporter.py), [temp_file_cleaner.py](/Users/nguyennhan18/Documents/Lesson-Plan-Generator/app/backend/src/lessonai/utils/temp_file_cleaner.py), [routes/slides.py](/Users/nguyennhan18/Documents/Lesson-Plan-Generator/app/backend/src/lessonai/api/routes/slides.py), [FunctionPlotter.jsx](/Users/nguyennhan18/Documents/Lesson-Plan-Generator/app/frontend/src/shared/math/FunctionPlotter.jsx).

R01 — tạo module thuần `lessonai/services/math_expression.py`:

- Luồng duy nhất: giới hạn đầu vào → tokenize/chuẩn hóa → cây cú pháp giới hạn → kiểm tra toàn bộ cây → dựng đối tượng toán bằng constructor cho phép.
- Bản đầu hỗ trợ số hữu hạn, tập biến theo ngữ cảnh, ngoặc, dấu một ngôi, phép cộng/trừ/nhân/chia/lũy thừa, các hàm `sin/cos/tan/log/exp/sqrt/Abs` và hằng đã khai báo. Graph chỉ cho biến `x`; kiểm định có tập biến riêng.
- Khóa ưu tiên toán tử và các dạng `^`, `ln`, `abs`, phép nhân ngầm bằng fixture trước khi thay parser. Tên nhiều ký tự/chỉ số phải được khai báo; biểu thức mơ hồ trả chưa hỗ trợ.
- Không chuyển chuỗi chưa tin cậy vào `sympify`, `parse_expr`, `eval`, `exec` hoặc compile cây đầu vào. Từ chối attribute, import, gọi hàm ngoài danh sách, chuỗi, indexing, lambda, comprehension và phép gán. Giới hạn phải có trước các phép tính tạo số lớn.
- Giới hạn chiều dài/token/node/độ sâu/hằng số/lũy thừa. Tác vụ symbolic nặng chạy trong worker có thể kết thúc theo timeout và có giới hạn số job đồng thời; timeout của HTTP đơn thuần không được coi là đã dừng công việc tính toán.
- LaTeX được chuyển trong phạm vi hỗ trợ rồi đi qua cùng parser. Không hỗ trợ thì trả `unverified`, không tự suy ra đúng. `lambdify`, nếu còn dùng, chỉ nhận cây đã kiểm tra, tên ký hiệu đã giới hạn và module tính toán cố định.
- Thay mọi điểm parse: thăm dò graph, graph chính, đường biên bất phương trình, enrich, validator, export. Thăm dò khả năng vẽ không được có parser riêng.

R12 — tạo module thấp tầng `lessonai/core/render_runtime.py` chứa khóa và quản lý vòng đời figure:

- Figure/buffer thuộc từng job; dùng `fig.savefig`/`fig.tight_layout`, dọn bằng `finally`. Khóa chung trong mỗi tiến trình bảo vệ toàn bộ vùng Matplotlib, gồm công thức, không chỉ thao tác lưu.
- Giữ parse/LLM ngoài khóa. Module này không import exporter/service, tránh vòng import vì `services/rendering.py` hiện đang gọi các exporter.
- Cleanup chỉ đóng tài nguyên của job tương ứng; API bảo trì không được đóng figure đang được request khác sử dụng. Cache và tệp tạm dùng khóa theo nội dung và job.

R02 — chuyển FunctionPlotter thành client của API render:

- Bỏ `new Function`, bỏ đồ thị `y=0` khi lỗi; thông tin nghiệm/đỉnh chỉ lấy từ kết quả phân tích có hợp đồng rõ.
- Hủy request cũ, kiểm tra request ID, thu hồi object URL. Ảnh cũ không được hiển thị dưới nhãn biểu thức mới khi request mới lỗi.
- Thay đổi biểu thức/miền vẽ phải làm mất hiệu lực cache ảnh ở editor, Copilot và mọi đường export.

Nghiệm thu M1: payload marker bị từ chối trước tác dụng phụ ở tất cả đường vào; `log/exp/Abs` vẽ đúng trên miền hợp lệ; hàm có gián đoạn không bị nối sai qua điểm không xác định; input quá giới hạn được dừng; hai tác vụ xen kẽ trả đúng figure/nội dung và cleanup không phá tác vụ còn lại. Sau đợt chạy có giới hạn, số figure/job chưa giải phóng không tăng theo tổng tác vụ. So sánh với kết quả tham chiếu, không chỉ kiểm tra ảnh khác bytes hoặc HTTP 200.

**M2 — Hợp đồng dữ liệu, thao tác và xuất file**

Kế hoạch triển khai chi tiết ngày **03/11/2026**: [M2 — hợp đồng dữ liệu và thao tác tin cậy](remediation-m2-contracts-workflows.md). Đây là kế hoạch PR03–PR08, chưa phải nghiệm thu M2; các phần dùng toán/ảnh và patch toán phải giữ cổng phụ thuộc M1.

Tệp chính: [slide_schema.py](/Users/nguyennhan18/Documents/Lesson-Plan-Generator/app/backend/src/lessonai/schemas/slide_schema.py), [chat_schema.py](/Users/nguyennhan18/Documents/Lesson-Plan-Generator/app/backend/src/lessonai/schemas/chat_schema.py), [SlideEditorScreen.jsx](/Users/nguyennhan18/Documents/Lesson-Plan-Generator/app/frontend/src/features/slide-editor/SlideEditorScreen.jsx), [App.jsx](/Users/nguyennhan18/Documents/Lesson-Plan-Generator/app/frontend/src/App.jsx), [slideDeckStorage.js](/Users/nguyennhan18/Documents/Lesson-Plan-Generator/app/frontend/src/shared/storage/slideDeckStorage.js), [documentExportActions.js](/Users/nguyennhan18/Documents/Lesson-Plan-Generator/app/frontend/src/features/exports/documentExportActions.js).

R05/R16/R19 — chuẩn hóa và migration:

- Thêm `schema_version`, `project_id`, `deck_id`, `slide_id`, revision nội dung; `slide_index` bắt đầu từ 1 chỉ biểu thị vị trí. ID không đổi khi thêm/xóa/sắp xếp.
- Lưu dự án gồm giáo án, dàn ý đã duyệt, cấu hình, deck, scene và chú thích. Chú thích gắn với project/deck/slide ID; nạp lại khi đổi bài. Cache render không phải nguồn nội dung và không làm tăng revision nội dung.
- Adapter chuyển dữ liệu cũ tại biên vào, dùng chung cho nạp storage, editor và export. `slide_number` được chuyển sang tên chuẩn; hai tên mâu thuẫn phải báo lỗi. Không âm thầm loại slide để làm payload hợp lệ.
- Mapping nguồn cũ `{source, slide_id}` sang `SourceRef` phải giữ loại và ID nguồn. Kiểm thử JSON round trip; việc sửa assertion của test cũ chưa phải migration.
- Kiểm kê trường prompt/UI/export trước khi siết schema, gồm bảng, hình và dữ liệu render. Trường nghiệp vụ chưa được mô hình hóa phải được bổ sung hoặc từ chối rõ; không lặng lẽ bỏ dữ liệu.
- Tách hợp lệ về cấu trúc khỏi đủ nội dung để giảng: cho lưu slide nháp đang trống; kiểm tra vai trò slide ở M3 quyết định khả năng dùng/xuất hoàn chỉnh.

R07 — xuất đúng bài hoặc trả lỗi:

- Gỡ fallback đổi nội dung ở cả router và hàm đồng bộ Word. Kiểm tra một lần ở biên và truyền cùng snapshot nội dung đến Word/PPTX/ZIP; các exporter không tự chọn bài khác.
- Lỗi thiếu dữ liệu 400, sai schema 422, xung đột phiên bản 409, lỗi chuyển đổi nội bộ 500. Lỗi có `code`, `message`, `request_id`; giữ nguyên ngoại lệ HTTP.
- Frontend chỉ tải khi đúng content type/định dạng; đọc JSON lỗi và giữ bản soạn khi thất bại. ZIP chỉ báo hoàn tất nếu có đủ thành phần được yêu cầu.
- Phân biệt xuất nháp với xuất bản được đánh dấu sẵn sàng sau M3. Payload có trường `ready` do client gửi không thay thế kiểm định nội dung tại backend.

R03 — Copilot trả lời và sửa trên cùng dữ liệu:

- Một lần sinh có cấu trúc trả cả `ai_response` và patch tùy chọn; bỏ patch dựa trên số slide và nhánh nghiệp vụ theo `PYTEST_CURRENT_TEST`. Test inject/mock gateway qua cùng luồng chạy thật.
- Patch gồm proposal ID, deck/slide ID, base revision và hash nội dung gốc; chỉ cho sửa các trường cho phép. Nội dung và đích sửa được kiểm tra ở backend. JSON hợp lệ không được xem là chứng minh đúng toán hoặc đúng chủ đề.
- Server lưu proposal theo chủ phiên với TTL; API áp dụng tra proposal đã được kiểm tra, không tin patch tùy ý từ browser. UI xem trước thay đổi rồi gọi API áp dụng.
- Khi revision/hash khác, trả 409; frontend cũng kiểm tra revision lúc nhận kết quả, tránh ghi đè một chỉnh sửa vừa phát sinh. Áp dụng hợp lệ tăng revision, giữ trường không liên quan và xóa cache phụ thuộc.
- Với editor cục bộ còn lưu nội dung ở client, đây là bảo vệ xung đột trong một phiên. Nếu triển khai chỉnh sửa nhiều người, cần nguồn revision có thẩm quyền ở server; không tuyên bố payload stateless đã giải quyết cộng tác nhiều người.
- LLM lỗi/JSON sai/đích sai: patch null, deck không đổi. Đề xuất chưa kiểm chứng được đánh dấu cần rà soát; không được trình bày như lời giải đã xác minh. Bỏ hoặc sửa các công thức mẫu sai đã biết.

R13/R21 — biên phiên và nhập dữ liệu:

- Bỏ session ID cố định. Cấp phiên riêng gắn với chủ phiên và project; đọc/xóa lịch sử, tạo/áp dụng proposal đều kiểm tra sở hữu. UUID khó đoán không thay thế kiểm tra quyền.
- Với chế độ cục bộ, dùng phiên do server cấp và giới hạn truy cập local. Chế độ dùng chung cần xác thực người dùng, lưu trữ phiên phù hợp nhiều worker, allowlist origin và quyền quản trị cho API bảo trì trước khi bật. Nút làm mới chat phải xóa đúng phiên backend.
- Đọc upload theo giới hạn bytes; kiểm tra định dạng thực, số entry và dung lượng giải nén của Office ZIP, giới hạn trang/shape/hàng/ô. Quá dung lượng trả 413; định dạng không hỗ trợ trả 415.
- Parser nặng chạy ngoài event loop, có timeout và khả năng dừng job phù hợp; chỉ đưa sang thread không được coi là giới hạn CPU/thời gian. Dọn tệp đúng job. Test dùng file nhỏ được cấu hình vượt ngưỡng thấp, không tạo thử tải làm cạn máy.

R14 — sửa đơn vị thống kê:

- API giữ tỷ lệ 0–1, thống nhất cả dữ liệu mẫu; UI nhân 100 khi trình bày phần trăm. Số học sinh ưu tiên đếm từ phân nhóm backend để tránh lệch do làm tròn; tổng nhóm bằng cỡ mẫu.
- Nghiệm thu phổ điểm 0%, 50%, 100% và biên 5/8; dữ liệu `2,4,8,10` phải cho 2 học sinh dưới 5, 2 từ 8 trở lên, nhóm còn lại 0; CV được định dạng đúng.

Nghiệm thu M2: thêm → sửa → xóa/đổi thứ tự → xuất PPTX/ZIP; reload khôi phục đúng dự án; hai bài không trộn chú thích/chat; patch cũ bị từ chối; lỗi xuất không trả file khác bài; hai chủ phiên không đọc/xóa/áp dụng dữ liệu của nhau. R01/R02/R03/R05/R07/R12 có thể được đóng sau khi toàn bộ điều kiện tương ứng đạt, kể cả khi các mốc chất lượng bài giảng phía sau chưa hoàn thành.

**M3 — Nội dung toán có cấu trúc và kiểm định thực sự**

Tệp chính: [lessonGenerationActions.js](/Users/nguyennhan18/Documents/Lesson-Plan-Generator/app/frontend/src/features/generation/lessonGenerationActions.js), [schemas.py](/Users/nguyennhan18/Documents/Lesson-Plan-Generator/app/backend/src/lessonai/schemas/schemas.py), [generation](/Users/nguyennhan18/Documents/Lesson-Plan-Generator/app/backend/src/lessonai/services/generation), [prompts](/Users/nguyennhan18/Documents/Lesson-Plan-Generator/app/backend/src/lessonai/prompts), [curriculum_registry.py](/Users/nguyennhan18/Documents/Lesson-Plan-Generator/app/backend/src/lessonai/rag/curriculum_registry.py), [context_builder.py](/Users/nguyennhan18/Documents/Lesson-Plan-Generator/app/backend/src/lessonai/rag/context_builder.py), [retriever.py](/Users/nguyennhan18/Documents/Lesson-Plan-Generator/app/backend/src/lessonai/rag/retriever.py), [parsers](/Users/nguyennhan18/Documents/Lesson-Plan-Generator/app/backend/src/lessonai/parsers), [geometry.py](/Users/nguyennhan18/Documents/Lesson-Plan-Generator/app/backend/src/lessonai/services/geometry.py).

R04/R10 — khóa ý định bài dạy xuyên suốt:

- Truyền dàn ý đã duyệt với ID từng mục, thứ tự, tiêu đề, ý chính, vai trò, visual và số slide sang cả bước lập giáo án và sinh deck; generator/fallback cùng nhận hợp đồng này.
- Truyền các lựa chọn provider/model có hỗ trợ tới gateway; response ghi nguồn sinh thực tế và việc fallback. UI không tự nhận mọi kết quả là Gemini thành công.
- Xác định `lesson_id` qua đối chiếu tên chuẩn/cụm đặc hiệu; người dùng chọn ID hợp lệ thì ưu tiên ID đó. Trường hợp mơ hồ yêu cầu chọn bài ở bước dàn ý, không tự lấy bài đơn điệu.
- Generator giữ mục đã duyệt và ánh xạ mọi slide về mục nguồn. Nếu phải tách slide vì quá dài, trả lý do và bản dàn ý điều chỉnh để giáo viên duyệt, không âm thầm bỏ nội dung.

R08/R19/R20 — bảo toàn đơn vị kiến thức:
- Mở rộng schema hiện có theo hướng block có ID: định nghĩa/giả thiết, công thức, đề bài, bước giải, bảng, hình, quiz, kết luận; có nguồn và vị trí trong tài liệu gốc. Dùng migration v1 → v2, không tạo một schema cạnh tranh riêng cho canvas.
- Ingest giữ OMML/ảnh/bảng/group và dữ liệu nguồn. Chuyển đổi công thức trong phạm vi kiểm tra được; với MathType/OLE hoặc loại chưa hỗ trợ, giữ bản gốc và báo phần chưa trích được. Không báo nhập đầy đủ nếu công thức đã mất.
- Thay cắt `bullet_points[:3/4]` bằng chọn đơn vị hoàn chỉnh theo mục tiêu và ngân sách nội dung. Đơn vị quá dài được tách có liên kết, giữ giả thiết và kết luận.
- Giữ tham chiếu asset tới context/fallback/export. Câu cần hình/bảng mà asset chưa có phải bị loại khỏi sinh tự động hoặc để nháp với lý do, không tự bịa hình.
- Lọc cứng lớp/chương trình/bài học; đánh dấu CT 2006 và CT 2018 rõ để không trộn nguồn ngoài phạm vi. Nguồn không đủ tốt được cách ly, không dùng lời giải mẫu chung để lấp chỗ trống.
- Dữ liệu mới được tạo vào staging, so diff và kiểm định trước khi cập nhật runtime; giữ phiên bản/checksum và khả năng quay lại dữ liệu đã duyệt.

R09 — kiểm định quyết định trạng thái sử dụng:

- Một báo cáo theo revision/hash bao phủ mọi trường toán: block, `worked_solution_steps`, công thức chính, quiz/đáp án/giải thích, chart, scene và phần lời giảng có khẳng định toán.
- Phân biệt kết quả kiểm từng mệnh đề: `verified`, `failed`, `unverified`; ghi phương pháp và phạm vi. Không có cảnh báo hoặc LLM tự khai `verified` không đủ để xác nhận đúng.
- Kiểm tra điều kiện/miền xác định khi so sánh biểu thức; phần nằm ngoài engine phải cần rà soát chuyên môn. Timeout cũng là chưa kiểm chứng.
- Kiểm tra theo vai trò: ví dụ phải có đề/dữ kiện/bước giải/kết luận; single-choice bốn lựa chọn phải có đúng một đáp án, nhãn không trùng; hình/bảng được tham chiếu phải tồn tại; định lí phải có điều kiện. Các loại quiz khác có schema riêng.
- Kiểm tra khớp đề–lời giải–đáp án và mục tiêu–chuỗi hoạt động. LLM có thể giúp chỉ ra nghi vấn, không là nguồn xác minh duy nhất.
- Dùng cùng validator ở generate, fallback, edit/apply-patch và export; thay đổi nội dung làm mất hiệu lực kết quả cũ. Frontend xử lý `is_valid/errors` của giáo án trước bước tiếp theo.

| Trạng thái tài liệu | Điều kiện | Hành vi |
| --- | --- | --- |
| `draft` | Đang soạn hoặc thiếu nội dung | Cho lưu/xem; xuất nháp phải có nhãn rõ |
| `needs_review` | Có nội dung chưa kiểm chứng hoặc nghi vấn | Hiển thị vị trí/lý do; chỉ xuất theo luồng nháp |
| `blocked` | Có lỗi toán đã xác định, thiếu dữ kiện bắt buộc hoặc dữ liệu không hợp lệ | Chặn áp dụng/phát hành và xuất hoàn chỉnh; vẫn giữ để sửa |
| `ready` | Đạt quy tắc cấu trúc; mệnh đề bắt buộc đã được engine trong phạm vi hỗ trợ hoặc người có chuyên môn xác nhận | Cho xuất/phát hành theo phạm vi đã duyệt |

Trạng thái do backend tính từ nội dung hiện hành; xác nhận chuyên môn được lưu theo revision và mệnh đề, không là một checkbox chung có thể bỏ qua lỗi đã xác định.

R11/R15 — một scene cho tính toán và hình vẽ:

- Scene chứa điểm/cạnh/mặt, đơn vị, tham số, giả thiết và loại hình rõ. Phân biệt chóp đều với chóp có cạnh bên vuông góc đáy; không đổi mô hình hiện có sang giả thiết khác mà giữ nguyên tên bài.
- Renderer 3D và phép tính cùng dùng tọa độ chuẩn; phép chiếu camera không được làm biến dạng tọa độ mô hình. Nghiệm thu bằng bất biến cạnh đáy, cạnh bên, góc, chân đường cao và thể tích.
- Snapshot khóa theo `slide_id + scene_hash + camera`; xuất từng scene tương ứng. Bỏ sao chép ảnh mô hình đang mở sang mọi slide; thiếu snapshot phù hợp phải render lại hoặc báo thiếu.

Nghiệm thu M3: `1+1=3` trong lời giải bị phát hiện; thiếu hình/điều kiện/đáp án lệch không được ready; ứng dụng tích phân chọn `M12-C4-B3`; dàn ý sửa được giữ ở đầu ra; chuỗi giáo án–slide–lời giải–nguồn nhất quán. Chóp đều có cạnh bên bằng nhau, deck lập phương/chóp xuất đúng ảnh từng trang. Kiểm tra cả provider mock và nhánh fallback qua cùng validator.

**M4 — Bố cục theo khối và bản xuất có thể giảng dạy**

Tệp chính: [PresentationStage.jsx](/Users/nguyennhan18/Documents/Lesson-Plan-Generator/app/frontend/src/features/presentation/PresentationStage.jsx), [MathText.jsx](/Users/nguyennhan18/Documents/Lesson-Plan-Generator/app/frontend/src/shared/math/MathText.jsx), [styles](/Users/nguyennhan18/Documents/Lesson-Plan-Generator/app/frontend/src/styles), [slide_exporter.py](/Users/nguyennhan18/Documents/Lesson-Plan-Generator/app/backend/src/lessonai/exporters/slide_exporter.py), [docx_exporter.py](/Users/nguyennhan18/Documents/Lesson-Plan-Generator/app/backend/src/lessonai/exporters/docx_exporter.py).

- Xây ba layout đầu tiên: khái niệm + điều kiện + minh họa; ví dụ với đề/bước giải/kết luận; câu hỏi với hình/bảng và phương án. Chọn layout theo vai trò và lượng nội dung.
- Canvas là mặt bố cục với hệ tọa độ/kích thước và các block có ID. Text/công thức, hình, bảng và chú thích có vùng đo riêng; có thể dùng DOM/SVG cho phần đọc được và canvas cho 3D/nét vẽ theo chức năng hiện có.
- Dùng layout spec và style token chung cho web/PPTX. Chốt mức chữ tối thiểu trong mẫu duyệt; nếu vượt vùng chứa thì tách trang/bước, không cắt mất giả thiết hay thu nhỏ vô hạn.
- Đưa `worked_solution_steps` lên mặt slide, cho reveal theo bước trên web và build-up phù hợp trong PPTX; notes giữ kịch bản giáo viên. Công thức dưới dạng ảnh phải được mô tả đúng giới hạn chỉnh sửa trong tài liệu sản phẩm.
- Bỏ ép màu KaTeX toàn cục; công thức nhận màu phù hợp vùng chứa. Snapshot kiểm tra nền sáng/tối, bảng, công thức dài, quiz và lời giải.
- Chú thích được gắn ID và nạp lại đúng bài/trang. Phím tắt không chiếm thao tác khi giáo viên nhập chat/công thức; cache và state cục bộ đổi theo slide ID, không theo chỉ số mảng.
- Poll khởi tạo 0, lưu/reset theo question ID; giao diện mô tả đúng chế độ thu phiếu hiện có. Kênh bình chọn từ thiết bị học sinh là hạng mục sau nếu chưa triển khai.

Nghiệm thu M4: đọc lại và render PPTX xác nhận có lời giải trên mặt trang, đúng ảnh, không chồng/cắt khối. Giáo viên thực hiện được tiến trình đặt vấn đề → lập luận → kết luận trên cả web và bản xuất. Reload/đổi bài/sắp xếp không đưa nét vẽ hay phiếu sang câu khác. Các tính năng kéo thả tự do của canvas được để sau khi layout theo khối đạt các điều kiện này.

**M5 — Bộ bài chuẩn, CI và phát hành**

Đóng R22 bằng audit mới tại thời điểm triển khai, nâng dependency có kiểm soát và cập nhật lockfile; không lấy số phiên bản trong báo cáo lịch sử làm trạng thái hiện tại. Đưa MathLive vào dependency được khóa và bundle; kiểm tra nhập công thức khi không có CDN. Ghi rõ phạm vi advisory còn lại nếu có.

R23 đã được cải thiện bởi package/Makefile/CI/test frontend hiện có. Phần còn lại là nghiệm thu từ checkout sạch, test hành vi thực và tài liệu đúng khả năng sản phẩm:

- Giữ các test nhanh đang có; thêm E2E trình duyệt dùng backend thật và provider giả lập ở ranh giới LLM. Mock HTTP 200 cho payload bất kỳ không thay thế kiểm tra editor–API–export.
- Chạy CI: backend/frontend unit và integration → critical regressions → E2E → build → kiểm tra nội dung/layout trên fixture. Lint phải có chế độ exit khác 0 khi vi phạm tiêu chí; việc công cụ chạy hết không được xem là dữ liệu đã đạt.
- Fixture và dữ liệu runtime tối thiểu phải có trong checkout hoặc bước dựng tái lập có checksum. Không phụ thuộc `data/raw` trên máy cá nhân hoặc một báo cáo JSON cũ để làm test đạt.
- Thay đổi API/schema có fixture migration và diff OpenAPI được review. Cập nhật fixture chỉ sau khi kiểm tra tác động; không giữ nguyên hợp đồng cũ bằng cách bỏ qua trường mới cần thiết.
- Kiểm thử LLM thật là job riêng khi có khóa; lưu provider/model, phiên bản prompt/dataset và kết quả. Skip do thiếu khóa phải hiển thị; không dùng kết quả deterministic để tuyên bố đã kiểm chứng provider thật.
- Cập nhật endpoint, cách chạy, chế độ local/shared, giới hạn nhập và mức chỉnh sửa công thức thực tế trong README/tài liệu. Log request/job/revision đủ truy vết, không ghi khóa hoặc toàn bộ bảng điểm vào log.

Bộ nghiệm thu đầu tiên dùng sáu bài đã có trong registry:

| Nhóm | Bài đại diện | Điều cần chứng minh |
| --- | --- | --- |
| Đạo hàm | M12-C1-B1 — Đơn điệu và cực trị | Miền, dấu đạo hàm, bảng/đồ thị và kết luận khớp |
| Nguyên hàm | M12-C4-B1 | Họ nguyên hàm có hằng số, bước giải đúng; Copilot không đổi sang hình học |
| Ứng dụng tích phân | M12-C4-B3 | Chọn đúng bài, đúng cận/miền và ý nghĩa diện tích |
| Thống kê | M12-C3-B2 | Công thức/đơn vị/số liệu và kết luận nhất quán |
| Oxyz | M12-C5-B1 — Phương trình mặt phẳng | Điều kiện và dữ kiện hình học đúng |
| Xác suất | M12-C6-B2 — Toàn phần và Bayes | Biến cố/điều kiện/mẫu số đúng, giải thích rõ |

Thêm fixture hình lập phương và chóp đều cho engine/ảnh, không suy ra mọi bài trong chương đã đạt từ một fixture. Mỗi bài đại diện cần ít nhất một ví dụ hoàn chỉnh được kiểm tra độc lập và một lỗi chủ đích mà validator phải bắt.

Cổng phát hành kỹ thuật: toàn bộ sáu lỗi trọng yếu và RF01 có regression test đạt; không có test trọng yếu bị skip; không đổi/mất nội dung khi lỗi; clone sạch qua các check bắt buộc. Cổng dùng chung dịch vụ bổ sung cách ly/chủ sở hữu và giới hạn tài nguyên, không tự bật chỉ vì chế độ local chạy được.

Cổng công bố bài sẵn sàng giảng dạy: trong tập bài được bật có 0 lỗi chặn đã xác định, đủ hình/bảng/lời giải/nguồn bắt buộc; mọi mệnh đề bắt buộc có bằng chứng kiểm định hoặc duyệt chuyên môn theo revision; giáo viên kiểm tra đủ độ sâu, tiến trình dạy và bản PPTX. Tỷ lệ lint không thay thế đánh giá này. Mở rộng từng nhóm bài sau nghiệm thu, không tuyên bố toàn bộ Toán 12 đã đạt cùng lúc.

**Danh sách PR theo thứ tự thực hiện**

| PR | Phạm vi review được | Phụ thuộc |
| --- | --- | --- |
| 00 | Audit chạy được, baseline mới, chặn tạm các đường nguy hiểm/đổi bài | Bắt đầu |
| 01 | Parser an toàn và toàn bộ đường parse — R01 | 00 |
| 02 | Runtime render chung và frontend render — R12/R02 | 01 |
| 03 | ID/revision, adapter dữ liệu cũ, editor và lưu dự án — R05/R16/R19 | 00 |
| 04 | Hợp đồng lỗi và xuất snapshot đúng bài — R07 | 03; kiểm tra lại với 02 |
| 05 | Phiên riêng và kiểm tra quyền — R13 | 03 |
| 06 | Copilot có cấu trúc, proposal và áp dụng có kiểm tra — R03 | 01/03/05 |
| 07 | Giới hạn upload và worker parse — R21 | 00 |
| 08 | Đơn vị và số đếm thống kê — R14 | 00 |
| 09 | Dàn ý xuyên suốt và nhận diện đúng bài — R04/R10 | 03 |
| 10 | Block schema, migration và kiểm định/trạng thái — R09/R19 | 01/03/09 |
| 11 | Ingest/RAG giữ đơn vị kiến thức và asset — R08/R20 | 07/10 |
| 12 | Scene chuẩn và snapshot từng slide — R11/R15 | 03/10 |
| 13 | Layout web/PPTX, lời giải và theme — R06/R17 | 02/10/11/12 |
| 14 | Chú thích, reload/reveal và poll theo ID — R16/R18 | 03/13 |
| 15 | Nghiệm thu cuối, dependency, CI/E2E và tài liệu — R22/R23 | Các PR liên quan đã đạt |

Kiểm thử/E2E và cập nhật tài liệu đi cùng từng PR; PR 15 tổng hợp nghiệm thu, không dồn toàn bộ kiểm thử tới cuối. R22 cần được kiểm kê từ M0; nếu audit mới cho thấy dependency có lỗ hổng đang nằm trên đường sử dụng thực tế, đưa bản vá lên PR sớm phù hợp.

Mỗi PR gồm: tình huống trước/sau, test tái hiện, thay đổi nhỏ nhất cần thiết, migration nếu có, kết quả và giới hạn. Không sửa kỳ vọng test để hợp thức hóa mất metadata, bài sai hay đồ thị thay thế. Hoàn tác tính năng bằng cờ tắt và giữ bản nháp; không hoàn tác sang parser nguy hiểm hoặc fallback đổi bài.

**Ma trận đóng lỗi**

| Mã | Đóng khi có bằng chứng | Mốc |
| --- | --- | --- |
| R01 | Từ chối marker và giới hạn tài nguyên ở mọi điểm parse; toán được hỗ trợ vẫn đúng | M1 |
| R02 | Browser không thực thi chuỗi; hàm đúng hiển thị đúng, lỗi không tạo đường giả | M1 |
| R03 | Trả lời/patch cùng bài, đúng ID/revision; offline không patch mẫu | M2 |
| R04 | Dàn ý sửa đổi được giữ xuyên suốt generation và fallback | M3 |
| R05 | Thêm/sửa/xóa/đổi thứ tự rồi xuất API thật, không lỗi hợp đồng | M2 |
| R06 | Lời giải hiện trên mặt slide PPTX và tiến trình giảng đọc được | M4 |
| R07 | Input/export lỗi trả đúng lỗi; không file khác bài; ZIP đủ thành phần | M2 |
| R08 | Đơn vị kiến thức và asset/nguồn được giữ; câu thiếu dữ kiện bị chặn | M3 |
| R09 | Lỗi trong mọi trường toán bị xét; chưa kiểm chứng không tự ready | M3 |
| R10 | Bộ tên đặc hiệu/ID/không xác định được định tuyến đúng | M3 |
| R11 | Scene và phép tính chung nguồn; bất biến hình học đạt | M3 |
| R12 | Xen kẽ render/cleanup không nhầm hoặc đóng tài nguyên của job khác | M1 |
| R13 | Hai chủ phiên không truy cập lịch sử/proposal của nhau; reset đúng | M2 |
| R14 | Tỷ lệ/CV và số đếm khớp API–UI trên các phổ điểm biên | M2 |
| R15 | Deck nhiều scene xuất đúng ảnh từng slide và phiên bản | M3 |
| R16 | Project/slide ID, reload và chú thích đúng sau đổi/sắp xếp bài | M2 + M4 |
| R17 | Công thức đọc được trong toàn bộ theme/layout thuộc phạm vi bật | M4 |
| R18 | Bắt đầu 0, reset/cách ly theo câu; nhãn đúng chế độ hoạt động | M4 |
| R19 | Metadata/block/table không mất qua migration và JSON round trip | M2 + M3 |
| R20 | Formula/asset có cấu trúc hoặc báo phần không trích được; không mất thầm lặng | M3 |
| R21 | Input quá giới hạn bị từ chối, parser nặng không giữ event loop/job vô hạn | M2 |
| R22 | Audit mới được xử lý theo phạm vi; runtime editor công thức được khóa/bundle | M5 |
| R23 | Clone sạch chạy CI/hành trình thật; tài liệu đúng khả năng; dữ liệu tái lập | M0 + M5 |
| RF01 | Hai CLI chạy được, đọc đúng module và có smoke test | M0 |

Một lỗi chỉ chuyển sang “đã sửa” khi có mã thay đổi, test đạt và bằng chứng đi kèm. Việc viết kế hoạch, tắt tạm tính năng hoặc làm xanh bộ test cũ chưa đáp ứng điều kiện này.
