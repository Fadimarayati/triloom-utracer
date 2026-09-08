"""PDF report generation for Triloom UTRacer."""

from __future__ import annotations

from html import escape
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image as ReportImage
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .models import AnalysisResult


CONTENT_WIDTH = 7.4 * inch


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
    styles = _styles()

    story = [
        Paragraph("TRILOOM UTRACER :: RESULT REPORT", styles["CodeTitle"]),
        _code_block(_query_summary(result), styles),
        Spacer(1, 0.08 * inch),
        Paragraph("TOP HIT", styles["CodeHeading"]),
        _code_block(_top_hit_summary(result), styles),
        Spacer(1, 0.08 * inch),
        Paragraph("SOURCE SCAN", styles["CodeHeading"]),
        _source_scan_table(result, styles),
        Spacer(1, 0.08 * inch),
        Paragraph("RANKED CANDIDATES", styles["CodeHeading"]),
        _candidate_table(result, styles),
        Spacer(1, 0.08 * inch),
        Paragraph("SEGMENT MAP", styles["CodeHeading"]),
        _segment_table(result, styles),
        Spacer(1, 0.08 * inch),
        Paragraph("SIGNALS / NOTICES", styles["CodeHeading"]),
        _code_block(_evidence_summary(result), styles),
    ]

    if result.normalized.warnings:
        story.extend(
            [
                Spacer(1, 0.06 * inch),
                Paragraph("WARNINGS", styles["CodeHeading"]),
                _code_block("\n".join(f"- {warning}" for warning in result.normalized.warnings), styles),
            ]
        )

    image_items = _visual_items(result)
    if image_items:
        story.extend([Spacer(1, 0.12 * inch), Paragraph("VISUALS", styles["CodeHeading"])])
        for label, image_path, max_height in image_items:
            story.append(Paragraph(label, styles["CodeLabel"]))
            story.append(_scaled_image(image_path, CONTENT_WIDTH, max_height))
            story.append(Spacer(1, 0.08 * inch))

    doc.build(story)
    return path


def _styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="CodeTitle",
            parent=styles["Normal"],
            fontName="Courier-Bold",
            fontSize=15,
            leading=18,
            textColor=colors.HexColor("#111827"),
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CodeHeading",
            parent=styles["Normal"],
            fontName="Courier-Bold",
            fontSize=10.5,
            leading=12.5,
            textColor=colors.HexColor("#111827"),
            spaceBefore=4,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CodeLabel",
            parent=styles["Normal"],
            fontName="Courier-Bold",
            fontSize=8.5,
            leading=10,
            textColor=colors.HexColor("#374151"),
            spaceAfter=3,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CodeBlock",
            parent=styles["Normal"],
            fontName="Courier",
            fontSize=8.2,
            leading=10,
            borderWidth=0.35,
            borderColor=colors.HexColor("#d1d5db"),
            borderPadding=6,
            backColor=colors.HexColor("#fbfbfb"),
            wordWrap="CJK",
        )
    )
    styles.add(
        ParagraphStyle(
            name="TableCell",
            parent=styles["Normal"],
            fontName="Courier",
            fontSize=6.9,
            leading=8.1,
            wordWrap="CJK",
        )
    )
    styles.add(
        ParagraphStyle(
            name="TableHead",
            parent=styles["TableCell"],
            fontName="Courier-Bold",
            textColor=colors.HexColor("#111827"),
        )
    )
    return styles


def _query_summary(result: AnalysisResult) -> str:
    query_name = result.query_id or "unlabeled-query"
    return "\n".join(
        [
            f"query_id:        {query_name}",
            f"length_nt:       {result.normalized.length}",
            f"molecule:        {result.normalized.molecule}",
            f"gc_fraction:     {result.normalized.gc_fraction:.1%}",
            f"ambiguous_bases: {result.normalized.ambiguous_count}",
            f"conclusion:      {result.conclusion}",
            f"confidence:      {result.top_confidence:.1%}",
        ]
    )


