# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
import shutil
from copy import deepcopy
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION_START
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Emu, Inches, Pt, RGBColor
from docx.table import Table
from docx.text.paragraph import Paragraph
from PIL import Image


SCRIPT_DIR = Path(__file__).resolve().parent
CODE_DIR = SCRIPT_DIR.parent
FIG_DIR = CODE_DIR / "输出结果" / "figures"
DOCX_IN = Path(r"C:\Users\22672\Desktop\政府采购异常低价风险识别与监管研究_图表公式优化版.docx")
FORMULA_SOURCE = Path(r"C:\Users\22672\Desktop\政府采购异常低价风险识别与监管研究_最终版.docx")
DOCX_OUT = Path(r"C:\Users\22672\Desktop\政府采购异常低价风险识别与监管研究_格式规范修订版.docx")
CODE_OUT = SCRIPT_DIR / DOCX_OUT.name
AUDIT_OUT = SCRIPT_DIR / "format_requirements_audit.json"
CROPPED_FIG_DIR = FIG_DIR / "docx_without_embedded_titles"


FIG_CAPTION_RE = re.compile(r"^图\s*(\d+)\s*(.*)$")
TABLE_CAPTION_RE = re.compile(r"^表\s*(\d+)\s*(.*)$")
FORMULA_CAPTION_RE = re.compile(r"^公式[（(]\s*(\d+)\s*[）)]$")
FIG_REF_RE = re.compile(r"图\s*(\d+)")

REMOVED_FIGURE_NO = 31
FORMULA_LABEL = "\u516c\u5f0f"
FORMULA_LABEL_RE = re.compile(r"\u516c\u5f0f\((\d+)\)")
FORMULA_LINE_RE = re.compile(r"\u516c\u5f0f\(\d+\)$")
FORMULA_TEXTS = {
    1: "R_i=M_i/B_i,  G_i=1-R_i",
    2: "T_{g,\u03b1}=Q_\u03b1(R_i|c_i=g),  \u03b1\u2208{0.05,0.10}",
    3: "T_{g,IQR}=Q_{1,g}-1.5(Q_{3,g}-Q_{1,g})",
    4: "Z_i=(R_i-Median_g)/(1.4826\u00d7MAD_g)",
    5: "A_i=I_{i,65}+I_{i,10%}+I_{i,5%}+I_{i,IQR}+I_{i,Z}",
    6: "E_i=0.30IF_i+0.25LOF_i+0.20OCSVM_i+0.25A_i",
}

INK = RGBColor(0, 0, 0)
CAPTION_COLOR = RGBColor(23, 32, 51)


def iter_body_blocks(doc: Document):
    for child in doc.element.body.iterchildren():
        if child.tag == qn("w:p"):
            yield Paragraph(child, doc)
        elif child.tag == qn("w:tbl"):
            yield Table(child, doc)


def remove_paragraph(paragraph: Paragraph) -> None:
    element = paragraph._element
    element.getparent().remove(element)


def remove_table(table: Table) -> None:
    element = table._element
    element.getparent().remove(element)


def significant_before(blocks: list, index: int):
    for item in reversed(blocks[:index]):
        if isinstance(item, Table):
            return item
        text = item.text.strip()
        if text or item._p.xpath(".//w:drawing") or item._p.xpath(".//m:oMath|.//m:oMathPara"):
            return item
    return None


def clear_paragraph(paragraph: Paragraph) -> None:
    p_pr = paragraph._p.pPr
    for child in list(paragraph._p):
        if child is not p_pr:
            paragraph._p.remove(child)


def set_run_font(run, east_asia: str, size_pt: float, bold: bool = False, color: RGBColor = INK) -> None:
    run.font.name = "Times New Roman"
    if run._element.rPr is None:
        run._element.get_or_add_rPr()
    run._element.rPr.rFonts.set(qn("w:eastAsia"), east_asia)
    run.font.size = Pt(size_pt)
    run.font.bold = bold
    run.font.color.rgb = color


