"""Resource budgets are checked in the same killable process as parsing."""
import base64
import io
import os
from pathlib import PurePosixPath
import stat
import zipfile
from lxml import etree  # type: ignore[attr-defined]  # pyright: ignore[reportAttributeAccessIssue]
from lessonai.core.jobs import JobError

MAX_FILE = 12 * 1024 * 1024
MAX_UNPACKED = 60 * 1024 * 1024
MAX_ENTRIES = 3000


def inspect_office(content, extension):
    if not content.startswith(b"PK\x03\x04"):
        raise JobError("upload_format", "Tệp không phải gói Office hợp lệ")
    required = {".docx": "word/document.xml", ".pptx": "ppt/presentation.xml", ".xlsx": "xl/workbook.xml", ".xlsm": "xl/workbook.xml"}[extension]
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        entries = archive.infolist()
        if len(entries) > MAX_ENTRIES or required not in archive.namelist():
            raise JobError("upload_structure", "Cấu trúc Office không hợp lệ hoặc quá nhiều thành phần")
        total = 0
        for info in entries:
            path = PurePosixPath(info.filename)
            if path.is_absolute() or ".." in path.parts or "\\" in info.filename or info.flag_bits & 1 or stat.S_ISLNK(info.external_attr >> 16):
                raise JobError("upload_structure", "Thành phần nén không được phép")
            if info.file_size > MAX_FILE or info.file_size > max(info.compress_size * 200, 1024*1024):
                raise JobError("upload_limit", "Thành phần giải nén vượt giới hạn")
            with archive.open(info) as stream:
                size = 0
                while chunk := stream.read(65536):
                    size += len(chunk); total += len(chunk)
                    if size > MAX_FILE or total > MAX_UNPACKED:
                        raise JobError("upload_limit", "Tổng dữ liệu giải nén vượt giới hạn")
        for name in archive.namelist():
            if name.startswith("xl/worksheets/") and name.endswith(".xml"):
                # Bound sparse sheets too; metadata dimension alone is not trusted.
                raw = archive.read(name)
                if raw.count(b"<c ") > 100000 or raw.count(b"<row ") > 10000:
                    raise JobError("upload_limit", "Bảng tính vượt giới hạn số ô/hàng")
    return True


def office_assets(content, extension):
    """Preserve original equations/media; report unsupported semantic conversion."""
    blocks, assets, warnings = [], [], []
    prefix = "word/" if extension == ".docx" else "ppt/"
    parser = etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False)
    ns = {"m": "http://schemas.openxmlformats.org/officeDocument/2006/math"}
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        for name in archive.namelist():
            if name.startswith(prefix+"media/"):
                raw = archive.read(name)
                assets.append({"source_part": name, "sha256": __import__('hashlib').sha256(raw).hexdigest(), "data_base64": base64.b64encode(raw).decode()})
            elif name.startswith(prefix) and name.endswith(".xml"):
                xml = etree.fromstring(archive.read(name), parser)
                for index, equation in enumerate(xml.findall(".//m:oMath", ns)):
                    block = {"type": "equation_source", "source_part": name, "source_index": index,
                             "format": "omml", "xml": etree.tostring(equation, encoding="unicode"), "status": "needs_review"}
                    from lessonai.services.office_math import omml_to_latex
                    try:
                        block["latex_candidate"] = omml_to_latex(equation)
                        block["conversion_status"] = "converted_needs_review"
                    except ValueError as error:
                        block["conversion_status"] = "unsupported"
                        block["conversion_error"] = str(error)
                    blocks.append(block)
            if name.startswith(prefix+"embeddings/"):
                assets.append({"source_part": name, "format": "embedded_object", "data_base64": base64.b64encode(archive.read(name)).decode()})
                warnings.append({"source_part": name, "code": "embedded_object_unconverted", "message": "Giữ đối tượng gốc; chưa chuyển đổi MathType/OLE"})
    if blocks:
        warnings.append({"code": "omml_preserved", "message": "Công thức native được giữ trong khối nguồn; chưa chứng nhận chuyển đổi sang LaTeX hoặc trích xuất đầy đủ."})
    if assets:
        warnings.append({"code": "assets_preserved", "message": "Giữ asset gốc; cần đối chiếu vị trí và ý nghĩa với tài liệu."})
    return blocks, assets, warnings


def execute(operation, payload):
    content, filename = payload["content"], payload["filename"]
    extension = os.path.splitext(filename)[1].lower()
    if not content or len(content) > MAX_FILE:
        raise JobError("upload_limit", "Tệp rỗng hoặc vượt 12 MiB")
    if extension != ".csv":
        inspect_office(content, extension)
    if operation == "ingest.grades":
        if extension == ".csv" and (content.count(b"\n") > 10000 or any(len(line) > 20000 for line in content.splitlines())):
            raise JobError("upload_limit", "CSV vượt giới hạn hàng/độ dài")
        from lessonai.services.analytics import classify_grade_sheet
        return {"filename": filename, **classify_grade_sheet(content, filename=filename).to_dict()}
    if operation == "ingest.document":
        from lessonai.parsers.docx_parser import parse_docx
        from lessonai.parsers.pptx_parser import parse_pptx
        result = (parse_docx if extension == ".docx" else parse_pptx)(content)
        if result.get("total_slides", 0) > 300 or result.get("total_paragraphs", 0) > 10000:
            raise JobError("upload_limit", "Tài liệu vượt giới hạn trang/đoạn")
        if len(result.get("raw_text", "")) > 2_000_000:
            raise JobError("upload_limit", "Nội dung tài liệu quá dài")
        blocks, assets, warnings = office_assets(content, extension)
        result["blocks"] = (result.get("blocks") or []) + blocks
        from lessonai.services.artifact_provenance import read_office_provenance
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            provenance = read_office_provenance(archive)
        if provenance:
            result["provenance"] = provenance
            warnings.append({"code": "provenance_unverified", "message": "Giữ metadata nhập; cần đối chiếu với nguồn, không phục hồi trạng thái đã duyệt."})
        return {"filename": filename, **result, "assets": assets, "warnings": warnings,
                "extraction_status": "needs_review" if warnings else "text_extracted"}
    raise JobError("job_unsupported", "Tác vụ nhập chưa được hỗ trợ")
