> **Đã bị thay (2026-11-24):** spec #36 (thiết kế lại giao diện thành Bàn làm việc) thay spec #18 và chuỗi nhiều vai trò mô tả trong tài liệu này. Chỉ phần Cổng toán (#20–#24) còn được giữ, xem ADR 0008. Quyết định hiện hành nằm ở `docs/adr/0001`–`0009` và `GLOSSARY.md`.

# Quyết định thiết kế: tạo bài giảng nhiều vai trò

**Trạng thái:** D1–D13 đã được chủ dự án xác nhận là phạm vi demo đầu ngày 2026-11-22; đây là quyết định thiết kế, chưa phải tính năng đã triển khai. Các điểm còn mở bên dưới chưa được chốt.  
**Phạm vi demo đã nêu:** một bài Toán 12 có đồ thị thay đổi theo tham số, trình chiếu tương tác trong ứng dụng.  
**Ngày ghi:** 2026-11-21.

## Quyết định đã chốt

### D1. Cổng kiểm tra `math_spec`

- Mỗi mệnh đề bắt buộc trong `math_spec` có trạng thái riêng: `verified`, `unverified` hoặc `failed`. Các mục tối thiểu gồm công thức hàm, miền của tham số, từng điều kiện loại trừ và từng bước giải được dùng trong bài.
- Chỉ khi mọi mục bắt buộc đều `verified`, `math_spec` mới tự động chuyển sang vai trò Thiết kế trực quan.
- Với `failed`, vai trò Chuyên gia toán được tạo lại đúng phần lỗi, tối đa hai vòng. Nếu vẫn `failed`, dừng và báo giáo viên.
- Với `unverified`, không tự tạo lại; chuyển thẳng `math_spec` cho giáo viên. Giáo viên có thể duyệt, sửa hoặc từ chối. Mục được duyệt mang trạng thái riêng `teacher_approved`, kèm tên người duyệt, thời điểm và hash nội dung.
- Vai trò Thiết kế trực quan chỉ nhận mục `verified` hoặc `teacher_approved`. Không dựng thanh kéo khi miền tham số chưa có một trong hai trạng thái này.
- Đo tỷ lệ `math_spec` phải dừng ở cổng toán để xác định chỗ cần mở rộng bộ kiểm tra.

### D2. Ý nghĩa và hiệu lực của `verified`

- `verified` chỉ áp dụng cho từng mệnh đề, đúng trong phạm vi được phép kiểm công bố; không lan sang lời giải văn xuôi, slide hoặc cả khối nội dung.
- Bản ghi kiểm chứng gồm mệnh đề và hash của nó, tên và phiên bản phép kiểm, phạm vi công bố, và phương pháp kiểm chứng (ký hiệu hay phương pháp khác).
- Parse thành công hoặc thử một số giá trị mẫu không đủ để gắn `verified`. Kết quả mẫu là bằng chứng bổ trợ cho `unverified` và được hiển thị khi giáo viên duyệt.
- Khi nội dung mục đổi hash hoặc phiên bản phép kiểm thay đổi, kết quả kiểm chứng cũ hết hiệu lực và phải chạy lại. `teacher_approved` cũng gắn với hash; nội dung đổi thì giáo viên phải duyệt lại.
- Tính phù hợp của họ hàm và ý đồ tham số với mục tiêu bài học được giáo viên xác nhận ở điểm duyệt dàn ý; xem D4. Công thức cụ thể vẫn phải qua cổng toán.
- Đặc tả triển khai phải có bảng `mục bắt buộc → phép kiểm → phạm vi công bố`. Mỗi ô chưa có phép kiểm cần một ticket mở rộng hoặc quy tắc chuyển cho giáo viên duyệt.

### D3. Đổi công thức trong lúc trình chiếu

- Giáo viên có thể nhập công thức mới trong lúc dạy. Ứng dụng tính và kiểm tra trong vùng xem trước của giáo viên; kết quả mới chỉ xuất hiện trên màn chiếu sau khi giáo viên xác nhận.
- Việc kéo tham số trong miền đã duyệt cập nhật trực quan ngay. Đổi công thức tạo phiên bản `math_spec` mới; trạng thái kiểm chứng và phê duyệt gắn với hash cũ hết hiệu lực. Lời giải, chú thích và hình phụ thuộc công thức cũ phải được đánh dấu cần kiểm tra lại.
- Khi một phép tính không được hỗ trợ, ứng dụng báo rõ, không tự tạo nghiệm hoặc số liệu thay thế.

### D4. Ý đồ toán được duyệt ở dàn ý

- Giáo viên duyệt họ hàm, tên và vai trò của tham số, cùng hiện tượng muốn học sinh quan sát. Vai trò Chuyên gia toán đề xuất công thức cụ thể sau điểm duyệt này.
- Nếu vai trò Chuyên gia toán đổi sang họ hàm hoặc ý đồ khác, dàn ý phải được duyệt lại.
- Quyết định này đòi hỏi biểu diễn ý đồ toán rõ ràng tại điểm duyệt. `math_focus` hiện chỉ là chuỗi tùy chọn và giao diện chưa có ô sửa chuyên biệt; thiết kế schema/UI cụ thể còn chờ đặc tả.

### D5. Phạm vi bộ tính toán dùng chung

