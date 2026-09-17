import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}" />')
    tcPr.append(shd)

def create_detailed_report():
    doc = Document()
    
    # Page setup - Standard A4 Margins (Top/Bottom 2cm, Left 3cm, Right 1.5cm)
    for section in doc.sections:
        section.top_margin = Inches(0.79)
        section.bottom_margin = Inches(0.79)
        section.left_margin = Inches(1.18)
        section.right_margin = Inches(0.59)
        
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(12)
    font.color.rgb = RGBColor(0x22, 0x22, 0x22)
    
    # -------------------------------------------------------------
    # DOCUMENT TITLE & METADATA
    # -------------------------------------------------------------
    p_main = doc.add_paragraph()
    p_main.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_main = p_main.add_run("BÁO CÁO THẨM ĐỊNH KỸ THUẬT VÀ TIẾN ĐỘ DỰ ÁN (GIAI ĐOẠN 1)\n")
    r_main.font.bold = True
    r_main.font.size = Pt(16)
    r_main.font.color.rgb = RGBColor(0x8B, 0x00, 0x00) # Dark Red for serious tone
    
    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_sub = p_sub.add_run("Dự án: Hệ thống AI Sinh Giáo Án Chuẩn Công văn 5512 & Slide Bài Giảng Tự Động (LessonAI-5512)\n")
    r_sub.font.italic = True
    r_sub.font.size = Pt(12)
    
    p_role = doc.add_paragraph()
    p_role.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_role = p_role.add_run("Góc nhìn đánh giá: Technical Lead / Senior QC Auditor / Khách hàng thẩm định dự án\n")
    r_role.font.bold = True
    r_role.font.size = Pt(11)
    r_role.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
    
    p_div = doc.add_paragraph()
    p_div.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_div.add_run("―" * 55)
    
    # -------------------------------------------------------------
    # EXECUTIVE SUMMARY / LỜI MỞ ĐẦU THẨM ĐỊNH
    # -------------------------------------------------------------
    h_exec = doc.add_paragraph()
    r_he = h_exec.add_run("📌 LỜI MỞ ĐẦU: TỔNG QUAN ĐÁNH GIÁ THỰC TRẠNG (EXECUTIVE AUDIT SUMMARY)")
    r_he.font.bold = True
    r_he.font.size = Pt(13)
    r_he.font.color.rgb = RGBColor(0x00, 0x33, 0x66)
    
    p_ex = doc.add_paragraph()
    p_ex.paragraph_format.line_spacing = 1.15
    p_ex.add_run(
        "Báo cáo này được lập dưới góc nhìn nghiêm túc, thẳng thắn của một "
    )
    r_role_b = p_ex.add_run("Tech Lead & QC trưởng")
    r_role_b.font.bold = True
    p_ex.add_run(
        " phối hợp với góc nhìn của một "
    )
    r_cli_b = p_ex.add_run("Khách hàng thẩm định")
    r_cli_b.font.bold = True
    p_ex.add_run(
        ". Báo cáo loại bỏ hoàn toàn các nhận định tâng bốc hay tô hồng thực tế, nhằm mục đích "
    )
    r_raw_b = p_ex.add_run("bóc trần 100% bản chất hiện trạng mã nguồn và kiến trúc đồ án")
    r_raw_b.font.bold = True
    r_raw_b.font.color.rgb = RGBColor(0xC0, 0x00, 0x00)
    p_ex.add_run(
        " giúp tác giả có cái nhìn chuẩn xác nhất để khắc phục ở Giai đoạn 2.\n\n"
        "TỔNG KẾT THẨM ĐỊNH: Đồ án hiện tại mới chỉ dừng lại ở mức "
    )
    r_poc_b = p_ex.add_run("Proof of Concept (POC) / Khung Backend thử nghiệm thô ('Chạy được Script/API')")
    r_poc_b.font.bold = True
    p_ex.add_run(
        ", ước tính đạt khoảng "
    )
    r_pct_b = p_ex.add_run("30% – 35% khối lượng công việc")
    r_pct_b.font.bold = True
    p_ex.add_run(
        " của một sản phẩm hoàn chỉnh. Hệ thống mới chỉ chứng minh được tính khả thi về mặt thuật toán thô (gửi Yêu cầu -> Gemini ra JSON -> Xuất file Word/PPTX thô), "
        "tuyệt đối CHƯA THỂ đưa vào sử dụng thực tế và CHƯA CÓ tính sẵn sàng thương mại (Not Production-Ready).\n"
    )
    
    # -------------------------------------------------------------
    # SECTION I: ĐÁNH GIÁ MỨC ĐỘ HOÀN THÀNH THỰC TẾ
    # -------------------------------------------------------------
    h1 = doc.add_paragraph()
    r_h1 = h1.add_run("I. ĐÁNH GIÁ MỨC ĐỘ HOÀN THÀNH THỰC TẾ CÁC THÀNH PHẦN HỆ THỐNG")
    r_h1.font.bold = True
    r_h1.font.size = Pt(13)
    r_h1.font.color.rgb = RGBColor(0x00, 0x33, 0x66)
    
    table_comp = doc.add_table(rows=8, cols=4)
    table_comp.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = table_comp.rows[0].cells
    hdr[0].text = "Thành phần Mô-đun"
    hdr[1].text = "Trạng thái Mã nguồn Thực tế"
    hdr[2].text = "Đánh giáQC"
    hdr[3].text = "Mức độ %"
    for c in hdr:
        set_cell_background(c, "003366")
        for p in c.paragraphs:
            for r in p.runs:
                r.font.bold = True
                r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                
    rows_data = [
        ("API LLM Engine (ai_service.py)", "Tích hợp SDK Gemini 2.5 Flash, Structured Output JSON Schema", "Chạy được API thô, chưa có Streaming, phụ thuộc 100% API Gemini", "60%"),
        ("5512 Validator (validation.py)", "Kế thừa luật Rule-based: check 4 từ khóa & đếm ký tự > 10", "Quá máy móc thô sơ, chưa kiểm tra chất lượng sư phạm nội dung", "30%"),
        ("Auto-Retry Loop (ai_service.py)", "Vòng lặp gửi feedback lỗi 5512 cho Gemini sửa lại (max 2 lần)", "Tăng được độ chính xác khung JSON, nhưng tốn latency (chờ 15s)", "50%"),
        ("Docx Exporter (docx_exporter.py)", "Viết hàm bóc tách LaTeX -> MathML -> OMML XML trong Word", "Kỹ thuật khá tốt ở phần Math, nhưng trình bày trang Word còn thô", "65%"),
        ("Slide Generator (marp_converter.py)", "Chuyển JSON Slide sang Marp Markdown + npx Marp CLI PPTX", "Slide rất xấu, đơn điệu như ghi chú, không có visual element/ảnh thật", "40%"),
        ("RESTful Server (main.py)", "Khởi tạo 4 FastAPI endpoints tải stream file .docx / .pptx", "Mới dừng ở mức router đơn giản, không Auth, không Rate Limit", "35%"),
        ("Giao diện UI & Database", "Chưa triển khai dòng code nào (Mới gọi lệnh qua Swagger/Script)", "HOÀN TOÀN TRỐNG (0% Frontend & 0% Database Persistence)", "0%")
    ]
    for idx, row in enumerate(rows_data, start=1):
        cells = table_comp.rows[idx].cells
        cells[0].text = row[0]
        cells[1].text = row[1]
        cells[2].text = row[2]
        cells[3].text = row[3]
        if idx % 2 == 1:
            for c in cells:
                set_cell_background(c, "F2F4F7")
                
    doc.add_paragraph()
    
    # -------------------------------------------------------------
    # SECTION II: PHÂN TÍCH CHI TIẾT MỨC ĐỘ KỸ THUẬT (CƠ BẢN VS NÂNG CAO)
    # -------------------------------------------------------------
    h2 = doc.add_paragraph()
    r_h2 = h2.add_run("II. PHÂN TÍCH MỨC ĐỘ KỸ THUẬT ĐÃ XỬ LÝ (CƠ BẢN VS NÂNG CAO)")
    r_h2.font.bold = True
    r_h2.font.size = Pt(13)
    r_h2.font.color.rgb = RGBColor(0x00, 0x33, 0x66)
    
    tech_details = [
        ("1. Thiết kế Schema Dữ liệu (schemas.py, slide_schema.py)", "ĐÁNH GIÁ: CƠ BẢN",
         "• Thực tế mã nguồn: Sử dụng Pydantic v2 định nghĩa BaseModel cho Giáo án 5512 (Mục tiêu, 4 Hoạt động, 4 Bước thực hiện) và Slide Deck.\n"
         "• Góc nhìn QC/Leader: Đây mới chỉ là bước khai báo cấu trúc dữ liệu tiêu chuẩn (Data Modeling) ở mức cơ bản. Chưa có validation phức tạp ở cấp field (ví dụ: ràng buộc logic giữa thời lượng các hoạt động với tổng thời lượng bài dạy)."),
        
        ("2. Gọi LLM Gemini 2.5 Flash & Structured Output (ai_service.py)", "ĐÁNH GIÁ: CƠ BẢN - TRUNG BÌNH",
         "• Thực tế mã nguồn: Dùng SDK google-genai, cấu hình response_mime_type='application/json' và truyền response_schema=LessonPlanSchema.\n"
         "• Góc nhìn QC/Leader: Việc áp dụng Structured Output giúp giảm nguy cơ AI trả về JSON sai cú pháp. Tuy nhiên, kỹ thuật này hoàn toàn phụ thuộc vào API độc tôn của Google. Chưa có cơ chế Fallback sang các mô hình khác (như OpenAI GPT-4o, Claude 3.5 Sonnet hay LLM mã nguồn mở nội bộ) khi Gemini bị lỗi hoặc quá tải."),
        
        ("3. Bộ kiểm duyệt Quy chuẩn 5512 (validation.py)", "ĐÁNH GIÁ: CƠ BẢN (Rule-Based thô sơ)",
         "• Thực tế mã nguồn: Kiểm tra số lượng hoạt động (=4), kiểm tra từ khóa ('mở đầu', 'khởi động', 'hình thành kiến thức', 'luyện tập', 'vận dụng') và kiểm tra chuỗi bước > 10 ký tự.\n"
         "• Góc nhìn QC/Leader: Đây là bộ kiểm duyệt rất 'ngây thơ'. Một giáo án có thể ghi nội dung vô nghĩa nhưng chỉ cần dài > 10 ký tự và có chứa từ khóa 'khởi động' thì Validator vẫn đánh giá là HỢP LỆ. Hệ thống hoàn toàn thiếu khả năng đánh giá chiều sâu sư phạm hay tính đúng đắn về mặt tri thức."),
        
        ("4. Xử lý Chuyển đổi Công thức Toán LaTeX sang OMML Word (docx_exporter.py)", "ĐÁNH GIÁ: KHÁ - NÂNG CAO",
         "• Thực tế mã nguồn: Tự viết chuỗi bóc tách Regex phát hiện \\(...\\), $...$, chuyển LaTeX -> MathML (qua latex2mathml) -> OMML XML (qua mathml2omml) -> chèn vào Document qua docx.oxml.parse_xml. Đồng thời viết hàm clean_xml_string() lọc ký tự điều khiển rác.\n"
         "• Góc nhìn QC/Leader: Đây là điểm sáng kỹ thuật tốt nhất của đồ án hiện tại. Giải quyết được bài toán khó mà nhiều công cụ AI thương mại chưa làm tốt. Tuy nhiên, phần trình bày bố cục trang Word (style, bảng biểu) vẫn còn khá đơn điệu, chưa hỗ trợ các bài học có hình vẽ minh họa phức tạp (như TikZ/Geometry)."),
        
        ("5. Động cơ Slide Marp CLI (marp_converter.py, slide_exporter.py)", "ĐÁNH GIÁ: CƠ BẢN & CÒN HẠN CHẾ BẤT CẬP",
         "• Thực tế mã nguồn: Chuyển JSON Slide thành chuỗi Marp Markdown, sau đó gọi subprocess npx @marp-team/marp-cli để biên dịch sang file PPTX.\n"
         "• Góc nhìn QC/Leader: Đây là phương án 'chữa cháy' nhanh nhưng bộc lộ nhược điểm rất lớn. File PPTX tạo ra có chất lượng thẩm mỹ rất kém, bố cục bị gò bó như một file ghi chú văn bản trình chiếu. Người dùng không thể kéo thả hay chỉnh sửa các visual element như file PPTX thiết kế chuẩn."),
        
        ("6. FastAPI REST Server (main.py)", "ĐÁNH GIÁ: CƠ BẢN",
         "• Thực tế mã nguồn: Viết 4 endpoints đơn giản sử dụng Response(content=bytes, media_type=...).\n"
         "• Góc nhìn QC/Leader: Mới dừng ở mức Router chuyển tiếp dữ liệu. Thiếu toàn bộ các tính năng của một Backend sản phẩm: Không có Authentication/JWT, không có User Authorization, không có Rate Limiting, không có Async Task Queue (Celery/Redis) để xử lý tác vụ nặng.")
    ]
    
    for title, level, desc in tech_details:
        p_t = doc.add_paragraph()
        r_t1 = p_t.add_run(f"• {title} - ")
        r_t1.font.bold = True
        r_t2 = p_t.add_run(f"[{level}]\n")
        r_t2.font.bold = True
        r_t2.font.color.rgb = RGBColor(0xC0, 0x00, 0x00) if "CƠ BẢN" in level else RGBColor(0x00, 0x80, 0x00)
        
        p_d = doc.add_paragraph()
        p_d.paragraph_format.left_indent = Inches(0.25)
        p_d.paragraph_format.line_spacing = 1.15
        p_d.add_run(desc)
        
    doc.add_paragraph()
    
    # -------------------------------------------------------------
    # SECTION III: BÓC TRẦN TỪ THREAD 'QUESTION' VÀ LỊCH SỬ THẢO LUẬN
    # -------------------------------------------------------------
    h3 = doc.add_paragraph()
    r_h3 = h3.add_run("III. KHAI THÁC BÓC TRẦN TỪ THREAD 'QUESTION' & THẮC MẮC TRONG LỊCH SỬ DỰ ÁN")
    r_h3.font.bold = True
    r_h3.font.size = Pt(13)
    r_h3.font.color.rgb = RGBColor(0x00, 0x33, 0x66)
    
    p3 = doc.add_paragraph()
    p3.paragraph_format.line_spacing = 1.15
    p3.add_run(
        "Trong phiên trò chuyện 'question' và các phiên thảo luận kỹ thuật liên quan, tác giả đã đặt ra những câu hỏi mang tính 'bản chất bài toán'. "
        "Dưới đây là phần bóc tách thẳng thắn giữa câu hỏi của tác giả, hướng giải quyết đã tư vấn và THỰC TẾ ĐÁP ỨNG CỦA MÃ NGUỒN HIỆN TẠI:\n"
    )
    
    q_topics = [
        ("1. Thắc mắc trong thread 'question': Dự án AI chỉ cần 'Prompt + Result' hay bắt buộc phải có Cơ sở dữ liệu (Database)?",
         "• Thắc mắc của Tác giả: 'Tài liệu JSON Schema và ERD CSDL là gì? Tại sao lại cần CSDL? Nếu áp dụng AI không phải chỉ cần đơn giản là Prompt và kết quả nhận lại của AI hay sao? Phát triển dạng Chatbot có cần CSDL không?'\n"
         "• Hướng giải quyết đã gợi ý: Giải thích vai trò của CSDL trong việc lưu trữ User Profile, Lịch sử Giáo án, Quản lý các Template Slide, Cache kết quả LLM và quản lý trạng thái phiên làm việc.\n"
         "• BÓC TRẦN THỰC TẾ MÃ NGUỒN: Mã nguồn hiện tại ĐANG CHẠY HOÀN TOÀN THEO HƯỚNG PURE PROMPT / SCRIPT TẠM VẮNG CSDL. Khi gửi request, backend gọi AI rồi trả về file byte trực tiếp. Không có dòng code CSDL nào (chưa có PostgreSQL/MongoDB/SQLAlchemy). Đây chính là điểm yếu nhất khiến dự án không thể trở thành sản phẩm thực tế."),
        
        ("2. Thắc mắc về Chuyển đổi Công thức Toán LaTeX sang Microsoft Word",
         "• Thắc mắc của Tác giả: 'Làm sao khi kết quả trả về là file Word nhưng các công thức toán học được đưa về dạng chuẩn Word chứ không bị vỡ ảnh hay hiển thị dạng chuỗi LaTeX thô?'\n"
         "• Hướng giải quyết đã gợi ý: Sử dụng quy trình chuyển đổi 3 bước: LaTeX -> MathML -> OMML XML (Word Native Math).\n"
         "• BÓC TRẦN THỰC TẾ MÃ NGUỒN: Đã được thực hiện tốt trong docx_exporter.py qua hàm convert_latex_to_omml(). Công thức toán hiển thị sắc nét dưới dạng Native Equation trong Word. Điểm tồn đọng duy nhất là chưa hỗ trợ các hình vẽ toán học dạng TikZ hay hình khối phẳng."),
        
        ("3. Thắc mắc về Slide PowerPoint thô sơ & Hạn chế của Marp CLI",
         "• Thắc mắc của Tác giả: 'Tại sao khi để AI sinh ra slide ở dự án này, slide sinh ra như không thể chỉnh sửa được, nó như thể là 1 bức ảnh được AI gán vào? Vì sao lại có nguyên nhân này và hướng nào phục hồi?'\n"
         "• Hướng giải quyết đã gợi ý: Giải thích cơ chế của Marp CLI render Markdown ra PPTX dạng các khối tĩnh, và gợi ý chuyển sang dùng thư viện python-pptx để can thiệp native vào các shape/textbox/slide layout của PowerPoint.\n"
         "• BÓC TRẦN THỰC TẾ MÃ NGUỒN: Dự án HIỆN VẪN ĐANG DÙNG MARP CLI. Chưa chuyển sang python-pptx. Do đó, Slide sinh ra hiện tại vẫn bị gò bó, xấu, mang phong cách ghi chú thô, chưa có hình ảnh minh họa thật và hoàn toàn không đáp ứng được yêu cầu thẩm mỹ của một bài giảng điện tử chuyên nghiệp."),
        
        ("4. Thắc mắc về Logic Kiểm duyệt Quy chuẩn 5512",
         "• Thắc mắc của Tác giả: 'Xử lý AI và logic 5512 là những gì? Thể hiện qua các dòng code như thế nào? Liệu code của tôi đã giải quyết triệt để hay chưa?'\n"
         "• Hướng giải quyết đã gợi ý: Giải thích việc dùng Pydantic Schema để định khuôn JSON + dùng Validator rule-based check từ khóa + dùng Auto-retry loop.\n"
         "• BÓC TRẦN THỰC TẾ MÃ NGUỒN: Code hiện tại MỚI CHỈ GIẢI QUYẾT BỀ NỔI (ĐÚNG KHUNG JSON). Logic kiểm duyệt 5512 trong validation.py hoàn toàn chưa giải quyết triệt để tính đúng đắn sư phạm. Hệ thống chưa kiểm tra được nội dung có bị ảo giác (hallucination) hay không, thời lượng có hợp lý hay không.")
    ]
    
    for title, content in q_topics:
        p_qt = doc.add_paragraph()
        r_q = p_qt.add_run(title)
        r_q.font.bold = True
        r_q.font.color.rgb = RGBColor(0x00, 0x56, 0xB3)
        
        p_qb = doc.add_paragraph()
        p_qb.paragraph_format.left_indent = Inches(0.2)
        p_qb.paragraph_format.line_spacing = 1.15
        p_qb.add_run(content)
        doc.add_paragraph()
        
    # -------------------------------------------------------------
    # SECTION IV: CÁC KỸ THUẬT VÀ CÔNG NGHỆ ĐÃ SỬ DỤNG
    # -------------------------------------------------------------
    h4 = doc.add_paragraph()
    r_h4 = h4.add_run("IV. TỔNG HỢP CÁC KỸ THUẬT VÀ CÔNG NGHỆ ĐÃ SỬ DỤNG DƯỚI GÓC NHÌN QC")
    r_h4.font.bold = True
    r_h4.font.size = Pt(13)
    r_h4.font.color.rgb = RGBColor(0x00, 0x33, 0x66)
    
    techs = [
        ("Backend Framework", "Python 3.10+, FastAPI, Uvicorn, CORS Middleware", "Đủ dùng cho Prototype, nhưng thiếu Async Worker & Middleware an toàn."),
        ("AI / LLM Orchestration", "Google GenAI SDK, Gemini 2.5 Flash, Structured Outputs (JSON Schema)", "Ép định dạng tốt, nhưng phụ thuộc độc tôn vào API Gemini, dễ dính Quota Limit."),
        ("Data Schema & Validation", "Pydantic v2 (BaseModel), Rule-based Regex Matching", "Khai báo dữ liệu chuẩn, nhưng bộ Validator quá thô sơ."),
        ("Word Mathematics Engine", "python-docx, latex2mathml, mathml2omml, lxml parse_xml", "Kỹ thuật render công thức OMML native rất tốt."),
        ("Slide Presentation Engine", "Marp CLI (@marp-team/marp-cli via Node.js/npx subprocess)", "Giải pháp tạm thời thô sơ, tạo Slide xấu, không linh hoạt."),
        ("Utility & Storage", "python-dotenv, io.BytesIO (Memory Streaming)", "Xử lý stream bộ nhớ tốt, nhưng thiếu hoàn toàn CSDL persistent.")
    ]
    
    table_tech = doc.add_table(rows=len(techs)+1, cols=3)
    table_tech.alignment = WD_TABLE_ALIGNMENT.CENTER
    t_hdr = table_tech.rows[0].cells
    t_hdr[0].text = "Hạng mục Công nghệ"
    t_hdr[1].text = "Chi tiết Kỹ thuật Áp dụng"
    t_hdr[2].text = "Đánh giá Hạn chế của QC"
    for c in t_hdr:
        set_cell_background(c, "003366")
        for p in c.paragraphs:
            for r in p.runs:
                r.font.bold = True
                r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                
    for idx, (cat, spec, qc_eval) in enumerate(techs, start=1):
        cells = table_tech.rows[idx].cells
        cells[0].text = cat
        cells[1].text = spec
        cells[2].text = qc_eval
        if idx % 2 == 1:
            for c in cells:
                set_cell_background(c, "F2F4F7")
                
    doc.add_paragraph()
    
    # -------------------------------------------------------------
    # SECTION V: ĐÁNH GIÁ TRẦN TRỤI - ƯU ĐIỂM VÀ NHƯỢC ĐIỂM
    # -------------------------------------------------------------
    h5 = doc.add_paragraph()
    r_h5 = h5.add_run("V. ĐÁNH GIÁ TRẦN TRỤI: ƯU ĐIỂM VÀ NHƯỢC ĐIỂM CỦA DỰ ÁN HIỆN TẠI")
    r_h5.font.bold = True
    r_h5.font.size = Pt(13)
    r_h5.font.color.rgb = RGBColor(0x00, 0x33, 0x66)
    
    p_pro = doc.add_paragraph()
    r_pro = p_pro.add_run("1. Ưu điểm (Những điểm sáng kỹ thuật thực sự làm được):")
    r_pro.font.bold = True
    
    pros = [
        "Đã thông suốt luồng dữ liệu tự động 100%: Từ Yêu cầu người dùng -> LLM -> JSON -> File Word (.docx) & Slide PPTX (.pptx).",
        "Xử lý xuất sắc bài toán Công thức Toán học: Chuyển đổi thành công chuỗi LaTeX thành công thức OMML Native Equation hiển thị sắc nét trong Word.",
        "Kiểm soát cấu trúc dữ liệu đầu ra của AI: Áp dụng Pydantic Structured Output giúp kết quả trả về luôn đúng khung JSON 5512.",
        "Mã nguồn Backend tổ chức gọn gàng: Tách biệt các mô-đun ai_service, validation, docx_exporter, marp_converter giúp dễ đọc và nâng cấp."
    ]
    for pr in pros:
        p_item = doc.add_paragraph()
        p_item.paragraph_format.left_indent = Inches(0.25)
        p_item.add_run(f"✔  {pr}")
        
    p_con = doc.add_paragraph()
    r_con = p_con.add_run("\n2. Nhược điểm & Lỗ hổng nghiêm trọng (Dưới góc nhìn QC & Khách hàng):")
    r_con.font.bold = True
    
    cons = [
        "HOÀN TOÀN CHƯA CÓ GIAO DIỆN NGƯỜI DÙNG (NO UI): Người dùng bắt buộc phải dùng lệnh Terminal hoặc Swagger UI để gửi request. Đây là điểm trừ lớn nhất khiến dự án chưa có giá trị sử dụng thực tế.",
        "THIẾU CƠ SỞ DỮ LIỆU (NO DATABASE): Dự án hoàn toàn không có Database. Mọi dữ liệu sinh ra chỉ nằm ở bộ nhớ tạm hoặc lưu file thô. Không có quản lý người dùng, không có lịch sử giáo án, không lưu được phiên làm việc.",
        "SLIDE POWERPOINT RẤT XẤU VÀ ĐƠN ĐIỆU: Việc phụ thuộc vào Marp CLI khiến Slide sinh ra trông như một bản ghi chú văn bản thô, thiếu các element thị giác (visual elements), chưa chèn được hình ảnh thật (mới chỉ có text image_prompt).",
        "BỘ KIỂM DUYỆT 5512 QUÁ THÔ SƠ & DỄ BỊ QUA MẶT: Validator kiểm tra bằng từ khóa và đếm ký tự > 10. AI có thể sinh nội dung nhảm nhí nhưng nếu chứa từ khóa 'khởi động' thì Validator vẫn báo HỢP LỆ.",
        "THỜI GIAN PHẢN HỒI CHẬM (HIGH LATENCY): Việc gọi Gemini sinh JSON dài và thực hiện loop retry 2-3 lần khiến API phải chờ 10-20 giây. Không có cơ chế Streaming Progress khiến người dùng có cảm giác ứng dụng bị treo.",
        "PHỤ THUỘC ĐỘC TÔN VÀO GEMINI API: Hệ thống chưa có cơ chế Fallback. Nếu API Gemini bị quá tải, sập mạng hoặc hết Quota, toàn bộ ứng dụng sẽ đứng yên."
    ]
    for cn in cons:
        p_item = doc.add_paragraph()
        p_item.paragraph_format.left_indent = Inches(0.25)
        p_item.add_run(f"✖  {cn}")
        
    doc.add_paragraph()
    
    # -------------------------------------------------------------
    # SECTION VI: TỔNG HỢP VẤN ĐỀ ĐÃ GIẢI QUYẾT VÀ TỒN ĐỌC
    # -------------------------------------------------------------
    h6 = doc.add_paragraph()
    r_h6 = h6.add_run("VI. BẢNG ĐỐI CHIẾU VẤN ĐỀ ĐÃ GIẢI QUYẾT VÀ TỒN ĐỌC CHƯA GIẢI QUYẾT")
    r_h6.font.bold = True
    r_h6.font.size = Pt(13)
    r_h6.font.color.rgb = RGBColor(0x00, 0x33, 0x66)
    
    table_issues = doc.add_table(rows=7, cols=2)
    table_issues.alignment = WD_TABLE_ALIGNMENT.CENTER
    i_hdr = table_issues.rows[0].cells
    i_hdr[0].text = "ĐÃ GIẢI QUYẾT ĐƯỢC (Solved)"
    i_hdr[1].text = "TỒN ĐỌC CHƯA GIẢI QUYẾT (Unsolved / Pending)"
    for c in i_hdr:
        set_cell_background(c, "003366")
        for p in c.paragraphs:
            for r in p.runs:
                r.font.bold = True
                r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                
    issues_data = [
        ("Ép AI xuất JSON đúng khung Giáo án 5512 bằng Pydantic Schema.", "Chưa có Giao diện Web (UI) để giáo viên nhập liệu và chỉnh sửa."),
        ("Render công thức toán LaTeX thành OMML Native Equation chuẩn trong Word.", "Slide PPTX sinh qua Marp CLI rất thô sơ, chưa dùng python-pptx native template."),
        ("Lọc sạch ký tự rác XML ẩn tránh hỏng file .docx khi xuất.", "Chưa chèn được hình ảnh minh họa thật vào Slide (chỉ có dòng text image_prompt)."),
        ("Xây dựng bộ kiểm duyệt từ khóa 5512 cơ bản + Auto-retry loop.", "Validator chưa đánh giá được chất lượng nội dung hay tính đúng đắn sư phạm."),
        ("Tạo 4 REST API endpoints xuất stream file Word/PPTX.", "Hoàn toàn chưa có Cơ sở dữ liệu (Database) lưu trữ tài khoản và giáo án."),
        ("Chuyển đổi tự động từ Giáo án JSON -> Marp Slide Markdown.", "Chưa có cơ chế Async Streaming Response khiến người dùng chờ lâu (10-20s).")
    ]
    for idx, (sol, unsol) in enumerate(issues_data, start=1):
        cells = table_issues.rows[idx].cells
        cells[0].text = f"✔ {sol}"
        cells[1].text = f"✖ {unsol}"
        if idx % 2 == 1:
            for c in cells:
                set_cell_background(c, "F2F4F7")
                
    doc.add_paragraph()
    
    # -------------------------------------------------------------
    # SECTION VII: KẾT QUẢ ĐÃ VÀ ĐÀNG NHẬN ĐƯỢC THỂ HIỆN ĐIỀU GÌ?
    # -------------------------------------------------------------
    h7 = doc.add_paragraph()
    r_h7 = h7.add_run("VII. KẾT QUẢ ĐÃ VÀ ĐÀNG NHẬN ĐƯỢC THỰC CHẤT THỂ HIỆN ĐIỀU GÌ?")
    r_h7.font.bold = True
    r_h7.font.size = Pt(13)
    r_h7.font.color.rgb = RGBColor(0x00, 0x33, 0x66)
    
    p_ans = doc.add_paragraph()
    p_ans.paragraph_format.line_spacing = 1.15
    p_ans.add_run(
        "Dưới góc nhìn kiểm định khắt khe của Tech Lead và Khách hàng, kết quả hiện tại "
    )
    r_ev_b = p_ans.add_run("THỰC CHẤT THỂ HIỆN 3 ĐIỀU NGUYÊN BẢN SAU:")
    r_ev_b.font.bold = True
    p_ans.add_run(":\n\n")
    
    points = [
        ("1. CHỈ THỂ HIỆN TÍNH KHẢ THI VỀ MẶT THUẬT TOÁN (Proof of Concept - POC):", 
         "Kết quả chạy được hiện tại chứng minh rằng ý tưởng phối hợp AI + Pydantic Schema + Document Exporter là KHẢ THI. Luồng dữ liệu có thể chảy tự động từ câu lệnh của người dùng ra file Word và PowerPoint mà không bị gãy đoạn."),
        
        ("2. HOÀN TOÀN CHƯA THỂ HIỆN TÍNH SẴN SÀNG SỬ DỤNG (0% Production-Ready):", 
         "Dự án tuyệt đối CHƯA THỂ coi là một sản phẩm phần mềm hoàn chỉnh hay thương mại hóa. Thiếu Giao diện UI, thiếu Cơ sở dữ liệu, Slide xấu và Validator thô sơ khiến dự án hiện tại mới chỉ là một 'khung xương Backend thô', chưa thể giao cho bất kỳ giáo viên nào sử dụng thực tế."),
        
        ("3. ĐÓNG VAI TRÒ LÀM NỀN TẢNG THỬ NGHIỆM ĐỂ KHẮC PHỤC Ở GIAI ĐOẠN 2:", 
         "Những gì làm được ở Giai đoạn 1 có ý nghĩa 'làm móng' (Foundation): xác định mô hình dữ liệu đúng và thử nghiệm thuật toán xuất file thành công. Toàn bộ phần việc quyết định giá trị thật sự của đồ án (Giao diện người dùng Web, Thiết kế Slide PowerPoint đẹp chuyên nghiệp, Đánh giá nội dung Sư phạm bằng AI, Cơ sở dữ liệu persistent) đều nằm ở phía trước.")
    ]
    
    for title_p, desc_p in points:
        p_pt = doc.add_paragraph()
        r_p1 = p_pt.add_run(f"{title_p}\n")
        r_p1.font.bold = True
        r_p1.font.color.rgb = RGBColor(0x8B, 0x00, 0x00)
        
        p_pd = doc.add_paragraph()
        p_pd.paragraph_format.left_indent = Inches(0.25)
        p_pd.paragraph_format.line_spacing = 1.15
        p_pd.add_run(desc_p)
        doc.add_paragraph()
        
    # -------------------------------------------------------------
    # SECTION VIII: LỘ TRÌNH KHẮC PHỤC & KHUYẾN NGHỊ CỦA TECH LEAD / QC
    # -------------------------------------------------------------
    h8 = doc.add_paragraph()
    r_h8 = h8.add_run("VIII. KẾ HOẠCH HÀNH ĐỘNG & KHUYẾN NGHỊ KHẮC PHỤC DÀNH CHO TÁC GIẢ (STAGE 2 ROADMAP)")
    r_h8.font.bold = True
    r_h8.font.size = Pt(13)
    r_h8.font.color.rgb = RGBColor(0x00, 0x33, 0x66)
    
    p_re = doc.add_paragraph()
    p_re.paragraph_format.line_spacing = 1.15
    p_re.add_run(
        "Để đưa dự án từ một 'Script POC Backend thô' trở thành một 'Sản phẩm phần mềm thực sự hoàn chỉnh' phục vụ báo cáo Đồ án tốt nghiệp, "
        "Tech Lead & QC khuyến nghị tác giả cần triển khai ngay 5 hành động khắc phục ở Giai đoạn 2:\n\n"
    )
    
    actions = [
        ("1. Triển khai Cơ sở dữ liệu (Database Setup):",
         "Tích hợp PostgreSQL hoặc MongoDB kết hợp với SQLAlchemy/Prisma ORM. Tạo các bảng: Users (Giáo viên), LessonPlans (Giáo án đã lưu), SlideDecks (Slide đã tạo), SlideTemplates (Mẫu giao diện Slide)."),
        
        ("2. Xây dựng Giao diện Người dùng Web UI (React / Next.js):",
         "Phát triển giao diện Web chuyên nghiệp gồm: Màn hình nhập thông tin bài dạy, Màn hình Xem trước & Chỉnh sửa Giáo án (Live Editor), Màn hình Slide Preview tương tác và Nút tải file Word/PPTX."),
        
        ("3. Thay thế Marp CLI bằng Động cơ Slide Native (python-pptx):",
         "Chuyển đổi module xuất slide sang thư viện python-pptx native. Thiết kế các Slide Master Template sẵn có (màu sắc, logo, khung khái niệm, khung bài tập) để slide xuất ra đẹp như thiết kế tay."),
        
        ("4. Nâng cấp Bộ kiểm duyệt 5512 bằng LLM Evaluator:",
         "Không chỉ kiểm tra từ khóa thô sơ, xây dựng một Agent AI phụ trách Review Sư phạm (Pedagogical Reviewer) để chấm điểm và phát hiện lỗi logic bài học thực sự."),
        
        ("5. Bổ sung Tích hợp AI Sinh Hình ảnh & Streaming API:",
         "Tích hợp API Flux / Stable Diffusion / DALL-E để tự động tạo và chèn hình ảnh minh họa thật vào Slide. Tích hợp Server-Sent Events (SSE) để phát luồng tiến độ sinh giáo án theo thời gian thực (Real-time Progress).")
    ]
    
    for act_t, act_d in actions:
        p_at = doc.add_paragraph()
        r_a1 = p_at.add_run(f"{act_t}\n")
        r_a1.font.bold = True
        r_a1.font.color.rgb = RGBColor(0x00, 0x56, 0xB3)
        
        p_ad = doc.add_paragraph()
        p_ad.paragraph_format.left_indent = Inches(0.25)
        p_ad.paragraph_format.line_spacing = 1.15
        p_ad.add_run(act_d)
        doc.add_paragraph()
        
    output_path = "/Users/nguyennhan18/Documents/Lesson-Plan-Generator/report_GD1.docx"
    doc.save(output_path)
    print(f"🔥 Exhaustive, grounded report_GD1.docx saved successfully to {output_path}")

if __name__ == "__main__":
    create_detailed_report()
