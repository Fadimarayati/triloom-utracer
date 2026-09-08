"""End-to-end sequence forensic pipeline."""

from __future__ import annotations

from pathlib import Path

from .adapters.external import build_external_notices
from .adapters.local import LocalReferenceAdapter
from .classify import classify_sequence
from .models import AdapterNotice, AnalysisResult, Candidate, NormalizedSequence, SourceScan, VisualOutputs
from .ranking import select_segments
from .reference_io import write_json
from .report import write_pdf_report
from .sequences import normalize_sequence
from .visualization import write_visuals


def default_reference_path() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "references" / "sample_references.json"


def run_analysis(
    raw_sequence: str,
    *,
    output_dir: str | Path,
    references_path: str | Path | None = None,
    deep_external_search: bool = False,
    query_id: str | None = None,
) -> AnalysisResult:
    normalized = normalize_sequence(raw_sequence)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    reference_file = Path(references_path) if references_path else default_reference_path()
    local_adapter = LocalReferenceAdapter.from_file(reference_file)
    candidates = local_adapter.search(normalized)
    signals = classify_sequence(normalized)
    segments = select_segments(candidates, normalized.length)
    notices = build_external_notices(deep_external_search=deep_external_search)
    source_scans = build_source_scans(candidates, notices)

    conclusion, top_confidence = build_conclusion(normalized, candidates, segments, signals)
    result = AnalysisResult(
        normalized=normalized,
        conclusion=conclusion,
        top_confidence=top_confidence,
        candidates=candidates,
        segments=segments,
        classification_signals=signals,
        notices=notices,
        output_dir=output,
        query_id=query_id,
        source_scans=source_scans,
    )

    visual_paths = write_visuals(
        query_sequence=normalized.sequence,
        segments=segments,
        top_candidate=candidates[0] if candidates else None,
        output_dir=output,
    )
    result.visuals = VisualOutputs(
        query_track_svg=visual_paths["query_track_svg"],
        query_track_png=visual_paths["query_track_png"],
        alignment_svg=visual_paths["alignment_svg"],
        alignment_png=visual_paths["alignment_png"],
    )
    result.pdf_path = write_pdf_report(result, output / "triloom_utracer_report.pdf")
    write_json(output / "result.json", result.to_dict())
    return result


def build_source_scans(candidates: list[Candidate], notices: list[AdapterNotice]) -> list[SourceScan]:
    scans: list[SourceScan] = []
    by_source: dict[str, list[Candidate]] = {}
    for candidate in candidates:
        by_source.setdefault(candidate.reference.source, []).append(candidate)

    for source, source_candidates in sorted(by_source.items()):
        best = source_candidates[0]
        scans.append(
            SourceScan(
                source=source,
                status="hit",
                hit_count=len(source_candidates),
                best_reference=best.reference.name,
                best_identity=best.alignment.identity,
                best_query_coverage=best.alignment.query_coverage,
                best_reference_coverage=best.alignment.reference_coverage,
                best_origin_confidence=best.sequence_origin_confidence,
                best_canonical_confidence=best.canonical_identity_confidence,
                note=best.evidence[0] if best.evidence else "Local alignment hit.",
            )
        )

    for notice in notices:
        scan_status = "skipped" if notice.status.startswith("skipped") else notice.status
        scans.append(
            SourceScan(
                source=notice.adapter,
                status=scan_status,
                hit_count=0,
                note=notice.message,
            )
        )
    return scans


def build_conclusion(normalized: NormalizedSequence, candidates, segments, signals) -> tuple[str, float]:
    if not candidates:
        return "No confident local identity found; external or expanded local references recommended.", 0.0

    top = candidates[0]
    construct_labels = [signal.label for signal in signals if signal.kind in {"construct_feature", "translation_context"}]
    categories = {segment.category for segment in segments}
    sources = {segment.reference_id for segment in segments}
    segment_coverage = sum(segment.length for segment in segments) / max(1, normalized.length)
    looks_chimeric = len(sources) >= 2 and segment_coverage >= 0.6

    if top.exact_full_match:
        return (
            f"Exact {top.alignment.orientation} match to {top.reference.name}.",
            top.canonical_identity_confidence,
        )

    if looks_chimeric:
        main = top.reference.name
        extras = ", ".join(segment.label for segment in segments if segment.reference_id != top.reference.id)
        if construct_labels:
            return (
                f"Likely engineered/chimeric sequence dominated by {main}; additional segments: {extras}.",
                max(top.sequence_origin_confidence, segment_coverage * 0.9),
            )
        return (
            f"Likely composite sequence dominated by {main}; additional segments: {extras}.",
            max(top.sequence_origin_confidence, segment_coverage * 0.8),
        )

    if "utr" in categories or top.reference.category == "utr":
        return (
            f"Best local origin is {top.reference.name}; not an exact canonical identity because only part of the query/reference aligns.",
            top.sequence_origin_confidence,
        )

    return (
        f"Best local match is {top.reference.name}; expand references or external search for canonical identity.",
        top.sequence_origin_confidence,
    )