- Hệ thống hướng tới nhận nhiều công thức trong ngôn ngữ biểu thức được hỗ trợ và thử trực quan hóa bằng bộ phân tích, tính toán dùng chung; không viết một hàm riêng cho từng bài giảng.
- Chỉ kết quả có phép kiểm đúng phạm vi mới được trình bày là chính xác và `verified`. Nghiệm số hoặc giá trị gần đúng phải mang nhãn xấp xỉ và không được tự nâng lên `verified`.
- Nếu một phép giải hoặc dựng hình vượt phạm vi hỗ trợ, hệ thống báo rõ `unverified`/chưa hỗ trợ theo từng phép tính, không tạo kết quả thay thế. Khả năng nhập và vẽ không đồng nghĩa với khả năng giải chính xác mọi phương trình hoặc chứng minh mọi nhận định.
- Một bài Toán 12 có tham số vẫn là phạm vi kiểm chứng demo đầu; kiến trúc phải cho phép mở rộng ngôn ngữ biểu thức và các phép tính theo khả năng công bố.

### D6. Phản hồi khi kéo tham số

- Khi giáo viên kéo tham số trong miền đã duyệt, bộ tính toán cập nhật đồ thị và các giá trị thuộc khả năng đã công bố; thao tác này không gọi LLM.
- Mệnh đề hoặc lời giải không còn áp dụng tại giá trị tham số mới phải được đánh dấu cần xem lại. AI chỉ viết lại lời giải hoặc chú thích khi giáo viên yêu cầu riêng.
- Cần đo riêng thời gian tạo bài và độ trễ cập nhật trực quan; chưa có số đo hay ngưỡng được chốt cho luồng mới.

### D7. Phụ thuộc từ nội dung hiển thị đến `math_spec`

- Mỗi công thức, bước giải, nhãn đồ thị và mệnh đề toán hiển thị tham chiếu mục tương ứng trong `math_spec` bằng ID và hash.
- Khi công thức hoặc giá trị tham số thay đổi, chỉ các mục phụ thuộc cần được đánh dấu xem lại. Nếu không xác định được quan hệ phụ thuộc, đánh dấu toàn slide để tránh giữ nội dung có thể đã sai.
- Cách biểu diễn điều kiện áp dụng theo giá trị tham số và cách làm mới các mục phụ thuộc sẽ được chốt trong hợp đồng chi tiết.

### D8. Phiên bản bàn giao giữa các vai trò

- Mỗi vai trò tạo một kết quả bất biến, có `schema_version`, ID/phiên bản kết quả, vai trò tạo, hash của dữ liệu đầu vào và hash nội dung. Kết quả do LLM tạo cũng phải giữ thông tin model và phiên bản prompt để truy vết.
- Sửa đổi tạo phiên bản mới; không ghi đè kết quả cũ. Bộ điều phối từ chối kết quả tham chiếu hash đầu vào đã cũ và làm lại các kết quả phụ thuộc theo hợp đồng.
- Cách lưu trữ, định dạng chính xác của vỏ metadata và thời hạn giữ lịch sử phiên bản còn chờ đặc tả.

### D9. Quyền sửa của vai trò Phản biện

- Phản biện trả danh sách lỗi gồm kết quả bị ảnh hưởng, đường dẫn đến mục lỗi, mức độ, lý do và vai trò chịu trách nhiệm; Phản biện không trực tiếp sửa kết quả của vai trò khác.
- Bộ điều phối giao lỗi về vai trò sở hữu. Vai trò đó tạo phiên bản sửa mới; bản cũ được giữ để đối chiếu. Các kết quả phụ thuộc phải được kiểm tra lại theo hash mới.
- Lỗi có phép kiểm xác định trả `failed` được giao vai trò sở hữu sửa. Nghi ngờ toán mà máy chưa chứng minh được trở thành `unverified` và chuyển giáo viên, không tự tạo lại. Góp ý diễn đạt hoặc sư phạm được ghi để giáo viên duyệt. Mức độ do LLM tự gắn không đủ để tạo trạng thái `verified` hay kích hoạt vòng sửa tự động.

### D10. Giới hạn vòng sửa

- Với lỗi cấu trúc hoặc lỗi khớp dàn ý–giáo án–slide có phép kiểm xác định, vai trò sở hữu được sửa tối đa hai vòng cho mỗi kết quả, tương tự cổng toán ở D1.
- Sau hai vòng vẫn lỗi, bộ điều phối dừng và báo giáo viên. Giữ phiên bản gần nhất đã qua kiểm tra nếu có; nếu chưa có, giữ bản giáo viên đang làm. Không tự xuất kết quả lỗi.

### D11. Ca demo và kết quả toán cần hiển thị

- Ca demo đầu là bài Toán 12 khảo sát sự biến thiên của `f_a(x) = x^3 - 3*a*x` với `a` trong đoạn `[-2, 2]`. Đây là ca nghiệm thu đầu tiên, không giới hạn bộ tính toán dùng chung vào họ hàm này.
- Khi đổi `a`, ứng dụng phải cập nhật đồ thị, đạo hàm, các nghiệm thực và điểm cực trị; xử lý đúng ba miền `a < 0`, `a = 0`, `a > 0`. Lời giải hoặc nhãn không còn áp dụng phải được đánh dấu xem lại.
- Các mệnh đề dự kiến dùng làm oracle cho kiểm thử: `f'_a(x) = 3*x^2 - 3*a`; với `a < 0`, hàm tăng và chỉ có nghiệm thực `x = 0`, không có cực trị; với `a = 0`, `x = 0` là điểm dừng nhưng không phải cực trị; với `a > 0`, nghiệm thực là `0` và `±sqrt(3*a)`, cực đại tại `(-sqrt(a), 2*a*sqrt(a))` và cực tiểu tại `(sqrt(a), -2*a*sqrt(a))`. Đây là mục tiêu cần kiểm chứng độc lập, chưa phải kết quả chạy thử hay phê duyệt chuyên môn.

