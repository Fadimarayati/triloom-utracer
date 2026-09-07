"""Reference and external-search adapters."""

from .external import build_external_notices
from .local import LocalReferenceAdapter

__all__ = ["LocalReferenceAdapter", "build_external_notices"]