def _top_hit_summary(result: AnalysisResult) -> str:
    if not result.candidates:
        return "best_hit: none\nnext_step: add local references or enable planned external searches"
    top = result.candidates[0]
    lines = [
        f"name:            {top.reference.name}",
        f"source:          {top.reference.source}",
        f"accession:       {top.reference.accession or '-'}",
        f"category:        {top.reference.category}",
        f"utr_type:        {top.reference.utr_type or '-'}",
        f"organism:        {top.reference.organism or '-'}",
        f"orientation:     {top.alignment.orientation}",
        f"identity:        {top.alignment.identity:.1%}",
        f"query_coverage:  {top.alignment.query_coverage:.1%}",
        f"ref_coverage:    {top.alignment.reference_coverage:.1%}",
        f"origin_score:    {top.sequence_origin_confidence:.1%}",
        f"canonical_score: {top.canonical_identity_confidence:.1%}",
        f"exact_full:      {str(top.exact_full_match).lower()}",
    ]
    if top.reference.provenance:
        lines.append(f"provenance:      {top.reference.provenance}")
    if top.reference.provenance_url:
        lines.append(f"url:             {top.reference.provenance_url}")
    return "\n".join(lines)


def _source_scan_table(result: AnalysisResult, styles) -> Table:
    rows = [
        [
            _cell("source", styles, header=True),
            _cell("status", styles, header=True),
            _cell("hits", styles, header=True),
            _cell("best_hit", styles, header=True),
            _cell("id/q/r", styles, header=True),
            _cell("origin/canon", styles, header=True),
            _cell("note", styles, header=True),
        ]
    ]
    for scan in result.source_scans:
        rows.append(
            [
                _cell(scan.source, styles),
                _cell(scan.status, styles),
                _cell(str(scan.hit_count), styles),
                _cell(scan.best_reference or "-", styles),
                _cell(
                    f"{_pct(scan.best_identity)}/{_pct(scan.best_query_coverage)}/{_pct(scan.best_reference_coverage)}",
                    styles,
                ),
                _cell(f"{_pct(scan.best_origin_confidence)}/{_pct(scan.best_canonical_confidence)}", styles),
                _cell(scan.note or "-", styles),
            ]
        )
    if len(rows) == 1:
        rows.append([_cell("-", styles) for _ in range(7)])

    table = Table(
        rows,
        colWidths=[0.95 * inch, 0.6 * inch, 0.35 * inch, 1.75 * inch, 0.95 * inch, 0.9 * inch, 1.9 * inch],
        repeatRows=1,
    )
    table.setStyle(_table_style())
    return table


def _candidate_table(result: AnalysisResult, styles) -> Table:
    rows = [
        [
            _cell("#", styles, header=True),
            _cell("candidate", styles, header=True),
            _cell("source", styles, header=True),
            _cell("id", styles, header=True),
            _cell("qcov", styles, header=True),
            _cell("rcov", styles, header=True),
            _cell("origin", styles, header=True),
            _cell("canon", styles, header=True),
            _cell("evidence", styles, header=True),
        ]
    ]
    for index, candidate in enumerate(result.candidates[:10], start=1):
        evidence_parts = [*candidate.evidence[:2]]
        if candidate.reference.provenance:
            evidence_parts.append(candidate.reference.provenance)
        evidence = "; ".join(evidence_parts) or "-"
        rows.append(
            [
                _cell(str(index), styles),
                _cell(candidate.reference.name, styles),
                _cell(candidate.reference.source, styles),
                _cell(_pct(candidate.alignment.identity), styles),
                _cell(_pct(candidate.alignment.query_coverage), styles),
                _cell(_pct(candidate.alignment.reference_coverage), styles),
                _cell(_pct(candidate.sequence_origin_confidence), styles),
                _cell(_pct(candidate.canonical_identity_confidence), styles),
                _cell(evidence, styles),
            ]
        )
    if len(rows) == 1:
        rows.append([_cell("-", styles) for _ in range(9)])

    table = Table(
        rows,
        colWidths=[
            0.28 * inch,
            1.55 * inch,
            0.85 * inch,
            0.42 * inch,
            0.45 * inch,
            0.45 * inch,
            0.5 * inch,
            0.5 * inch,
            2.4 * inch,
        ],
        repeatRows=1,
    )
    table.setStyle(_table_style())
    return table


