"""External adapter architecture.

These adapters intentionally emit notices instead of live queries. This keeps
the MVP private by default while documenting where production integrations
belong.
"""

from __future__ import annotations

from utr_forensics.adapters.base import ExternalAdapterSpec
from utr_forensics.models import AdapterNotice


EXTERNAL_ADAPTERS = [
    ExternalAdapterSpec(
        name="ncbi_blast",
        role="Search endogenous transcript/genome similarity through the NCBI BLAST URL API",
        source_url="https://blast.ncbi.nlm.nih.gov/doc/blast-help/urlapi.html",
    ),
    ExternalAdapterSpec(
        name="ncbi_univec_vecscreen",
        role="Screen vector, adaptor, linker, and cloning contamination with UniVec/VecScreen",
        source_url="https://www.ncbi.nlm.nih.gov/tools/vecscreen/",
    ),
    ExternalAdapterSpec(
        name="rnacentral_rfam",
        role="Check RNAcentral and Rfam for ncRNA or structured-RNA origin evidence",
        source_url="https://docs.rfam.org/en/latest/api.html",
    ),
    ExternalAdapterSpec(
        name="addgene",
        role="Search plasmid/vector context and deposited construct sequences",
        source_url="https://www.addgene.org/developers/",
    ),
    ExternalAdapterSpec(
        name="lens_patseq",
        role="Search patent-associated biological sequences and manufacturer-like inventions",
        source_url="https://www.lens.org/lens/bio/patseq",
    ),
    ExternalAdapterSpec(
        name="manufacturer_corpora",
        role="Search local or licensed manufacturer sequence catalogs",
        source_url=None,
    ),
    ExternalAdapterSpec(
        name="literature_search",
        role="Search publications and supplementary files for named UTR constructs",
        source_url="https://www.ncbi.nlm.nih.gov/pmc/tools/ftp/",
    ),
]


def build_external_notices(*, deep_external_search: bool) -> list[AdapterNotice]:
    return [adapter.notice(deep_external_search=deep_external_search) for adapter in EXTERNAL_ADAPTERS]

