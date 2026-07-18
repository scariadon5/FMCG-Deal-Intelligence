import re
from io import BytesIO
from docx import Document
from docx.shared import Pt

BOLD_PATTERN = re.compile(r"\*\*(.+?)\*\*")


def _add_runs_with_bold(paragraph, text):
    """Split on **bold** markers and add runs preserving bold formatting."""
    pos = 0
    for match in BOLD_PATTERN.finditer(text):
        if match.start() > pos:
            paragraph.add_run(text[pos:match.start()])
        bold_run = paragraph.add_run(match.group(1))
        bold_run.bold = True
        pos = match.end()
    if pos < len(text):
        paragraph.add_run(text[pos:])


def markdown_to_docx(markdown_text, title="FMCG Deal Intelligence Newsletter"):
    """
    Converts the newsletter's markdown structure into a Word document.
    Handles: # / ## / ### headings, "- " bullet lines, and plain
    "**Deal name** — description" paragraph lines (older newsletter style).
    """
    doc = Document()

    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

    lines = markdown_text.split("\n")

    for raw_line in lines:
        line = raw_line.rstrip()

        if not line.strip():
            continue

        if line.startswith("### "):
            doc.add_heading(line[4:].strip(), level=2)
        elif line.startswith("## "):
            doc.add_heading(line[3:].strip(), level=1)
        elif line.startswith("# "):
            doc.add_heading(line[2:].strip(), level=0)
        elif line.strip().startswith("- "):
            p = doc.add_paragraph(style="List Bullet")
            _add_runs_with_bold(p, line.strip()[2:])
        else:
            p = doc.add_paragraph()
            _add_runs_with_bold(p, line.strip())

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()
