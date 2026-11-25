# LessonAI-5512

Xưởng soạn bài cho giáo viên Toán 12 THPT (GDPT 2018, Công văn 5512): AI tạo bản nháp, giáo viên duyệt, chỉnh sửa, trình chiếu và xuất bản.

## Sản phẩm

**Bài giảng**:
Gói trọn một tiết dạy, gồm một Dàn ý cùng Kế hoạch bài dạy và Bộ slide dựng từ Dàn ý đó.
_Avoid_: gói kép, dual package (khi nói về khái niệm, không phải định dạng tệp)

**Kế hoạch bài dạy**:
Văn bản tổ chức tiết dạy theo cấu trúc Công văn 5512: mục tiêu, thiết bị, và tiến trình bốn hoạt động.
_Avoid_: giáo án, lesson plan, bài giảng

**Bộ slide**:
Chuỗi Slide dùng để Trình chiếu trên lớp, được dựng từ Dàn ý của cùng Bài giảng.
_Avoid_: slide deck, bài giảng, bài thuyết trình

**Bản soạn**:
Phiên bản Bài giảng mà giáo viên đang làm việc; mọi lỗi của AI hay của hệ thống đều không được làm mất hoặc thay thế nó.
_Avoid_: bản nháp đang mở, active draft

**Phiên bản**:
Một bản lưu cố định của Bản soạn; mỗi lần tạo lại bằng AI sinh ra một Phiên bản mới, các Phiên bản cũ vẫn mở lại được.
_Avoid_: snapshot, bản sao lưu

**Chuẩn tối thiểu**:
Bộ điều kiện nội dung mà Kế hoạch bài dạy phải đạt thì mới được xuất ra DOCX hoặc PPTX.
_Avoid_: hợp lệ 5512, validation (khi nói về nội dung sư phạm)

**Xác nhận chuyên môn**:
Lời xác nhận của giáo viên rằng đã đối chiếu đề, điều kiện, lời giải, nguồn và tiến trình của đúng một phiên bản Bộ slide hoặc Kế hoạch bài dạy. Khác với việc xác nhận dữ kiện của một Yêu cầu trực quan.
_Avoid_: duyệt bài, approve, "xác nhận" (khi không rõ là loại nào)

**Bản nháp**:
Bộ slide hoặc Kế hoạch bài dạy chưa có Xác nhận chuyên môn cho phiên bản hiện tại.
_Avoid_: draft (khi thật ra đang nói về Bản soạn)

**Cần xem lại**:
Trạng thái của một phần nội dung được dựng từ dữ liệu đã đổi: slide của một Mục dàn ý đã sửa, Kế hoạch bài dạy lệch Dàn ý, hoặc nội dung dựa trên một Mệnh đề toán đã đổi.
_Avoid_: stale, đã đổi, lỗi thời

## Dàn ý và slide

**Dàn ý**:
Danh sách có thứ tự các Mục dàn ý mà giáo viên duyệt trước khi hệ thống dựng Bộ slide hay Kế hoạch bài dạy.
_Avoid_: outline, đề cương, khung bài

**Mục dàn ý**:
Một ý trọn vẹn của Dàn ý, thuộc đúng một Hoạt động và có một Loại mục, mang số slide và số phút dự kiến, có thể kèm Yêu cầu trực quan. Mọi Slide đều thuộc đúng một Mục dàn ý.
_Avoid_: slide dàn ý, outline item, ý chính

**Loại mục**:
Loại nội dung của một Mục dàn ý: Mở đầu, Tình huống khởi động, Kiến thức trọng tâm, Ví dụ, Bài luyện tập, Câu hỏi trắc nghiệm hoặc Tổng kết.
_Avoid_: visual type, loại slide, kiểu slide

**Slide**:
Một khung trình chiếu tỉ lệ 16:9 chứa các phần tử (chữ, công thức, bảng, ảnh, Hình tương tác, Bảng biến thiên) đặt ở vị trí cụ thể.
_Avoid_: trang, page

**Bố cục mẫu**:
Cách xếp sẵn vị trí ban đầu của các phần tử trên một Slide, ứng với Loại mục của nó; AI chọn Bố cục mẫu chứ không tự đặt tọa độ.
_Avoid_: layout, template

**Trình chiếu**:
Chế độ chiếu Bộ slide toàn màn hình ngay trong hệ thống, nơi giáo viên dạy và thao tác Hình tương tác.
_Avoid_: present mode, chế độ thuyết trình

## Yêu cầu trực quan

**Yêu cầu trực quan**:
Yêu cầu có một đồ thị hàm số, một hình không gian hoặc một Bảng biến thiên cho một Mục dàn ý, kèm dữ kiện cụ thể (biểu thức, khoảng vẽ, loại hình, tọa độ, số đo). Chỉ có hiệu lực khi giáo viên đã xác nhận dữ kiện; AI chỉ được đề xuất.
_Avoid_: hình minh họa, visual, trực quan hóa, ý đồ toán

