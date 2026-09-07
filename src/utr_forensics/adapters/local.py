"""Local reference-corpus adapter."""

from __future__ import annotations

from pathlib import Path

from utr_forensics.alignment import smith_waterman
from utr_forensics.models import Candidate, NormalizedSequence, ReferenceRecord
from utr_forensics.ranking import score_candidate, sort_candidates
from utr_forensics.reference_io import load_reference_file
from utr_forensics.sequences import reverse_complement


class LocalReferenceAdapter:
    name = "local_reference"

    def __init__(self, references: list[ReferenceRecord], *, min_score: int = 10, min_identity: float = 0.65):
        self.references = references
        self.min_score = min_score
        self.min_identity = min_identity

    @classmethod
    def from_file(cls, path: str | Path, *, min_score: int = 10, min_identity: float = 0.65) -> "LocalReferenceAdapter":
        return cls(load_reference_file(path), min_score=min_score, min_identity=min_identity)

    def search(self, query: NormalizedSequence) -> list[Candidate]:
        candidates: list[Candidate] = []
        query_sequence = query.sequence
        reverse_query = reverse_complement(query_sequence)

        for reference in self.references:
            forward = smith_waterman(
                query_sequence,
                reference.sequence,
                orientation="forward",
                original_query_length=query.length,
            )
            reverse = smith_waterman(
                reverse_query,
                reference.sequence,
                orientation="reverse_complement",
                original_query_length=query.length,
            )
            best = forward
            if (reverse.score, reverse.identity, reverse.reference_coverage) > (
                forward.score,
                forward.identity,
                forward.reference_coverage,
            ):
                best = reverse

            if best.score < self.min_score or best.identity < self.min_identity:
                continue
            if len(reference.sequence) < 20 and best.identity < 0.9:
                continue

            exact_forward = query_sequence == reference.sequence
            exact_reverse = reverse_query == reference.sequence
            evidence = _build_evidence(query_sequence, reverse_query, reference, best, exact_forward, exact_reverse)
            raw_candidate = Candidate(
                reference=reference,
                alignment=best,
                rank_score=0.0,
                sequence_origin_confidence=0.0,
                canonical_identity_confidence=0.0,
                exact_full_match=exact_forward or exact_reverse,
                evidence=tuple(evidence),
            )
            candidates.append(score_candidate(raw_candidate))

        return sort_candidates(candidates)


class UTRdbAdapter(LocalReferenceAdapter):
    """Adapter for local UTRdb FASTA/JSON exports."""

    name = "utrdb_local_dump"


class GENCODEAdapter(LocalReferenceAdapter):
    """Adapter for pre-extracted local GENCODE UTR FASTA/JSON corpora."""

    name = "gencode_local_release"


class RefSeqAdapter(LocalReferenceAdapter):
    """Adapter for pre-extracted local RefSeq UTR FASTA/JSON corpora."""

    name = "refseq_local_release"


def _build_evidence(
    query_sequence: str,
    reverse_query: str,
    reference: ReferenceRecord,
    alignment,
    exact_forward: bool,
    exact_reverse: bool,
) -> list[str]:
    evidence: list[str] = []
    if exact_forward:
        evidence.append("Full query is an exact forward-strand match to the reference.")
    elif exact_reverse:
        evidence.append("Full query is an exact reverse-complement match to the reference.")
    elif reference.sequence in query_sequence:
        evidence.append("Reference sequence is contained exactly inside the forward query.")
    elif reference.sequence in reverse_query:
        evidence.append("Reference sequence is contained exactly inside the reverse-complement query.")
    else:
        evidence.append("Best local alignment found by Smith-Waterman.")

    evidence.append(
        f"Alignment spans query {alignment.query_start + 1}-{alignment.query_end} "
        f"and reference {alignment.ref_start + 1}-{alignment.ref_end}."
    )
    if reference.provenance:
        evidence.append(reference.provenance)
    return evidence
