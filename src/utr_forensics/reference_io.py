"""Reference-corpus loading helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .models import ReferenceRecord
from .sequences import normalize_sequence


def load_reference_file(path: str | Path) -> list[ReferenceRecord]:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".json":
        return load_json_references(path)
    if suffix in {".fa", ".fasta", ".fna"}:
        return load_fasta_references(path)
    raise ValueError(f"Unsupported reference file type: {path.suffix}")


def load_json_references(path: str | Path) -> list[ReferenceRecord]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Reference JSON must be a list of records.")
    return [record_from_mapping(item) for item in data]


def load_fasta_references(path: str | Path, *, source: str = "local_fasta") -> list[ReferenceRecord]:
    records: list[ReferenceRecord] = []
    current_header: str | None = None
    parts: list[str] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(">"):
            if current_header is not None:
                records.append(_record_from_fasta(current_header, parts, source))
            current_header = stripped[1:].strip()
            parts = []
        else:
            parts.append(stripped)
    if current_header is not None:
        records.append(_record_from_fasta(current_header, parts, source))
    return records


def record_from_mapping(mapping: dict) -> ReferenceRecord:
    normalized = normalize_sequence(str(mapping["sequence"]))
    return ReferenceRecord(
        id=str(mapping.get("id") or mapping.get("accession") or mapping["name"]),
        name=str(mapping.get("name") or mapping.get("id") or "unnamed reference"),
        sequence=normalized.sequence,
        source=str(mapping.get("source") or "local_json"),
        category=str(mapping.get("category") or "unknown"),
        utr_type=mapping.get("utr_type"),
        organism=mapping.get("organism"),
        accession=mapping.get("accession"),
        canonical_id=mapping.get("canonical_id"),
        provenance=mapping.get("provenance"),
        provenance_url=mapping.get("provenance_url"),
        provenance_score=float(mapping.get("provenance_score", 0.5)),
    )


def write_json(path: str | Path, payload: dict) -> None:
    Path(path).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _record_from_fasta(header: str, sequence_parts: Iterable[str], source: str) -> ReferenceRecord:
    first_token = header.split()[0] if header.split() else header
    normalized = normalize_sequence("".join(sequence_parts))
    return ReferenceRecord(
        id=first_token,
        name=header or first_token,
        sequence=normalized.sequence,
        source=source,
        category="unknown",
        accession=first_token,
        provenance=f"Loaded from local FASTA file with header: {header}",
        provenance_score=0.5,
    )

