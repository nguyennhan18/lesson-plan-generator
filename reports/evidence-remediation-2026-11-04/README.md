# Bằng chứng sửa lỗi — 04/11/2026

Các log/JSON/ảnh trong thư mục là kết quả kiểm tra cục bộ của đợt thực hiện, chưa phải nghiệm thu toàn dự án. Đọc [báo cáo thực hiện](../remediation-implementation-2026-11-03.md) để hiểu số đếm, thời điểm và giới hạn.

- `backend-and-frontend.txt`, `critical.txt`: bộ đầy đủ và chốt kỹ thuật.
- `browser-e2e.txt`: 11 ca qua backend thật, API key tắt; không đo chất lượng LLM live.
- `clean-*.txt`: cài và kiểm tra bản sao sạch macOS, chưa phải hosted CI.
- `acceptance-probes*.json`: probe hành vi; probe frontend bằng Node không tính là E2E.
- `*-audit-20261103.json`: snapshot dependency audit ngày 03/11.
- `source-inventory-summary.json`: 2.741 nguồn chờ duyệt, không chứa toàn văn kho.
- `migrated-*.json`: danh sách kiểm tra cũ đã thay/bỏ theo hợp đồng mới.
- `pptx-function.png`, `pptx-geometry.png`: ảnh render LibreOffice của bản PPTX kiểm thử; không chứng nhận mọi layout.
- `request-id-followup.txt`: kiểm tra riêng sau sửa request ID ở chốt body/Origin.
- `workspace-fingerprints.json`: SHA-256 của mã/config/test tại thời điểm chụp; không gồm docs/reports hay artifact sinh tự động.

Tệp kiểm thử dùng số liệu và đề tổng hợp, không được đưa vào bài người dùng. Kết quả “đạt” phải đọc đúng phạm vi từng phép kiểm tra.
