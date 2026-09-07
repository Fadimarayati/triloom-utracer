import unittest

from utr_forensics.sequences import SequenceValidationError, normalize_sequence, reverse_complement


class SequenceTests(unittest.TestCase):
    def test_normalizes_fasta_rna(self):
        normalized = normalize_sequence(">seq\nacgu acgu\n")
        self.assertEqual(normalized.sequence, "ACGTACGT")
        self.assertEqual(normalized.molecule, "rna")
        self.assertTrue(normalized.warnings)

    def test_rejects_invalid_characters(self):
        with self.assertRaises(SequenceValidationError):
            normalize_sequence("ACGTXYZ")

    def test_reverse_complement_keeps_iupac(self):
        self.assertEqual(reverse_complement("ACGTRYSWKMBDHVN"), "NBDHVKMWSRYACGT")


if __name__ == "__main__":
    unittest.main()

