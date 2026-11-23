# Glossary

Thuật ngữ của miền "tạo bài giảng nhiều vai trò". Chỉ chứa định nghĩa; quyết định thiết kế nằm ở `docs/architecture/multi-role-generation-decisions.md`.

## Vai trò và bàn giao

**Vai trò (role)**:
Một bước AI trong chuỗi tạo bài giảng, có nhiệm vụ, hợp đồng kết quả và kết quả bàn giao riêng. Ví dụ: Chuyên gia toán, Thiết kế trực quan, Phản biện.

**Bàn giao (handoff)**:
Kết quả bất biến mà một vai trò trao cho vai trò kế tiếp. Sửa đổi tạo phiên bản mới, không ghi đè bản cũ.

**Lượt tạo bài (generation run)**:
Một lần chuỗi vai trò chạy từ dàn ý đã duyệt đến Phản biện. Các phiên bản kết quả của một lượt được giữ để truy vết.

## Toán và kiểm chứng

**Ý đồ toán**:
Họ hàm, tham số (tên, vai trò, khoảng tương tác) và hiện tượng giáo viên muốn học sinh quan sát, được giáo viên duyệt ở điểm duyệt dàn ý.

**Điều kiện áp dụng**:
Khoảng giá trị của tham số mà trong đó một mệnh đề toán hoặc nhãn còn đúng. Ngoài khoảng này, nội dung phụ thuộc mệnh đề đó là "cần xem lại".


**`math_spec`**:
Đặc tả toán của một bài: công thức hàm, miền của tham số, điều kiện loại trừ và các bước giải được dùng, mỗi thành phần là một mệnh đề toán.
_Tránh_: "lời giải" (là văn xuôi, không nằm trong `math_spec`).

**Mệnh đề toán**:
Một khẳng định toán đơn lẻ trong `math_spec`, mang trạng thái kiểm chứng riêng.

**Cổng toán**:
Điểm kiểm tra bắt buộc: chỉ khi mọi mệnh đề toán bắt buộc là `verified` hoặc `teacher_approved` thì `math_spec` mới chuyển sang vai trò kế tiếp.

**`verified`**:
Mệnh đề đã được máy chứng minh, đúng trong phạm vi công bố của phép kiểm. Không lan sang lời giải văn xuôi, slide hay cả khối nội dung.

**`unverified`**:
Mệnh đề chưa được máy chứng minh. Không tự tạo lại; chuyển giáo viên duyệt, sửa hoặc từ chối.

**`failed`**:
Mệnh đề mà phép kiểm xác định đã chỉ ra là sai.

**`teacher_approved`**:
Mệnh đề `unverified` được giáo viên duyệt, kèm người duyệt, thời điểm và hash nội dung. Không thay thế kiểm chứng máy với nhãn toán động chính xác trong demo.

**Phạm vi công bố**:
Giới hạn mà một phép kiểm tuyên bố là đã chứng minh được (loại biểu thức, miền biến, phiên bản phép kiểm). `verified` chỉ có nghĩa trong phạm vi này.

**Cần xem lại (stale)**:
Dấu hiệu rằng nội dung hiển thị phụ thuộc vào mệnh đề toán đã đổi hash hoặc không còn áp dụng tại giá trị tham số mới.
