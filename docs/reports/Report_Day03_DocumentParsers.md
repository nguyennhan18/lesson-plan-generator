# 📊 BÁO CÁO TIẾN ĐỘ VÀ NGHIỆM THU CHI TIẾT NGÀY 3
## PARSER TIẾP NHẬN FILE CŨ (PPTX PARSER & DOCX PARSER) & CẤU TRÚC CÂY ĐỐI TƯỢNG OPENXML

**Ngày thực hiện:** 12/10/2026 - 13/10/2026  
**Dự án:** Lesson Plan Generator & Interactive Slide Studio (GDPT 2018)  
**Trạng thái nghiệm thu (DoD):** 🎯 **ĐẠT 100% (5/5 Test Cases PASSED trong 0.06s)**  

---

## 📋 I. TỔNG QUAN VỀ QUY TRÌNH VÀ NGHIỆM THU TASK NGÀY 3

Trong Ngày 3, chúng ta đã hoàn thành trọn vẹn hệ thống **Document Ingestion Parser** tiếp nhận các tài liệu có sẵn của giáo viên (`.pptx` và `.docx`), vận hành đúng theo khung giờ chuẩn 8 tiếng/ngày:

| Mã Task | Nội dung công việc | File thực hiện | Trạng thái |
| :--- | :--- | :--- | :---: |
| **Briefing** | Thiết kế module dùng chung (Nguyên lý DRY): đọc luồng bộ nhớ `read_source()`, làm sạch văn bản `clean_text()` và schema đầu ra `ParsedDocumentResponse`. | `project/app/parsers/common.py` | ✅ **100%** |
| **Task 3.1** | Xây dựng bộ bóc tách PowerPoint (`pptx_parser.py`): duyệt đệ quy `Slide` $\rightarrow$ `Shape` / `GroupShape` $\rightarrow$ `TextFrame`, `Table` và `NotesSlide`. | `project/app/parsers/pptx_parser.py` | ✅ **100%** |
| **Task 3.2** | Xây dựng bộ bóc tách Word (`docx_parser.py`): duyệt tuần tự khối `CT_P` & `CT_Tbl`, khử trùng lặp ô gộp (`_tc`), nhận diện tiêu đề bài học chuẩn CV 5512. | `project/app/parsers/docx_parser.py` | ✅ **100%** |
| **Task 3.3** | Tạo `ingest_router` và endpoint `POST /api/v1/ingest/parse-document` tiếp nhận `UploadFile`, trả về dữ liệu chuẩn hóa theo `ParsedDocumentResponse`. | `project/app/main.py` | ✅ **100%** |
| **Task 3.4** | Viết bộ kiểm thử tự động 5 Test Cases với file Giáo án 5512 thật (`GA_test_5512.docx`) và file Slide thật (`test_15.pptx`). | `project/test/test_day3_parsers.py` | ✅ **100%** |
| **Task 3.5** | Nghiệm thu DoD, phân tích sâu cấu trúc cây đối tượng OpenXML của Word & PowerPoint, đóng gói báo cáo kỹ thuật. | `Report_Task/Report_Day03_DocumentParsers.md` | ✅ **100%** |

---

## 🏛️ II. GIẢI THÍCH CHI TIẾT CẤU TRÚC CÂY ĐỐI TƯỢNG OPENXML (WORD & POWERPOINT)

Đây là phần kiến thức nền tảng cốt lõi của **Task 3.5** để giải trình và phản biện trước Hội đồng chấm Đồ án.

### 1. Bản chất Vật lý của File `.docx` và `.pptx` (Open Packaging Conventions - OPC)
* Một file `.docx` hoặc `.pptx` **không phải là một file đơn lẻ**, mà bản chất là một **tệp nén `.zip` (PKZip Archive)** tuân theo chuẩn quốc tế **ECMA-376 / ISO/IEC 29500 (Office Open XML)**.
* Nếu đổi đuôi `giao_an.docx` thành `giao_an.zip` và giải nén, bên trong là một hệ thống thư mục chứa các file XML và tài nguyên:
  * **Trong `.docx`:** `word/document.xml` (nội dung chính), `word/styles.xml` (kiểu chữ Heading/Normal), `docProps/core.xml` (metadata).
  * **Trong `.pptx`:** `ppt/presentation.xml` (khung bài trình chiếu), `ppt/slides/slide1.xml`, `slide2.xml`... (từng trang slide), `ppt/notesSlides/notesSlide1.xml` (ghi chú của giáo viên).
* **Lưu ý kiến trúc quan trọng (ZIP Central Directory):** Bảng mục lục trung tâm của định dạng ZIP nằm ở **cuối cùng của file**. Vì vậy, thư viện `python-docx` và `python-pptx` luôn cần luồng dữ liệu hỗ trợ phương thức `.seek()` (như `io.BytesIO`) để nhảy xuống cuối luồng đọc mục lục trước khi giải nén từng phần tử XML.