def set_paragraph_font(paragraph: Paragraph, east_asia: str, size_pt: float, bold: bool = False) -> None:
    if not paragraph.runs and paragraph.text:
        paragraph.add_run(paragraph.text)
    for run in paragraph.runs:
        if run._r.xpath(".//w:drawing"):
            continue
        set_run_font(run, east_asia=east_asia, size_pt=size_pt, bold=bold)


def set_exact_line(paragraph: Paragraph, size_pt: float = 24) -> None:
    fmt = paragraph.paragraph_format
    fmt.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    fmt.line_spacing = Pt(size_pt)


def set_caption_text(paragraph: Paragraph, text: str) -> None:
    clear_paragraph(paragraph)
    run = paragraph.add_run(text)
    set_run_font(run, east_asia="宋体", size_pt=12, bold=True, color=CAPTION_COLOR)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_before = Pt(4)
    paragraph.paragraph_format.space_after = Pt(6)


def get_picture_width(paragraph: Paragraph) -> Emu | None:
    extents = paragraph._p.xpath(".//wp:extent")
    if not extents:
        return None
    cx = extents[0].get("cx")
    return Emu(int(cx)) if cx else None


def figure_source(old_no: int) -> Path | None:
    matches = sorted(FIG_DIR.glob(f"Fig{old_no:02d}_*.png"))
    matches = [p for p in matches if not re.match(rf"Fig{old_no:02d}[A-Za-z]", p.stem)]
    return matches[0] if matches else None


def cropped_without_title(old_no: int) -> Path | None:
    src = figure_source(old_no)
    if src is None:
        return None
    CROPPED_FIG_DIR.mkdir(parents=True, exist_ok=True)
    out = CROPPED_FIG_DIR / f"Fig{old_no - 1:02d}_from_{src.name}"
    with Image.open(src) as image:
        rgb = image.convert("RGB")
        top = int(rgb.height * (0.075 if rgb.width / rgb.height < 2.5 else 0.095))
        cropped = rgb.crop((0, top, rgb.width, rgb.height))
        cropped.save(out, quality=96)
    return out


def replace_picture(paragraph: Paragraph, image_path: Path) -> None:
    width = get_picture_width(paragraph) or Inches(5.85)
    clear_paragraph(paragraph)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_before = Pt(4)
    paragraph.paragraph_format.space_after = Pt(3)
    paragraph.add_run().add_picture(str(image_path), width=width)


def remove_and_renumber_figures(doc: Document) -> dict:
    blocks = list(iter_body_blocks(doc))
    removed = None
    renumbered: list[str] = []

    for idx, block in enumerate(blocks):
        if not isinstance(block, Paragraph):
            continue
        match = FIG_CAPTION_RE.match(block.text.strip())
        if not match:
            continue
        old_no = int(match.group(1))
        title = match.group(2).strip()
        image_block = significant_before(blocks, idx)
        if old_no == REMOVED_FIGURE_NO:
            if isinstance(image_block, Paragraph) and image_block._p.xpath(".//w:drawing"):
                remove_paragraph(image_block)
            remove_paragraph(block)
            removed = f"图{old_no} {title}"
        elif old_no > REMOVED_FIGURE_NO:
            new_no = old_no - 1
            set_caption_text(block, f"图{new_no} {title}")
            cropped = cropped_without_title(old_no)
            if cropped and isinstance(image_block, Paragraph) and image_block._p.xpath(".//w:drawing"):
                replace_picture(image_block, cropped)
            renumbered.append(f"图{old_no} -> 图{new_no}")

    for paragraph in doc.paragraphs:
        if paragraph._p.xpath(".//w:drawing"):
            continue
        if FIG_CAPTION_RE.match(paragraph.text.strip()):
            continue
        for run in paragraph.runs:
            if run._r.xpath(".//w:drawing"):
                continue
            run.text = FIG_REF_RE.sub(
                lambda m: f"图{int(m.group(1)) - 1}" if int(m.group(1)) > REMOVED_FIGURE_NO else m.group(0),
                run.text,
            )
    return {"removed_figure": removed, "renumbered_figures": renumbered}


