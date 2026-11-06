from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path

from docx import Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph


BODY_START_RE = re.compile(r"(\u4e00[\u3001.\uff0e]\s*\u5f15\u8a00|\u5f15\u8a00$)")
BODY_END_RE = re.compile(r"(\u53c2\u8003\u6587\u732e|References)")


DELETE_BLOCK_INDICES = {
    85,
    92,
    100,
    109,
    114,
    117,
    120,
    128,
    131,
    142,
    145,
    162,
    166,
    174,
    177,
    182,
    186,
    189,
    195,
    217,
    220,
    228,
    232,
    235,
    238,
    248,
    257,
    260,
    269,
    272,
    273,
    279,
    283,
    300,
    304,
    308,
    311,
    315,
    320,
    329,
    333,
    342,
    346,
    350,
    353,
    356,
    370,
    380,
}


def iter_blocks(doc: Document):
    for child in doc.element.body.iterchildren():
        if isinstance(child, CT_P):
            paragraph = Paragraph(child, doc)
            yield "p", paragraph, paragraph.text
        elif isinstance(child, CT_Tbl):
            table = Table(child, doc)
            table_text = "\n".join("|".join(cell.text for cell in row.cells) for row in table.rows)
            yield "tbl", table, table_text


def body_bounds(blocks: list[tuple[str, object, str]]) -> tuple[int, int]:
    start = None
    end = None
    for index, (_, _, text) in enumerate(blocks):
        compact = "".join(text.split())
        if start is None and BODY_START_RE.search(compact):
            start = index
        if start is not None and BODY_END_RE.search(compact):
            end = index
            break
    if start is None:
        raise RuntimeError("Could not locate body start heading.")
    if end is None:
        end = len(blocks)
    return start, end


def body_char_count(doc: Document) -> int:
    blocks = list(iter_blocks(doc))
    start, end = body_bounds(blocks)
    return sum(len(text) for _, _, text in blocks[start:end])


def paragraph_preview(paragraph: Paragraph) -> str:
    text = paragraph.text.strip().replace("\n", " ")
    return text[:100]


def delete_paragraph(paragraph: Paragraph) -> None:
    element = paragraph._element
    parent = element.getparent()
    if parent is not None:
        parent.remove(element)


def main() -> None:
    input_path = Path(os.environ["DOCX_PATH"])
    output_path = input_path.with_name(input_path.stem + "_写作形式精简修订版.docx")
    audit_path = output_path.with_name("thesis_narrative_density_audit.json")

    shutil.copy2(input_path, output_path)
    doc = Document(output_path)
    blocks = list(iter_blocks(doc))
    before = body_char_count(doc)

    removed: list[dict[str, object]] = []
    for index, (kind, obj, text) in sorted(enumerate(blocks), reverse=True):
        if index not in DELETE_BLOCK_INDICES:
            continue
        if kind != "p":
            raise RuntimeError(f"Configured block {index} is not a paragraph.")
        paragraph = obj
        assert isinstance(paragraph, Paragraph)
        removed.append({"block_index": index, "chars": len(paragraph.text.strip()), "preview": paragraph_preview(paragraph)})
        delete_paragraph(paragraph)

    doc.save(output_path)
    verified_doc = Document(output_path)
    after = body_char_count(verified_doc)
    audit = {
        "input": str(input_path),
        "output": str(output_path),
        "body_char_count_before": before,
        "body_char_count_after": after,
        "target_range": [15500, 16000],
        "removed_paragraphs": len(removed),
        "removed_chars": sum(item["chars"] for item in removed),
        "kept_fonts": "No font/style normalization was applied; edits only removed redundant explanatory paragraphs.",
        "removed": sorted(removed, key=lambda item: item["block_index"]),
    }
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: audit[k] for k in audit if k != "removed"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
