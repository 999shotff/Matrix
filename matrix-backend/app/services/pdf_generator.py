from __future__ import annotations
import os
import uuid
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from app.models import QuestionPaper

OUTPUT_DIR = Path(os.getenv("STORAGE_DIR", "./storage")) / "papers"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

styles = getSampleStyleSheet()
title_style = ParagraphStyle(
    "PaperTitle", parent=styles["Title"], alignment=TA_CENTER, fontSize=16, spaceAfter=4
)
meta_style = ParagraphStyle(
    "Meta", parent=styles["Normal"], alignment=TA_CENTER, fontSize=10, textColor=colors.grey
)
section_style = ParagraphStyle(
    "Section", parent=styles["Heading2"], fontSize=12.5, spaceBefore=16, spaceAfter=4
)
instructions_style = ParagraphStyle(
    "Instructions", parent=styles["Italic"], fontSize=9.5, textColor=colors.grey, spaceAfter=8
)
question_style = ParagraphStyle(
    "Question", parent=styles["Normal"], fontSize=11, leading=15, spaceAfter=8, alignment=TA_LEFT
)


def render_pdf(paper: QuestionPaper, session_id: str) -> str:
    """Renders the paper to a PDF file on disk and returns its file id
    (used to build the download URL)."""
    file_id = f"{session_id}-{uuid.uuid4().hex[:8]}.pdf"
    dest = OUTPUT_DIR / file_id

    doc = SimpleDocTemplate(
        str(dest), pagesize=A4,
        topMargin=20 * mm, bottomMargin=20 * mm, leftMargin=18 * mm, rightMargin=18 * mm,
    )
    story = []

    story.append(Paragraph(paper.title, title_style))
    meta_bits = [f"Total marks: {paper.total_marks}"]
    if paper.duration_minutes:
        meta_bits.append(f"Duration: {paper.duration_minutes} min")
    story.append(Paragraph("  |  ".join(meta_bits), meta_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", color=colors.lightgrey, thickness=0.75))

    for section in paper.sections:
        story.append(Paragraph(section.name, section_style))
        if section.instructions:
            story.append(Paragraph(section.instructions, instructions_style))
        for q in section.questions:
            story.append(Paragraph(f"<b>{q.number}.</b> {q.text} <i>[{q.marks} marks]</i>", question_style))

    if paper.notes:
        story.append(Spacer(1, 14))
        story.append(HRFlowable(width="100%", color=colors.lightgrey, thickness=0.75))
        story.append(Paragraph(f"<i>{paper.notes}</i>", instructions_style))

    doc.build(story)
    return file_id


def pdf_path(file_id: str) -> Path:
    return OUTPUT_DIR / file_id