### D12. Cổng kiểm chứng cho nhãn toán động trong demo

- Các nhãn chính xác về đạo hàm, nghiệm và cực trị của ca D11 phải được máy kiểm chứng trên cả ba miền `a < 0`, `a = 0`, `a > 0` trước khi demo hiển thị như kết quả chính xác. Thử vài giá trị mẫu không thay thế phép kiểm này.
- Mỗi mệnh đề lưu phép kiểm và phạm vi công bố theo D2. Nếu chưa chứng minh được tính đầy đủ hoặc điều kiện áp dụng, nhãn tương ứng vẫn là `unverified` và không được trình bày như kết quả chính xác tự động. `teacher_approved` không thay thế yêu cầu kiểm chứng máy của các nhãn động chính xác trong ca demo này.
- Giáo viên kiểm duyệt diễn đạt và ý đồ sư phạm của phần lời giải. Đây là cổng khác với phép kiểm toán cho nhãn động.

### D13. Chọn model cho các vai trò trong demo

- Mọi vai trò AI của demo đầu dùng cùng một model/provider được chọn qua LLM Gateway hiện có. Các vai trò vẫn có prompt, hợp đồng kết quả và kết quả bàn giao riêng.
- Ghi model/provider thực tế, phiên bản prompt và hash đầu vào cho từng lần gọi vai trò. Cấu hình model riêng theo vai trò được để lại cho giai đoạn sau.

## Khả năng mã nguồn hiện tại cần tính đến

| Nội dung | Hiện có | Khoảng trống cho demo |
|---|---|---|
| Đẳng thức | `math_worker._verify` kiểm đẳng thức số, đồng nhất thức đa thức bậc tối đa 8 và một số đồng nhất thức phân thức một biến có miền khớp | Chưa xác minh mọi điều kiện tham số, suy luận và lời giải văn xuôi |
| Đồ thị | `math_worker._plot` nhận biểu thức theo `x`, tính miền và các đoạn đồ thị; có chế độ hàm gốc hoặc đạo hàm | Chưa nhận tham số động, thanh kéo, hoặc tự tính mọi nghiệm/cực trị |
| Hình học | `geometry_scene` hỗ trợ lập phương và hai loại chóp đáy vuông, với dữ kiện cạnh đáy/chiều cao | Chưa có hợp đồng cho hình học tổng quát hoặc thay đổi loại hình tự do |

Đây là mô tả khả năng hiện tại, không phải kết quả kiểm thử trong phiên thiết kế này.

## Điểm còn mở

Đặc tả `/to-spec` phải giữ các mục này trong phần **Điểm còn mở**, với cột người quyết định và hạn chót. Ngày 2026-11-22 chủ dự án xác nhận: người quyết định cho O3–O7 là "Chủ dự án"; hạn chót là "trước khi bàn giao đặc tả `/to-spec`", chưa có ngày lịch cụ thể. D1–D13 được xác nhận không có nghĩa các mục chưa chốt đã được giải quyết.

| Mã | Quyết định còn mở cần ghi trong đặc tả | Người quyết định | Hạn chót |
|---|---|---|---|
| O2 | **Đã chốt** (2026-11-22): hướng cho các mệnh đề tại O2.1–O2.6 và cách xử lý mục chưa có phép kiểm ở O2.7 (áp dụng D1, D2, D5, D12) | Chủ dự án | Đã chốt |
| O3 | **Đã chốt hướng** (2026-11-23): nơi lưu, hàm băm, cách trỏ lỗi, trường vỏ bàn giao, đồ thị phụ thuộc, chính sách tạo lại và giữ lịch sử, xem O3.1–O3.8. Định dạng JSON chi tiết thuộc đặc tả | Chủ dự án | Trước khi bàn giao đặc tả `/to-spec` |
| O4 | Đã chốt hướng cho demo đầu, xem O4.1. Còn mở: cấu hình model riêng theo vai trò và cách đo chất lượng/chi phí sau demo | Chủ dự án | Trước khi bàn giao đặc tả `/to-spec` (phần sau demo: chưa chốt) |
| O5 | Đã chốt hướng giao diện, xem O5.1. Biểu diễn điều kiện áp dụng đã chốt ở O3.7. Còn mở: thao tác chi tiết của giao diện (thuộc đặc tả) | Chủ dự án | Trước khi bàn giao đặc tả `/to-spec` |
| O6 | Đã chốt: hoãn sang giai đoạn sau, xem O6.1. Quy tắc kiểm tra khi đổi loại hình hoặc tham số chưa được thiết kế | Chủ dự án | Giai đoạn sau demo (chưa chốt) |
| O7 | Đã chốt quy trình, xem O7.1. Còn mở: giá trị ngưỡng, chờ phép đo nền | Chủ dự án | Sau khi có phép đo nền; ngưỡng phải chốt trước khi bàn giao đặc tả `/to-spec` |

### O2.1 — Nhãn đạo hàm (đã chốt hướng, chưa triển khai)

