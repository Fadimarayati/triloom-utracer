import tempfile
import unittest
from pathlib import Path

from utr_forensics.pipeline import run_analysis


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


if __name__ == "__main__":
    unittest.main()
