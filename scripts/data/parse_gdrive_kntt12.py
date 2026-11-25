#!/usr/bin/env python3
"""
Bộ phân tích cú pháp <pdf2xml> từ 32 bài giảng PowerPoint Toán 12 Kết nối tri thức (CT GDPT 2018)
thành kho dữ liệu Pedagogical RAG có cấu trúc (slides_kntt12.jsonl & decks_kntt12.json).
"""
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

BASE_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "slides_kntt12"
XML_DIR = BASE_DIR / "xml"
SLIDES_OUT = BASE_DIR / "slides_kntt12.jsonl"
DECKS_OUT = BASE_DIR / "decks_kntt12.json"


def map_filename_to_metadata(filename: str) -> Dict[str, Any]:
    """Ánh xạ tên file sang Chương, Bài và lesson_id chuẩn CT GDPT 2018."""
    ch_match = re.search(r"Chương\s*(\d+|[IVX]+)", filename, flags=re.I)
    bai_match = re.search(r"Bài\s*(\d+)", filename, flags=re.I)

    roman_map = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6}
    chapter = None
    if ch_match:
        raw_c = ch_match.group(1).upper()
        chapter = roman_map.get(raw_c) or (int(raw_c) if raw_c.isdigit() else None)

    lesson_num = int(bai_match.group(1)) if bai_match else None

    # Map Bài 1..19 của SGK Toán 12 Kết nối tri thức sang lesson_id chuẩn
    kntt_lesson_map = {
        1: ("M12-C1-B1", 1, "Tính đơn điệu và cực trị của hàm số"),
        2: ("M12-C1-B2", 1, "Giá trị lớn nhất và giá trị nhỏ nhất của hàm số"),
        3: ("M12-C1-B3", 1, "Đường tiệm cận của đồ thị hàm số"),
        4: ("M12-C1-B4", 1, "Khảo sát sự biến thiên và vẽ đồ thị của hàm số"),
        5: ("M12-C1-B5", 1, "Ứng dụng đạo hàm để giải quyết một số vấn đề liên quan đến thực tiễn"),
        6: ("M12-C2-B1", 2, "Vectơ trong không gian"),
        7: ("M12-C2-B2", 2, "Hệ trục toạ độ trong không gian"),
        8: ("M12-C2-B2", 2, "Biểu thức tọa độ của các phép toán vectơ"),
        9: ("M12-C3-B1", 3, "Khoảng biến thiên và khoảng tứ phân vị của mẫu số liệu ghép nhóm"),
        10: ("M12-C3-B2", 3, "Phương sai và độ lệch chuẩn của mẫu số liệu ghép nhóm"),
        11: ("M12-C4-B1", 4, "Nguyên hàm"),
        12: ("M12-C4-B2", 4, "Tích phân"),
        13: ("M12-C4-B3", 4, "Ứng dụng hình học của tích phân"),
        14: ("M12-C5-B1", 5, "Phương trình mặt phẳng"),
        15: ("M12-C5-B2", 5, "Phương trình đường thẳng trong không gian"),
        16: ("M12-C5-B3", 5, "Công thức tính góc trong không gian"),
        17: ("M12-C5-B3", 5, "Phương trình mặt cầu"),
        18: ("M12-C6-B1", 6, "Xác suất có điều kiện"),
        19: ("M12-C6-B2", 6, "Công thức xác suất toàn phần và công thức Bayes"),
    }

    if lesson_num in kntt_lesson_map:
        lid, ch, title = kntt_lesson_map[lesson_num]
        return {
            "lesson_id": lid,
            "chapter": ch,
            "kntt_lesson_number": lesson_num,
            "lesson_title": f"Bài {lesson_num}: {title}",
            "category": "core_lesson",
        }

    if "Bài tập cuối chương" in filename and chapter:
        return {
            "lesson_id": f"M12-C{chapter}-BT",
            "chapter": chapter,
            "kntt_lesson_number": None,
            "lesson_title": f"Bài tập cuối chương {chapter}",
            "category": "chapter_review",
        }

    if any(k in filename for k in ["HĐTH", "HĐTN", "GeoGebra", "3D"]):
        return {
            "lesson_id": "M12-HDTN",
            "chapter": 0,
            "kntt_lesson_number": None,
            "lesson_title": filename.replace(".pdf", ""),
            "category": "experiential_activity",
        }

    return {
        "lesson_id": "M12-ONTAP",
        "chapter": 0,
        "kntt_lesson_number": None,
        "lesson_title": filename.replace(".pdf", ""),
        "category": "year_review",
    }


