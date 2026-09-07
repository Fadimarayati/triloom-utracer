"""SVG and PNG visual outputs for sequence forensic results."""

from __future__ import annotations

from html import escape
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .alignment import match_line
from .models import Candidate, SegmentCall


PALETTE = [
    "#2a9d8f",
    "#e76f51",
    "#457b9d",
    "#f2b134",
    "#7a5cfa",
    "#6a994e",
    "#bc4749",
]


def write_visuals(
    *,
    query_sequence: str,
    segments: list[SegmentCall],
    top_candidate: Candidate | None,
    output_dir: str | Path,
) -> dict[str, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = {
        "query_track_svg": output / "query_track.svg",
        "query_track_png": output / "query_track.png",
        "alignment_svg": output / "alignment_view.svg",
        "alignment_png": output / "alignment_view.png",
    }
    paths["query_track_svg"].write_text(render_query_track_svg(query_sequence, segments), encoding="utf-8")
    write_query_track_png(query_sequence, segments, paths["query_track_png"])
    paths["alignment_svg"].write_text(render_alignment_svg(top_candidate), encoding="utf-8")
    write_alignment_png(top_candidate, paths["alignment_png"])
    return paths


def render_query_track_svg(query_sequence: str, segments: list[SegmentCall]) -> str:
    length = max(1, len(query_sequence))
    width = 1000
    left = 80
    right = 40
    track_width = width - left - right
    row_height = 44
    height = 135 + max(1, len(segments)) * row_height
    y0 = 74

    def x_for(position: int) -> float:
        return left + track_width * position / length

    rows = []
    rows.append(f'<line x1="{left}" y1="{y0}" x2="{left + track_width}" y2="{y0}" stroke="#4b5563" stroke-width="8" stroke-linecap="round" />')
    rows.append(f'<text x="{left}" y="{y0 - 18}" font-size="13" fill="#111827">Query: {length} nt</text>')
    rows.append(f'<text x="{left}" y="{y0 + 30}" font-size="11" fill="#4b5563">1</text>')
    rows.append(f'<text x="{left + track_width - 24}" y="{y0 + 30}" font-size="11" fill="#4b5563">{length}</text>')

    if not segments:
        rows.append(f'<text x="{left}" y="{y0 + 70}" font-size="14" fill="#7f1d1d">No reference segments passed the display threshold.</text>')
    for index, segment in enumerate(segments):
        color = PALETTE[index % len(PALETTE)]
        y = y0 + 48 + index * row_height
        x = x_for(segment.query_start)
        w = max(2, x_for(segment.query_end) - x)
        label = f"{segment.label} ({segment.query_start + 1}-{segment.query_end}, {segment.identity:.0%})"
        rows.append(f'<rect x="{x:.2f}" y="{y}" width="{w:.2f}" height="20" rx="4" fill="{color}" />')
        rows.append(f'<line x1="{x:.2f}" y1="{y}" x2="{x:.2f}" y2="{y - 12}" stroke="{color}" stroke-width="1.5" />')
        rows.append(f'<text x="{left}" y="{y + 36}" font-size="12" fill="#111827">{escape(label)}</text>')

    return "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            '<rect width="100%" height="100%" fill="#ffffff" />',
            '<text x="24" y="28" font-size="18" font-family="Arial, sans-serif" font-weight="700" fill="#111827">Triloom UTRacer Query Segment Evidence</text>',
            f'<g font-family="Arial, sans-serif">{chr(10).join(rows)}</g>',
            "</svg>",
        ]
    )


def render_alignment_svg(top_candidate: Candidate | None, wrap: int = 80) -> str:
    width = 1040
    if top_candidate is None:
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="140" viewBox="0 0 {width} 140">'
            '<rect width="100%" height="100%" fill="#ffffff" />'
            '<text x="24" y="32" font-size="18" font-family="Arial, sans-serif" font-weight="700" fill="#111827">Base-Level Alignment</text>'
            '<text x="24" y="76" font-size="14" font-family="Arial, sans-serif" fill="#7f1d1d">No local alignment passed the threshold.</text>'
            "</svg>"
        )

    alignment = top_candidate.alignment
    matches = match_line(alignment.aligned_query, alignment.aligned_reference)
    chunks = []
    for start in range(0, len(alignment.aligned_query), wrap):
        chunks.append(
            (
                alignment.aligned_query[start : start + wrap],
                matches[start : start + wrap],
                alignment.aligned_reference[start : start + wrap],
            )
        )

    line_height = 19
    block_height = line_height * 4 + 16
    height = 110 + len(chunks) * block_height
    rows = [
        f'<text x="24" y="32" font-size="18" font-family="Arial, sans-serif" font-weight="700" fill="#111827">Base-Level Alignment</text>',
        f'<text x="24" y="58" font-size="13" font-family="Arial, sans-serif" fill="#374151">{escape(top_candidate.reference.name)}; {alignment.orientation}; identity {alignment.identity:.1%}; query coverage {alignment.query_coverage:.1%}</text>',
    ]
    y = 88
    for query_chunk, match_chunk, ref_chunk in chunks:
        rows.append(_svg_alignment_line("Query", query_chunk, match_chunk, y))
        rows.append(_svg_match_line(match_chunk, y + line_height))
        rows.append(_svg_alignment_line("Ref", ref_chunk, match_chunk, y + line_height * 2))
        y += block_height

    return "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            '<rect width="100%" height="100%" fill="#ffffff" />',
            *rows,
            "</svg>",
        ]
    )


