"""Candidate scoring and segment selection."""

from __future__ import annotations

from .models import Candidate, SegmentCall


def score_candidate(candidate: Candidate) -> Candidate:
    alignment = candidate.alignment
    provenance = max(0.0, min(1.0, candidate.reference.provenance_score))
    identity = alignment.identity
    query_cov = alignment.query_coverage
    ref_cov = alignment.reference_coverage
    min_cov = min(query_cov, ref_cov)

    if candidate.exact_full_match:
        origin_confidence = 1.0
        canonical_confidence = 1.0
    else:
        origin_confidence = min(1.0, 0.55 * identity + 0.25 * ref_cov + 0.10 * query_cov + 0.10 * provenance)
        canonical_confidence = min(1.0, 0.50 * identity + 0.20 * min_cov + 0.20 * query_cov * ref_cov + 0.10 * provenance)

    rank_score = (
        alignment.score
        * (0.55 + 0.25 * identity + 0.10 * ref_cov + 0.10 * provenance)
        * (0.75 + 0.25 * query_cov)
    )

    return Candidate(
        reference=candidate.reference,
        alignment=alignment,
        rank_score=rank_score,
        sequence_origin_confidence=origin_confidence,
        canonical_identity_confidence=canonical_confidence,
        exact_full_match=candidate.exact_full_match,
        evidence=candidate.evidence,
    )


def sort_candidates(candidates: list[Candidate]) -> list[Candidate]:
    return sorted(
        candidates,
        key=lambda c: (
            c.exact_full_match,
            c.rank_score,
            c.alignment.score,
            c.alignment.identity,
            c.alignment.reference_coverage,
        ),
        reverse=True,
    )


def select_segments(candidates: list[Candidate], query_length: int) -> list[SegmentCall]:
    """Pick a compact, non-overlapping decomposition of the query."""

    if query_length <= 0:
        return []

    occupied = [False] * query_length
    segments: list[SegmentCall] = []
    eligible = [
        candidate
        for candidate in candidates
        if candidate.alignment.query_span >= 6
        and candidate.alignment.identity >= 0.72
        and candidate.alignment.score >= 10
    ]
    eligible.sort(
        key=lambda c: (
            c.alignment.query_span,
            c.alignment.identity,
            c.alignment.reference_coverage,
            c.reference.provenance_score,
        ),
        reverse=True,
    )

    for candidate in eligible:
        start = max(0, min(query_length, candidate.alignment.query_start))
        end = max(0, min(query_length, candidate.alignment.query_end))
        if end <= start:
            continue
        overlap = sum(1 for pos in range(start, end) if occupied[pos])
        if overlap / (end - start) > 0.35:
            continue
        for pos in range(start, end):
            occupied[pos] = True
        confidence = min(candidate.sequence_origin_confidence, candidate.alignment.identity)
        segments.append(
            SegmentCall(
                query_start=start,
                query_end=end,
                label=candidate.reference.name,
                category=candidate.reference.category,
                source=candidate.reference.source,
                reference_id=candidate.reference.id,
                identity=candidate.alignment.identity,
                orientation=candidate.alignment.orientation,
                confidence=confidence,
            )
        )

    return sorted(segments, key=lambda segment: (segment.query_start, segment.query_end))