def _segment_table(result: AnalysisResult, styles) -> Table:
    rows = [
        [
            _cell("query_span", styles, header=True),
            _cell("segment", styles, header=True),
            _cell("type", styles, header=True),
            _cell("source", styles, header=True),
            _cell("id", styles, header=True),
            _cell("orient", styles, header=True),
            _cell("conf", styles, header=True),
        ]
    ]
    for segment in result.segments:
        rows.append(
            [
                _cell(f"{segment.query_start + 1}-{segment.query_end}", styles),
                _cell(segment.label, styles),
                _cell(segment.category, styles),
                _cell(segment.source, styles),
                _cell(_pct(segment.identity), styles),
                _cell(segment.orientation, styles),
                _cell(_pct(segment.confidence), styles),
            ]
        )
    if len(rows) == 1:
        rows.append([_cell("-", styles) for _ in range(7)])

    table = Table(
        rows,
        colWidths=[0.7 * inch, 2.0 * inch, 0.8 * inch, 0.95 * inch, 0.45 * inch, 0.7 * inch, 0.5 * inch],
        repeatRows=1,
    )
    table.setStyle(_table_style())
    return table


def _evidence_summary(result: AnalysisResult) -> str:
    lines: list[str] = []
    for signal in result.classification_signals[:12]:
        span = ""
        if signal.query_start is not None and signal.query_end is not None:
            span = f" query={signal.query_start + 1}-{signal.query_end}"
        evidence = signal.evidence or "Detected by local heuristic scan."
        lines.append(f"- {signal.kind}: {signal.label}; conf={signal.confidence:.1%}{span}; {evidence}")
    for notice in result.notices:
        url = f"; url={notice.source_url}" if notice.source_url else ""
        lines.append(f"- adapter: {notice.adapter}; status={notice.status}; {notice.message}{url}")
    return "\n".join(lines) if lines else "No extra signals or adapter notices recorded."


def _visual_items(result: AnalysisResult) -> list[tuple[str, Path, float]]:
    items: list[tuple[str, Path, float]] = []
    if result.visuals.query_track_png and Path(result.visuals.query_track_png).exists():
        items.append(("query_track.png", Path(result.visuals.query_track_png), 2.25 * inch))
    if result.visuals.alignment_png and Path(result.visuals.alignment_png).exists():
        items.append(("alignment_view.png", Path(result.visuals.alignment_png), 2.65 * inch))
    return items


def _scaled_image(path: Path, width: float, max_height: float):
    with PILImage.open(path) as image:
        pixel_width, pixel_height = image.size
    display_height = width * (pixel_height / max(1, pixel_width))
    if display_height > max_height:
        width = width * (max_height / display_height)
        display_height = max_height
    return ReportImage(str(path), width=width, height=display_height)


def _cell(text: object, styles, *, header: bool = False) -> Paragraph:
    style_name = "TableHead" if header else "TableCell"
    value = "" if text is None else str(text)
    return Paragraph(escape(value).replace("\n", "<br/>"), styles[style_name])


def _code_block(text: str, styles) -> Paragraph:
    return Paragraph(escape(text).replace("\n", "<br/>"), styles["CodeBlock"])


def _pct(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.0%}"


def _table_style() -> TableStyle:
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f3f4f6")),
            ("FONTNAME", (0, 0), (-1, -1), "Courier"),
            ("FONTSIZE", (0, 0), (-1, -1), 6.9),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d1d5db")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]
    )
