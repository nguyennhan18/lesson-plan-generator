# Bộ hồ sơ khởi động dự án LessonAI-5512

Bộ hồ sơ này chuẩn bị nền tảng cho dự án **Hệ thống tự động soạn Giáo án theo Công văn 5512 và Slide bài giảng Toán học**. Tài liệu được viết theo hướng có thể dùng làm baseline cho phân tích, thiết kế, triển khai PoC và viết báo cáo học thuật. Các chỉ tiêu ghi “mục tiêu” hoặc “TBD” không được coi là kết quả đã đạt.

## Cấu trúc bàn giao

| Nhóm | Tệp | Nội dung |
|---|---|---|
| Chuẩn bị kỹ thuật | `01_ky-thuat/01-chuan-bi-ky-thuat-moi-truong.md` | Stack, LLM routing, cài đặt, CI/CD, rủi ro |
| Đặc tả yêu cầu | `02_tai-lieu-thiet-ke/02-SRS.md` | Actor, FR/NFR, quy tắc 5512, nghiệm thu |
| Kiến trúc | `02_tai-lieu-thiet-ke/03-system-architecture.md` | Luồng hệ thống, sequence, bảo mật, vận hành |
| CSDL | `02_tai-lieu-thiet-ke/04-database-design.md` | ERD, bảng, chỉ mục, migration, backup |
| API/UI | `02_tai-lieu-thiet-ke/05-api-ui-ux-spec.md` | Endpoint, schema, lỗi, wireframe, UX |
| Báo cáo | `03_bao-cao/01-de-cuong-va-chuong-1-3.md` | Đề cương, Gantt, Chương 1–3 |
| PoC | `03_bao-cao/02-poc-evaluation-report.md` | Phương pháp, KPI, bảng ghi kết quả |
| Phụ lục | `05_phu_luc/sources.txt` | Danh mục nguồn tham chiếu |

## Ma trận truy vết

| Yêu cầu | Thiết kế | Kiểm thử |
|---|---|---|
| FR-02/FR-03: sinh và kiểm tra 5512 | SRS, Orchestrator, Validator | Schema validity, 4-activity exactness |
| FR-05: hình học | Architecture, Geometry asset | Fixture, constraint check, latency |
| FR-06: DOCX | API/UI, Renderer | Openability, heading/table/image count |
| FR-07: PPTX | API/UI, Renderer | Slide count, notes, visual checklist |
| FR-08/FR-10: duyệt/audit | DB, Architecture | RBAC, state transition, audit completeness |

## Thứ tự thực hiện khuyến nghị

Đọc SRS để chốt phạm vi, sau đó khóa schema JSON và bộ fixture. Tiếp theo dựng FastAPI/database, tích hợp LLM Gateway với output có cấu trúc, xây validator 5512, rồi tích hợp MCP_Geometry và renderer. Frontend chỉ nên mở rộng sau khi API contract và golden files ổn định. Cuối cùng chạy PoC theo báo cáo đánh giá, mời giáo viên chấm độc lập và cập nhật các trường `TBD` bằng số liệu thực.

## Các quyết định cần chốt với nhóm dự án

| Quyết định | Lựa chọn cần chốt |
|---|---|
| Nhà cung cấp LLM | API riêng, mô hình nội bộ hoặc endpoint tương thích OpenAI |
| Phạm vi lớp | THCS, THPT hoặc cả hai trong PoC |
| Kho tệp | S3-compatible, MinIO nội bộ hoặc dịch vụ trường |
| MCP Geometry | Dịch vụ Python riêng, subprocess sandbox hoặc server nội bộ |
| Template | Mẫu DOCX/PPTX của trường và quy tắc font/logo |
| Dữ liệu đánh giá | 30 đề chuẩn hóa và danh sách giáo viên chấm |
| Bảo mật | SSO/RBAC, retention, vị trí lưu dữ liệu và consent LLM |

## Ghi chú nguồn

Cấu trúc khung kế hoạch bài dạy cần được đối chiếu bản Công văn 5512 và Phụ lục IV do đơn vị chủ quản cung cấp [1]. MCP được tham chiếu theo đặc tả 2025-06-18 [2]. FastAPI, python-pptx và OpenAPI được tham chiếu từ tài liệu chính thức [3] [4] [5].

[1]: https://boiduonghanoi.edu.vn/mod/folder/view.php?id=175 "Kho Công văn 5512 và phụ lục"  
[2]: https://modelcontextprotocol.io/specification/2025-06-18 "MCP Specification"  
[3]: https://fastapi.tiangolo.com/ "FastAPI Documentation"  
[4]: https://python-pptx.readthedocs.io/ "python-pptx Documentation"  
[5]: https://spec.openapis.org/oas/latest.html "OpenAPI Specification"
