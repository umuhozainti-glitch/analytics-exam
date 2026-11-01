"""Render REPORT.md and its local figures as a paginated PDF."""
from __future__ import annotations

import argparse
from html.parser import HTMLParser
from pathlib import Path
from xml.sax.saxutils import escape

import markdown
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Image, KeepTogether, PageBreak, Paragraph, Preformatted, SimpleDocTemplate, Spacer


class ReportParser(HTMLParser):
    def __init__(self, root: Path, styles):
        super().__init__(convert_charrefs=True)
        self.root = root
        self.styles = styles
        self.story = []
        self.mode = None
        self.parts: list[str] = []

    def _flush(self):
        text = "".join(self.parts).strip()
        self.parts = []
        if not text:
            return
        if self.mode == "pre":
            self.story.append(Preformatted(text, self.styles["CodeBlock"]))
        else:
            style = self.styles.get(self.mode, self.styles["BodyText"])
            if self.mode == "MyBullet":
                text = "&#8226; " + text
            paragraph = Paragraph(text, style)
            if text.startswith("<b>Figure "):
                self.story.append(PageBreak())
                paragraph.keepWithNext = True
            self.story.append(paragraph)

    def handle_starttag(self, tag, attrs):
        if tag in ("h1", "h2", "h3", "p", "li", "pre"):
            self._flush()
            self.mode = {"h1": "Title", "h2": "Heading2", "h3": "Heading3", "p": "BodyText", "li": "MyBullet", "pre": "pre"}[tag]
        elif tag in ("strong", "b", "em", "i", "code") and self.mode != "pre":
            self.parts.append({"strong": "<b>", "b": "<b>", "em": "<i>", "i": "<i>", "code": "<font name='Courier'>"}[tag])
        elif tag == "a" and self.mode != "pre":
            self.parts.append("<font color='blue'>")
        elif tag == "img":
            self._flush()
            src = dict(attrs).get("src", "")
            path = (self.root / src).resolve()
            if path.is_file():
                image = Image(str(path), width=6.8 * inch, height=4.4 * inch, kind="proportional")
                image.hAlign = "CENTER"
                self.story.extend([image, Spacer(1, 8)])

    def handle_endtag(self, tag):
        if tag in ("strong", "b", "em", "i", "code") and self.mode != "pre":
            self.parts.append({"strong": "</b>", "b": "</b>", "em": "</i>", "i": "</i>", "code": "</font>"}[tag])
        elif tag == "a" and self.mode != "pre":
            self.parts.append("</font>")
        elif tag in ("h1", "h2", "h3", "p", "li", "pre"):
            self._flush()
            self.mode = None
            self.story.append(Spacer(1, 5 if tag in ("h1", "h2", "h3") else 3))
        elif tag == "br" and self.mode and self.mode != "pre":
            self.parts.append("<br/>")

    def handle_data(self, data):
        if self.mode == "pre":
            self.parts.append(data)
        elif self.mode:
            self.parts.append(escape(data))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="REPORT.md")
    parser.add_argument("--output", default="REPORT.pdf")
    args = parser.parse_args()
    source = Path(args.input).resolve()
    root = source.parent
    styles = getSampleStyleSheet()
    styles["Title"].fontSize = 18
    styles["Title"].leading = 22
    styles["Title"].alignment = TA_CENTER
    styles["Heading2"].textColor = colors.HexColor("#1b4332")
    styles["Heading3"].textColor = colors.HexColor("#2d6a4f")
    styles.add(ParagraphStyle(name="CodeBlock", fontName="Courier", fontSize=8, leading=10, leftIndent=12))
    styles.add(ParagraphStyle(name="MyBullet", parent=styles["BodyText"], leftIndent=16, firstLineIndent=-10, spaceAfter=4))
    html = markdown.markdown(source.read_text(encoding="utf-8"), extensions=["tables", "fenced_code"])
    content = ReportParser(root, styles)
    content.feed(html)

    def add_page_number(canvas, document):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.grey)
        canvas.drawRightString(letter[0] - 0.65 * inch, 0.4 * inch, f"{document.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(args.output, pagesize=letter, rightMargin=0.65 * inch, leftMargin=0.65 * inch, topMargin=0.6 * inch, bottomMargin=0.65 * inch, title="Distributed Multi-Model Analytics for E-commerce Data")
    doc.build(content.story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    print(f"Created {args.output}")


if __name__ == "__main__":
    main()
