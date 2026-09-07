"""Concise PDF report generation."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .models import AnalysisResult


def write_pdf_report(result: AnalysisResult, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(path),
        pagesize=letter,
        leftMargin=0.55 * inch,
        rightMargin=0.55 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
        title="Triloom UTRacer Report",
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Small", parent=styles["BodyText"], fontSize=8.5, leading=10))
    styles.add(ParagraphStyle(name="Tight", parent=styles["BodyText"], fontSize=9.5, leading=11))

    story = [
        Paragraph("Triloom UTRacer Report", styles["Title"]),
        Paragraph(f"<b>Conclusion:</b> {result.conclusion}", styles["Tight"]),
        Paragraph(f"<b>Confidence:</b> {result.top_confidence:.0%}", styles["Tight"]),
        Paragraph(
            f"<b>Query:</b> {result.normalized.length} nt; {result.normalized.molecule}; "
            f"GC {result.normalized.gc_fraction:.1%}",
            styles["Tight"],
        ),
        Spacer(1, 0.12 * inch),
    ]

    if result.visuals.query_track_png and Path(result.visuals.query_track_png).exists():
        story.extend([Image(str(result.visuals.query_track_png), width=7.1 * inch, height=2.15 * inch), Spacer(1, 0.08 * inch)])
    if result.visuals.alignment_png and Path(result.visuals.alignment_png).exists():
        story.extend([Image(str(result.visuals.alignment_png), width=7.1 * inch, height=2.45 * inch), Spacer(1, 0.12 * inch)])

    story.append(Paragraph("Ranked Candidates", styles["Heading2"]))
    story.append(_candidate_table(result, styles["Small"]))
    story.append(Spacer(1, 0.1 * inch))

    story.append(Paragraph("Segment Calls", styles["Heading2"]))
    story.append(_segment_table(result, styles["Small"]))
    story.append(Spacer(1, 0.1 * inch))

    story.append(Paragraph("Evidence Trail", styles["Heading2"]))
    for line in _evidence_lines(result):
        story.append(Paragraph(line, styles["Small"]))

    if result.normalized.warnings:
        story.append(Spacer(1, 0.06 * inch))
        story.append(Paragraph("Warnings", styles["Heading2"]))
        for warning in result.normalized.warnings:
            story.append(Paragraph(warning, styles["Small"]))

    doc.build(story)
    return path


def _candidate_table(result: AnalysisResult, style) -> Table:
    rows = [["Rank", "Candidate", "Ident", "Q cov", "R cov", "Origin", "Canonical", "Prov"]]
    for index, candidate in enumerate(result.candidates[:8], start=1):
        rows.append(
            [
                str(index),
                Paragraph(candidate.reference.name, style),
                f"{candidate.alignment.identity:.0%}",
                f"{candidate.alignment.query_coverage:.0%}",
                f"{candidate.alignment.reference_coverage:.0%}",
                f"{candidate.sequence_origin_confidence:.0%}",
                f"{candidate.canonical_identity_confidence:.0%}",
                candidate.reference.source,
            ]
        )
    if len(rows) == 1:
        rows.append(["-", "No local candidate above threshold", "-", "-", "-", "-", "-", "-"])

    table = Table(rows, colWidths=[0.35 * inch, 2.3 * inch, 0.5 * inch, 0.5 * inch, 0.5 * inch, 0.6 * inch, 0.65 * inch, 1.05 * inch])
    table.setStyle(_table_style())
    return table


def _segment_table(result: AnalysisResult, style) -> Table:
    rows = [["Query span", "Segment", "Type", "Ident", "Orient", "Confidence"]]
    for segment in result.segments:
        rows.append(
            [
                f"{segment.query_start + 1}-{segment.query_end}",
                Paragraph(segment.label, style),
                segment.category,
                f"{segment.identity:.0%}",
                segment.orientation,
                f"{segment.confidence:.0%}",
            ]
        )
    if len(rows) == 1:
        rows.append(["-", "No decomposition above threshold", "-", "-", "-", "-"])
    table = Table(rows, colWidths=[0.8 * inch, 2.5 * inch, 1.1 * inch, 0.55 * inch, 1.0 * inch, 0.85 * inch])
    table.setStyle(_table_style())
    return table


def _table_style() -> TableStyle:
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d1d5db")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
        ]
    )


def _evidence_lines(result: AnalysisResult) -> list[str]:
    lines: list[str] = []
    for signal in result.classification_signals[:8]:
        span = ""
        if signal.query_start is not None and signal.query_end is not None:
            span = f" ({signal.query_start + 1}-{signal.query_end})"
        lines.append(f"{signal.label}{span}: {signal.evidence or 'Detected by heuristic scan.'}")
    for notice in result.notices[:5]:
        lines.append(f"{notice.adapter}: {notice.status}; {notice.message}")
    return lines or ["No additional evidence was recorded."]
