"""
Unit & Integration Tests for Validation Suite, Chronology, and Anomaly Auditing Service.
Includes tests for:
- Exact incident matching (issue_type, entity_id, violating_value)
- Incorrect entity IDs rejection
- Incorrect violating values rejection
- False positive penalties
- Missed anomaly (false negative) penalties
- Delivery date chronology verification
- Recall notification scoping by recall_case_id
"""

import unittest
from pharmatrace.config import settings
from pharmatrace.services.audit_service import AuditService
from pharmatrace.core.enums import EdgeCaseType

class TestAuditService(unittest.TestCase):
    def test_validation_suite_and_benchmark(self):
        auditor = AuditService(settings.data_dir)
        results = auditor.run_all_validations()

        self.assertIn("checks", results)
        self.assertIn("summary_counts", results)
        
        checks = results["checks"]
        self.assertTrue(checks["primary_key_uniqueness"]["passed"])
        self.assertTrue(checks["foreign_key_integrity"]["passed"], "Foreign key integrity check must pass with only the expected ghost lot")
        self.assertEqual(checks["foreign_key_integrity"]["expected_planted_violations"], 1)
        self.assertEqual(checks["foreign_key_integrity"]["unexpected_violations"], 0)
        self.assertTrue(checks["enum_compliance"]["passed"])
        self.assertTrue(checks["date_chronology"]["passed"], "Complete supply chain timeline chronology must pass")
        
        benchmark = checks["anomaly_ground_truth_benchmark"]
        self.assertEqual(benchmark["ground_truth_total"], 4)
        self.assertEqual(benchmark["detected_total"], 4)
        self.assertEqual(benchmark["true_positives"], 4)
        self.assertEqual(benchmark["false_positives"], 0)
        self.assertEqual(benchmark["false_negatives"], 0)
        self.assertEqual(benchmark["precision"], 1.0)
        self.assertEqual(benchmark["recall"], 1.0)
        self.assertEqual(benchmark["f1_score"], 1.0)
        self.assertEqual(len(benchmark["matched_incidents"]), 4)

        # Verify that all 4 matched incidents match entity IDs and violating values
        for match in benchmark["matched_incidents"]:
            det = match["detected"]
            gt = match["ground_truth"]
            self.assertEqual(det["issue_type"], gt["issue_type"])
            self.assertEqual(det["entity_id"], gt["entity_id"])
            self.assertTrue(AuditService.values_match(det["violating_value"], gt["violating_value"]))

    def test_benchmark_rejects_incorrect_entity_id(self):
        auditor = AuditService(settings.data_dir)
        auditor.ground_truth = [
            {
                "issue_type": EdgeCaseType.DELIVERED_EXCEEDS_PRODUCED.value,
                "entity_id": "DEL-2026-000122",
                "violating_value": "1137.11"
            }
        ]
        # Detected anomaly with wrong entity ID (e.g. finished lot ID instead of delivery ID)
        auditor.detected_anomalies = [
            {
                "issue_type": EdgeCaseType.DELIVERED_EXCEEDS_PRODUCED.value,
                "entity_id": "FINLOT-2026-000002",
                "violating_value": "1137.11"
            }
        ]
        bm = auditor.benchmark_against_ground_truth()
        self.assertEqual(bm["true_positives"], 0, "Anomaly with incorrect entity ID must NOT count as true positive")
        self.assertEqual(bm["false_positives"], 1)
        self.assertEqual(bm["false_negatives"], 1)
        self.assertEqual(bm["f1_score"], 0.0)

    def test_benchmark_rejects_incorrect_violating_value(self):
        auditor = AuditService(settings.data_dir)
        auditor.ground_truth = [
            {
                "issue_type": EdgeCaseType.DELIVERED_EXCEEDS_PRODUCED.value,
                "entity_id": "DEL-2026-000122",
                "violating_value": "1137.11"
            }
        ]
        # Detected anomaly with wrong violating value (e.g. 1310.66 instead of 1137.11)
        auditor.detected_anomalies = [
            {
                "issue_type": EdgeCaseType.DELIVERED_EXCEEDS_PRODUCED.value,
                "entity_id": "DEL-2026-000122",
                "violating_value": "1310.66"
            }
        ]
        bm = auditor.benchmark_against_ground_truth()
        self.assertEqual(bm["true_positives"], 0, "Anomaly with incorrect violating value must NOT count as true positive")
        self.assertEqual(bm["false_positives"], 1)
        self.assertEqual(bm["false_negatives"], 1)
        self.assertEqual(bm["f1_score"], 0.0)

    def test_benchmark_penalizes_false_positives(self):
        auditor = AuditService(settings.data_dir)
        auditor.ground_truth = [
            {
                "issue_type": EdgeCaseType.MISSING_INPUT_LOT.value,
                "entity_id": "CON-2026-999999",
                "violating_value": "RAWLOT-SUP-99999-2026-999999"
            }
        ]
        # Detected anomaly has 1 true positive and 1 spurious false positive
        auditor.detected_anomalies = [
            {
                "issue_type": EdgeCaseType.MISSING_INPUT_LOT.value,
                "entity_id": "CON-2026-999999",
                "violating_value": "RAWLOT-SUP-99999-2026-999999"
            },
            {
                "issue_type": EdgeCaseType.DELIVERED_EXCEEDS_PRODUCED.value,
                "entity_id": "DEL-SPURIOUS-001",
                "violating_value": "9999.0"
            }
        ]
        bm = auditor.benchmark_against_ground_truth()
        self.assertEqual(bm["true_positives"], 1)
        self.assertEqual(bm["false_positives"], 1)
        self.assertEqual(bm["false_negatives"], 0)
        self.assertEqual(bm["precision"], 0.5)
        self.assertEqual(bm["recall"], 1.0)
        self.assertAlmostEqual(bm["f1_score"], 0.6667, places=3)

    def test_benchmark_penalizes_missed_anomalies(self):
        auditor = AuditService(settings.data_dir)
        auditor.ground_truth = [
            {
                "issue_type": EdgeCaseType.MISSING_INPUT_LOT.value,
                "entity_id": "CON-2026-999999",
                "violating_value": "RAWLOT-SUP-99999-2026-999999"
            },
            {
                "issue_type": EdgeCaseType.DELIVERED_EXCEEDS_PRODUCED.value,
                "entity_id": "DEL-2026-000122",
                "violating_value": "1137.11"
            }
        ]
        # Detected only detects 1 of the 2 planted cases
        auditor.detected_anomalies = [
            {
                "issue_type": EdgeCaseType.MISSING_INPUT_LOT.value,
                "entity_id": "CON-2026-999999",
                "violating_value": "RAWLOT-SUP-99999-2026-999999"
            }
        ]
        bm = auditor.benchmark_against_ground_truth()
        self.assertEqual(bm["true_positives"], 1)
        self.assertEqual(bm["false_positives"], 0)
        self.assertEqual(bm["false_negatives"], 1)
        self.assertEqual(bm["precision"], 1.0)
        self.assertEqual(bm["recall"], 0.5)
        self.assertAlmostEqual(bm["f1_score"], 0.6667, places=3)

    def test_date_chronology_catches_delivery_before_manufacturing(self):
        auditor = AuditService(settings.data_dir)
        auditor.tables = {
            "production_orders": [],
            "material_lots": [],
            "production_order_lot_consumptions": [],
            "finished_lots": [
                {
                    "finished_lot_id": "FINLOT-TEST-001",
                    "production_order_id": "WO-001",
                    "manufacture_date": "2026-07-15T12:00:00"
                }
            ],
            "shipments": [
                {
                    "shipment_id": "SHP-TEST-001",
                    "ship_date": "2026-02-10T08:00:00",
                    "actual_arrival_date": "2026-02-12T10:00:00"
                }
            ],
            "deliveries": [
                {
                    "delivery_id": "DEL-TEST-001",
                    "finished_lot_id": "FINLOT-TEST-001",
                    "shipment_id": "SHP-TEST-001",
                    "delivery_date": "2026-02-11T14:00:00"
                }
            ]
        }
        res = auditor.check_date_chronology()
        self.assertFalse(res["passed"], "Must detect delivery dated before finished lot manufacture")
        self.assertGreaterEqual(res["violations_count"], 1)

    def test_recall_notification_scoped_by_recall_case_id(self):
        """
        Verifies that a delivery notified under Recall Case A is NOT treated as
        notified under Recall Case B.
        """
        auditor = AuditService(settings.data_dir)
        auditor.tables = {
            "production_order_lot_consumptions": [],
            "finished_lots": [
                {"finished_lot_id": "FINLOT-001", "production_order_id": "WO-001", "status": "RECALLED", "warehouse_qty": 0.0, "quarantine_qty": 0.0}
            ],
            "deliveries": [
                {"delivery_id": "DEL-001", "finished_lot_id": "FINLOT-001", "customer_id": "CUST-001"}
            ],
            "recall_cases": [
                {"recall_case_id": "REC-CASE-A", "trigger_entity_type": "FINISHED_LOT", "trigger_entity_id": "FINLOT-001"},
                {"recall_case_id": "REC-CASE-B", "trigger_entity_type": "FINISHED_LOT", "trigger_entity_id": "FINLOT-001"}
            ],
            "recall_actions": [
                # Notice sent ONLY under REC-CASE-A
                {"recall_case_id": "REC-CASE-A", "action_type": "CUSTOMER_RECALL_NOTICE", "target_entity_type": "CUSTOMER_DELIVERY", "target_entity_id": "DEL-001"}
            ]
        }
        res = auditor.check_lifecycle_states()
        self.assertFalse(res["passed"], "Recall B must report missed customer notification even if Recall A notified that delivery")
        
        missed = [a for a in auditor.detected_anomalies if a["issue_type"] == EdgeCaseType.RECALL_MISSED_CUSTOMER.value]
        self.assertEqual(len(missed), 1)
        self.assertEqual(missed[0]["entity_id"], "REC-CASE-B")

    def test_inventory_movement_reconciliation(self):
        """
        Verifies that finished lot inventory movements reconcile with available and quarantine balances.
        """
        auditor = AuditService(settings.data_dir)
        auditor.load_data()
        res = auditor.check_inventory_movements()
        self.assertTrue(res["passed"], f"Inventory movements failed to reconcile: {res.get('discrepancies')}")
        self.assertEqual(res["discrepancies_count"], 0)

    def test_recall_scope_reconciliation(self):
        """
        Verifies that recall cases accurately reconcile recovered quantities against action records.
        """
        auditor = AuditService(settings.data_dir)
        auditor.load_data()
        res = auditor.check_recall_scope_completion()
        self.assertTrue(res["passed"], f"Recall scope audit reported unaccounted discrepancies: {res.get('discrepancies')}")
        self.assertEqual(res["discrepancies_count"], 0)
        self.assertGreater(res["total_actions_completed"], 0)

    def test_benchmark_zero_detections_zero_ground_truth(self):
        """
        Confirms benchmark precision, recall, and F1 calculations for zero detections
        and zero ground-truth anomalies (clean dataset).
        """
        auditor = AuditService(settings.data_dir)
        auditor.ground_truth = []
        auditor.detected_anomalies = []
        bm = auditor.benchmark_against_ground_truth()
        self.assertEqual(bm["precision"], 1.0)
        self.assertEqual(bm["recall"], 1.0)
        self.assertEqual(bm["f1_score"], 1.0)
        self.assertEqual(bm["false_positives"], 0)
        self.assertEqual(bm["false_negatives"], 0)

    def test_clean_dataset_has_zero_false_positives(self):
        """
        Tests a clean dataset generated with no planted anomalies to verify zero false positives.
        """
        from pharmatrace.services.generator_service import GeneratorService
        import tempfile, shutil
        tmp_dir = tempfile.mkdtemp()
        try:
            gen = GeneratorService(seed=9999, scale="starter", inject_anomalies=False)
            gen.generate()
            gen.export(tmp_dir)

            clean_auditor = AuditService(tmp_dir)
            results = clean_auditor.run_all_validations()
            self.assertEqual(results["summary_counts"]["planted_edge_cases_detected"], 0, "Clean dataset must produce 0 anomaly detections")
            self.assertEqual(results["unexpected_violations_count"], 0, "Clean dataset must produce 0 unexpected violations")
            bm = results["checks"]["anomaly_ground_truth_benchmark"]
            self.assertEqual(bm["false_positives"], 0)
            self.assertEqual(bm["f1_score"], 1.0)
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_each_anomaly_type_verified_individually(self):
        """
        Verifies each of the four anomaly types individually, checking entity ID, parent ID, and violating value.
        """
        auditor = AuditService(settings.data_dir)
        auditor.run_all_validations()

        anom_map = {a["issue_type"]: a for a in auditor.detected_anomalies}
        gt_map = {g["issue_type"]: g for g in auditor.ground_truth}
        self.assertEqual(len(anom_map), 4, "Must detect all 4 distinct anomaly types")
        self.assertEqual(len(gt_map), 4, "Must have all 4 distinct anomaly types in ground truth")

        for issue_type, det in anom_map.items():
            self.assertIn(issue_type, gt_map, f"Detected issue {issue_type} must be in ground truth")
            gt = gt_map[issue_type]
            self.assertEqual(det["entity_id"], gt["entity_id"], f"Entity ID mismatch for {issue_type}")
            self.assertEqual(det["parent_id"], gt["parent_id"], f"Parent ID mismatch for {issue_type}")
            self.assertTrue(AuditService.values_match(det["violating_value"], gt["violating_value"]), f"Violating value mismatch for {issue_type}")

    def test_multiple_anomalies_same_type_handling(self):
        """
        Tests benchmark handling when multiple anomalies of the same type exist.
        """
        auditor = AuditService(settings.data_dir)
        auditor.ground_truth = [
            {"issue_type": "MISSING_INPUT_LOT", "entity_id": "CON-1", "violating_value": "RAW-1"},
            {"issue_type": "MISSING_INPUT_LOT", "entity_id": "CON-2", "violating_value": "RAW-2"}
        ]
        # Detected only matches one
        auditor.detected_anomalies = [
            {"issue_type": "MISSING_INPUT_LOT", "entity_id": "CON-1", "violating_value": "RAW-1"},
            {"issue_type": "MISSING_INPUT_LOT", "entity_id": "CON-3", "violating_value": "RAW-3"}  # False positive
        ]
        bm = auditor.benchmark_against_ground_truth()
        self.assertEqual(bm["true_positives"], 1)
        self.assertEqual(bm["false_positives"], 1)
        self.assertEqual(bm["false_negatives"], 1)
        self.assertEqual(bm["f1_score"], 0.5)

if __name__ == "__main__":
    unittest.main()
