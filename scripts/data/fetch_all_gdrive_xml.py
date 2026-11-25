#!/usr/bin/env python3
"""
Trích xuất toàn bộ nội dung <pdf2xml> từ chế độ Xem trước (Preview) của 32 file PDF
Toán 12 Kết nối tri thức (CT GDPT 2018) trên Google Drive.
"""
import concurrent.futures
import gzip
import json
import os
import re
import ssl
import time
import urllib.request
from pathlib import Path

SSL_CTX = ssl._create_unverified_context()

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
OUT_DIR = RAW_DIR / "slides_kntt12" / "xml"
OUT_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
}


def fetch_bytes(url: str, timeout: int = 25) -> bytes:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as resp:
        return resp.read()


def process_one(idx: int, item: dict) -> dict:
    fid = item["file_id"]
    fname = item["filename"]
    xml_path = OUT_DIR / f"{idx:02d}_{fid}.xml"

    if xml_path.exists() and xml_path.stat().st_size > 500:
        return {"index": idx, "file_id": fid, "filename": fname, "status": "cached", "size": xml_path.stat().st_size}

    for attempt in range(3):
        try:
            view_url = f"https://drive.google.com/file/d/{fid}/view"
            view_html = fetch_bytes(view_url).decode("utf-8", errors="ignore")

            m = re.search(r'"(https://drive\.google\.com/viewer/upload\?ds\\u003d[^"]+)"', view_html)
            if not m:
                raise RuntimeError("viewer/upload URL not found in view page")

            upload_url = m.group(1).replace(r"\u003d", "=").replace(r"\u0026", "&")
            upload_raw = fetch_bytes(upload_url).decode("utf-8", errors="ignore")
            upload_json = json.loads(upload_raw.lstrip(")]}'\n"))

            press_rel = upload_json.get("press")
            if not press_rel:
                raise RuntimeError("press endpoint missing in upload_json")

            press_url = f"https://drive.google.com/viewer/{press_rel}"
            press_bytes = fetch_bytes(press_url)

            # Decompress if gzipped
            if press_bytes[:2] == b"\x1f\x8b":
                xml_str = gzip.decompress(press_bytes).decode("utf-8", errors="ignore")
            else:
                xml_str = press_bytes.decode("utf-8", errors="ignore")

            xml_path.write_text(xml_str, encoding="utf-8")
            return {"index": idx, "file_id": fid, "filename": fname, "status": "ok", "size": len(xml_str)}
        except Exception as e:
            if attempt == 2:
                return {"index": idx, "file_id": fid, "filename": fname, "status": "error", "error": str(e)}
            time.sleep(1.5 * (attempt + 1))


def main():
    with open(OUT_DIR.parent / "gdrive_files.json", "r", encoding="utf-8") as f:
        files = json.load(f)

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futs = [pool.submit(process_one, idx, item) for idx, item in enumerate(files, 1)]
        for fut in concurrent.futures.as_completed(futs):
            res = fut.result()
            results.append(res)
            print(f"[{res['index']:02d}/32] {res['status'].upper()} | {res['filename']} ({res.get('size', res.get('error'))})")

    results.sort(key=lambda x: x["index"])
    ok_count = sum(1 for r in results if r["status"] in {"ok", "cached"})
    print(f"\nCompleted: {ok_count}/{len(files)} files extracted successfully.")
    with open(OUT_DIR.parent / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