---

### 2. Cấu trúc Cây Đối tượng OpenXML của PowerPoint (`python-pptx`)

```
Presentation (ppt/presentation.xml)
 ├── core_properties (docProps/core.xml -> title, author...)
 └── slides: SlideCollection
       └── Slide (ppt/slides/slide{N}.xml)
             ├── shapes: SlideShapes
             │     ├── title: Shape (Title Placeholder mặc định của Slide)
             │     ├── Shape (Khung văn bản thường: has_text_frame == True)
             │     │     └── text_frame: TextFrame (<p:txBody>)
             │     │           └── paragraphs: List[_Paragraph] (<a:p>)
             │     │                 └── runs: List[_Run] (<a:r> -> <a:t> Chữ hiển thị)
             │     ├── GraphicFrame (Khung bảng biểu: has_table == True)
             │     │     └── table: Table (<a:tbl>)
             │     │           └── rows: _RowCollection (<a:tr>)
             │     │                 └── cells: _CellCollection (<a:tc>)
             │     │                       ├── text: str
             │     │                       ├── is_merge_origin: bool (Ô gốc bắt đầu gộp)
             │     │                       └── is_spanned: bool (Ô bị gộp chìm vào ô gốc)
             │     └── GroupShape (Nhóm đối tượng: shape_type == MSO_SHAPE_TYPE.GROUP)
             │           └── shapes: GroupShapes (<p:grpSp> -> Chứa đệ quy các Shape con bên trong!)
             │
             └── notes_slide: NotesSlide (ppt/notesSlides/notesSlide{N}.xml - kiểm tra qua has_notes_slide)
                   └── notes_text_frame: TextFrame (Chứa kịch bản lời thoại của Giáo viên)
```

#### 🔍 4 Đặc điểm kỹ thuật quan trọng trên cây PowerPoint đã xử lý trong code:
1. **Đệ quy `GroupShape` (`<p:grpSp>`):** Khi giáo viên chọn nhiều hộp chữ rồi nhấn `Ctrl + G` (Group), các hộp chữ đó không còn nằm ở cấp 1 của `slide.shapes` nữa mà nằm lồng bên trong `group_shape.shapes`. Hàm `_extract_shapes_text()` sử dụng đệ quy để quét sâu tới mọi cấp Group.
2. **Thứ tự Z-Order vs Tọa độ `shape.top`:** Danh sách `slide.shapes` được lưu theo thứ tự lớp vẽ (Z-order) chứ không phải từ trên xuống dưới. Khi slide không dùng Title Placeholder chuẩn, hàm `_get_title()` sắp xếp các shape theo tọa độ dọc `shape.top` tăng dần để lấy đúng dòng chữ nằm ở đỉnh trang làm tiêu đề.
3. **Ô gộp trong bảng PowerPoint (`cell.is_spanned`):** Khi gộp ô trong bảng PPTX, các ô bị gộp chìm có thuộc tính `is_spanned == True`. Hàm `_extract_table()` kiểm tra cờ này và gán `""` để không bị lặp lại nội dung của ô gốc.
4. **Cạm bẫy khởi tạo ngầm `slide.notes_slide`:** Nếu gọi trực tiếp `slide.notes_slide` trên một slide chưa có ghi chú, `python-pptx` sẽ tự động tạo thêm một file XML `notesSlide` rỗng vào bộ nhớ. Do đó, hàm `_get_notes()` luôn kiểm tra chốt chặn `if not getattr(slide, "has_notes_slide", False): return ""` trước tiên.

---

### 3. Cấu trúc Cây Đối tượng OpenXML của Word (`python-docx`)

```
Document (word/document.xml)
 ├── core_properties (docProps/core.xml)
 ├── paragraphs: List[Paragraph] (Chỉ chứa các đoạn văn cấp 1, tách rời khỏi bảng)
 ├── tables: List[Table] (Chỉ chứa các bảng cấp 1, tách rời khỏi đoạn văn)
 └── element.body: CT_Body (<w:body> - Nút gốc chứa toàn bộ phần tử theo ĐÚNG THỨ TỰ xuất hiện)
       ├── CT_P (<w:p>) ──(Bọc qua Paragraph(child, doc))──> Paragraph
       │     ├── style.name ("Title", "Heading 1", "Normal"...)
       │     └── text (Gom từ các thẻ <w:r> -> <w:t>)
       │
       └── CT_Tbl (<w:tbl>) ──(Bọc qua Table(child, doc))──> Table
             └── rows: _Rows (<w:tr>)
                   └── cells: _Cells (<w:tc>)
                         ├── _tc: CT_Tc (Con trỏ tới thẻ XML <w:tc> thực tế trong bộ nhớ)
                         └── text: str (Nội dung văn bản trong ô)
```

