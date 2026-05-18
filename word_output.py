"""
word_output.py
Builds the output Word document.
Structure per table:
  [Heading]   Table title (from headers)
  [Summary]   AI-generated bullet points (data from table)
  [Snapshot]  Visual screenshot of the table from PDF
  [Divider]
"""

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from PIL import Image
import io


def build_word_report(
    tables: list,
    pdf_filename: str,
    ref_filename: str = None,
) -> bytes:
    """
    tables: list of dicts, each with:
        - headers, rows, snapshot (PIL Image)
        - summary (list of bullet strings)
        - match_label (str)
        - match_score (float)
        - ref_match (dict or None)
    """
    doc = Document()

    # ── Page margins ──────────────────────────────────────────────────────────
    for sec in doc.sections:
        sec.top_margin    = Inches(0.75)
        sec.bottom_margin = Inches(0.75)
        sec.left_margin   = Inches(1.0)
        sec.right_margin  = Inches(1.0)

    # ── Title block ───────────────────────────────────────────────────────────
    title = doc.add_heading("Table Extraction Report", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    sub = doc.add_paragraph(f"Source: {pdf_filename}")
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub.runs[0].font.size      = Pt(10)
    sub.runs[0].font.color.rgb = RGBColor(0x70, 0x70, 0x70)

    if ref_filename:
        ref_note = doc.add_paragraph(f"Reference style: {ref_filename}")
        ref_note.alignment = WD_ALIGN_PARAGRAPH.CENTER
        ref_note.runs[0].font.size      = Pt(9)
        ref_note.runs[0].font.color.rgb = RGBColor(0x4C, 0xAF, 0x50)
        ref_note.runs[0].bold = True

    doc.add_paragraph()

    intro_text = (
        f"This report contains {len(tables)} table(s) extracted from the PDF. "
        "Each section includes an AI-generated summary (using real data from the table) "
        "followed by a visual snapshot of the table."
    )
    intro = doc.add_paragraph(intro_text)
    intro.runs[0].font.size      = Pt(10)
    intro.runs[0].font.color.rgb = RGBColor(0x44, 0x44, 0x44)
    doc.add_paragraph()

    # ── One section per table ─────────────────────────────────────────────────
    for i, table in enumerate(tables, start=1):
        label    = table.get("match_label") or f"Table {i}"
        summary  = table.get("summary", ["No summary available."])
        snapshot = table.get("snapshot")
        headers  = table.get("headers", [])
        n_rows   = table.get("total_rows", 0)
        n_cols   = table.get("total_cols", 0)
        score    = table.get("match_score", 0)
        has_ref  = table.get("ref_match") is not None

        # ── Section heading ───────────────────────────────────────────────────
        heading_text = f"Table {i}  |  {label}"
        h = doc.add_heading(heading_text, level=1)
        h.runs[0].font.color.rgb = RGBColor(0x1F, 0x49, 0x7D)

        # Metadata line
        meta_parts = [f"{n_rows} rows × {n_cols} cols"]
        if has_ref:
            meta_parts.append(f"Reference match: {int(score * 100)}%")
        meta_p = doc.add_paragraph("  |  ".join(meta_parts))
        meta_p.runs[0].font.size      = Pt(9)
        meta_p.runs[0].font.color.rgb = RGBColor(0x88, 0x88, 0x88)
        meta_p.runs[0].italic         = True

        doc.add_paragraph()

        # ── Summary label ─────────────────────────────────────────────────────
        lbl_p = doc.add_paragraph()
        lbl_r = lbl_p.add_run("Summary")
        lbl_r.bold           = True
        lbl_r.font.size      = Pt(11)
        lbl_r.font.color.rgb = RGBColor(0x2E, 0x74, 0xB5)

        # ── Bullet points ─────────────────────────────────────────────────────
        for bullet in summary:
            p = doc.add_paragraph(style="List Bullet")
            r = p.add_run(bullet)
            r.font.size = Pt(10)

        doc.add_paragraph()

        # ── Snapshot label ────────────────────────────────────────────────────
        snap_p = doc.add_paragraph()
        snap_r = snap_p.add_run("Table Snapshot")
        snap_r.bold           = True
        snap_r.font.size      = Pt(11)
        snap_r.font.color.rgb = RGBColor(0x2E, 0x74, 0xB5)

        # ── Snapshot image ────────────────────────────────────────────────────
        if snapshot:
            buf = io.BytesIO()
            snapshot.save(buf, format="PNG")
            buf.seek(0)
            img_w, img_h = snapshot.size
            max_w  = 6.0
            aspect = img_h / max(img_w, 1)
            width  = min(max_w, img_w / 96)
            doc.add_picture(buf, width=Inches(width))
        else:
            ph = doc.add_paragraph("[Table snapshot not available]")
            ph.runs[0].font.italic    = True
            ph.runs[0].font.color.rgb = RGBColor(0xAA, 0xAA, 0xAA)

        # ── Divider ───────────────────────────────────────────────────────────
        doc.add_paragraph()
        _add_rule(doc)
        doc.add_paragraph()

    # ── Footer ────────────────────────────────────────────────────────────────
    foot = doc.add_paragraph(
        "Generated by PDF Table Extractor  —  Powered by Amazon Bedrock (Claude)"
    )
    foot.alignment            = WD_ALIGN_PARAGRAPH.CENTER
    foot.runs[0].font.size    = Pt(8)
    foot.runs[0].font.color.rgb = RGBColor(0xAA, 0xAA, 0xAA)

    out = io.BytesIO()
    doc.save(out)
    out.seek(0)
    return out.getvalue()


def _add_rule(doc):
    p   = doc.add_paragraph()
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bot  = OxmlElement("w:bottom")
    bot.set(qn("w:val"),   "single")
    bot.set(qn("w:sz"),    "6")
    bot.set(qn("w:space"), "1")
    bot.set(qn("w:color"), "CCCCCC")
    pBdr.append(bot)
    pPr.append(pBdr)
