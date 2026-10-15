# Hướng dẫn Đóng góp (Contributing Guidelines)

Cảm ơn bạn đã quan tâm và muốn đóng góp cho dự án **LessonAI-5512**! Chúng tôi hoan nghênh mọi đóng góp từ sửa lỗi nhỏ, bổ sung tài liệu đến phát triển các tính năng mới.

---

## 🛠️ Quy trình Đóng góp

1. **Fork Kho lưu trữ:**
   Nhấn nút **Fork** ở góc trên bên phải trang GitHub của dự án để tạo bản sao trên tài khoản cá nhân của bạn.

2. **Clone về máy cá nhân:**
   ```bash
   git clone https://github.com/NguyenNhan18/Lesson-Plan-Generator.git
   cd Lesson-Plan-Generator
   ```

3. **Tạo nhánh tính năng mới (Branch):**
   Đặt tên nhánh rõ ràng phản ánh nội dung thay đổi:
   ```bash
   git checkout -b feature/ten-tinh-nang-moi
   # hoặc: git checkout -b fix/ten-loi-can-sua
   ```

4. **Thực hiện thay đổi & Quy chuẩn Commit:**
   Tuân thủ định dạng [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat(...)`: Thêm tính năng mới
   - `fix(...)`: Sửa lỗi
   - `docs(...)`: Cập nhật tài liệu
   - `refactor(...)`: Tái cấu trúc mã nguồn
   - `test(...)`: Bổ sung hoặc chỉnh sửa bộ kiểm thử

5. **Chạy kiểm thử trước khi commit:**
   Đảm bảo toàn bộ bộ kiểm thử tự động của backend vượt qua mà không có lỗi:
   ```bash
   cd app/backend
   source venv/bin/activate
   pytest
   ```

6. **Tạo Pull Request (PR):**
   - Đẩy nhánh của bạn lên GitHub: `git push origin feature/ten-tinh-nang-moi`
   - Mở Pull Request từ nhánh của bạn vào nhánh `main` của kho lưu trữ gốc.
   - Mô tả chi tiết vấn đề được giải quyết và các bước kiểm thử đã thực hiện.

---

## 💡 Đề xuất & Báo cáo Lỗi (Issues)

Nếu bạn phát hiện lỗi hoặc có ý tưởng cải tiến:
- Kiểm tra danh sách [GitHub Issues](https://github.com/NguyenNhan18/Lesson-Plan-Generator/issues) xem vấn đề đã được đề cập chưa.
- Mở một Issue mới với tiêu đề súc tích, các bước tái hiện lỗi (nếu có) và hành vi mong đợi.