def get_formula_nodes() -> dict[int, list]:
    source = Document(str(FORMULA_SOURCE))
    formulas: dict[int, list] = {}
    for paragraph in source.paragraphs:
        text = paragraph.text.strip()
        match = FORMULA_CAPTION_RE.match(text)
        nodes = paragraph._p.xpath(".//m:oMath|.//m:oMathPara")
        if match and nodes:
            formulas[int(match.group(1))] = [deepcopy(node) for node in nodes]
    return formulas


def drawing_aspect(paragraph: Paragraph) -> float | None:
    extents = paragraph._p.xpath(".//wp:extent")
    if not extents:
        return None
    cx = int(extents[0].get("cx"))
    cy = int(extents[0].get("cy"))
    return cx / cy if cy else None


def is_formula_picture(paragraph: Paragraph) -> bool:
    aspect = drawing_aspect(paragraph)
    return bool(aspect and aspect > 7.0 and not paragraph.text.strip())


def set_table_width(table: Table, pct: int = 5000) -> None:
    tbl_pr = table._tbl.tblPr
    tbl_w = tbl_pr.find(qn("w:tblW"))
    if tbl_w is None:
        tbl_w = OxmlElement("w:tblW")
        tbl_pr.append(tbl_w)
    tbl_w.set(qn("w:w"), str(pct))
    tbl_w.set(qn("w:type"), "pct")


def set_table_border_none(table: Table) -> None:
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
        node.set(qn("w:sz"), "0")
        node.set(qn("w:space"), "0")
        node.set(qn("w:color"), "FFFFFF")


def set_cell_border_none(cell) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    borders = tc_pr.find(qn("w:tcBorders"))
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        tc_pr.append(borders)
    for edge in ["top", "left", "bottom", "right", "insideH", "insideV"]:
        node = borders.find(qn(f"w:{edge}"))
        if node is None:
            node = OxmlElement(f"w:{edge}")
            borders.append(node)
        node.set(qn("w:val"), "single")
        node.set(qn("w:sz"), "0")
        node.set(qn("w:space"), "0")
        node.set(qn("w:color"), "FFFFFF")


def set_table_width_dxa(table: Table, width_dxa: int) -> None:
    tbl_pr = table._tbl.tblPr
    tbl_w = tbl_pr.find(qn("w:tblW"))
    if tbl_w is None:
        tbl_w = OxmlElement("w:tblW")
        tbl_pr.append(tbl_w)
    tbl_w.set(qn("w:w"), str(width_dxa))
    tbl_w.set(qn("w:type"), "dxa")


def set_table_grid(table: Table, widths_dxa: list[int]) -> None:
    tbl_grid = table._tbl.tblGrid
    if tbl_grid is None:
        tbl_grid = OxmlElement("w:tblGrid")
        table._tbl.insert(1, tbl_grid)
    for child in list(tbl_grid):
        tbl_grid.remove(child)
    for width in widths_dxa:
        grid_col = OxmlElement("w:gridCol")
        grid_col.set(qn("w:w"), str(width))
        tbl_grid.append(grid_col)


def set_cell_width(cell, width_dxa: int) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_w = tc_pr.find(qn("w:tcW"))
    if tc_w is None:
        tc_w = OxmlElement("w:tcW")
        tc_pr.append(tc_w)
    tc_w.set(qn("w:w"), str(width_dxa))
    tc_w.set(qn("w:type"), "dxa")


def clear_cell(cell) -> None:
    for paragraph in cell.paragraphs:
        clear_paragraph(paragraph)


def insert_formula_table_after(doc: Document, paragraph: Paragraph, formula_no: int, nodes: list) -> Table:
    table = doc.add_table(rows=1, cols=2)
    paragraph._p.addnext(table._tbl)
    set_table_border_none(table)
    set_table_width(table)
    left, right = table.cell(0, 0), table.cell(0, 1)
    left.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    right.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    set_cell_width(left, 7600)
    set_cell_width(right, 1200)
    clear_cell(left)
    clear_cell(right)
    lp = left.paragraphs[0]
    lp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    lp.paragraph_format.space_before = Pt(4)
    lp.paragraph_format.space_after = Pt(4)
    for node in nodes:
        lp._p.append(deepcopy(node))
    rp = right.paragraphs[0]
    rp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    rp.paragraph_format.space_before = Pt(4)
    rp.paragraph_format.space_after = Pt(4)
    run = rp.add_run(f"公式({formula_no})")
    set_run_font(run, east_asia="宋体", size_pt=12)
    remove_paragraph(paragraph)
    return table