- Với ca D11, mở rộng phép kiểm để nhận biểu thức hàm đã phân tích an toàn, lấy đạo hàm ký hiệu theo `x` trong worker, rồi chứng minh nhãn đạo hàm đề xuất bằng phép so sánh đồng nhất thức đa thức; không coi việc vẽ hoặc lấy mẫu là chứng minh.
- Phạm vi dự kiến công bố cho phép kiểm này là các biểu thức đa thức trong giới hạn parser/worker và bậc tối đa 8, với `x`, `a` là biến thực. Riêng `f_a(x)=x^3-3*a*x`, chứng minh `f'_a(x)=3*x^2-3*a` trên mọi `x`, `a` thực bao phủ cả ba miền `a<0`, `a=0`, `a>0` trong `[-2,2]`. Phạm vi và phiên bản của phép kiểm triển khai thực tế phải được ghi kèm mệnh đề/hash theo D2; không tự nâng các bước giải hoặc nhãn khác lên `verified`.
- Nếu phép kiểm không chứng minh được mệnh đề trong phạm vi công bố, trả `unverified`; giáo viên có thể xem theo D1, nhưng `teacher_approved` không thay thế kiểm chứng máy để hiển thị nhãn đạo hàm động là kết quả chính xác trong demo theo D12.
- Bằng chứng chọn hướng: `_verify` hiện chứng minh được một số đồng nhất thức đa thức nhưng chưa nhận quan hệ “là đạo hàm của”; `_plot` có lấy đạo hàm để vẽ nhưng chỉ phân tích biểu thức theo `x` và lấy mẫu hữu hạn. Mốc #3 đạt 15/15 hành vi kỹ thuật, song năm ca `valid` vẫn có cảnh báo, gồm mệnh đề chưa xác minh; đó không phải bằng chứng nhãn đạo hàm đã được chứng minh.

### O2.2 — Nghiệm thực và tính đầy đủ (đã chốt hướng, chưa triển khai)

- Mở rộng phép kiểm nghiệm có thể tái sử dụng cho đa thức theo `x` với một tham số thực khi phân tích được thành các nhân tử bậc thấp. Phép kiểm phải chứng minh cả từng nghiệm ứng viên lẫn tính đầy đủ của tập nghiệm trên từng miền tham số; không viết kết quả cố định riêng cho bài D11 và không suy từ vài mẫu số.
- Với `f_a(x)=x^3-3*a*x`, chứng minh đồng nhất thức `f_a(x)=x*(x^2-3*a)` và dùng điều kiện dấu để chứng minh: `a<0` chỉ có nghiệm thực `x=0`; `a=0` chỉ có nghiệm thực `x=0`; `a>0` có đúng các nghiệm thực `x=0` và `x=±sqrt(3*a)`. Phạm vi công bố là từng miền đã được chứng minh trong `a∈[-2,2]`, không khẳng định giải được mọi đa thức hay tự mở rộng sang cực trị.
- Chỉ gắn `verified` cho mệnh đề nghiệm khi có bằng chứng ký hiệu về cả giá trị và tính đầy đủ, kèm hash mệnh đề, tên/phiên bản/phạm vi phép kiểm theo D2. Nếu không chứng minh được một miền, mệnh đề tương ứng là `unverified`; giáo viên xem theo D1 nhưng không thể thay bằng `teacher_approved` để hiển thị nhãn nghiệm động chính xác trong demo theo D12.
- Bằng chứng chọn hướng: `_verify` hiện có thể kiểm tra đồng nhất thức đa thức nhưng không có phép giải phương trình, phân tích dấu theo miền tham số hoặc chứng minh tính đầy đủ của nghiệm. Mốc #3 không kiểm tra nghiệm của hàm có tham số; 15/15 ca kỹ thuật không xác nhận mệnh đề này.

### O2.3 — Cực trị và tính đầy đủ (đã chốt hướng, chưa triển khai)

- Mở rộng phép kiểm có thể tái sử dụng cho đa thức theo `x` với một tham số thực thuộc phạm vi chứng minh được: dùng đạo hàm đã kiểm chứng theo O2.1, tìm đầy đủ điểm dừng, rồi chứng minh dấu đạo hàm trên từng miền tham số để phân loại cực trị. Không coi đồ thị lấy mẫu hoặc chỉ thế điểm vào công thức là bằng chứng về tính đầy đủ.
- Với `f'_a(x)=3*(x^2-a)`, chứng minh: `a<0` thì đạo hàm dương với mọi `x` thực, không có cực trị; `a=0` có điểm dừng `x=0` nhưng dấu đạo hàm không đổi, không có cực trị; `a>0` có đúng hai điểm dừng `x=±sqrt(a)` với dấu đạo hàm lần lượt `+,−,+`, nên cực đại tại `(-sqrt(a),2*a*sqrt(a))` và cực tiểu tại `(sqrt(a),-2*a*sqrt(a))`. Kiểm chứng ký hiệu cả tọa độ lẫn tính đầy đủ; phạm vi công bố chỉ gồm từng miền đã chứng minh trong `a∈[-2,2]`.
- Từng mệnh đề điểm dừng, dấu, loại cực trị, tọa độ và tính đầy đủ có trạng thái/bằng chứng riêng theo D2. Nếu một phần chưa chứng minh được, phần đó là `unverified`; giáo viên được xem theo D1, nhưng không thay thế kiểm chứng máy để hiển thị nhãn cực trị động chính xác theo D12.
- Bằng chứng chọn hướng: `_verify` hiện chỉ kiểm một số đẳng thức, `_plot` tính/lấy mẫu đạo hàm theo `x` nhưng không chứng minh bất đẳng thức, đổi dấu hay danh sách cực trị đầy đủ. Mốc #3 vẫn có cảnh báo ở các ca `valid` và không chứa phép nghiệm thu cực trị theo tham số.

