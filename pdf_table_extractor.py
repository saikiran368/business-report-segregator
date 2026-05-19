"""
pdf_table_extractor.py
Extracts tables AND snapshots from a PDF.
- snapshot      : tight crop of table only (used in Word report)
- snapshot_with_title : extended crop including area above table (used for AI header ID)
"""

import pdfplumber
import fitz
from PIL import Image

SNAPSHOT_DPI     = 150
MAX_WORD_WIDTH   = 6.0
TITLE_LOOKAHEAD  = 70   # pts above table top to include for title detection


def extract_all_tables(pdf_path: str) -> list:
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

                x0, top, x1, bottom = tobj.bbox

                # Tight snapshot for Word report
                snapshot = _crop(pdf_path, page_num - 1,
                                 x0, top, x1, bottom,
                                 page.width, page.height,
                                 pad_top=8)

                # Extended snapshot (includes title area above) for Claude Vision
                title_top = max(0, top - TITLE_LOOKAHEAD)
                snapshot_with_title = _crop(pdf_path, page_num - 1,
                                            x0, title_top, x1, bottom,
                                            page.width, page.height,
                                            pad_top=4)

                results.append({
                    "page":                page_num,
                    "table_index":         idx,
                    "bbox":                tobj.bbox,
                    "all_rows":            cleaned,
                    "headers":             cleaned[0] if cleaned else [],
                    "rows":                cleaned[1:] if len(cleaned) > 1 else [],
                    "total_rows":          len(cleaned) - 1,
                    "total_cols":          len(cleaned[0]) if cleaned else 0,
                    "snapshot":            snapshot,
                    "snapshot_with_title": snapshot_with_title,
                    "source":              "pdf",
                })

    return results


def _crop(pdf_path, page_idx, x0, top, x1, bottom, page_w, page_h, pad_top=8):
    """Renders a region of the PDF page as a PIL image."""
    zoom = SNAPSHOT_DPI / 72
    doc  = fitz.open(pdf_path)
    page = doc[page_idx]
    pix  = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    img  = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    doc.close()

    sx = pix.width  / page_w
    sy = pix.height / page_h

    px0 = max(0, int(x0 * sx) - 8)
    py0 = max(0, int(top * sy) - pad_top)
    px1 = min(pix.width,  int(x1 * sx) + 8)
    py1 = min(pix.height, int(bottom * sy) + 8)

    return img.crop((px0, py0, px1, py1))


def snapshot_word_width(snapshot) -> float:
    """Returns Word insertion width in inches, capped at MAX_WORD_WIDTH."""
    if snapshot is None:
        return 0.0
    return min(MAX_WORD_WIDTH, snapshot.size[0] / SNAPSHOT_DPI)
