# Phạm vi benchmark và triage đầu tiên

15 ca trong `data/fixtures/math12_benchmark_suite.json` khai báo 9 lesson_id:

| lesson_id | Chủ đề | Ca benchmark |
|---|---|---|
| M12-C1-B1 | Đơn điệu, cực trị; thay đổi giả thiết | VALID-01, FAULTY-01, CONTRA-02 |
| M12-C1-B2 | GTLN/GTNN, điều kiện căn | UNDER-02 |
| M12-C1-B3 | Tiệm cận, bảo toàn miền xác định | VALID-02, UNDER-01 |
| M12-C2-B1 | Vectơ không gian, hình lập phương | VALID-03, CONTRA-01 |
| M12-C3-B1 | Khoảng biến thiên, khoảng tứ phân vị | FAULTY-03 |
| M12-C4-B1 | Nguyên hàm, đồng nhất thức | FAULTY-02 |
| M12-C4-B2 | Biểu thức vượt giới hạn, đầu vào độc hại | OOS-02 |
| M12-CD-B1 | Khối chóp: đều, chân đường cao, thiếu giả thiết | VALID-04, VALID-05, UNDER-03 |
| M12-CD-B2 | Khối ngoài phạm vi hỗ trợ | OOS-01 |

Tiền tố đầy đủ của mỗi case_id là `BM-`.

Số ứng viên thô theo thứ tự bảng: câu hỏi 261, 32, 47, 19, 13, 5, 28, 16, 65; slide 82, 55, 51, 106, 53, 85, 86, 0, 0. Đây là số đếm theo lesson_id, chưa qua duyệt hoặc kiểm tra phù hợp nội dung.

Runner `scripts/quality/run_benchmark_suite.py` dùng slide/biểu thức/geometry nhúng trong fixture để gọi math worker và endpoint chất lượng/hình ảnh. Nó không truy hồi câu hỏi RAG theo ID. Vì vậy danh sách trên là phạm vi chủ đề khai báo, chưa phải bằng chứng các nguồn RAG đã được benchmark sử dụng. Không có danh sách question_id thực sự được truy hồi để gọi là lô đã được kiểm chứng.

Lô đề xuất phải tách các ca OOS (kiểm tra từ chối) khỏi nhu cầu nguồn giảng dạy, rồi gắn từng nguồn cụ thể với tình huống kiểm thử truy hồi. Bộ triage hiện mới là prototype kiểm tra phân thức; auto_pass vẫn tắt. Chưa có tập hiệu chuẩn 30–50 ca hay số liệu độ nhạy.
