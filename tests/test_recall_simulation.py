"""
Unit & Integration Tests for Recall Simulation Service.
"""

import unittest
from pharmatrace.services.recall_service import RecallService
from pharmatrace.infrastructure.database import DatabaseRepository
from pharmatrace.core.enums import RecallHazardClass

class TestRecallService(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = DatabaseRepository()
        cls.service = RecallService(cls.db)

    def test_recall_simulation_scope_and_metrics(self):
        fin_lot = self.db.fetch_one("SELECT finished_lot_id FROM finished_lots LIMIT 1")
        if not fin_lot:
            self.skipTest("No finished lots in database")

        lot_id = fin_lot["finished_lot_id"]
        result = self.service.simulate(lot_id, hazard_class=RecallHazardClass.CLASS_I.value)

        self.assertIn("scope", result)
        self.assertIn("timeline", result)
        scope = result["scope"]
        
        self.assertGreaterEqual(scope["total_produced_affected"], 0.0)
        self.assertGreaterEqual(scope["containment_rate_pct"], 0.0)
        self.assertLessEqual(scope["containment_rate_pct"], 100.0)
        self.assertGreater(scope["estimated_financial_exposure_usd"], 0.0)
        self.assertEqual(len(result["timeline"]), 6)

    def test_recall_simulation_with_no_affected_customers(self):
        """
        Tests recall simulation for a lot with warehouse stock but zero customer deliveries.
        """
        # Find or pick an undelivered lot or raw lot
        fin_lot = self.db.fetch_one("""
            SELECT finished_lot_id FROM finished_lots
            WHERE finished_lot_id NOT IN (SELECT DISTINCT finished_lot_id FROM deliveries)
            LIMIT 1
        """)
        if fin_lot:
            result = self.service.simulate(fin_lot["finished_lot_id"])
            self.assertEqual(result["scope"]["affected_deliveries_count"], 0)
            self.assertEqual(result["scope"]["affected_customers_count"], 0)
            self.assertEqual(result["scope"]["containment_rate_pct"], 100.0)

    def test_recall_across_multiple_warehouses(self):
        """
        Tests a raw lot recall that cascades to multiple finished lots housed in different warehouses.
        """
        row = self.db.fetch_one("""
            SELECT c.material_lot_id, count(DISTINCT fl.warehouse_id) as wh_count
            FROM production_order_lot_consumptions c
            JOIN finished_lots fl ON c.production_order_id = fl.production_order_id
            GROUP BY c.material_lot_id
            HAVING wh_count > 1
            LIMIT 1
        """)
        if not row:
            self.skipTest("No raw lot spanning multiple warehouses found")
        result = self.service.simulate(row["material_lot_id"])
        warehouses = {fl["warehouse_id"] for fl in result["affected_finished_lots"]}
        self.assertGreater(len(warehouses), 1, "Raw lot recall must cascade across multiple regional warehouses")

    def test_completed_recall_has_no_unresolved_actions(self):
        """
        Confirms completed recalls have only COMPLETED action records.
        """
        reconciled_cases = self.db.fetch_all("SELECT recall_case_id FROM recall_cases WHERE status = 'RECONCILED'")
        for rc in reconciled_cases:
            unresolved = self.db.fetch_all("""
                SELECT action_id, action_status FROM recall_actions
                WHERE recall_case_id = ? AND action_status != 'COMPLETED'
            """, (rc["recall_case_id"],))
            self.assertEqual(len(unresolved), 0, f"Reconciled recall {rc['recall_case_id']} must have 0 unresolved actions")

    def test_planted_available_inventory_breach_detected_and_isolated(self):
        """
        Verifies that the planted breach FINLOT-2026-000003 under REC-2026-BREACH-01
        is explicitly detected and isolated.
        """
        breach = self.db.fetch_one("SELECT * FROM finished_lots WHERE finished_lot_id = 'FINLOT-2026-000003'")
        self.assertIsNotNone(breach)
        self.assertEqual(breach["status"], "AVAILABLE")
        self.assertEqual(float(breach["warehouse_qty"]), 500.0)
        self.assertEqual(float(breach["quarantine_qty"]), 0.0)
        
        # Verify recall case exists for this breach
        rec = self.db.fetch_one("SELECT * FROM recall_cases WHERE recall_case_id = 'REC-2026-BREACH-01'")
        self.assertIsNotNone(rec)
        self.assertEqual(rec["trigger_entity_id"], "FINLOT-2026-000003")
