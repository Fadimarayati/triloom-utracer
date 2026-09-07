# Reference And API Notes

These notes capture the public access patterns used to shape the adapters. Live network integrations are intentionally not enabled in the MVP.

## UTRdb

UTRdb is a curated database of eukaryotic 5-prime and 3-prime untranslated regions and supports organism-level data downloads. The MVP includes a local-file adapter so downloaded UTRdb FASTA/JSON exports can be indexed without sending user sequences outside the machine.

Useful sources:

- UTRdb site: https://utrdb.cloud.ba.infn.it/
- UTRdb paper / database description: https://academic.oup.com/nar/article/38/suppl_1/D75/3112292

## GENCODE

GENCODE releases are available through the project website and FTP, including GTF/GFF3 annotation and transcript FASTA files. A production adapter should derive 5-prime and 3-prime UTR intervals from transcript annotations and genome/transcript FASTA for the target species and release.

Useful source:

- GENCODE data access: https://www.gencodegenes.org/pages/data_access.html

## RefSeq

RefSeq records can be accessed from NCBI release files, NCBI Datasets, or E-utilities. A production adapter should pin database version/release, accession, organism, and retrieval date.

Useful sources:

- RefSeq overview: https://www.ncbi.nlm.nih.gov/refseq/
- NCBI Datasets: https://www.ncbi.nlm.nih.gov/datasets/docs/v2/
- E-utilities: https://www.ncbi.nlm.nih.gov/books/NBK25499/

## NCBI BLAST

NCBI BLAST offers a URL/API interface for submitting and retrieving searches. Production use should follow NCBI's usage guidance, include a tool/email where appropriate, avoid rapid polling, and cache results.

Useful source:

- BLAST URL API: https://blast.ncbi.nlm.nih.gov/doc/blast-help/urlapi.html

## UniVec / VecScreen

VecScreen compares a query to UniVec to identify vector/adaptor/linker-derived segments. A production adapter should use it as a contamination/construct-origin check rather than a canonical UTR identity source.

Useful source:

- VecScreen: https://www.ncbi.nlm.nih.gov/tools/vecscreen/

## RNAcentral And Rfam

RNAcentral and Rfam can help distinguish ncRNA or structured RNA origins from UTR annotations. A production adapter should separate "noncoding RNA origin" evidence from "canonical UTR identity" evidence.

Useful sources:

- RNAcentral API help: https://rnacentral.org/help/public-database
- Rfam API docs: https://docs.rfam.org/en/latest/api.html

## Addgene

Addgene is useful for vector/plasmid sequence context. Depending on endpoint availability and terms, production integration may require API access, browser workflow support, or local downloaded corpora.

Useful source:

- Addgene developers: https://www.addgene.org/developers/

## Patent / PatSeq Search

Patent sequence resources are important for synthetic or manufacturer-designed UTRs that may not appear in genome databases. Production integration should keep patent source, jurisdiction, publication number, sequence id, and retrieval date.

Useful source:

- Lens PatSeq: https://www.lens.org/lens/bio/patseq

