# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
import shutil
from copy import deepcopy
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from docx.table import Table
from docx.text.paragraph import Paragraph
from PIL import Image


SCRIPT_DIR = Path(__file__).resolve().parent
CODE_DIR = SCRIPT_DIR.parent
FIG_DIR = CODE_DIR / "输出结果" / "figures"
FORMULA_DIR = FIG_DIR / "formulas"

SOURCE_DOCX = Path(r"C:\Users\22672\Desktop\政府采购异常低价风险识别与监管研究_最终版.docx")
DESKTOP_OUT = Path(r"C:\Users\22672\Desktop\政府采购异常低价风险识别与监管研究_图表公式优化版.docx")
CODE_OUT = SCRIPT_DIR / DESKTOP_OUT.name
AUDIT_OUT = SCRIPT_DIR / "caption_audit_visual_refresh.json"

TABLE_CAPTION_RE = re.compile(r"^表\s*(\d+)\s*(.*)$")
FIGURE_CAPTION_RE = re.compile(r"^图\s*(\d+)\s*(.*)$")
FORMULA_RE = re.compile(r"^公式[（(]\s*(\d+)\s*[）)]$")
TABLE_REF_RE = re.compile(r"表\s*(\d+)")

INK = RGBColor(23, 32, 51)
MUTED = RGBColor(78, 88, 102)
HEADER_FILL = "0F2E4D"
HEADER_TEXT = "FFFFFF"
ROW_FILL = "F6FAFD"
BORDER = "D6DEE8"

FORMULAS = {
    1: r"$R_i=\frac{M_i}{B_i},\quad G_i=1-R_i$",
    2: r"$T_{g,\alpha}=Q_{\alpha}(R_i\mid c_i=g),\quad \alpha\in\{0.05,0.10\}$",
    3: r"$T_{g,IQR}=Q_{1,g}-1.5\left(Q_{3,g}-Q_{1,g}\right)$",
    4: r"$Z_i=\frac{R_i-\mathrm{Median}_g}{1.4826\times \mathrm{MAD}_g}$",
    5: r"$A_i=I_{i,65}+I_{i,10\%}+I_{i,5\%}+I_{i,IQR}+I_{i,Z}$",
    6: r"$E_i=0.30\,IF_i+0.25\,LOF_i+0.20\,OCSVM_i+0.25\,A_i$",
}


def iter_body_blocks(doc: Document):
    for child in doc.element.body.iterchildren():
        if child.tag == qn("w:p"):
            yield Paragraph(child, doc)
        elif child.tag == qn("w:tbl"):
            yield Table(child, doc)


def block_text(block) -> str:
    return block.text.strip() if isinstance(block, Paragraph) else ""


def significant_after(blocks: list, index: int):
    for item in blocks[index + 1 :]:
        if isinstance(item, Table):
            return item
        if isinstance(item, Paragraph):
            text = item.text.strip()
            has_drawing = bool(item._p.xpath(".//w:drawing"))
            has_math = bool(item._p.xpath(".//m:oMath|.//m:oMathPara"))
            if text or has_drawing or has_math:
                return item
    return None


def significant_before(blocks: list, index: int):
    for item in reversed(blocks[:index]):
        if isinstance(item, Table):
            return item
        if isinstance(item, Paragraph):
            text = item.text.strip()
            has_drawing = bool(item._p.xpath(".//w:drawing"))
            has_math = bool(item._p.xpath(".//m:oMath|.//m:oMathPara"))
            if text or has_drawing or has_math:
                return item
    return None


def remove_paragraph(paragraph: Paragraph) -> None:
    element = paragraph._element
    element.getparent().remove(element)


def clear_paragraph(paragraph: Paragraph) -> None:
    p_pr = paragraph._p.pPr
    for child in list(paragraph._p):
        if child is not p_pr:
            paragraph._p.remove(child)


def set_paragraph_text(paragraph: Paragraph, text: str) -> None:
    clear_paragraph(paragraph)
    run = paragraph.add_run(text)
    set_run_font(run, size=10.5, bold=True)


