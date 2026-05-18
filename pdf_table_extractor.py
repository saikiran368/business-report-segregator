"""
pdf_table_extractor.py
Extracts tables AND snapshots from a PDF.
Returns rich table objects with data + image crop.
"""

import pdfplumber
import fitz
from PIL import Image
import io


def extract_all_tables(pdf_path: str) -> list:
    """
    Extracts all tables from a PDF with:
    - Raw data (headers + rows)
    - Visual snapshot of the table region
    - Page number, position

    Returns list of dicts.
    """
    results = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            table_objs = page.find_tables()
            table_data = page.extract_tables()

            for idx, (tobj, tdata) in enumerate(zip(table_objs, table_data), start=1):
                if not tdata or len(tdata) < 1:
                    continue

                cleaned = [
                    [str(c).strip() if c is not None else "" for c in row]
                    for row in tdata
                ]

                # Snapshot
                snapshot = _snapshot_table(
                    pdf_path, page_num - 1, tobj.bbox,
                    page.width, page.height
                )

                results.append({
                    "page":        page_num,
                    "table_index": idx,
                    "bbox":        tobj.bbox,
                    "all_rows":    cleaned,       # ALL rows including header
                    "headers":     cleaned[0] if cleaned else [],
                    "rows":        cleaned[1:] if len(cleaned) > 1 else [],
                    "total_rows":  len(cleaned) - 1,
                    "total_cols":  len(cleaned[0]) if cleaned else 0,
                    "snapshot":    snapshot,
                    "source":      "pdf",
                })

    return results


def _snapshot_table(pdf_path, page_idx, bbox, page_w, page_h, dpi=150):
    doc  = fitz.open(pdf_path)
    page = doc[page_idx]
    zoom = dpi / 72
    mat  = fitz.Matrix(zoom, zoom)
    pix  = page.get_pixmap(matrix=mat)
    img  = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    x0, top, x1, bottom = bbox
    sx = pix.width  / page_w
    sy = pix.height / page_h

    px0 = max(0, int(x0 * sx) - 8)
    py0 = max(0, int(top * sy) - 8)
    px1 = min(pix.width,  int(x1 * sx) + 8)
    py1 = min(pix.height, int(bottom * sy) + 8)

    doc.close()
    return img.crop((px0, py0, px1, py1))