#### 🔍 2 Đặc điểm kỹ thuật quan trọng trên cây Word đã xử lý trong code:
1. **Bảo toàn thứ tự xuất hiện bằng Generator `_iter_block_items(doc)`:**
   * Trong Giáo án Công văn 5512, các đoạn văn dẫn nhập và bảng 2 cột (*Hoạt động của GV & HS* | *Sản phẩm dự kiến*) nằm đan xen nhau.
   * Nếu đọc `doc.paragraphs` riêng rồi mới đọc `doc.tables`, toàn bộ thứ tự bài dạy sẽ bị đảo lộn.
   * Hàm `_iter_block_items(doc)` duyệt trực tiếp `doc.element.body.iterchildren()`: gặp thẻ `CT_P` (`<w:p>`) thì `yield Paragraph`, gặp thẻ `CT_Tbl` (`<w:tbl>`) thì `yield Table`, giữ nguyên 100% mạch văn bản từ trên xuống dưới.
2. **Cơ chế con trỏ `_tc` của Ô gộp (`Merged Cells`) trong Word:**
   * Khác với PowerPoint, khi gộp 2 ô trên cùng một hàng trong bảng Word (`gridSpan`), `row.cells` vẫn trả về 2 đối tượng ` _Cell`, nhưng **cả 2 đối tượng này đều trỏ về cùng một địa chỉ vùng nhớ XML `cell._tc` (`CT_Tc`)**.
   * Hàm `_dedupe_row_cells(row)` dùng tập hợp `seen_tc = set()` để kiểm tra `cell._tc`: nếu thẻ `_tc` đã xuất hiện trong hàng thì bỏ qua ngay, kết hợp với kiểm tra `row_cells == rows[-1]` trong `_table_to_rows()` để khử luôn trường hợp gộp dọc (`vMerge`).

---

## 🧠 III. TỔNG HỢP CÁC KIẾN THỨC & KỸ THUẬT ĐÃ ÁP DỤNG TRONG NGÀY 3