def write_query_track_png(query_sequence: str, segments: list[SegmentCall], path: str | Path) -> None:
    length = max(1, len(query_sequence))
    width = 1200
    left = 100
    right = 60
    track_width = width - left - right
    row_height = 50
    height = 165 + max(1, len(segments)) * row_height
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    font = _font(16)
    small = _font(13)
    title = _font(23)

    draw.text((28, 24), "Triloom UTRacer Query Segment Evidence", fill="#111827", font=title)
    y0 = 94
    draw.line((left, y0, left + track_width, y0), fill="#4b5563", width=8)
    draw.text((left, y0 - 28), f"Query: {length} nt", fill="#111827", font=small)
    draw.text((left, y0 + 18), "1", fill="#4b5563", font=small)
    draw.text((left + track_width - 34, y0 + 18), str(length), fill="#4b5563", font=small)

    if not segments:
        draw.text((left, y0 + 70), "No reference segments passed the display threshold.", fill="#7f1d1d", font=font)

    for index, segment in enumerate(segments):
        color = PALETTE[index % len(PALETTE)]
        y = y0 + 54 + index * row_height
        x = left + track_width * segment.query_start / length
        x2 = left + track_width * segment.query_end / length
        draw.rounded_rectangle((x, y, max(x + 2, x2), y + 22), radius=4, fill=color)
        label = f"{segment.label} ({segment.query_start + 1}-{segment.query_end}, {segment.identity:.0%})"
        draw.text((left, y + 30), label, fill="#111827", font=small)

    image.save(path)


def write_alignment_png(top_candidate: Candidate | None, path: str | Path, wrap: int = 80) -> None:
    width = 1280
    title = _font(24)
    font = _mono_font(16)
    small = _font(14)
    if top_candidate is None:
        image = Image.new("RGB", (width, 160), "white")
        draw = ImageDraw.Draw(image)
        draw.text((30, 26), "Base-Level Alignment", fill="#111827", font=title)
        draw.text((30, 78), "No local alignment passed the threshold.", fill="#7f1d1d", font=small)
        image.save(path)
        return

    alignment = top_candidate.alignment
    matches = match_line(alignment.aligned_query, alignment.aligned_reference)
    chunks = [
        (
            alignment.aligned_query[start : start + wrap],
            matches[start : start + wrap],
            alignment.aligned_reference[start : start + wrap],
        )
        for start in range(0, len(alignment.aligned_query), wrap)
    ]
    line_height = 22
    block_height = line_height * 4 + 18
    height = 120 + len(chunks) * block_height
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw.text((30, 24), "Base-Level Alignment", fill="#111827", font=title)
    subtitle = (
        f"{top_candidate.reference.name}; {alignment.orientation}; "
        f"identity {alignment.identity:.1%}; query coverage {alignment.query_coverage:.1%}"
    )
    draw.text((30, 60), subtitle, fill="#374151", font=small)

    y = 96
    for query_chunk, match_chunk, ref_chunk in chunks:
        _draw_alignment_row(draw, "Query", query_chunk, match_chunk, 30, y, font)
        _draw_match_row(draw, match_chunk, 30, y + line_height, font)
        _draw_alignment_row(draw, "Ref", ref_chunk, match_chunk, 30, y + line_height * 2, font)
        y += block_height

    image.save(path)


def _svg_alignment_line(label: str, sequence: str, match_chunk: str, y: int) -> str:
    spans = []
    x = 86
    for base, marker in zip(sequence, match_chunk):
        color = "#047857" if marker == "|" else "#b91c1c" if marker == "*" else "#6b7280"
        spans.append(f'<tspan x="{x}" fill="{color}">{escape(base)}</tspan>')
        x += 11
    return (
        f'<text x="24" y="{y}" font-size="14" font-family="Courier New, monospace" fill="#111827">'
        f'<tspan x="24">{label:<5}</tspan>{"".join(spans)}</text>'
    )


def _svg_match_line(match_chunk: str, y: int) -> str:
    spans = []
    x = 86
    for marker in match_chunk:
        color = "#047857" if marker == "|" else "#b91c1c" if marker == "*" else "#6b7280"
        spans.append(f'<tspan x="{x}" fill="{color}">{escape(marker or " ")}</tspan>')
        x += 11
    return f'<text x="24" y="{y}" font-size="14" font-family="Courier New, monospace">{"".join(spans)}</text>'


def _draw_alignment_row(draw: ImageDraw.ImageDraw, label: str, sequence: str, markers: str, x: int, y: int, font) -> None:
    draw.text((x, y), f"{label:<6}", fill="#111827", font=font)
    cx = x + 80
    for base, marker in zip(sequence, markers):
        fill = "#047857" if marker == "|" else "#b91c1c" if marker == "*" else "#6b7280"
        draw.text((cx, y), base, fill=fill, font=font)
        cx += 13


def _draw_match_row(draw: ImageDraw.ImageDraw, markers: str, x: int, y: int, font) -> None:
    cx = x + 80
    for marker in markers:
        fill = "#047857" if marker == "|" else "#b91c1c" if marker == "*" else "#6b7280"
        draw.text((cx, y), marker, fill=fill, font=font)
        cx += 13


def _font(size: int):
    for name in ("arial.ttf", "Calibri.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _mono_font(size: int):
    for name in ("consola.ttf", "cour.ttf", "DejaVuSansMono.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()
