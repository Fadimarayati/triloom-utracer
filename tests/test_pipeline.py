import tempfile
import unittest
from pathlib import Path

from utr_forensics.models import SourceScan
from utr_forensics.pipeline import report_filename, run_analysis


EXAMPLE = "TAATACGACTCACTATAGGGACATTTGCTTCTGACACAACTGTGTTCACTAGCAACCTCAAACAGACACCGCCACCATGG"


class PipelineTests(unittest.TestCase):
    def test_pipeline_produces_ranked_segments_and_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_analysis(EXAMPLE, output_dir=tmp, query_id="TriUTR-test")
            payload = (Path(tmp) / "result.json").read_text(encoding="utf-8")
            self.assertIn("engineered", result.conclusion.lower())
            self.assertEqual(result.query_id, "TriUTR-test")
            self.assertGreaterEqual(len(result.source_scans), 1)
            self.assertIn('"id": "TriUTR-test"', payload)
            self.assertIn('"source_scans"', payload)
            self.assertGreaterEqual(len(result.candidates), 3)
            self.assertGreaterEqual(len(result.segments), 3)
            self.assertTrue(Path(result.visuals.query_track_svg).exists())
            self.assertTrue(Path(result.visuals.query_track_png).exists())
            self.assertTrue(Path(result.visuals.alignment_svg).exists())
            self.assertTrue(Path(result.visuals.alignment_png).exists())
            self.assertTrue(Path(result.pdf_path).exists())
            self.assertEqual(Path(result.pdf_path).name, "TriUTR-test_triloom_utracer_report.pdf")

    def test_pipeline_can_append_external_source_scans(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_analysis(
                EXAMPLE,
                output_dir=tmp,
                extra_source_scans=[
                    SourceScan(
                        source="NCBI_BLAST_refseq_rna",
                        status="hit",
                        hit_count=1,
                        best_reference="Example external hit",
                        best_identity=1.0,
                        best_query_coverage=0.8,
                        best_reference_coverage=0.1,
                        note="Live external search summary.",
                    )
                ],
            )
            source_names = [scan.source for scan in result.source_scans]
            self.assertIn("NCBI_BLAST_refseq_rna", source_names)
            self.assertNotIn("ncbi_blast", source_names)
            self.assertNotIn("ncbi_blast", [notice.adapter for notice in result.notices])

    def test_report_filename_is_safe_and_stable(self):
        self.assertEqual(report_filename(None), "triloom_utracer_report.pdf")
        self.assertEqual(report_filename("TriUTR 0001/alpha"), "TriUTR_0001_alpha_triloom_utracer_report.pdf")


if __name__ == "__main__":
    unittest.main()
