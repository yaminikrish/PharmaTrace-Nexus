"""
Automated Validation and Anomaly Auditing Suite for Lot Traceability & Recall Simulation.
Delegates to pharmatrace.services.audit_service.AuditService.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from pharmatrace.services.audit_service import AuditService

class TraceabilityValidator:
    def __init__(self, data_dir: str):
        self.svc = AuditService(data_dir)

    def load_data(self):
        self.svc.load_data()

    def run_all_validations(self):
        return self.svc.run_all_validations()

    def export_summary(self, filepath: str):
        self.svc.export_summary(filepath)

def main():
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "data"
    validator = TraceabilityValidator(data_dir)
    results = validator.run_all_validations()
    
    print("\n" + "="*65)
    print("LOT TRACEABILITY & RECALL VALIDATION REPORT")
    print("="*65)
    print(f"Overall Status:        {results['overall_system_status']}")
    print(f"Total Tables Verified: {results['total_tables_checked']}")
    print(f"Total Rows Inspected:  {results['summary_counts']['total_rows_inspected']:,}")
    print(f"Primary Key Check:     {'PASS' if results['checks']['primary_key_uniqueness']['passed'] else 'FAIL'}")
    print(f"Foreign Key Check:     {results['checks']['foreign_key_integrity']['violations_count']} violation(s) (expected due to planted ghost lot)")
    print(f"Enum Compliance:       {'PASS' if results['checks']['enum_compliance']['passed'] else 'FAIL'}")
    print(f"Date Chronology:       {'PASS' if results['checks']['date_chronology']['passed'] else 'FAIL'}")
    print(f"Arithmetic Discrepancies: {results['checks']['arithmetic_reconciliation']['discrepancies_count']} (expected due to planted yield excess)")
    print("-" * 65)
    bm = results["checks"]["anomaly_ground_truth_benchmark"]
    print("ANOMALY DETECTION BENCHMARK vs. GROUND TRUTH:")
    print(f"  Planted Anomalies:   {bm['ground_truth_total']}")
    print(f"  Detected Anomalies:  {bm['detected_total']}")
    print(f"  Precision:           {bm['precision'] * 100:.1f}%")
    print(f"  Recall:              {bm['recall'] * 100:.1f}%")
    print(f"  F1 Score:            {bm['f1_score']:.4f}")
    print("=" * 65 + "\n")

    summary_path = os.path.join(data_dir, "validation_summary.json")
    validator.export_summary(summary_path)
    print(f"[+] Validation report exported to: {summary_path}")

if __name__ == "__main__":
    main()