1. **Nguyên lý DRY (*Don't Repeat Yourself*) & In-Memory Stream (`BytesIO`):**
   * Tách `read_source()` và `clean_text()` ra module dùng chung `common.py`.
   * Chuẩn hóa mọi kiểu đầu vào (`str`, `Path`, `bytes`, `BytesIO`, `BinaryIO`) về luồng bộ nhớ `BytesIO`, giúp hệ thống đọc file hoàn toàn trên RAM mà không cần ghi file tạm ra ổ cứng.
2. **Kỹ thuật làm sạch văn bản Office (`clean_text`):**
   * Xử lý các ký tự đặc thù của Microsoft Office: khoảng trắng không ngắt `\xa0` (*Non-breaking space*), ký tự độ rộng bằng không `\u200b` (*Zero-width space*), byte rỗng `\x00`, và chuyển ký tự xuống dòng mềm `\x0b` (*Vertical Tab* khi bấm `Shift + Enter`) thành `\n`.
3. **Kiến trúc Modular Routing với `APIRouter` của FastAPI:**
   * Sử dụng `ingest_router = APIRouter(prefix="/api/v1/ingest", tags=["Ingest"])` kết hợp `app.include_router(ingest_router)` để gom nhóm các API tiếp nhận dữ liệu đầu vào (dùng cho cả Ngày 3 và Ngày 4).
4. **Cơ chế `UploadFile = File(...)` và hằng số `Ellipsis` (`...`):**
   * Sử dụng `python-multipart` để giải mã gói tin HTTP `multipart/form-data`.
   * Sử dụng đối tượng `Ellipsis` (`...`) của Python trong `File(...)` để đánh dấu trường tải file là **Bắt buộc (Required)** trên FastAPI và Swagger UI.
5. **Hợp đồng dữ liệu đầu ra với `response_model=ParsedDocumentResponse`:**
   * Định nghĩa Pydantic schema `ParsedDocumentResponse` làm khuôn mẫu thống nhất cho cả `.pptx` và `.docx`, giúp FastAPI tự động kiểm định đầu ra và sinh tài liệu mẫu trên Swagger UI (`/docs`).
6. **Phân tích đánh đổi kiến trúc (Trade-off Analysis): Đọc trực tiếp vs Chunked Streaming:**
   * Đánh giá ưu/nhược điểm giữa `await file.read()` và đọc theo từng `chunk`. Với quy mô file giáo án/slide (40KB – 5MB) và đặc thù *ZIP Central Directory* nằm ở cuối file của chuẩn OpenXML, việc đọc trực tiếp trên RAM kết hợp `read_source()` mang lại sự tinh gọn và tốc độ tối ưu nhất ở giai đoạn hiện tại.

---

## 💻 IV. CHI TIẾT TOÀN BỘ MÃ NGUỒN ĐÃ XÂY DỰNG TRONG NGÀY 3

### 1. File [`project/app/parsers/common.py`](file:///Users/nguyennhan18/Documents/Lesson-Plan-Generator/project/app/parsers/common.py)
```python
import re
from io import BytesIO
from pathlib import Path
from typing import BinaryIO, Union, List, Dict, Any, Optional
from pydantic import BaseModel, Field

Source = Union[str, Path, bytes, BinaryIO, BytesIO]


def read_source(source: Source) -> BytesIO:
    if isinstance(source, (str, Path)):
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"Không tìm thấy file: {path}")
        return BytesIO(path.read_bytes())

    if isinstance(source, bytes):
        return BytesIO(source)

    if isinstance(source, BytesIO):
        source.seek(0)
        return source

    if hasattr(source, "read"):
        if hasattr(source, "seek"):
            source.seek(0)
        data = source.read()
        return BytesIO(data if isinstance(data, bytes) else data.encode("utf-8"))

    raise TypeError(f"Định dạng input không được hỗ trợ {type(source)}")


def clean_text(text: str | None) -> str:
    """
    Làm sạch văn bản thô bóc tách từ file Word (.docx) và PowerPoint (.pptx):
    - Xử lý giá trị None hoặc chuỗi rỗng.
    - Xóa ký tự ẩn (null byte \x00, zero-width space \u200b, vertical tab \x0b).
    - Chuẩn hóa khoảng trắng không ngắt (\xa0) về dấu cách thường.
    - Gộp nhiều dấu cách/tab liên tiếp trên cùng một dòng và lọc bỏ các dòng trống thừa.
    """
    if not text:
        return ""

    # 1. Loại bỏ các ký tự điều khiển ẩn thường gặp trong XML của Office
    cleaned = (
        text.replace("\xa0", " ")
        .replace("\u200b", "")
        .replace("\x00", "")
        .replace("\x0b", "\n")  # Vertical tab (Shift+Enter trong Word/PPTX) -> xuống dòng
    )
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")

    # 2. Chuẩn hóa từng dòng: gộp khoảng trắng thừa và bỏ dòng trống
    lines = []
    for line in cleaned.split("\n"):
        normalized_line = re.sub(r"[ \t]+", " ", line).strip()
        if normalized_line:
            lines.append(normalized_line)

    return "\n".join(lines)


class ParsedDocumentResponse(BaseModel):
    """Schema chuẩn hóa dữ liệu JSON đầu ra cho cả PPTX và DOCX Parser"""
    filename: str = Field(default="", description="Tên file gốc tải lên")
    file_type: str = Field(description="Loại tài liệu: 'pptx' hoặc 'docx'")
    title: str = Field(description="Tiêu đề bài giảng / giáo án nhận diện được")
    raw_text: str = Field(description="Toàn bộ nội dung văn bản đã làm sạch để đưa vào AI")

    # Trường chi tiết dành cho file PowerPoint (.pptx)
    total_slides: Optional[int] = Field(default=None, description="Tổng số trang slide (nếu là pptx)")
    slides: Optional[List[Dict[str, Any]]] = Field(default=None, description="Chi tiết từng trang slide")

    # Trường chi tiết dành cho file Word (.docx)
    total_paragraphs: Optional[int] = Field(default=None, description="Tổng số đoạn văn (nếu là docx)")
    total_tables: Optional[int] = Field(default=None, description="Tổng số bảng biểu (nếu là docx)")
    paragraphs: Optional[List[str]] = Field(default=None, description="Danh sách các đoạn văn")
    tables: Optional[List[List[List[str]]]] = Field(default=None, description="Danh sách các bảng biểu")
    blocks: Optional[List[Dict[str, Any]]] = Field(default=None, description="Các khối nội dung theo thứ tự từ trên xuống")
```

---

### 2. File [`project/app/parsers/pptx_parser.py`](file:///Users/nguyennhan18/Documents/Lesson-Plan-Generator/project/app/parsers/pptx_parser.py)
```python
from typing import List, Tuple, Any, Dict
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

try:
    from .common import Source, read_source, clean_text
except ImportError:
    from parsers.common import Source, read_source, clean_text


def _extract_shapes_text(
    shapes: Any,
    skip_shape: Any = None
) -> Tuple[List[str], List[List[List[str]]]]:
    """
    Duyệt đệ quy qua danh sách shapes của một slide để bóc tách:
    1. paragraphs (List[str]): Danh sách các đoạn văn bản đã làm sạch.
    2. tables (List[List[List[str]]]): Danh sách các bảng (mỗi bảng gồm các hàng -> các ô).
    """
    paragraphs: List[str] = []
    tables: List[List[List[str]]] = []

    for shape in shapes:
        # Bỏ qua shape tiêu đề nếu đã được lấy riêng ở slide.shapes.title
        if skip_shape is not None and shape == skip_shape:
            continue

        # 1. TRƯỜNG HỢP ĐỆ QUY: Nếu là GroupShape -> duyệt sâu vào các shape con bên trong
        if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
            sub_paragraphs, sub_tables = _extract_shapes_text(
                shape.shapes, skip_shape=skip_shape
            )
            paragraphs.extend(sub_paragraphs)
            tables.extend(sub_tables)
            continue

        # 2. TRƯỜNG HỢP KHUNG VĂN BẢN (Text Frame)
        if getattr(shape, "has_text_frame", False):
            for para in shape.text_frame.paragraphs:
                cleaned_para = clean_text(para.text)
                if cleaned_para:
                    paragraphs.append(cleaned_para)

        # 3. TRƯỜNG HỢP BẢNG BIỂU (Table)
        if getattr(shape, "has_table", False):
            table_rows = _extract_table(shape.table)
            if table_rows:
                tables.append(table_rows)

    return paragraphs, tables


def _extract_table(table: Any) -> List[List[str]]:
    """
    Chuyển đối tượng bảng (Table) của python-pptx thành ma trận 2 chiều list[list[str]]:
    - Làm sạch văn bản trong từng ô bằng clean_text().
    - Xử lý ô bị gộp (is_spanned) để không lặp nội dung.
    - Loại bỏ các hàng hoàn toàn trống.
    """
    table_rows: List[List[str]] = []

    for row in table.rows:
        row_cells: List[str] = []
        for cell in row.cells:
            if getattr(cell, "is_spanned", False):
                row_cells.append("")
            else:
                row_cells.append(clean_text(cell.text))

        if any(row_cells):
            table_rows.append(row_cells)

    return table_rows


def _get_title(slide: Any) -> str:
    """
    Lấy tiêu đề của một trang Slide PowerPoint:
    - Ưu tiên 1: Lấy từ placeholder tiêu đề chuẩn (slide.shapes.title).
    - Ưu tiên 2 (Fallback): Tìm shape văn bản nằm ở vị trí cao nhất trên slide (shape.top nhỏ nhất).
    """
    title_shape = getattr(slide.shapes, "title", None)
    if title_shape is not None and getattr(title_shape, "has_text_frame", False):
        title_text = clean_text(title_shape.text)
        if title_text:
            return title_text

    text_shapes = [
        shape for shape in slide.shapes
        if getattr(shape, "has_text_frame", False) and clean_text(shape.text)
    ]
    if text_shapes:
        text_shapes.sort(key=lambda s: (getattr(s, "top", 0) or 0))
        first_text = clean_text(text_shapes[0].text)
        return first_text.split("\n")[0]

    return ""


def _get_notes(slide: Any) -> str:
    """
    Trích xuất lời thoại / ghi chú của giáo viên (Speaker Notes) trong một trang Slide.
    """
    if not getattr(slide, "has_notes_slide", False):
        return ""

    try:
        notes_slide = slide.notes_slide
        if notes_slide is not None and notes_slide.notes_text_frame is not None:
            return clean_text(notes_slide.notes_text_frame.text)
    except Exception:
        return ""

    return ""


def parse_pptx(source: Source) -> Dict[str, Any]:
    """
    Hàm chính bóc tách toàn bộ nội dung file PowerPoint (.pptx).
    """
    stream = read_source(source)
    prs = Presentation(stream)

    slides_data: List[Dict[str, Any]] = []
    raw_blocks: List[str] = []
    presentation_title: str = ""

    for idx, slide in enumerate(prs.slides, start=1):
        title_shape = getattr(slide.shapes, "title", None)
        title = _get_title(slide)

        paragraphs, tables = _extract_shapes_text(
            slide.shapes, skip_shape=title_shape
        )

        if title and paragraphs and paragraphs[0] == title:
            paragraphs = paragraphs[1:]

        notes = _get_notes(slide)

        if not presentation_title and title:
            presentation_title = title

        slides_data.append({
            "slide_index": idx,
            "title": title,
            "paragraphs": paragraphs,
            "tables": tables,
            "notes": notes,
        })

        block_lines: List[str] = [
            f"--- SLIDE {idx}{f': {title}' if title else ''} ---"
        ]
        if paragraphs:
            block_lines.extend(paragraphs)
        for table in tables:
            for row in table:
                block_lines.append(" | ".join(row))
        if notes:
            block_lines.append(f"[Ghi chú GV]: {notes}")

        raw_blocks.append("\n".join(block_lines))

    if not presentation_title:
        meta_title = clean_text(getattr(prs.core_properties, "title", ""))
        presentation_title = meta_title or "Bài giảng PowerPoint"

    return {
        "file_type": "pptx",
        "title": presentation_title,
        "total_slides": len(slides_data),
        "slides": slides_data,
        "raw_text": "\n\n".join(raw_blocks),
    }
```

---

### 3. File [`project/app/parsers/docx_parser.py`](file:///Users/nguyennhan18/Documents/Lesson-Plan-Generator/project/app/parsers/docx_parser.py)
```python
from typing import List, Dict, Any, Iterator, Union
from docx import Document
from docx.document import Document as _Document
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph

try:
    from .common import Source, read_source, clean_text
except ImportError:
    from parsers.common import Source, read_source, clean_text


def _dedupe_row_cells(row: Any) -> List[str]:
    """
    Trích xuất danh sách văn bản các ô (cells) trên một hàng của bảng Word,
    đồng thời khử trùng lặp các ô bị gộp ngang/dọc (Merged Cells) qua thẻ XML `cell._tc`.
    """
    cells_text: List[str] = []
    seen_tc = set()

    for cell in row.cells:
        tc = getattr(cell, "_tc", None)
        if tc is not None:
            if tc in seen_tc:
                continue
            seen_tc.add(tc)

        cells_text.append(clean_text(cell.text))

    return cells_text


def _table_to_rows(table: Any) -> List[List[str]]:
    """
    Chuyển một bảng (Table) trong Word thành danh sách các hàng list[list[str]].
    """
    rows: List[List[str]] = []

    for row in table.rows:
        row_cells = _dedupe_row_cells(row)

        if not any(row_cells):
            continue

        if rows and row_cells == rows[-1]:
            continue

        rows.append(row_cells)

    return rows


def _detect_title(doc: Any) -> str:
    """
    Tự động nhận diện tiêu đề bài học từ đối tượng Document của python-docx.
    """
    non_empty_paras: List[str] = []
    lesson_keywords = ("tên bài dạy", "bài dạy:", "bài ", "chủ đề", "chuyên đề")

    for para in doc.paragraphs:
        text = clean_text(para.text)
        if not text:
            continue

        non_empty_paras.append(text)
        style_name = getattr(getattr(para, "style", None), "name", "") or ""
        lower_text = text.lower()

        if style_name.lower() in ("title", "heading 1"):
            return text

        if lower_text.startswith(lesson_keywords):
            return text

    if non_empty_paras:
        return non_empty_paras[0]

    for table in doc.tables:
        rows = _table_to_rows(table)
        if rows and rows[0]:
            for cell_text in rows[0]:
                if cell_text:
                    return cell_text.split("\n")[0]

    meta_title = clean_text(getattr(doc.core_properties, "title", ""))
    return meta_title or "Giáo án Word"


def _iter_block_items(parent: Any) -> Iterator[Union[Paragraph, Table]]:
    """
    Bộ sinh (Generator) duyệt tuần tự các khối nội dung (Paragraph và Table)
    theo đúng thứ tự xuất hiện từ trên xuống dưới trong tài liệu Word.
    """
    if isinstance(parent, _Document):
        parent_elm = parent.element.body
    elif isinstance(parent, _Cell):
        parent_elm = parent._tc
    else:
        parent_elm = parent.element.body

    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)


def parse_docx(source: Source) -> Dict[str, Any]:
    """
    Hàm chính bóc tách toàn bộ nội dung file Giáo án Word (.docx).
    """
    stream = read_source(source)
    doc = Document(stream)

    title = _detect_title(doc)

    paragraphs: List[str] = []
    tables: List[List[List[str]]] = []
    blocks: List[Dict[str, Any]] = []
    raw_lines: List[str] = []

    for item in _iter_block_items(doc):
        if isinstance(item, Paragraph):
            text = clean_text(item.text)
            if text:
                paragraphs.append(text)
                blocks.append({"type": "paragraph", "text": text})
                raw_lines.append(text)

        elif isinstance(item, Table):
            rows = _table_to_rows(item)
            if rows:
                tables.append(rows)
                blocks.append({"type": "table", "rows": rows})
                table_text = "\n".join(" | ".join(row) for row in rows)
                raw_lines.append(f"[BẢNG]:\n{table_text}")

    return {
        "file_type": "docx",
        "title": title,
        "total_paragraphs": len(paragraphs),
        "total_tables": len(tables),
        "paragraphs": paragraphs,
        "tables": tables,
        "blocks": blocks,
        "raw_text": "\n\n".join(raw_lines),
    }
```

---

### 4. Endpoint `/api/v1/ingest/parse-document` trong [`project/app/main.py`](file:///Users/nguyennhan18/Documents/Lesson-Plan-Generator/project/app/main.py#L240-L280)
```python
ingest_router = APIRouter(
    prefix="/api/v1/ingest",
    tags=["Ingest"]
)

@ingest_router.post("/parse-document", response_model=ParsedDocumentResponse)
async def parse_document_endpoint(
    file: UploadFile = File(..., description="File giáo án (.docx) or slide (.pptx) cần bóc tách")
):
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()

    if ext not in (".pptx", ".docx"):
        raise HTTPException(
            status_code=400,
            detail=f"định dạng '{ext}' không được hỗ trợ. Chỉ chấp nhận file .pptx or docx"
        )

    try:
        content = await file.read()
        if not content:
            raise HTTPException(
                status_code=400,
                detail="File tải lên rỗng"
            )
        if ext == ".pptx":
            parsed_result = parse_pptx(content)
        elif ext == ".docx":
            parsed_result = parse_docx(content)

        return {
            "filename": filename,
            **parsed_result,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi phân tích file '{filename}' : {str(e)}"
        )
    finally:
        await file.close()

app.include_router(ingest_router)
```

---

### 5. File [`project/test/test_day3_parsers.py`](file:///Users/nguyennhan18/Documents/Lesson-Plan-Generator/project/test/test_day3_parsers.py) (Unit & Integration Test Script)
```python
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Thêm đường dẫn project/app vào sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
APP_DIR = ROOT_DIR / "project" / "app"
sys.path.insert(0, str(APP_DIR))

from parsers.common import clean_text, ParsedDocumentResponse
from parsers.docx_parser import parse_docx
from parsers.pptx_parser import parse_pptx
from main import app

client = TestClient(app)

DOCX_SAMPLE = ROOT_DIR / "document" / "GA_test_5512.docx"
PPTX_SAMPLE = ROOT_DIR / "project" / "test" / "pptx" / "test_15.pptx"


def test_clean_text():
    """
    Test Case 1: Kiểm tra hàm làm sạch văn bản clean_text() trong common.py.
    """
    raw = "  Bài 1:\xa0Phương trình\u200b   bậc hai \x0b Dòng phụ \r\n\r\n   Dòng 2   "
    cleaned = clean_text(raw)
    assert cleaned == "Bài 1: Phương trình bậc hai\nDòng phụ\nDòng 2"
    assert clean_text(None) == ""
    assert clean_text("   \n\t  ") == ""


def test_parse_docx_real_file():
    """
    Test Case 2: Kiểm tra parse_docx() với file Giáo án 5512 thực tế (GA_test_5512.docx).
    """
    assert DOCX_SAMPLE.exists(), f"Không tìm thấy file mẫu: {DOCX_SAMPLE}"
    result = parse_docx(DOCX_SAMPLE)

    assert result["file_type"] == "docx"
    assert isinstance(result["title"], str) and len(result["title"]) > 0
    assert result["total_paragraphs"] > 0 or result["total_tables"] > 0
    assert isinstance(result["raw_text"], str) and len(result["raw_text"]) > 100
    assert isinstance(result["blocks"], list) and len(result["blocks"]) > 0

    print(f"\n[DOCX] Tiêu đề: {result['title']}")
    print(f"[DOCX] Số đoạn văn: {result['total_paragraphs']} | Số bảng: {result['total_tables']}")


def test_parse_pptx_real_file():
    """
    Test Case 3: Kiểm tra parse_pptx() với file PowerPoint bài giảng thực tế (test_15.pptx).
    """
    assert PPTX_SAMPLE.exists(), f"Không tìm thấy file mẫu: {PPTX_SAMPLE}"
    result = parse_pptx(PPTX_SAMPLE)

    assert result["file_type"] == "pptx"
    assert isinstance(result["title"], str) and len(result["title"]) > 0
    assert result["total_slides"] > 0
    assert len(result["slides"]) == result["total_slides"]
    assert isinstance(result["raw_text"], str) and len(result["raw_text"]) > 50

    print(f"\n[PPTX] Tiêu đề: {result['title']}")
    print(f"[PPTX] Tổng số slide: {result['total_slides']}")


def test_ingest_api_upload_docx_and_pptx():
    """
    Test Case 4: Kiểm tra API POST /api/v1/ingest/parse-document với cả 2 định dạng .docx và .pptx.
    """
    # 1. Upload file DOCX
    with open(DOCX_SAMPLE, "rb") as f:
        res_docx = client.post(
            "/api/v1/ingest/parse-document",
            files={"file": (DOCX_SAMPLE.name, f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        )
    assert res_docx.status_code == 200
    data_docx = res_docx.json()
    assert data_docx["filename"] == DOCX_SAMPLE.name
    assert data_docx["file_type"] == "docx"
    assert len(data_docx["raw_text"]) > 100
    # Kiểm định khớp chuẩn ParsedDocumentResponse
    validated_docx = ParsedDocumentResponse(**data_docx)
    assert validated_docx.file_type == "docx"

    # 2. Upload file PPTX
    with open(PPTX_SAMPLE, "rb") as f:
        res_pptx = client.post(
            "/api/v1/ingest/parse-document",
            files={"file": (PPTX_SAMPLE.name, f, "application/vnd.openxmlformats-officedocument.presentationml.presentation")}
        )
    assert res_pptx.status_code == 200
    data_pptx = res_pptx.json()
    assert data_pptx["filename"] == PPTX_SAMPLE.name
    assert data_pptx["file_type"] == "pptx"
    assert data_pptx["total_slides"] > 0
    validated_pptx = ParsedDocumentResponse(**data_pptx)
    assert validated_pptx.file_type == "pptx"


def test_ingest_api_invalid_extension_and_empty_file():
    """
    Test Case 5: Kiểm tra chốt chặn lỗi 400 khi tải lên định dạng không hỗ trợ (.txt) hoặc file rỗng (0 bytes).
    """
    # 1. File sai định dạng (.txt)
    res_invalid = client.post(
        "/api/v1/ingest/parse-document",
        files={"file": ("bai_giang.txt", b"Noi dung text", "text/plain")}
    )
    assert res_invalid.status_code == 400

    # 2. File đúng đuôi .docx nhưng rỗng (0 bytes)
    res_empty = client.post(
        "/api/v1/ingest/parse-document",
        files={"file": ("giao_an_rong.docx", b"", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    )
    assert res_empty.status_code == 400


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
```

---

## 📊 V. KẾT QUẢ KIỂM THỬ TỰ ĐỘNG CHỐT SỔ (TERMINAL OUTPUT)

Chạy bộ test kiểm thử 5 kịch bản với `pytest`:
```bash
/Users/nguyennhan18/Documents/Lesson-Plan-Generator/project/venv/bin/python /Users/nguyennhan18/Documents/Lesson-Plan-Generator/project/test/test_day3_parsers.py
```

**Kết quả màn hình thực tế:**
```text
============================= test session starts ==============================
platform darwin -- Python 3.13.7, pytest-9.1.1, pluggy-1.6.0 -- /Users/nguyennhan18/Documents/Lesson-Plan-Generator/project/venv/bin/python
rootdir: /Users/nguyennhan18/Documents/Lesson-Plan-Generator
plugins: anyio-4.14.2
collected 5 items                                                              

project/test/test_day3_parsers.py::test_clean_text PASSED
project/test/test_day3_parsers.py::test_parse_docx_real_file 
[DOCX] Tiêu đề: BÀI 3: CẤP SỐ CỘNG
[DOCX] Số đoạn văn: 31 | Số bảng: 4
PASSED
project/test/test_day3_parsers.py::test_parse_pptx_real_file 
[PPTX] Tiêu đề: MÔN TOÁN HỌC - LỚP 11
[PPTX] Tổng số slide: 8
PASSED
project/test/test_day3_parsers.py::test_ingest_api_upload_docx_and_pptx PASSED
project/test/test_day3_parsers.py::test_ingest_api_invalid_extension_and_empty_file PASSED

========================= 5 passed, 1 warning in 0.06s =========================
```

---

## 🎯 VI. KẾ HOẠCH BẮT ĐẦU NGÀY 4 (MODULE PHÂN LOẠI HỌC LỰC LỚP TỪ BẢNG ĐIỂM)

**Mục tiêu Ngày 4:** Xây dựng bộ phân tích thống kê bảng điểm học sinh để tự động gán nhãn trình độ lớp (`BASIC`, `STANDARD`, `ADVANCED`) (`project/app/services/grade_classifier.py`)
* **Task 4.1 (Sáng):** Viết module `project/app/services/grade_classifier.py` đọc file Excel/CSV bảng điểm lớp học.
* **Task 4.2 (Sáng):** Xây dựng thuật toán thống kê: Tính Điểm trung bình ($\mu$), Độ lệch chuẩn ($\sigma$), Tỉ lệ điểm dưới trung bình ($< 5.0$) và Tỉ lệ điểm Giỏi ($\ge 8.0$).
* **Task 4.3 (Chiều):** Hàm gán nhãn: Tự động kết luận trình độ lớp (`basic`, `standard`, `advanced`) và sinh gợi ý trọng tâm bài dạy (`target_outcome`).
* **Task 4.4 (Chiều):** Tích hợp API phân loại học lực vào `ingest_router` trong `main.py`.
* **Task 4.5 (Cuối ngày):** Chạy kiểm thử với các bảng điểm mẫu giả lập và nghiệm thu DoD Ngày 4.