### O2.4 — Miền tương tác của `a` (đã chốt hướng, chưa triển khai)

- `a∈[-2,2]` là khoảng tương tác được chọn cho ca demo D11, không phải miền xác định tối đa của hàm: đa thức `f_a(x)=x^3-3*a*x` xác định với mọi `x`, `a` thực. Việc chọn khoảng này và ý đồ sư phạm thuộc điểm duyệt dàn ý D4.
- Mở rộng phép kiểm có thể tái sử dụng để chứng minh mệnh đề riêng rằng mọi giá trị `a` trong khoảng tương tác đã khai báo đều an toàn cho biểu thức được hỗ trợ, với mọi `x` thực thuộc phạm vi công bố; đồng thời bộ tính toán phải chặn giá trị thanh kéo nằm ngoài khoảng đã duyệt. Riêng ca D11, chứng minh an toàn trên toàn bộ `[-2,2]`, gồm ba miền `a<0`, `a=0`, `a>0`. Không suy từ việc parser đọc được biểu thức hoặc thử vài giá trị mẫu.
- Chỉ gắn `verified` cho mệnh đề an toàn của khoảng thực sự được chứng minh, kèm hash, tên/phiên bản/phạm vi/phương pháp phép kiểm theo D2; không gắn nhãn đó cho tính tối ưu của khoảng hay ý đồ sư phạm. Nếu không chứng minh được, mệnh đề là `unverified` để giáo viên xem theo D1. Theo D1, chỉ dựng thanh kéo khi miền có trạng thái `verified` hoặc `teacher_approved`; các nhãn kết quả động vẫn phải thỏa D12.
- Bằng chứng chọn hướng: `math_expression.py` phân tích biểu thức nhưng không có hợp đồng chứng minh khoảng hay lượng từ; `_domain` trong `math_worker.py` xét miền theo một biến, còn `_plot` lấy mẫu theo `x`. Mốc #3 không kiểm tra an toàn của khoảng tham số. Cần mở rộng phép kiểm, không coi khả năng hiển thị đồ thị là chứng minh.

### O2.5 — Điều kiện loại trừ (đã chốt hướng, chưa triển khai)

- Mở rộng phép kiểm để chứng minh riêng mệnh đề về danh sách điều kiện loại trừ của từng biểu thức bắt buộc trong `math_spec`, kể cả mệnh đề danh sách rỗng. Với lớp đa thức được hỗ trợ, chứng minh bằng cấu trúc biểu thức rằng không có điểm loại trừ trên miền biến thực đã công bố; riêng `f_a(x)=x^3-3*a*x` không loại trừ `x` hoặc `a` thực nào. Không lấy kết quả parse thành công làm bằng chứng miền xác định.
- Với biểu thức có mẫu số, căn, log hoặc điều kiện phụ thuộc tham số, chỉ gắn `verified` cho từng điều kiện và cho tính đầy đủ của danh sách khi phép kiểm chứng minh được trên toàn bộ khoảng `a` đã khai báo và miền `x` được công bố. Phần chưa chứng minh được là `unverified` để giáo viên duyệt theo D1, không ngầm coi danh sách rỗng; kết quả thử mẫu chỉ là bằng chứng bổ trợ theo D2.
- Mỗi mệnh đề điều kiện loại trừ mang hash, tên/phiên bản/phạm vi/phương pháp phép kiểm riêng theo D2. Phạm vi công bố của phép kiểm đa thức không tự mở rộng sang phân thức hoặc hàm khác. Quyết định này là hướng mở rộng phép kiểm cho O2, chưa khẳng định worker hiện đã hỗ trợ.
- Bằng chứng chọn hướng: `_domain` trong `math_worker.py` giữ các lỗ của biểu thức gốc và tìm nghiệm mẫu số theo một biến; `_verify` chỉ so sánh miền của hai biểu thức hữu tỉ khi có đúng một biến. Chưa có phép chứng minh danh sách loại trừ đầy đủ theo cặp `(x,a)` hay cả khoảng tham số.

### O2.6 — Từng bước giải dùng trong bài (đã chốt hướng, chưa triển khai)

- Tách lời giải thành các mệnh đề toán có cấu trúc để kiểm tra từng bước trong phạm vi các phép kiểm đã chốt ở O2.1–O2.5. Mỗi bước có trạng thái và bằng chứng riêng theo D1–D2; một bước được chứng minh không tự làm các bước khác hoặc lời giải văn xuôi thành `verified`.
- Mở rộng phép kiểm có thể tái sử dụng cho các phép biến đổi đại số, đạo hàm, nghiệm, xét dấu và phân loại cực trị thuộc phạm vi đã công bố của ca D11. Chỉ gắn `verified` nếu chứng minh được mệnh đề cụ thể của bước đó trên toàn bộ miền áp dụng. Diễn giải bằng lời, ý đồ sư phạm hoặc bước ngoài phạm vi phép kiểm là `unverified` để giáo viên duyệt; riêng nhãn toán động chính xác vẫn phải qua cổng máy của D12.
- Quyết định này xác định đơn vị kiểm chứng và cách chuyển giáo viên, chưa chốt định dạng JSON hoặc quan hệ phụ thuộc chi tiết giữa các bước; những phần đó thuộc O3. `_verify` hiện kiểm được một số đẳng thức nhưng chưa xác minh được chuỗi suy luận hoặc lời giải văn xuôi.

