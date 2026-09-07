"""Adapter protocols and reusable metadata."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from utr_forensics.models import AdapterNotice, Candidate, NormalizedSequence


class ReferenceSearchAdapter(Protocol):
    name: str

    def search(self, query: NormalizedSequence) -> list[Candidate]:
        ...


@dataclass(frozen=True)
class ExternalAdapterSpec:
    name: str
    role: str
    source_url: str | None
    live_in_mvp: bool = False

    def notice(self, *, deep_external_search: bool) -> AdapterNotice:
        if deep_external_search and not self.live_in_mvp:
            return AdapterNotice(
                adapter=self.name,
                status="planned_not_executed",
                message=(
                    f"{self.role}. Adapter interface is present, but the MVP does not submit live queries. "
                    "Implement credentials, rate limits, caching, and consent before enabling."
                ),
                source_url=self.source_url,
            )
        return AdapterNotice(
            adapter=self.name,
            status="skipped_local_only",
            message="Skipped because the run is local-only and no query sequence was sent externally.",
            source_url=self.source_url,
        )
