# Triloom UTRacer

Triloom UTRacer is a local-first MVP for tracing unknown UTR-like nucleotide sequences. It accepts a raw DNA/RNA string, normalizes and validates it, checks both strands, searches local reference corpora, ranks candidate identities, decomposes chimeric constructs into annotated segments, and emits visual plus PDF outputs.

The default mode is private and local-only. External services are represented as modular adapters and are not contacted unless future adapters are explicitly enabled.

## What the MVP does

- Accepts raw nucleotide strings or FASTA-like input.
- Normalizes RNA `U` to DNA `T`, strips whitespace and line numbers, validates IUPAC bases, and preserves warnings.
- Searches forward and reverse-complement orientations.
- Checks sequence class signals such as UTR-like length, Kozak/start context, T7 promoter, poly(A)/poly(T), restriction sites, possible CDS fragments, and construct/linker motifs.
- Performs exact, contained, and Smith-Waterman local similarity matching against local/internal references.
- Decomposes likely engineered/chimeric sequences into non-overlapping annotated query segments.
- Ranks candidates with identity, query coverage, reference coverage, provenance, sequence-origin confidence, and canonical-identity confidence.
- Writes a horizontal query-track visual and a base-level alignment/mismatch visual as SVG and PNG.
- Generates a compact, code-like PDF result report with the top conclusion, source-by-source scan summary, best hit, ranked candidates, evidence trail, segment calls, and visuals.
- Includes a dependency-light CLI and simple local web UI.

## Repository layout

```text
src/utr_forensics/
  adapters/          Reference and external-search adapter interfaces
  alignment.py       Smith-Waterman local alignment
  classify.py        Sequence-type and construct-signal checks
  cli.py             Command-line entry point
  pipeline.py        End-to-end orchestration
  report.py          PDF report writer
  sequences.py       Normalization, validation, reverse complement
  visualization.py   SVG/PNG visual renderers
  webapp.py          Local paste-and-run UI
data/references/     Demo local reference corpus
examples/            Example unknown sequence
tests/               Unit and end-to-end tests
docs/                Adapter/source notes
```

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -r requirements.txt
```

If `python` is not on PATH inside Codex Desktop, use the bundled runtime path shown by the app or run with an installed Python 3.10+ interpreter.

## CLI usage

From the repository root:

```powershell
$env:PYTHONPATH = "src"
python -m utr_forensics.cli run --sequence-file examples/example_sequence.txt --out analysis_runs/example
```

Add a stable query label when comparing real unknowns:

```powershell
$env:PYTHONPATH = "src"
python -m utr_forensics.cli run --sequence-file examples/example_sequence.txt --query-id TriUTR-0001 --out analysis_runs/TriUTR-0001
```

Or paste a raw sequence:

```powershell
$env:PYTHONPATH = "src"
python -m utr_forensics.cli run --sequence "TAATACGACTCACTATAGGGACATTTGCTTCTGACACAACTGTGTTCACTAGCAACCTCAAACAGACACCGCCACCATGG"
```

The command writes:

- `result.json`
- `query_track.svg` and `query_track.png`
- `alignment_view.svg` and `alignment_view.png`
- `triloom_utracer_report.pdf`

## Local web UI

```powershell
$env:PYTHONPATH = "src"
python -m utr_forensics.cli web --port 8765
```

Open `http://127.0.0.1:8765`, paste a sequence, choose local-only or deep-search planning mode, and run the analysis. Results render in the browser and are saved under `web_runs/`.

## External search architecture

The MVP keeps these adapters as explicit interfaces/placeholders:

- UTRdb local dump adapter
- GENCODE local release adapter
- RefSeq local release adapter
- NCBI BLAST adapter placeholder
- NCBI UniVec/VecScreen adapter placeholder
- RNAcentral/Rfam adapter placeholder
- Addgene adapter placeholder
- patent/PatSeq adapter placeholder
- manufacturer-corpus adapter placeholder
- literature-search adapter placeholder

See `docs/reference_sources.md` for the verified public access patterns and implementation notes.

## Tests

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests
```

## Privacy

By default, sequence analysis uses only local files and writes outputs to the selected output directory. Do not commit private reference corpora, access tokens, `.env` files, or generated reports containing confidential sequences.
