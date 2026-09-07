import unittest

from utr_forensics.adapters.local import LocalReferenceAdapter
from utr_forensics.alignment import smith_waterman
from utr_forensics.models import ReferenceRecord
from utr_forensics.sequences import normalize_sequence, reverse_complement


class AlignmentTests(unittest.TestCase):
    def test_smith_waterman_local_match(self):
        alignment = smith_waterman("GGGACGTACGTCCC", "ACGTACGT")
        self.assertEqual(alignment.query_start, 3)
        self.assertEqual(alignment.query_end, 11)
        self.assertEqual(alignment.identity, 1.0)
        self.assertEqual(alignment.reference_coverage, 1.0)

    def test_local_adapter_detects_reverse_complement(self):
        reference = ReferenceRecord(
            id="ref",
            name="reference",
            sequence="ACGTACGA",
            source="test",
            provenance_score=1.0,
        )
        raw_query = reverse_complement(reference.sequence)
        result = LocalReferenceAdapter([reference]).search(normalize_sequence(raw_query))
        self.assertEqual(result[0].alignment.orientation, "reverse_complement")
        self.assertTrue(result[0].exact_full_match)


if __name__ == "__main__":
    unittest.main()

