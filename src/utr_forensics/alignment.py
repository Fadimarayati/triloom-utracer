"""Local alignment for short nucleotide forensic matching."""

from __future__ import annotations

from .models import AlignmentResult


def smith_waterman(
    query: str,
    reference: str,
    *,
    orientation: str = "forward",
    original_query_length: int | None = None,
    match_score: int = 2,
    mismatch_score: int = -1,
    gap_score: int = -2,
) -> AlignmentResult:
    """Compute a Smith-Waterman local alignment.

    Coordinates are zero-based, half-open. For reverse-complement orientation,
    query coordinates are mapped back to the original query coordinate system.
    """

    n = len(query)
    m = len(reference)
    if n == 0 or m == 0:
        return AlignmentResult(
            orientation=orientation,
            score=0,
            query_start=0,
            query_end=0,
            ref_start=0,
            ref_end=0,
            aligned_query="",
            aligned_reference="",
            matches=0,
            mismatches=0,
            gaps=0,
            identity=0.0,
            query_coverage=0.0,
            reference_coverage=0.0,
        )

    scores = [[0] * (m + 1) for _ in range(n + 1)]
    pointers = [[""] * (m + 1) for _ in range(n + 1)]
    best_score = 0
    best_i = 0
    best_j = 0

    for i in range(1, n + 1):
        q = query[i - 1]
        for j in range(1, m + 1):
            r = reference[j - 1]
            diag = scores[i - 1][j - 1] + (match_score if q == r else mismatch_score)
            up = scores[i - 1][j] + gap_score
            left = scores[i][j - 1] + gap_score
            value = max(0, diag, up, left)
            scores[i][j] = value
            if value == 0:
                pointers[i][j] = ""
            elif value == diag:
                pointers[i][j] = "D"
            elif value == up:
                pointers[i][j] = "U"
            else:
                pointers[i][j] = "L"
            if value > best_score:
                best_score = value
                best_i = i
                best_j = j

    aligned_query: list[str] = []
    aligned_ref: list[str] = []
    i = best_i
    j = best_j
    while i > 0 and j > 0 and scores[i][j] > 0:
        pointer = pointers[i][j]
        if pointer == "D":
            aligned_query.append(query[i - 1])
            aligned_ref.append(reference[j - 1])
            i -= 1
            j -= 1
        elif pointer == "U":
            aligned_query.append(query[i - 1])
            aligned_ref.append("-")
            i -= 1
        elif pointer == "L":
            aligned_query.append("-")
            aligned_ref.append(reference[j - 1])
            j -= 1
        else:
            break

    query_start = i
    query_end = best_i
    ref_start = j
    ref_end = best_j
    aligned_query_str = "".join(reversed(aligned_query))
    aligned_ref_str = "".join(reversed(aligned_ref))

    if orientation == "reverse_complement":
        original_length = original_query_length or n
        mapped_start = original_length - query_end
        mapped_end = original_length - query_start
        query_start, query_end = mapped_start, mapped_end

    matches = 0
    mismatches = 0
    gaps = 0
    query_bases = 0
    ref_bases = 0
    for q, r in zip(aligned_query_str, aligned_ref_str):
        if q != "-":
            query_bases += 1
        if r != "-":
            ref_bases += 1
        if q == "-" or r == "-":
            gaps += 1
        elif q == r:
            matches += 1
        else:
            mismatches += 1

    compared = matches + mismatches + gaps
    identity = matches / compared if compared else 0.0
    query_coverage = query_bases / (original_query_length or n) if (original_query_length or n) else 0.0
    reference_coverage = ref_bases / m if m else 0.0

    return AlignmentResult(
        orientation=orientation,
        score=best_score,
        query_start=query_start,
        query_end=query_end,
        ref_start=ref_start,
        ref_end=ref_end,
        aligned_query=aligned_query_str,
        aligned_reference=aligned_ref_str,
        matches=matches,
        mismatches=mismatches,
        gaps=gaps,
        identity=identity,
        query_coverage=query_coverage,
        reference_coverage=reference_coverage,
    )


def match_line(aligned_query: str, aligned_reference: str) -> str:
    """Return a compact visual line for a pairwise alignment."""

    chars: list[str] = []
    for q, r in zip(aligned_query, aligned_reference):
        if q == "-" or r == "-":
            chars.append(" ")
        elif q == r:
            chars.append("|")
        else:
            chars.append("*")
    return "".join(chars)

