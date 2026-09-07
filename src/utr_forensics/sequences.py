"""Sequence normalization and strand utilities."""

from __future__ import annotations

import re

from .models import NormalizedSequence


DNA_BASES = set("ACGTRYSWKMBDHVN")
RNA_BASES = set("ACGURYSWKMBDHVN")
ALL_BASES = DNA_BASES | RNA_BASES

COMPLEMENT = str.maketrans(
    {
        "A": "T",
        "C": "G",
        "G": "C",
        "T": "A",
        "U": "A",
        "R": "Y",
        "Y": "R",
        "S": "S",
        "W": "W",
        "K": "M",
        "M": "K",
        "B": "V",
        "D": "H",
        "H": "D",
        "V": "B",
        "N": "N",
    }
)


class SequenceValidationError(ValueError):
    """Raised when a query cannot be interpreted as a nucleotide sequence."""


def normalize_sequence(raw: str) -> NormalizedSequence:
    """Normalize raw DNA/RNA or FASTA-like input into uppercase DNA bases."""

    if raw is None:
        raise SequenceValidationError("No sequence was provided.")

    lines: list[str] = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(">"):
            continue
        lines.append(stripped)

    collapsed = "".join(lines) if lines else raw
    cleaned = re.sub(r"[\s0-9]", "", collapsed).upper()
    if not cleaned:
        raise SequenceValidationError("The sequence is empty after removing FASTA headers and whitespace.")

    invalid = sorted({base for base in cleaned if base not in ALL_BASES})
    if invalid:
        raise SequenceValidationError(f"Invalid nucleotide characters: {', '.join(invalid)}")

    warnings: list[str] = []
    has_t = "T" in cleaned
    has_u = "U" in cleaned
    if has_t and has_u:
        molecule = "mixed_dna_rna"
        warnings.append("Input contains both T and U; U was converted to T for analysis.")
    elif has_u:
        molecule = "rna"
        warnings.append("RNA input detected; U was converted to T for DNA-style reference matching.")
    else:
        molecule = "dna"

    normalized = cleaned.replace("U", "T")
    ambiguous = sorted({base for base in normalized if base not in {"A", "C", "G", "T"}})
    if ambiguous:
        warnings.append(f"Ambiguous IUPAC bases retained: {', '.join(ambiguous)}.")

    return NormalizedSequence(raw=raw, sequence=normalized, molecule=molecule, warnings=tuple(warnings))


def reverse_complement(sequence: str) -> str:
    """Return the reverse complement of a normalized DNA/RNA sequence."""

    return sequence.upper().translate(COMPLEMENT)[::-1].replace("U", "T")


def gc_fraction(sequence: str) -> float:
    if not sequence:
        return 0.0
    return sum(1 for base in sequence.upper() if base in {"G", "C"}) / len(sequence)

