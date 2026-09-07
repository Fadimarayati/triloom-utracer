"""Sequence-type and construct-signal heuristics."""

from __future__ import annotations

import re

from .models import ClassificationSignal, NormalizedSequence


RESTRICTION_SITES = {
    "EcoRI": "GAATTC",
    "BamHI": "GGATCC",
    "HindIII": "AAGCTT",
    "XhoI": "CTCGAG",
    "NotI": "GCGGCCGC",
    "BsaI": "GGTCTC",
    "SapI": "GCTCTTC",
}


def classify_sequence(normalized: NormalizedSequence) -> list[ClassificationSignal]:
    sequence = normalized.sequence
    signals: list[ClassificationSignal] = []

    if 20 <= len(sequence) <= 2000:
        signals.append(
            ClassificationSignal(
                kind="sequence_class",
                label="UTR-compatible length",
                confidence=0.55,
                evidence=f"{len(sequence)} nt query is within a common UTR-fragment range.",
            )
        )

    if normalized.gc_fraction < 0.25 or normalized.gc_fraction > 0.75:
        signals.append(
            ClassificationSignal(
                kind="composition",
                label="Unusual GC fraction",
                confidence=0.45,
                evidence=f"GC fraction is {normalized.gc_fraction:.2f}.",
            )
        )

    if normalized.ambiguous_count:
        signals.append(
            ClassificationSignal(
                kind="composition",
                label="Ambiguous bases present",
                confidence=0.6,
                evidence=f"{normalized.ambiguous_count} non-ACGT IUPAC bases retained.",
            )
        )

    for match in re.finditer("TAATACGACTCACTATAGGG", sequence):
        signals.append(
            ClassificationSignal(
                kind="construct_feature",
                label="T7 promoter motif",
                confidence=0.95,
                query_start=match.start(),
                query_end=match.end(),
                evidence="Exact T7 promoter motif detected.",
            )
        )

    for match in re.finditer(r"GCC[AG]CCATGG", sequence):
        signals.append(
            ClassificationSignal(
                kind="translation_context",
                label="Kozak/start motif",
                confidence=0.85,
                query_start=match.start(),
                query_end=match.end(),
                evidence="Matches GCCRCCATGG-style start context.",
            )
        )

    for match in re.finditer(r"A{12,}$", sequence):
        signals.append(
            ClassificationSignal(
                kind="tail",
                label="Poly(A) tail",
                confidence=0.9,
                query_start=match.start(),
                query_end=match.end(),
                evidence="Query ends with a long A run.",
            )
        )

    for match in re.finditer(r"T{12,}$", sequence):
        signals.append(
            ClassificationSignal(
                kind="tail",
                label="Poly(T) tail / reverse-complement poly(A)",
                confidence=0.85,
                query_start=match.start(),
                query_end=match.end(),
                evidence="Query ends with a long T run.",
            )
        )

    for motif in ("AATAAA", "ATTAAA"):
        for match in re.finditer(motif, sequence):
            signals.append(
                ClassificationSignal(
                    kind="polyadenylation",
                    label=f"Polyadenylation signal {motif}",
                    confidence=0.7,
                    query_start=match.start(),
                    query_end=match.end(),
                    evidence="Canonical or common alternative polyadenylation signal.",
                )
            )

    for enzyme, motif in RESTRICTION_SITES.items():
        for match in re.finditer(motif, sequence):
            signals.append(
                ClassificationSignal(
                    kind="construct_feature",
                    label=f"{enzyme} restriction site",
                    confidence=0.65,
                    query_start=match.start(),
                    query_end=match.end(),
                    evidence=f"Detected {motif}.",
                )
            )

    longest_orf = _longest_orf(sequence)
    if longest_orf >= 90 and longest_orf / max(1, len(sequence)) >= 0.35:
        signals.append(
            ClassificationSignal(
                kind="sequence_class",
                label="Possible CDS fragment",
                confidence=0.75,
                evidence=f"Longest ATG-to-stop ORF is {longest_orf} nt.",
            )
        )

    if not any(signal.kind == "construct_feature" for signal in signals) and longest_orf < 90:
        signals.append(
            ClassificationSignal(
                kind="sequence_class",
                label="No obvious construct feature in heuristic scan",
                confidence=0.35,
                evidence="Local heuristics did not find common promoter, linker, or restriction motifs.",
            )
        )

    return signals


def _longest_orf(sequence: str) -> int:
    stops = {"TAA", "TAG", "TGA"}
    longest = 0
    for frame in range(3):
        start = None
        for pos in range(frame, len(sequence) - 2, 3):
            codon = sequence[pos : pos + 3]
            if start is None and codon == "ATG":
                start = pos
            elif start is not None and codon in stops:
                longest = max(longest, pos + 3 - start)
                start = None
        if start is not None:
            longest = max(longest, len(sequence) - start)
    return longest

