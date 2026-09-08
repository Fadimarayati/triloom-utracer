"""Command-line interface for Triloom UTRacer."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .pipeline import default_reference_path, run_analysis
from .sequences import SequenceValidationError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="triloom-utracer", description="Trace unknown UTR-like nucleotide sequences.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run the pipeline on a sequence.")
    source = run_parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--sequence", help="Raw DNA/RNA sequence string.")
    source.add_argument("--sequence-file", type=Path, help="File containing a raw sequence or FASTA entry.")
    run_parser.add_argument("--references", type=Path, default=default_reference_path(), help="Local JSON/FASTA reference corpus.")
    run_parser.add_argument("--out", type=Path, default=Path("analysis_runs/latest"), help="Output directory.")
    run_parser.add_argument("--query-id", help="Optional identifier shown in result files and PDF reports.")
    run_parser.add_argument(
        "--deep-external-search",
        action="store_true",
        help="Emit the planned external-search adapter steps. The MVP still does not submit live external queries.",
    )

    web_parser = subparsers.add_parser("web", help="Start the simple local web UI.")
    web_parser.add_argument("--host", default="127.0.0.1", help="Bind host.")
    web_parser.add_argument("--port", type=int, default=8765, help="Bind port.")
    web_parser.add_argument("--references", type=Path, default=default_reference_path(), help="Local JSON/FASTA reference corpus.")
    web_parser.add_argument("--out", type=Path, default=Path("web_runs"), help="Base output directory for web runs.")

    args = parser.parse_args(argv)
    if args.command == "run":
        return _run(args)
    if args.command == "web":
        from .webapp import serve

        serve(host=args.host, port=args.port, references_path=args.references, output_base=args.out)
        return 0
    return 2


def _run(args) -> int:
    raw = args.sequence if args.sequence is not None else args.sequence_file.read_text(encoding="utf-8")
    try:
        result = run_analysis(
            raw,
            output_dir=args.out,
            references_path=args.references,
            deep_external_search=args.deep_external_search,
            query_id=args.query_id,
        )
    except SequenceValidationError as exc:
        print(f"Sequence validation failed: {exc}", file=sys.stderr)
        return 1

    print(f"Conclusion: {result.conclusion}")
    print(f"Confidence: {result.top_confidence:.0%}")
    print(f"Output directory: {result.output_dir.resolve()}")
    print(f"PDF: {result.pdf_path.resolve() if result.pdf_path else 'not generated'}")
    print("Top candidates:")
    for index, candidate in enumerate(result.candidates[:5], start=1):
        print(
            f"  {index}. {candidate.reference.name} | "
            f"identity {candidate.alignment.identity:.0%}, "
            f"query {candidate.alignment.query_coverage:.0%}, "
            f"reference {candidate.alignment.reference_coverage:.0%}, "
            f"origin {candidate.sequence_origin_confidence:.0%}, "
            f"canonical {candidate.canonical_identity_confidence:.0%}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
