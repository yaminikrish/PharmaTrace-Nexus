"""
Cryptographic Checksum and Reproducibility Verification Utilities.
Computes SHA-256 digests and validates bitwise determinism across generations.
"""

import os
import hashlib
from typing import Dict, Any

class ChecksumVerifier:
    @staticmethod
    def compute_directory_checksums(directory: str) -> Dict[str, Dict[str, Any]]:
        csv_dir = os.path.join(directory, "csv")
        results = {}
        if os.path.exists(csv_dir):
            for filename in sorted(os.listdir(csv_dir)):
                if filename.endswith(".csv"):
                    filepath = os.path.join(csv_dir, filename)
                    with open(filepath, "rb") as f:
                        content = f.read()
                        sha = hashlib.sha256(content).hexdigest()
                        row_count = len(content.splitlines()) - 1
                        results[filename] = {
                            "sha256": sha,
                            "rows": row_count,
                            "bytes": len(content)
                        }

        # Ground truth
        gt_file = os.path.join(directory, "ground_truth.json")
        if os.path.exists(gt_file):
            with open(gt_file, "rb") as f:
                content = f.read()
                results["ground_truth.json"] = {
                    "sha256": hashlib.sha256(content).hexdigest(),
                    "bytes": len(content)
                }

        # SQLite
        db_file = os.path.join(directory, "traceability.db")
        if os.path.exists(db_file):
            with open(db_file, "rb") as f:
                results["traceability.db"] = {
                    "bytes": len(f.read())
                }
        return results

    @staticmethod
    def compare_checksums(run1_meta: Dict[str, Dict[str, Any]], run2_meta: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        all_match = True
        comparison = {}
        for file, meta1 in run1_meta.items():
            meta2 = run2_meta.get(file, {})
            rows1 = meta1.get("rows", "-")
            rows2 = meta2.get("rows", "-")
            sha1 = meta1.get("sha256", "")
            sha2 = meta2.get("sha256", "")

            if sha1 and sha2:
                match = (sha1 == sha2 and rows1 == rows2)
            else:
                match = (meta1.get("bytes") == meta2.get("bytes"))

            if not match:
                all_match = False

            comparison[file] = {
                "run1_rows": rows1,
                "run2_rows": rows2,
                "identical": match
            }

        return {
            "all_identical": all_match,
            "comparison": comparison
        }