### O2.7 — Mục chưa có phép kiểm (đối chiếu quyết định đã có)

- Không cần quyết định mới: theo D1 và D2, mục bắt buộc chưa có phép kiểm là `unverified`, không tự tạo lại, chuyển giáo viên duyệt/sửa/từ chối và ghi rõ ô thiếu phép kiểm trong bảng `mục bắt buộc → phép kiểm → phạm vi công bố`. Kết quả thử mẫu chỉ là bằng chứng bổ trợ. Theo D5, phép tính vượt khả năng phải báo chưa hỗ trợ; theo D12, giáo viên duyệt không thay được chứng minh máy cho nhãn đạo hàm, nghiệm hoặc cực trị động chính xác của demo.
- Khi triển khai, từng ô thiếu phải có ticket mở rộng hoặc quy tắc chuyển giáo viên cụ thể theo D2. Đây là áp dụng D1/D2/D5/D12, không coi việc thiếu checker là `failed` và không phát sinh vòng tạo lại tự động.

### O3.1 — Nơi lưu kết quả vai trò và lịch sử (đã chốt hướng, chưa triển khai)

- Lưu cùng bản ghi dự án trong IndexedDB bằng một trường tùy chọn mới ở mức cao nhất (tên dự kiến `role_runs`). Không tăng `schema_version`; việc tăng lên 3 là quyết định riêng của chủ dự án theo `AGENTS.md`.
- Kiểm tra mã (chỉ đọc, chưa chạy): `saveProject` lưu nguyên bản ghi bằng `structuredClone`, nên trường lạ không bị xóa ở lớp lưu trữ. Tuy nhiên `App.jsx` dựng bản lưu từ `projectMeta.current` (bản ghi lúc nạp) cộng các trường đã biết. Trường mới chỉ được lưu đúng khi thay đổi lúc chạy được đưa vào `currentProject` và vào danh sách phụ thuộc của effect lưu. Đặc tả phải nêu việc này và có test lưu rồi nạp lại.
- Server không lưu kết quả vai trò, vì trạng thái phiên server nằm trong bộ nhớ và mất khi khởi động lại.

### O3.2 — Hàm băm dùng chung (đã chốt hướng, chưa triển khai)

- Mọi hash trong D2, D7, D8 dùng một hàm: JSON chuẩn hóa rồi `sha256`, theo cách `canonical()` trong `visual_requirements.py` đang làm. Mỗi hash kèm `hash_version` để đổi cách băm sau này mà không nhầm với hash cũ.

### O3.3 — Cách trỏ tới mục lỗi (đã chốt hướng, chưa triển khai)

- Danh sách lỗi của Phản biện (D9) trỏ bằng ID ổn định của mục cộng hash, nhất quán với D7. Với văn xuôi chưa có ID, dùng ID slide cộng tên trường. Không dùng đường dẫn theo vị trí.

### O3.4 — Trường tối thiểu của vỏ bàn giao (đã chốt hướng, chưa triển khai)

- Ngoài các trường ở D8, D13 và O4.1, thêm `supersedes` (ID phiên bản bị thay thế, rỗng với bản đầu) và `created_at`. Không thêm trường khác trong demo trừ khi lúc đặc tả phát hiện thiếu.

### O3.5 — Đồ thị phụ thuộc giữa các vai trò (đã chốt hướng, chưa triển khai)

- Tuần tự: dàn ý đã duyệt → `math_spec` → `visual_spec` → giáo án → slide → Phản biện. Slide được sinh từ giáo án. Chạy song song giáo án và slide chưa nằm trong demo; xem xét sau khi có số đo nền theo O7.1.

### O3.6 — Khi nào tạo lại phần phụ thuộc (đã chốt hướng, chưa triển khai)

- Trong một lượt tạo bài: bộ điều phối tạo lại các kết quả phụ thuộc theo thứ tự đồ thị O3.5, mỗi kết quả chịu giới hạn hai vòng sửa của D10.
- Sau khi bài có sẵn (giáo viên sửa tay, hoặc đổi công thức lúc chiếu theo D3): mục phụ thuộc chỉ được đánh dấu "Cần xem lại"; chỉ tạo lại khi giáo viên yêu cầu. Kéo tham số không gọi LLM (D6).

### O3.7 — Điều kiện áp dụng theo tham số (đã chốt hướng, chưa triển khai)

- Mỗi mệnh đề toán và nhãn động khai báo điều kiện áp dụng có cấu trúc: tham số và khoảng áp dụng (ví dụ `a ∈ (-2, 0)`), do bộ tính toán đánh giá trực tiếp, không qua LLM.
- Khoảng áp dụng phải nằm trong phạm vi công bố của phép kiểm (D2). Điều kiện không biểu diễn được thì mệnh đề bị đánh dấu "Cần xem lại", không tự coi là còn áp dụng.

### O3.8 — Giữ lịch sử phiên bản (đã chốt hướng, chưa triển khai)