**Hình tương tác**:
Đồ thị hàm số hoặc hình không gian trên Slide mà giáo viên thao tác trực tiếp khi Trình chiếu; chỉ tồn tại nhờ một Yêu cầu trực quan đã xác nhận.
_Avoid_: hình minh họa, mô hình 3D (khi nói chung chung)

**Hình Oxyz**:
Hình không gian gồm các điểm, vectơ, đường thẳng, mặt phẳng và mặt cầu đặt trong hệ trục tọa độ Oxyz, dựng từ tọa độ hoặc phương trình đã xác nhận.
_Avoid_: cảnh 3D, scene

**Bảng biến thiên**:
Bảng ghi dấu của đạo hàm và chiều biến thiên của một hàm số (kể cả bảng xét dấu), do hệ thống tính từ biểu thức trong một Yêu cầu trực quan đã xác nhận.
_Avoid_: BBT, bảng (khi nói chung chung)

## Kiểm chứng toán

**Mệnh đề toán**:
Một khẳng định toán đơn lẻ, như một điểm cực trị, một dòng của Bảng biến thiên hay một bước giải, mang trạng thái kiểm chứng riêng.
_Avoid_: lời giải (là văn xuôi, gồm nhiều mệnh đề)

**`math_spec`**:
Tập Mệnh đề toán của một Bài giảng được gửi cho Cổng toán: công thức hàm, miền xác định, điều kiện loại trừ và các bước giải được dùng.

**Cổng toán**:
Phép kiểm bắt buộc mà một Mệnh đề toán phải qua trước khi được hiển thị như kết quả chính xác.

**`verified`**:
Mệnh đề đã được máy chứng minh, đúng trong Phạm vi công bố của phép kiểm. Không lan sang lời giải văn xuôi, slide hay cả khối nội dung.

**`unverified`**:
Mệnh đề chưa được máy chứng minh; không được hiển thị như kết quả chính xác.

**`failed`**:
Mệnh đề mà phép kiểm đã chỉ ra là sai.

**`teacher_approved`**:
Mệnh đề `unverified` được giáo viên duyệt, kèm người duyệt, thời điểm và hash nội dung; không thay thế kiểm chứng máy với nhãn toán do hệ thống tính.

**Phạm vi công bố**:
Giới hạn mà một phép kiểm tuyên bố đã chứng minh được (loại biểu thức, miền biến, phiên bản phép kiểm); `verified` chỉ có nghĩa trong phạm vi này.

## Cấu trúc Kế hoạch bài dạy

**Hoạt động**:
Một trong bốn chặng của tiến trình dạy học (Khởi động, Hình thành kiến thức, Luyện tập, Vận dụng), gồm Mục tiêu, Nội dung, Sản phẩm và Tổ chức thực hiện.
_Avoid_: activity, bước (bước là một phần của Tổ chức thực hiện)

**Tổ chức thực hiện**:
Bốn bước của một Hoạt động: chuyển giao nhiệm vụ, thực hiện nhiệm vụ, báo cáo thảo luận, kết luận nhận định.
_Avoid_: execution, các bước

**Kiến thức trọng tâm**:
Định nghĩa, định lý hoặc công thức mà học sinh phải nắm sau Hoạt động Hình thành kiến thức.
_Avoid_: nội dung chính, lý thuyết

**Ví dụ**:
Bài toán mẫu do giáo viên trình bày, có đề bài, lời giải từng bước và đáp án.
_Avoid_: bài mẫu, ví dụ minh họa (khi không có lời giải)

**Bài luyện tập**:
Bài toán học sinh tự giải, có đề bài, đáp án và Mức độ.
_Avoid_: bài tập (khi không rõ là Ví dụ hay Bài luyện tập), câu hỏi

**Câu hỏi trắc nghiệm**:
Câu hỏi có bốn phương án A, B, C, D với đúng một phương án đúng; mỗi phương án sai kèm lời giải thích vì sao sai.
_Avoid_: quiz, live poll, câu hỏi (khi không nói rõ là trắc nghiệm)

**Mức độ**:
Mức yêu cầu nhận thức của một Bài luyện tập: nhận biết, thông hiểu, hoặc vận dụng.
_Avoid_: độ khó, level

**Phiếu học tập**:
Tờ nhiệm vụ phát cho học sinh trong một Hoạt động; không bắt buộc.
_Avoid_: worksheet, phiếu bài tập

## Nguồn tri thức

**Nguồn đã duyệt**:
Đơn vị nội dung SGK mà một người duyệt thật đã chấp thuận; chỉ nguồn này mới được đưa vào ngữ cảnh cho AI.
_Avoid_: corpus, dữ liệu RAG
