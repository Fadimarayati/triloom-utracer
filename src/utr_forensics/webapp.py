"""Small local web UI using only the Python standard library."""

from __future__ import annotations

import html
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .pipeline import run_analysis
from .sequences import SequenceValidationError


class UTRRequestHandler(BaseHTTPRequestHandler):
    references_path: Path
    output_base: Path

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path.startswith("/runs/"):
            self._serve_artifact(parsed.path)
            return
        self._send_html(_page())

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/run":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8")
        form = urllib.parse.parse_qs(body)
        raw_sequence = form.get("sequence", [""])[0]
        query_id = form.get("query_id", [""])[0].strip() or None
        deep = form.get("deep_external_search", ["off"])[0] == "on"
        run_id = time.strftime("%Y%m%d-%H%M%S")
        output_dir = self.output_base / run_id
        try:
            result = run_analysis(
                raw_sequence,
                output_dir=output_dir,
                references_path=self.references_path,
                deep_external_search=deep,
                query_id=query_id,
            )
            track_svg = Path(result.visuals.query_track_svg).read_text(encoding="utf-8") if result.visuals.query_track_svg else ""
            alignment_svg = Path(result.visuals.alignment_svg).read_text(encoding="utf-8") if result.visuals.alignment_svg else ""
            result_html = _result_panel(result, run_id, track_svg, alignment_svg)
            self._send_html(_page(raw_sequence=raw_sequence, query_id=query_id or "", result_html=result_html, deep=deep))
        except SequenceValidationError as exc:
            self._send_html(_page(raw_sequence=raw_sequence, query_id=query_id or "", error=str(exc), deep=deep), status=400)

    def _serve_artifact(self, url_path: str) -> None:
        relative = Path(url_path.removeprefix("/runs/"))
        path = (self.output_base / relative).resolve()
        base = self.output_base.resolve()
        if base not in path.parents and path != base:
            self.send_error(403)
            return
        if not path.exists() or not path.is_file():
            self.send_error(404)
            return
        content_types = {
            ".pdf": "application/pdf",
            ".json": "application/json",
            ".svg": "image/svg+xml",
            ".png": "image/png",
        }
        payload = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_types.get(path.suffix.lower(), "application/octet-stream"))
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_html(self, markup: str, *, status: int = 200) -> None:
        payload = markup.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args) -> None:
        return


def serve(*, host: str, port: int, references_path: str | Path, output_base: str | Path) -> None:
    handler = UTRRequestHandler
    handler.references_path = Path(references_path)
    handler.output_base = Path(output_base)
    handler.output_base.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer((host, port), handler)
    print(f"Triloom UTRacer UI running at http://{host}:{port}")
    server.serve_forever()