- Giữ đủ mọi phiên bản của lượt tạo bài hiện tại để truy vết (D8, D9). Khi giáo viên bắt đầu lượt tạo mới cho cùng bài, bỏ lịch sử lượt cũ.
- Bản ghi `teacher_approved` được giữ lại kèm hash; mệnh đề giống hệt xuất hiện lại thì không phải duyệt lại.
- `role_runs` không lưu ảnh render hay base64 (dữ liệu phái sinh). Đặc tả phải định nghĩa mốc "lượt tạo mới" và có test `QuotaExceededError`, vì `AGENTS.md` ghi lưu trữ phía trình duyệt chưa được kiểm tra trường hợp này.

### O3.9 — Biểu diễn ý đồ toán ở dàn ý (đã chốt hướng thiết kế, chưa duyệt triển khai)

- Thêm đối tượng có cấu trúc gồm họ hàm, tham số (tên, vai trò, khoảng tương tác) và hiện tượng cần quan sát. Giữ `math_focus` làm chuỗi mô tả để tương thích. Khoảng tương tác của tham số do giáo viên duyệt ở D4 và là đầu vào của O2.4.
- Thay đổi này chạm schema và `app/backend/tests/fixtures/api_contract.json`, thuộc mục **hỏi trước** của `AGENTS.md`. Đây mới là quyết định thiết kế; chủ dự án phải duyệt riêng trước khi sửa mã.

### O3.10 — Hợp đồng API đã được chủ dự án duyệt (2026-11-23, ticket #19)

- Bốn endpoint mới, không giữ trạng thái, dùng request model Pydantic: `POST /api/v1/math-spec/verify`, `POST /api/v1/math-spec/evaluate`, `POST /api/v1/math-spec/approve`, `POST /api/v1/orchestrator/run`. Không có endpoint riêng cho tạo lại phần phụ thuộc hay xác nhận "Chiếu".
- `run` chạy một giai đoạn mỗi request (toán, trực quan, giáo án, slide, phản biện), mang theo kết quả vai trò trước đó; server tự kiểm điều kiện tiên quyết, hash đầu vào, giới hạn hai vòng và cổng toán.
- Bản ghi lưu ở trình duyệt không ký HMAC, chỉ gắn hash; `verified` được server kiểm lại khi cần dùng. Lưu khóa bền để ký là quyết định riêng, chưa làm.
- Cổng toán dừng trả HTTP 200 kèm trạng thái dừng có cấu trúc. Không thêm trường vào phần chi tiết lỗi.
- Thêm `math_intent` tùy chọn vào mục dàn ý, giữ `math_focus`; `role_runs` không tăng `schema_version`.
- Phạm vi cập nhật `api_contract.json` chỉ gồm các mục trên; ngoài đó cần duyệt lại.
- Rủi ro chưa quyết định: `evaluate` chạy trong tiến trình con `spawn` nên có độ trễ khởi động mỗi lần gọi; phải đo ở ticket #34 trước khi kết luận cách cập nhật khi kéo thanh trượt. Spec #18 (Further Notes) liệt kê điều kiện duyệt hẹp hơn thực tế; ticket #19 là bản đầy đủ.

### Bảng mục bắt buộc → phép kiểm → phạm vi công bố (theo D2)

Cập nhật mỗi khi một phép kiểm được thêm. Ô chưa có phép kiểm: mệnh đề là `unverified` và chuyển giáo viên duyệt (O2.7), kèm ticket mở rộng.