def insert_formula_text_table_after(doc: Document, paragraph: Paragraph, formula_no: int, formula_text: str) -> Table:
    formula_left_dxa = 6612
    formula_right_dxa = 1700
    table = doc.add_table(rows=1, cols=2)
    paragraph._p.addnext(table._tbl)
    table.autofit = False
    set_table_border_none(table)
    set_table_width_dxa(table, formula_left_dxa + formula_right_dxa)
    set_table_grid(table, [formula_left_dxa, formula_right_dxa])

    left, right = table.cell(0, 0), table.cell(0, 1)
    left.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    right.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    set_cell_width(left, formula_left_dxa)
    set_cell_width(right, formula_right_dxa)
    set_cell_border_none(left)
    set_cell_border_none(right)
    clear_cell(left)
    clear_cell(right)

    lp = left.paragraphs[0]
    lp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    lp.paragraph_format.space_before = Pt(2)
    lp.paragraph_format.space_after = Pt(2)
    formula_run = lp.add_run(formula_text)
    set_formula_run_font(formula_run, size_pt=10)

    rp = right.paragraphs[0]
    rp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    rp.paragraph_format.space_before = Pt(2)
    rp.paragraph_format.space_after = Pt(2)
    label_run = rp.add_run(f"{FORMULA_LABEL}({formula_no})")
    set_run_font(label_run, east_asia="\u5b8b\u4f53", size_pt=12)

    remove_paragraph(paragraph)
    return table


def set_formula_run_font(run, size_pt: float = 12) -> None:
    run.font.name = "Cambria Math"
    run.font.size = Pt(size_pt)
    run.font.bold = False
    if run._element.rPr is None:
        run._element.get_or_add_rPr()
    r_fonts = run._element.rPr.rFonts
    for key in ("ascii", "hAnsi", "cs", "eastAsia"):
        r_fonts.set(qn(f"w:{key}"), "Cambria Math")


def set_formula_tabs(paragraph: Paragraph) -> None:
    section = paragraph.part.document.sections[0]
    usable_width = section.page_width - section.left_margin - section.right_margin
    tab_stops = paragraph.paragraph_format.tab_stops
    try:
        tab_stops.clear_all()
    except AttributeError:
        pass
    tab_stops.add_tab_stop(Emu(int(usable_width)), WD_TAB_ALIGNMENT.RIGHT)


def set_editable_formula_line(paragraph: Paragraph, formula_no: int, formula_text: str) -> None:
    clear_paragraph(paragraph)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
    paragraph.paragraph_format.space_before = Pt(6)
    paragraph.paragraph_format.space_after = Pt(6)
    set_exact_line(paragraph)
    set_formula_tabs(paragraph)

    formula_run = paragraph.add_run(formula_text)
    set_formula_run_font(formula_run, size_pt=11)
    number_tab = paragraph.add_run()
    number_tab.add_tab()
    label_run = paragraph.add_run(f"{FORMULA_LABEL}({formula_no})")
    set_run_font(label_run, east_asia="\u5b8b\u4f53", size_pt=12)


def replace_formula_pictures_with_editable(doc: Document) -> dict:
    formula_picture_paragraphs = [p for p in doc.paragraphs if p._p.xpath(".//w:drawing") and is_formula_picture(p)]
    converted = []
    for formula_no, paragraph in zip(sorted(FORMULA_TEXTS), formula_picture_paragraphs):
        insert_formula_text_table_after(doc, paragraph, formula_no, FORMULA_TEXTS[formula_no])
        converted.append(f"{FORMULA_LABEL}({formula_no})")
    return {"editable_formulas": converted}


def apply_page_setup(doc: Document) -> None:
    for section in doc.sections:
        section.page_width = Cm(21)
        section.page_height = Cm(29.7)
        section.top_margin = Cm(2.54)
        section.bottom_margin = Cm(2.54)
        section.left_margin = Cm(3.17)
        section.right_margin = Cm(3.17)


