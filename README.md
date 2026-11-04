# LessonAI-5512

Ứng dụng local giúp giáo viên soạn, sửa, lưu dự án, trình chiếu và xuất DOCX/PPTX/ZIP. AI tạo **bản nháp cần kiểm tra**. Không có bài mẫu, dàn ý dự phòng hay hình học mặc định được đưa vào bài đang soạn khi dịch vụ lỗi.

## Cài đặt và chạy

Môi trường nghiệm thu local: Python 3.13. Cấu hình CI dùng Python 3.13 và Node.js 22.

```bash
python3.13 -m venv app/backend/venv
app/backend/venv/bin/python -m pip install -r app/backend/requirements-lock.txt
app/backend/venv/bin/python -m pip install --no-deps -e app/backend
npm --prefix app/frontend ci
npm --prefix app/frontend run build
make backend
```

Mở `http://127.0.0.1:8000`. Khi phát triển giao diện, chạy thêm `make frontend` và mở `http://127.0.0.1:5173`.

Để dùng AI, tạo `app/backend/.env`, cấu hình khóa của nhà cung cấp bạn chọn:

```dotenv
GEMINI_API_KEY=
GROQ_API_KEY=
OPENROUTER_API_KEY=
```

Không cần khóa để biên tập thủ công, lưu, kiểm tra số học, dựng hình từ dữ kiện hoặc xuất bản soạn. Khi không gọi được nhà cung cấp, ứng dụng báo lỗi và giữ bài hiện hành. Khóa API không đưa vào frontend.

## Quy trình sử dụng

1. Tạo dự án trống hoặc phục hồi tệp JSON của chính bạn. Có thể soạn thủ công tại **Biên Tập Slide**.
2. Nếu dùng AI: nhập chủ đề → tạo dàn ý → sửa và duyệt dàn ý → sinh giáo án và slide. Số trang, ID, thứ tự, tiêu đề và ý đã duyệt được kiểm tra ở backend.
3. Biên tập nội dung và lưu. Dự án được lưu trong IndexedDB; có nút tải JSON dự phòng. Lỗi lưu được hiển thị để xử lý.
4. Với hình/đồ thị: đối chiếu đề bài, nhập đủ dữ kiện và xác nhận. Không xác nhận hoặc sửa giả thiết sau đó thì hình cũ không còn được coi là hợp lệ.
5. Chạy **Kiểm tra bài**. Lỗi đã xác định chặn việc duyệt; phần chưa kiểm chứng vẫn cần giáo viên xem xét. Xác nhận chuyên môn chỉ áp dụng cho nội dung của phiên bản đã kiểm tra.
6. Trình chiếu, hiện từng bước giải, chú thích theo slide hoặc dùng bảng phụ. Xuất PPTX/ZIP lấy bản dữ liệu hiện hành; trang tiếp nối giữ lời giải và nội dung dài. DOCX được ghi là bản nháp vì việc duyệt slide không chứng nhận riêng giáo án.

## Phạm vi kiểm chứng

| Thành phần | Đã hỗ trợ | Giới hạn |
|---|---|---|
| Biểu thức | Parser giới hạn; số, `x`, phép toán và `sin`, `cos`, `tan`, `log`, `exp`, `sqrt`, `Abs` | Cú pháp ngoài phạm vi bị từ chối; không chạy mã do AI sinh |
| Đồ thị | Hàm gốc/đạo hàm, miền xác định từ biểu thức gốc; cấp số cộng rời rạc; hệ bất phương trình tuyến tính từ hệ số | Miền nghiệm chỉ biểu diễn trong cửa sổ đã chọn; không nhận đa giác AI tự vẽ làm căn cứ |
| Hình học | Lập phương; chóp đều đáy vuông; chóp đáy vuông có SA vuông góc đáy | Các hình khác chưa được bật. Web và PPTX dùng cùng tọa độ; góc nhìn/bố cục không cam kết giống từng pixel |
| Toán trong bài | Duyệt công thức ở cả bước giải, nội dung, bảng và đáp án; chặn đẳng thức số học sai | Đồng nhất thức cần khai báo vai trò rõ; phương trình, điều kiện, lập luận và sư phạm chưa được chứng minh tự động |
| RAG | Giữ đơn vị nguồn đầy đủ, hash và asset; chỉ đưa nguồn có hồ sơ duyệt khớp hash vào ngữ cảnh | Kho học liệu local chưa có nghiệm thu chuyên môn; lint sạch không đồng nghĩa đúng toán |
| Nhập Office | Giới hạn dung lượng/giải nén/thời gian; giữ XML OMML và asset gốc | Chưa tự chuyển hoàn chỉnh OMML/MathType/OLE thành nội dung biên tập; API báo rõ phần cần đối chiếu |
| Xuất | Không tự chèn hoạt động thiếu hoặc bài thay thế; có nhãn bản nháp, manifest và checksum | Công thức không chuyển được sẽ giữ nguồn LaTeX; cần xem lại bố cục bản xuất, nhất là công thức/bảng dài |