| Mục bắt buộc | Phép kiểm (tên, phiên bản) | Phạm vi công bố | Trạng thái |
|---|---|---|---|
| Nhãn đạo hàm theo biến | `derivative_polynomial_identity` v1, ký hiệu | Đa thức theo biến và tối đa hai tham số thực, tổng bậc tối đa 8 (tính cả tham số); đúng với mọi giá trị thực; biểu thức không xác định (ví dụ chia cho 0) là `unverified` | Đã triển khai (#20) |
| Nghiệm thực và tính đầy đủ | `real_roots_factorized_sign` v1, ký hiệu | Đa thức theo biến và tối đa một tham số thực, tổng bậc tối đa 8, phân tích được thành các nhân tử bậc tối đa 2 theo biến trên từng miền dấu của tham số (`a < 0`, `a = 0`, `a > 0`) hoặc không tham số; ngoài phạm vi hoặc nghiệm xấp xỉ là `unverified` | Đã triển khai (#21) |
| Điểm dừng, dấu đạo hàm, cực trị | `stationary_points_factorized_sign` v1, `derivative_sign_factorized` v1, `extrema_stationary_sign` v1, ký hiệu | Đa thức theo biến và tối đa một tham số thực, tổng bậc tối đa 8, đạo hàm phân tích được thành các nhân tử bậc tối đa 2 trên từng miền dấu của tham số (`a < 0`, `a = 0`, `a > 0`) hoặc không tham số; từng mệnh đề điểm dừng, dấu, cực trị có bằng chứng riêng | Đã triển khai (#22) |
| An toàn của khoảng tham số | `parameter_interval_safety` v1, ký hiệu | Đa thức theo biến và đúng một tham số thực, tổng bậc tối đa 8, kiểm tra cấu trúc AST không có phép chia/căn/log trên toàn đoạn tham số hữu hạn `[a_min, a_max]` và mọi `x` thực | Đã triển khai (#23) |
| Điều kiện loại trừ (kể cả rỗng) | `domain_exclusion_completeness` v1, ký hiệu | Đa thức (tổng bậc tối đa 8, danh sách loại trừ rỗng chứng minh bằng cấu trúc AST) và phân thức một biến có mẫu số bậc tối đa 2 trên tập số thực; biểu thức có căn/log/mẫu phụ thuộc tham số là `unverified` | Đã triển khai (#23) |
| Từng bước giải | `structured_solution_step` v1, ký hiệu | Bước giải có cấu trúc thuộc một trong các phép kiểm đã công bố (`identity`, `derivative`, `roots`, `stationary_points`, `sign`, `extrema`, `exclusions`); lời giải văn xuôi giữ `unverified` | Đã triển khai (#24) |
| Công thức hàm và họ hàm phù hợp ý đồ | Không phải phép kiểm máy | — | Giáo viên duyệt ý đồ ở dàn ý (D4); ticket #27 |

### O4.1 — Chuyển provider khi lỗi giữa chuỗi vai trò (đã chốt hướng, chưa triển khai)

- Demo đầu giữ nguyên cơ chế chuyển provider hiện có của LLM Gateway. Không thêm quy tắc chặn chuyển provider giữa chuỗi vai trò.
- Mỗi lần gọi vai trò ghi model/provider thực tế theo D13. Khi các vai trò trong một chuỗi chạy bằng model khác nhau do gateway chuyển provider, kết quả bàn giao mang cờ "nhiều model" để truy vết.
- Chính sách riêng theo vai trò, cấu hình model theo vai trò và cách đo chất lượng/chi phí để lại sau demo, như đã ghi ở O4.

### O5.1 — Giao diện xem trước của giáo viên (đã chốt hướng, chưa triển khai)

- Dùng một vùng xem trước ngay trong cửa sổ trình chiếu hiện có, có thao tác xác nhận "Chiếu" rõ ràng trước khi công thức mới lên màn chiếu (theo D3). Cửa sổ giáo viên riêng đồng bộ với màn chiếu (kiểu presenter) thuộc giai đoạn sau.
- Nội dung cũ được đánh dấu "Cần xem lại" theo đúng mức chi tiết của D7: chỉ các mục phụ thuộc; nếu không xác định được quan hệ thì đánh dấu cả slide.
- Giữ kiến trúc hiện có: trạng thái dùng chung ở `App.jsx`, không tạo kho trạng thái mới trong `src/features/*` (theo `AGENTS.md`).

### O6.1 — Hình học (đã chốt: hoãn)

- Hình học nằm ngoài phạm vi demo đầu. Khả năng của `geometry_scene` giữ nguyên; không thêm vai trò hay cổng kiểm riêng cho hình học trong demo. Việc mở rộng loại hình và quy tắc kiểm tra khi đổi loại hình hoặc tham số thuộc giai đoạn sau, cùng quyết định P4A.1 đang chờ trong `AGENTS.md`.

### O7.1 — Quy trình đặt ngưỡng thời gian (đã chốt quy trình, chưa có giá trị)

- Chưa chốt con số. Hiện repo chỉ có số đo độ trễ truy hồi RAG (`docs/rag/rag-performance-investigation.md`), chưa có số đo thời gian tạo bài hay độ trễ khi kéo tham số.
- Đo nền trước trên ca D11: thời gian tạo bài (tách thời gian các vòng sửa theo D1/D10) và độ trễ cập nhật khi kéo tham số (theo D6). Sau đó chủ dự án chốt ngưỡng dựa trên số đo.
- Tham chiếu duy nhất hiện có là SRS ("P95 tạo bản nháp dưới 60 giây; preview dưới 5 giây"). Đây chỉ là tham chiếu, không phải ngưỡng nghiệm thu của demo, và chưa tính vòng tạo lại tối đa hai lần.

## Lưu giữ tài liệu

- Quy tắc `.gitignore:61` (`docs/*`) bỏ qua file này, `GLOSSARY.md` không bị ignore. Ngày 2026-11-23, file quyết định và `docs/adr/0001-verified-chi-do-may-chung-minh.md` được đưa vào Git bằng `git add -f` theo tên tệp, trên nhánh `feat/multi-role-orchestrator`. `.gitignore` không bị sửa.
- Mọi tệp mới dưới `docs/` tiếp tục bị ignore: khi thêm ADR hoặc tài liệu mới phải `git add -f` theo tên tệp. `PROGRESS.md` đã được theo dõi nên không cần force-add. Nếu muốn theo dõi cả thư mục `docs/` về lâu dài, cần chốt phạm vi sửa `.gitignore` trước (mục "hỏi trước" của `AGENTS.md`).

## Tham chiếu mã nguồn

- `app/backend/src/lessonai/services/math_worker.py`: `_verify`, `_plot` và `_domain`.
- `app/backend/src/lessonai/services/math_expression.py`: parser có giới hạn; parse không phải chứng minh.
- `app/backend/src/lessonai/schemas/schemas.py`: `OutlineSlideItem.math_focus` hiện là chuỗi tùy chọn.
- `app/frontend/src/features/generation/OutlineWorkspace.jsx`: điểm duyệt dàn ý hiện tại.
- `app/frontend/src/shared/math/FunctionPlotter.jsx`: sửa công thức và xác nhận dữ kiện đồ thị hiện tại.
- `app/backend/src/lessonai/services/geometry_scene.py`: các loại hình đang hỗ trợ.