def is_level1(text: str) -> bool:
    return bool(re.match(r"^[一二三四五六七八九十]、", text))


def is_level2(text: str) -> bool:
    return bool(re.match(r"^（[一二三四五六七八九十]+）", text))


def is_level3(text: str) -> bool:
    return bool(re.match(r"^\d+(\.\d+)+\s*", text))


def style_document_text(doc: Document) -> dict:
    styled = {"level1": 0, "level2": 0, "level3": 0, "front_titles": 0, "body": 0}
    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if paragraph._p.xpath(".//w:drawing") or paragraph._p.xpath(".//m:oMath|.//m:oMathPara"):
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            continue
        if not text:
            continue
        if FIG_CAPTION_RE.match(text) or TABLE_CAPTION_RE.match(text):
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            paragraph.paragraph_format.space_before = Pt(4)
            paragraph.paragraph_format.space_after = Pt(6)
            set_paragraph_font(paragraph, "宋体", 12, bold=True)
            continue
        if FORMULA_LINE_RE.search(text):
            paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
            set_exact_line(paragraph)
            continue
        if text in {"摘要", "目录", "参考文献"}:
            set_paragraph_font(paragraph, "黑体", 14, bold=False)
            set_exact_line(paragraph)
            styled["front_titles"] += 1
        elif is_level1(text):
            set_paragraph_font(paragraph, "黑体", 15, bold=False)
            set_exact_line(paragraph)
            styled["level1"] += 1
        elif is_level2(text):
            set_paragraph_font(paragraph, "楷体", 14, bold=False)
            set_exact_line(paragraph)
            styled["level2"] += 1
        elif is_level3(text):
            set_paragraph_font(paragraph, "宋体", 12, bold=True)
            set_exact_line(paragraph)
            styled["level3"] += 1
        else:
            set_paragraph_font(paragraph, "宋体", 12, bold=False)
            set_exact_line(paragraph)
            styled["body"] += 1
    return styled


def audit_format(doc: Document) -> dict:
    section = doc.sections[0]
    fig_captions = [p.text.strip() for p in doc.paragraphs if FIG_CAPTION_RE.match(p.text.strip())]
    table_captions = [p.text.strip() for p in doc.paragraphs if TABLE_CAPTION_RE.match(p.text.strip())]
    body_text = "".join(t.text or "" for t in doc.element.body.xpath(".//w:t"))
    editable_formula_numbers = sorted({int(n) for n in FORMULA_LABEL_RE.findall(body_text)})
    formula_images = [
        p for p in doc.paragraphs if p._p.xpath(".//w:drawing") and is_formula_picture(p)
    ]
    return {
        "page": {
            "width_cm": round(section.page_width.cm, 2),
            "height_cm": round(section.page_height.cm, 2),
            "top_margin_cm": round(section.top_margin.cm, 2),
            "bottom_margin_cm": round(section.bottom_margin.cm, 2),
            "left_margin_cm": round(section.left_margin.cm, 2),
            "right_margin_cm": round(section.right_margin.cm, 2),
        },
        "figure_caption_count": len(fig_captions),
        "figure_captions_tail": fig_captions[-8:],
        "table_caption_count": len(table_captions),
        "table_captions_tail": table_captions[-5:],
        "editable_formula_mode": "editable text formula layout",
        "editable_formula_count": len(editable_formula_numbers),
        "formula_picture_count": len(formula_images),
        "data_table_caption_count": len(table_captions),
    }


def main() -> None:
    doc = Document(str(DOCX_IN))
    audit: dict = {}
    apply_page_setup(doc)
    audit.update(remove_and_renumber_figures(doc))
    audit.update(replace_formula_pictures_with_editable(doc))
    audit["text_styles_applied"] = style_document_text(doc)
    audit["format_check"] = audit_format(doc)

    doc.save(str(DOCX_OUT))
    shutil.copy2(DOCX_OUT, CODE_OUT)
    AUDIT_OUT.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(DOCX_OUT)
    print(CODE_OUT)
    print(AUDIT_OUT)


if __name__ == "__main__":
    main()
