"""Shared data models for the UTR forensics pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class NormalizedSequence:
    raw: str
    sequence: str
    molecule: str
    warnings: tuple[str, ...] = ()

    @property
    def length(self) -> int:
        return len(self.sequence)

    @property
    def gc_fraction(self) -> float:
        if not self.sequence:
            return 0.0
        gc = sum(1 for base in self.sequence if base in {"G", "C"})
        return gc / self.length

    @property
    def ambiguous_count(self) -> int:
        return sum(1 for base in self.sequence if base not in {"A", "C", "G", "T"})


@dataclass(frozen=True)
class ReferenceRecord:
    id: str
    name: str
    sequence: str
    source: str
    category: str = "unknown"
    utr_type: str | None = None
    organism: str | None = None
    accession: str | None = None
    canonical_id: str | None = None
    provenance: str | None = None
    provenance_url: str | None = None
    provenance_score: float = 0.5

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "source": self.source,
            "category": self.category,
            "utr_type": self.utr_type,
            "organism": self.organism,
            "accession": self.accession,
            "canonical_id": self.canonical_id,
            "provenance": self.provenance,
            "provenance_url": self.provenance_url,
            "provenance_score": self.provenance_score,
            "length": len(self.sequence),
        }


@dataclass(frozen=True)
class AlignmentResult:
    orientation: str
    score: int
    query_start: int
    query_end: int
    ref_start: int
    ref_end: int
    aligned_query: str
    aligned_reference: str
    matches: int
    mismatches: int
    gaps: int
    identity: float
    query_coverage: float
    reference_coverage: float

    @property
    def query_span(self) -> int:
        return max(0, self.query_end - self.query_start)

    @property
    def ref_span(self) -> int:
        return max(0, self.ref_end - self.ref_start)

    def to_dict(self) -> dict[str, Any]:
        return {
            "orientation": self.orientation,
            "score": self.score,
            "query_start": self.query_start,
            "query_end": self.query_end,
            "ref_start": self.ref_start,
            "ref_end": self.ref_end,
            "matches": self.matches,
            "mismatches": self.mismatches,
            "gaps": self.gaps,
            "identity": round(self.identity, 4),
            "query_coverage": round(self.query_coverage, 4),
            "reference_coverage": round(self.reference_coverage, 4),
            "aligned_query": self.aligned_query,
            "aligned_reference": self.aligned_reference,
        }


@dataclass(frozen=True)
class Candidate:
    reference: ReferenceRecord
    alignment: AlignmentResult
    rank_score: float
    sequence_origin_confidence: float
    canonical_identity_confidence: float
    exact_full_match: bool = False
    evidence: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "reference": self.reference.to_dict(),
            "alignment": self.alignment.to_dict(),
            "rank_score": round(self.rank_score, 4),
            "sequence_origin_confidence": round(self.sequence_origin_confidence, 4),
            "canonical_identity_confidence": round(self.canonical_identity_confidence, 4),
            "exact_full_match": self.exact_full_match,
            "evidence": list(self.evidence),
        }


@dataclass(frozen=True)
class ClassificationSignal:
    kind: str
    label: str
    confidence: float
    query_start: int | None = None
    query_end: int | None = None
    evidence: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "label": self.label,
            "confidence": round(self.confidence, 4),
            "query_start": self.query_start,
            "query_end": self.query_end,
            "evidence": self.evidence,
        }


@dataclass(frozen=True)
class SegmentCall:
    query_start: int
    query_end: int
    label: str
    category: str
    source: str
    reference_id: str
    identity: float
    orientation: str
    confidence: float

    @property
    def length(self) -> int:
        return max(0, self.query_end - self.query_start)

    def to_dict(self) -> dict[str, Any]:
        return {
            "query_start": self.query_start,
            "query_end": self.query_end,
            "label": self.label,
            "category": self.category,
            "source": self.source,
            "reference_id": self.reference_id,
            "identity": round(self.identity, 4),
            "orientation": self.orientation,
            "confidence": round(self.confidence, 4),
            "length": self.length,
        }


@dataclass(frozen=True)
class AdapterNotice:
    adapter: str
    status: str
    message: str
    source_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "adapter": self.adapter,
            "status": self.status,
            "message": self.message,
            "source_url": self.source_url,
        }


@dataclass
class VisualOutputs:
    query_track_svg: Path | None = None
    query_track_png: Path | None = None
    alignment_svg: Path | None = None
    alignment_png: Path | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "query_track_svg": str(self.query_track_svg) if self.query_track_svg else None,
            "query_track_png": str(self.query_track_png) if self.query_track_png else None,
            "alignment_svg": str(self.alignment_svg) if self.alignment_svg else None,
            "alignment_png": str(self.alignment_png) if self.alignment_png else None,
        }


@dataclass
class AnalysisResult:
    normalized: NormalizedSequence
    conclusion: str
    top_confidence: float
    candidates: list[Candidate]
    segments: list[SegmentCall]
    classification_signals: list[ClassificationSignal]
    notices: list[AdapterNotice]
    output_dir: Path
    visuals: VisualOutputs = field(default_factory=VisualOutputs)
    pdf_path: Path | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": {
                "sequence": self.normalized.sequence,
                "length": self.normalized.length,
                "molecule": self.normalized.molecule,
                "gc_fraction": round(self.normalized.gc_fraction, 4),
                "ambiguous_count": self.normalized.ambiguous_count,
                "warnings": list(self.normalized.warnings),
            },
            "conclusion": self.conclusion,
            "top_confidence": round(self.top_confidence, 4),
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "segments": [segment.to_dict() for segment in self.segments],
            "classification_signals": [signal.to_dict() for signal in self.classification_signals],
            "notices": [notice.to_dict() for notice in self.notices],
            "visuals": self.visuals.to_dict(),
            "pdf_path": str(self.pdf_path) if self.pdf_path else None,
        }