`ready` nghĩa là không có lỗi chặn trong phạm vi kiểm tra và giáo viên đã xác nhận phiên bản đó. Nó không có nghĩa LLM hay bộ kiểm định chứng minh được mọi nội dung.

## Dữ liệu và phạm vi triển khai

- Dự án nằm trong trình duyệt, theo project/deck/slide ID và revision. Xóa dữ liệu trình duyệt sẽ xóa bản local; dùng JSON dự phòng để chuyển máy/phục hồi.
- Hội thoại thuộc phiên chủ sở hữu local và bộ bài; đề xuất có thời hạn, kiểm tra phiên bản trước khi áp dụng và không áp dụng hai lần. Lịch sử server nằm trong RAM, không phải kho lưu dài hạn.
- Xác nhận hình và duyệt bài có thời hạn 24 giờ; khởi động lại backend hiện làm mất hiệu lực chữ ký. Dữ kiện/bản soạn vẫn còn, cần xác nhận lại.
- Đây là **mô hình một tiến trình, dùng local**. Cookie phiên và kiểm tra Origin không thay thế đăng nhập/phân quyền cho dịch vụ nhiều người dùng. Backend mặc định bind `127.0.0.1`.
- Upload tối đa 12 MiB/tệp, 16 MiB/request, 60 MiB sau giải nén, tối đa 3.000 thành phần Office. Worker có deadline và bị dừng khi quá hạn. Giới hạn bộ nhớ/CPU bằng `resource` áp dụng trên Linux; macOS có deadline và giới hạn đầu vào.
- Kho RAG đặt ở `app/backend/data`, hoặc cấu hình `LESSONAI_DATA_DIR`. Không có kho local thì không lấy nguồn thay thế từ bài khác.

Tạo danh sách nguồn để giáo viên rà soát (không tự gắn nhãn đã duyệt):

```bash
make prepare-source-review REVIEW_OUTPUT=/tmp/lessonai-review-unique
```

Nguồn được phép dùng cần bản ghi trong `LESSONAI_DATA_DIR/reviewed_sources.json`: `sha256`, `status: "approved"`, `reviewer`, `reviewed_at`. Hash phải khớp đúng đơn vị nguồn đã duyệt. Không sửa hàng loạt trạng thái chỉ để tăng số lượng nguồn sử dụng.

## Kiểm thử và bằng chứng

```bash
make test                  # Có cả kiểm tra kho học liệu local
make test-portable         # Không phụ thuộc kho học liệu và báo cáo chưa đưa vào Git
make test-critical
make test-e2e              # Backend thật + trình duyệt; không cần API key
make audit-acceptance REVIEW_OUTPUT=/tmp/lessonai-acceptance-unique
```

Playwright dùng Chrome đã cài trên macOS. Trên Linux hoặc máy chưa có trình duyệt: chạy `npx playwright install chromium` trong `app/frontend`. CI cài Chromium riêng. Các bài và số liệu trong kiểm thử chỉ là fixture kiểm thử, không thuộc luồng sản phẩm.

Các probe không ghi đè bằng chứng cũ. Báo cáo trình duyệt ở `app/frontend/playwright-report`; trace khi lỗi ở `app/frontend/test-results`.

Hợp đồng API đã thay đổi có chủ đích: bỏ `/api/v1/test-cases`; API hình học và xem bài mẫu cũ trả 410; Copilot yêu cầu phiên chủ sở hữu; lỗi trả `detail.code/message/request_id`; đầu vào trống/không hợp lệ trả lỗi, không trả bài mẫu.

Xem [báo cáo triển khai](reports/remediation-implementation-2026-11-03.md), [danh sách file thay đổi](reports/remediation-changed-files-2026-11-03.md) và [đánh giá kế hoạch sau triển khai](docs/plans/remediation-acceptance-2026-11-03.md).

Cập nhật 04/11/2026: **M1–M4 chưa đủ điều kiện bàn giao**. Khi có sửa slide chưa lưu, cần lưu trước khi chuyển màn hình hoặc xuất; khi nạp dự án lỗi, tự lưu tạm dừng để phục hồi. Nếu cổng 8000 đang bận, có thể chạy E2E bằng `LESSONAI_TEST_PORT=18080 npm --prefix app/frontend run test:e2e`.
