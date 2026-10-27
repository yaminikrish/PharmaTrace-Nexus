"""
Unit & Integration Tests for Step 10 Dual-Run Checksum Reproducibility.
"""

import unittest
import shutil
from pharmatrace.services.generator_service import GeneratorService
from pharmatrace.infrastructure.checksums import ChecksumVerifier

class TestReproducibility(unittest.TestCase):
    def test_dual_run_checksum_parity(self):
        dir1, dir2 = "test_unit_run1", "test_unit_run2"
        for d in [dir1, dir2]:
            shutil.rmtree(d, ignore_errors=True)

        try:
            g1 = GeneratorService(seed=20261022, scale="starter", inject_anomalies=True)
            g1.generate()
            g1.export(dir1)

            g2 = GeneratorService(seed=20261022, scale="starter", inject_anomalies=True)
            g2.generate()
            g2.export(dir2)

            chk1 = ChecksumVerifier.compute_directory_checksums(dir1)
            chk2 = ChecksumVerifier.compute_directory_checksums(dir2)
            comp = ChecksumVerifier.compare_checksums(chk1, chk2)

            self.assertTrue(comp["all_identical"], "Dual runs with identical seed must match 100% bitwise")
        finally:
            shutil.rmtree(dir1, ignore_errors=True)
            shutil.rmtree(dir2, ignore_errors=True)

if __name__ == "__main__":
    unittest.main()