def set_run_font(run, size: float = 10.5, bold: bool = False, color: RGBColor = INK) -> None:
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color


def style_caption(paragraph: Paragraph, keep_with_next: bool = False) -> None:
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fmt = paragraph.paragraph_format
    fmt.space_before = Pt(4)
    fmt.space_after = Pt(6)
    fmt.keep_with_next = keep_with_next
    for run in paragraph.runs:
        set_run_font(run, size=10.5, bold=True)


def set_cell_shading(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_margins(cell, top=70, start=90, bottom=70, end=90) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_mar = tc_pr.find(qn("w:tcMar"))
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for tag, value in {"top": top, "start": start, "bottom": bottom, "end": end}.items():
        node = tc_mar.find(qn(f"w:{tag}"))
        if node is None:
            node = OxmlElement(f"w:{tag}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_table_borders(table: Table, color: str = BORDER) -> None:
    tbl_pr = table._tbl.tblPr
    borders = tbl_pr.find(qn("w:tblBorders"))
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        tbl_pr.append(borders)
    for edge in ["top", "left", "bottom", "right", "insideH", "insideV"]:
        node = borders.find(qn(f"w:{edge}"))
        if node is None:
            node = OxmlElement(f"w:{edge}")
            borders.append(node)
        node.set(qn("w:val"), "single")
        node.set(qn("w:sz"), "6")
        node.set(qn("w:space"), "0")
        node.set(qn("w:color"), color)


def set_table_width(table: Table) -> None:
    tbl_pr = table._tbl.tblPr
    tbl_w = tbl_pr.find(qn("w:tblW"))
    if tbl_w is None:
        tbl_w = OxmlElement("w:tblW")
        tbl_pr.append(tbl_w)
    tbl_w.set(qn("w:w"), "5000")
    tbl_w.set(qn("w:type"), "pct")


def looks_numeric(text: str) -> bool:
    s = text.strip().replace(",", "").replace("%", "").replace("−", "-")
    if not s:
        return False
    try:
        float(s)
        return True
    except ValueError:
        return False


def style_table(table: Table) -> None:
    table.autofit = True
    set_table_width(table)
    set_table_borders(table)
    col_count = len(table.columns)
    compact = col_count >= 6 or len(table.rows) >= 10
    body_size = 7.4 if compact else 8.8
    header_size = 7.8 if compact else 8.6
    margins = {"top": 45, "start": 55, "bottom": 45, "end": 55} if compact else {}
    for r_idx, row in enumerate(table.rows):
        for c_idx, cell in enumerate(row.cells):
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            set_cell_margins(cell, **margins)
            if r_idx == 0:
                set_cell_shading(cell, HEADER_FILL)
            elif r_idx % 2 == 1:
                set_cell_shading(cell, ROW_FILL)
            else:
                set_cell_shading(cell, "FFFFFF")

            for paragraph in cell.paragraphs:
                paragraph.paragraph_format.space_before = Pt(0)
                paragraph.paragraph_format.space_after = Pt(0)
                paragraph.paragraph_format.line_spacing = 1.05
                if r_idx == 0 or c_idx > 0 and looks_numeric(cell.text):
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                else:
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
                for run in paragraph.runs:
                    set_run_font(
                        run,
                        size=header_size if r_idx == 0 else body_size,
                        bold=r_idx == 0,
                        color=RGBColor(255, 255, 255) if r_idx == 0 else INK,
                    )


def replace_table_references(paragraph: Paragraph, mapping: dict[int, int]) -> None:
    if TABLE_CAPTION_RE.match(paragraph.text.strip()):
        return
    for run in paragraph.runs:
        if run._r.xpath(".//w:drawing"):
            continue
        run.text = TABLE_REF_RE.sub(
            lambda match: f"表{mapping.get(int(match.group(1)), int(match.group(1)))}",
            run.text,
        )


def rename_and_remove_table_captions(doc: Document) -> dict:
    blocks = list(iter_body_blocks(doc))
    actual_mapping: dict[int, int] = {}
    orphan_titles: list[str] = []
    next_table_no = 1

    for idx, block in enumerate(blocks):
        if not isinstance(block, Paragraph):
            continue
        text = block.text.strip()
        match = TABLE_CAPTION_RE.match(text)
        if not match:
            continue
        old_no = int(match.group(1))
        title = match.group(2).strip()
        next_block = significant_after(blocks, idx)
        if isinstance(next_block, Table):
            actual_mapping[old_no] = next_table_no
            set_paragraph_text(block, f"表{next_table_no} {title}")
            style_caption(block, keep_with_next=True)
            next_table_no += 1
        else:
            orphan_titles.append(text)
            remove_paragraph(block)

    for paragraph in doc.paragraphs:
        replace_table_references(paragraph, actual_mapping)

    return {"table_number_mapping": actual_mapping, "removed_orphan_table_titles": orphan_titles}


def replace_figures(doc: Document) -> dict:
    blocks = list(iter_body_blocks(doc))
    replaced: list[str] = []
    missing: list[str] = []
    section = doc.sections[0]
    available_width = section.page_width - section.left_margin - section.right_margin
    max_width = min(available_width, Inches(6.25))

    for idx, block in enumerate(blocks):
        if not isinstance(block, Paragraph):
            continue
        match = FIGURE_CAPTION_RE.match(block.text.strip())
        if not match:
            continue
        fig_no = int(match.group(1))
        candidates = sorted(FIG_DIR.glob(f"Fig{fig_no:02d}_*.png"))
        candidates = [p for p in candidates if not re.match(rf"Fig{fig_no:02d}[A-Za-z]", p.stem)]
        if not candidates:
            missing.append(block.text.strip())
            continue
        image_path = candidates[0]
        image_block = significant_before(blocks, idx)
        if not isinstance(image_block, Paragraph) or not image_block._p.xpath(".//w:drawing"):
            missing.append(block.text.strip())
            continue

        with Image.open(image_path) as im:
            aspect = im.width / im.height
        if aspect < 0.85:
            width = min(max_width, Inches(4.75))
        elif aspect > 2.35:
            width = min(max_width, Inches(6.25))
        else:
            width = min(max_width, Inches(5.85))

        clear_paragraph(image_block)
        image_block.alignment = WD_ALIGN_PARAGRAPH.CENTER
        image_block.paragraph_format.space_before = Pt(4)
        image_block.paragraph_format.space_after = Pt(3)
        image_block.add_run().add_picture(str(image_path), width=width)
        style_caption(block, keep_with_next=False)
        replaced.append(f"图{fig_no}: {image_path.name}")

    return {"figures_replaced": replaced, "figures_missing": missing}


def append_formula_tabs(paragraph: Paragraph, formula_no: int, right_twips: int) -> None:
    math_nodes = [
        deepcopy(child)
        for child in list(paragraph._p)
        if child.tag in {qn("m:oMath"), qn("m:oMathPara")}
    ]
    p_pr = paragraph._p.get_or_add_pPr()
    tabs = p_pr.find(qn("w:tabs"))
    if tabs is not None:
        p_pr.remove(tabs)
    tabs = OxmlElement("w:tabs")
    center = OxmlElement("w:tab")
    center.set(qn("w:val"), "center")
    center.set(qn("w:pos"), str(right_twips // 2))
    right = OxmlElement("w:tab")
    right.set(qn("w:val"), "right")
    right.set(qn("w:pos"), str(right_twips))
    tabs.append(center)
    tabs.append(right)
    p_pr.append(tabs)

    jc = p_pr.find(qn("w:jc"))
    if jc is None:
        jc = OxmlElement("w:jc")
        p_pr.append(jc)
    jc.set(qn("w:val"), "left")

    for child in list(paragraph._p):
        if child is not p_pr:
            paragraph._p.remove(child)

    paragraph._p.append(make_tab_run())
    for node in math_nodes:
        paragraph._p.append(node)
    paragraph._p.append(make_tab_run())
    paragraph._p.append(make_text_run(f"公式({formula_no})"))

    paragraph.paragraph_format.space_before = Pt(6)
    paragraph.paragraph_format.space_after = Pt(6)
    paragraph.paragraph_format.first_line_indent = Pt(0)
    paragraph.paragraph_format.left_indent = Pt(0)


def make_tab_run():
    run = OxmlElement("w:r")
    tab = OxmlElement("w:tab")
    run.append(tab)
    return run


def make_text_run(text: str):
    run = OxmlElement("w:r")
    r_pr = OxmlElement("w:rPr")
    fonts = OxmlElement("w:rFonts")
    fonts.set(qn("w:ascii"), "Times New Roman")
    fonts.set(qn("w:eastAsia"), "宋体")
    size = OxmlElement("w:sz")
    size.set(qn("w:val"), "24")
    size_cs = OxmlElement("w:szCs")
    size_cs.set(qn("w:val"), "24")
    r_pr.extend([fonts, size, size_cs])
    run.append(r_pr)
    text_node = OxmlElement("w:t")
    text_node.set(qn("xml:space"), "preserve")
    text_node.text = text
    run.append(text_node)
    return run


def formula_font_path() -> str | None:
    for candidate in [
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
        r"C:\Windows\Fonts\simsun.ttc",
    ]:
        if Path(candidate).exists():
            return candidate
    return None


def create_formula_images() -> dict[int, Path]:
    FORMULA_DIR.mkdir(parents=True, exist_ok=True)
    font_path = formula_font_path()
    font_prop = matplotlib.font_manager.FontProperties(fname=font_path) if font_path else None
    paths: dict[int, Path] = {}
    for no, latex in FORMULAS.items():
        fig = plt.figure(figsize=(6.3, 0.55), dpi=360)
        fig.patch.set_facecolor("white")
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis("off")
        ax.text(0.46, 0.52, latex, ha="center", va="center", fontsize=15, color="#111827")
        ax.text(
            0.965,
            0.52,
            f"公式({no})",
            ha="right",
            va="center",
            fontsize=11,
            color="#111827",
            fontproperties=font_prop,
            fontweight="semibold",
        )
        out = FORMULA_DIR / f"Formula{no:02d}.png"
        fig.savefig(out, dpi=360, bbox_inches="tight", pad_inches=0.02, facecolor="white")
        plt.close(fig)
        paths[no] = out
    return paths


def format_formulas(doc: Document) -> dict:
    formula_images = create_formula_images()
    max_width = min(
        doc.sections[0].page_width - doc.sections[0].left_margin - doc.sections[0].right_margin,
        Inches(6.2),
    )
    changed = []
    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        match = FORMULA_RE.match(text)
        has_math = bool(paragraph._p.xpath(".//m:oMath|.//m:oMathPara"))
        if match and has_math:
            formula_no = int(match.group(1))
            clear_paragraph(paragraph)
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            paragraph.paragraph_format.space_before = Pt(6)
            paragraph.paragraph_format.space_after = Pt(6)
            paragraph.add_run().add_picture(str(formula_images[formula_no]), width=max_width)
            changed.append(f"公式({formula_no})")
    return {"formulas_formatted": changed}


def style_remaining_captions(doc: Document) -> None:
    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if FIGURE_CAPTION_RE.match(text):
            style_caption(paragraph, keep_with_next=False)
        elif TABLE_CAPTION_RE.match(text):
            style_caption(paragraph, keep_with_next=True)


def main() -> None:
    doc = Document(str(SOURCE_DOCX))
    audit: dict = {}
    audit.update(replace_figures(doc))
    audit.update(rename_and_remove_table_captions(doc))
    audit.update(format_formulas(doc))
    style_remaining_captions(doc)
    for table in doc.tables:
        style_table(table)

    doc.save(str(DESKTOP_OUT))
    shutil.copy2(DESKTOP_OUT, CODE_OUT)
    AUDIT_OUT.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(DESKTOP_OUT)
    print(CODE_OUT)
    print(AUDIT_OUT)


if __name__ == "__main__":
    main()