def _page(raw_sequence: str = "", query_id: str = "", result_html: str = "", error: str | None = None, deep: bool = False) -> str:
    checked = "checked" if deep else ""
    error_html = f'<div class="notice error">{html.escape(error)}</div>' if error else ""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Triloom UTRacer</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #111827;
      --muted: #4b5563;
      --line: #d1d5db;
      --panel: #f8fafc;
      --accent: #2a9d8f;
      --danger: #7f1d1d;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Arial, sans-serif;
      color: var(--ink);
      background: #ffffff;
    }}
    main {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 28px 18px 48px;
    }}
    h1 {{
      margin: 0 0 18px;
      font-size: clamp(28px, 4vw, 44px);
      letter-spacing: 0;
    }}
    form {{
      display: grid;
      gap: 14px;
      padding: 18px;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
    }}
    label {{ font-weight: 700; }}
    input[type="text"], textarea {{
      width: 100%;
      resize: vertical;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 12px;
      font: 15px/1.45 Consolas, "Courier New", monospace;
      color: var(--ink);
      background: #ffffff;
    }}
    input[type="text"] {{
      min-height: 44px;
      resize: none;
    }}
    textarea {{
      min-height: 190px;
    }}
    .row {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 14px;
    }}
    button {{
      appearance: none;
      border: 0;
      border-radius: 6px;
      background: var(--accent);
      color: #ffffff;
      font-weight: 700;
      padding: 11px 16px;
      cursor: pointer;
    }}
    button:focus-visible, input:focus-visible, textarea:focus-visible {{
      outline: 3px solid #a7f3d0;
      outline-offset: 2px;
    }}
    .notice {{
      margin: 14px 0;
      padding: 12px;
      border-radius: 6px;
      border: 1px solid var(--line);
      background: #ffffff;
    }}
    .error {{
      color: var(--danger);
      border-color: #fecaca;
      background: #fff1f2;
    }}
    .result {{
      margin-top: 18px;
      display: grid;
      gap: 16px;
    }}
    .panel {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
      overflow-x: auto;
    }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 10px;
    }}
    .metric {{
      border-left: 4px solid var(--accent);
      padding: 8px 10px;
      background: #f9fafb;
    }}
    .metric b {{
      display: block;
      font-size: 13px;
      color: var(--muted);
      margin-bottom: 4px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }}
    th, td {{
      border-bottom: 1px solid var(--line);
      text-align: left;
      padding: 8px;
      vertical-align: top;
    }}
    th {{ background: #f3f4f6; }}
    a {{ color: #0f766e; font-weight: 700; }}
  </style>
</head>
<body>
  <main>
    <h1>Triloom UTRacer</h1>
    <form method="post" action="/run">
      <label for="query_id">Query ID</label>
      <input type="text" id="query_id" name="query_id" value="{html.escape(query_id)}" placeholder="TriUTR-0001" />
      <label for="sequence">Sequence</label>
      <textarea id="sequence" name="sequence" spellcheck="false">{html.escape(raw_sequence)}</textarea>
      <div class="row">
        <label><input type="checkbox" name="deep_external_search" {checked} /> Deep external-search plan</label>
        <button type="submit">Run analysis</button>
      </div>
    </form>
    {error_html}
    {result_html}
  </main>
</body>
</html>"""


def _result_panel(result, run_id: str, track_svg: str, alignment_svg: str) -> str:
    rows = []
    for index, candidate in enumerate(result.candidates[:6], start=1):
        rows.append(
            "<tr>"
            f"<td>{index}</td>"
            f"<td>{html.escape(candidate.reference.name)}</td>"
            f"<td>{candidate.alignment.identity:.0%}</td>"
            f"<td>{candidate.alignment.query_coverage:.0%}</td>"
            f"<td>{candidate.alignment.reference_coverage:.0%}</td>"
            f"<td>{candidate.sequence_origin_confidence:.0%}</td>"
            f"<td>{candidate.canonical_identity_confidence:.0%}</td>"
            "</tr>"
        )
    if not rows:
        rows.append("<tr><td colspan='7'>No candidate above threshold.</td></tr>")

    return f"""
<section class="result">
  <div class="panel">
    <h2>Conclusion</h2>
    <div class="metrics">
      <div class="metric"><b>Top conclusion</b>{html.escape(result.conclusion)}</div>
      <div class="metric"><b>Confidence</b>{result.top_confidence:.0%}</div>
      <div class="metric"><b>Query</b>{result.normalized.length} nt; GC {result.normalized.gc_fraction:.1%}</div>
    </div>
    <p>
      <a href="/runs/{run_id}/triloom_utracer_report.pdf">PDF report</a>
      &nbsp; <a href="/runs/{run_id}/result.json">JSON</a>
      &nbsp; <a href="/runs/{run_id}/query_track.svg">Track SVG</a>
      &nbsp; <a href="/runs/{run_id}/alignment_view.svg">Alignment SVG</a>
    </p>
  </div>
  <div class="panel">{track_svg}</div>
  <div class="panel">{alignment_svg}</div>
  <div class="panel">
    <h2>Ranked Candidates</h2>
    <table>
      <thead><tr><th>Rank</th><th>Candidate</th><th>Identity</th><th>Q cov</th><th>R cov</th><th>Origin</th><th>Canonical</th></tr></thead>
      <tbody>{''.join(rows)}</tbody>
    </table>
  </div>
</section>"""