def merge_blocks_with_coords(page_elem: ET.Element) -> Tuple[str, List[str], str]:
    """
    Ghép các block văn bản từ một trang <page> theo toạ độ 2D (t, l),
    đồng thời hàn gắn các chỉ số trên/dưới bị tách block (VD: x + 2 ở cao độ nhỏ -> x^2).
    """
    raw_items = []
    for b in page_elem.findall("block"):
        l = int(b.attrib.get("l", 0))
        t = int(b.attrib.get("t", 0))
        w = int(b.attrib.get("w", 0))
        h = int(b.attrib.get("h", 0))
        texts = [tx.text.strip() for tx in b.findall("text") if tx.text and tx.text.strip()]
        if not texts:
            continue
        txt = " ".join(texts)
        raw_items.append({"l": l, "t": t, "w": w, "h": h, "text": txt})

    if not raw_items:
        return "", [], "SINGLE_COLUMN"

    # Kiểm tra bố cục 2 cột (nhiều block ở nửa trái l < 320 và nửa phải l >= 350 cùng cao độ)
    left_blocks = [x for x in raw_items if x["l"] < 320 and x["t"] > 75]
    right_blocks = [x for x in raw_items if x["l"] >= 350 and x["t"] > 75]
    layout_hint = "TWO_COLUMN" if (len(left_blocks) >= 2 and len(right_blocks) >= 2) else "SINGLE_COLUMN"

    # Sắp xếp từ trên xuống dưới (nhóm theo dòng t cách nhau <= 14px), từ trái sang phải
    raw_items.sort(key=lambda x: (x["t"] // 14, x["l"]))

    # Hàn gắn các mảnh công thức nhỏ (h <= 16) nằm ngay cạnh dòng chính
    merged_lines: List[str] = []
    for item in raw_items:
        txt = item["text"]
        if merged_lines and item["h"] <= 16 and len(txt) <= 12 and re.match(r"^[0-9nmkxy+\-=(),]+$", txt):
            prev = merged_lines[-1]
            # Nếu dòng trước kết thúc bằng biến và mảnh hiện tại là số mũ/chỉ số
            if re.search(r"[xytabnmkf)]$", prev) and re.match(r"^[0-9nmk]+(\b|[\s+\-=])", txt):
                merged_lines[-1] = f"{prev}^{txt}"
                continue
        merged_lines.append(txt)

    # Chuẩn hóa ký hiệu toán học phổ biến
    clean_lines: List[str] = []
    for line in merged_lines:
        line = re.sub(r"\s+", " ", line).strip()
        if line:
            clean_lines.append(line)

    title = clean_lines[0] if clean_lines else ""
    body = clean_lines[1:] if len(clean_lines) > 1 else []
    return title, body, layout_hint


def classify_slide_pedagogy(title: str, body: List[str], slide_no: int) -> Tuple[str, str, str]:
    """Phân loại activity_type, slide_role và layout_hint chuẩn CV 5512."""
    full_text = f"{title}\n" + "\n".join(body)
    lower = full_text.lower()

    if slide_no == 1 or "chào mừng các em" in lower:
        return "khoi_dong", "welcome", "TITLE_ONLY"

    if any(k in lower for k in ["khởi động", "tình huống mở đầu", "bài toán mở đầu"]):
        return "khoi_dong", "warm_up", "IMAGE_TEXT"

    if re.search(r"(?:^|\n)\s*[a-d]\.\s+", full_text, flags=re.I) and ("câu " in lower or "trắc nghiệm" in lower):
        return "luyen_tap", "quiz_mcq", "QUIZ_OPTION"

    if any(k in lower for k in ["ví dụ ", "luyện tập ", "bài tập", "giải:", "lời giải"]):
        if "vận dụng" in lower or "thực tiễn" in lower or "thực tế" in lower:
            return "van_dung", "application_problem", "TWO_COLUMN"
        return "luyen_tap", "worked_example", "TWO_COLUMN"

    if any(k in lower for k in ["ghi nhớ", "định nghĩa", "định lí", "công thức", "tổng quát", "kết luận"]):
        return "hinh_thanh_kien_thuc", "concept_definition", "CONCEPT_HIGHLIGHT"

    if any(k in lower for k in ["hđ1", "hđ2", "hđ3", "hđ4", "hoạt động", "khám phá", "chú ý", "nhận xét"]):
        return "hinh_thanh_kien_thuc", "guided_discovery", "SINGLE_COLUMN"

    if any(k in lower for k in ["vận dụng", "thử thách", "củng cố", "hướng dẫn về nhà", "tổng kết"]):
        return "van_dung", "summary_consolidation", "SINGLE_COLUMN"

    return "hinh_thanh_kien_thuc", "concept_explanation", "SINGLE_COLUMN"


def main():
    manifest_path = BASE_DIR / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    all_slides: List[Dict[str, Any]] = []
    decks_summary: List[Dict[str, Any]] = []

    for entry in manifest:
        if entry.get("status") not in {"ok", "cached"}:
            continue
        idx = entry["index"]
        fid = entry["file_id"]
        fname = entry["filename"]
        xml_path = XML_DIR / f"{idx:02d}_{fid}.xml"
        if not xml_path.exists():
            continue

        meta = map_filename_to_metadata(fname)
        xml_text = xml_path.read_text(encoding="utf-8", errors="ignore")
        try:
            root = ET.fromstring(xml_text)
        except Exception as e:
            print(f"XML parse error in {fname}: {e}")
            continue

        pages = root.findall("page")
        deck_slides = []
        activity_counts = {"khoi_dong": 0, "hinh_thanh_kien_thuc": 0, "luyen_tap": 0, "van_dung": 0}

        for s_idx, page in enumerate(pages, start=1):
            title, body, coord_layout = merge_blocks_with_coords(page)
            if not title and not body:
                continue
            act_type, role, ped_layout = classify_slide_pedagogy(title, body, s_idx)
            final_layout = ped_layout if ped_layout != "SINGLE_COLUMN" else coord_layout
            activity_counts[act_type] = activity_counts.get(act_type, 0) + 1

            slide_record = {
                "doc_id": f"KNTT12-{idx:02d}",
                "file_id": fid,
                "source_file": fname,
                "grade": 12,
                "curriculum": "GDPT_2018_KNTT",
                "lesson_id": meta["lesson_id"],
                "chapter": meta["chapter"],
                "kntt_lesson_number": meta["kntt_lesson_number"],
                "lesson_title": meta["lesson_title"],
                "category": meta["category"],
                "slide_no": s_idx,
                "total_slides_in_deck": len(pages),
                "title": title,
                "bullet_points": body,
                "full_text": "\n".join([title, *body]).strip(),
                "activity_type": act_type,
                "slide_role": role,
                "layout_hint": final_layout,
            }
            all_slides.append(slide_record)
            deck_slides.append(slide_record)

        decks_summary.append({
            "doc_id": f"KNTT12-{idx:02d}",
            "file_id": fid,
            "source_file": fname,
            "lesson_id": meta["lesson_id"],
            "chapter": meta["chapter"],
            "kntt_lesson_number": meta["kntt_lesson_number"],
            "lesson_title": meta["lesson_title"],
            "category": meta["category"],
            "total_slides": len(pages),
            "non_empty_slides": len(deck_slides),
            "activity_distribution": activity_counts,
            "sample_titles": [s["title"] for s in deck_slides[:10] if s["title"]],
        })

    with open(SLIDES_OUT, "w", encoding="utf-8") as f:
        for s in all_slides:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    with open(DECKS_OUT, "w", encoding="utf-8") as f:
        json.dump(decks_summary, f, ensure_ascii=False, indent=2)

    print(f"Parsed {len(decks_summary)} decks -> {len(all_slides)} slides saved to {SLIDES_OUT}")


if __name__ == "__main__":
    main()
