"""
Unit & Integration Tests for Genealogy Traversal Service.
"""

import unittest
from pharmatrace.services.genealogy_service import GenealogyService
from pharmatrace.infrastructure.database import DatabaseRepository

class TestGenealogyService(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = DatabaseRepository()
        cls.service = GenealogyService(cls.db)

    def test_downstream_traversal_structure(self):
        # Pick first available raw lot
        raw_lot = self.db.fetch_one("SELECT material_lot_id FROM material_lots LIMIT 1")
        if not raw_lot:
            self.skipTest("No material lots in database")
            
        lot_id = raw_lot["material_lot_id"]
        result = self.service.trace(lot_id, direction="downstream")
        
        self.assertEqual(result["root_id"], lot_id)
        self.assertEqual(result["direction"], "downstream")
        self.assertIsInstance(result["nodes"], list)
        self.assertIsInstance(result["links"], list)
        self.assertTrue(any(n["id"] == lot_id for n in result["nodes"]))

    def test_downstream_trace_raw_to_customers(self):
        """
        Traces a raw material lot forward to affected finished lots, deliveries, and customers.
        """
        # Pick a raw lot that is consumed in a production order with finished lots and deliveries
        row = self.db.fetch_one("""
            SELECT c.material_lot_id
            FROM production_order_lot_consumptions c
            JOIN finished_lots fl ON c.production_order_id = fl.production_order_id
            JOIN deliveries d ON fl.finished_lot_id = d.finished_lot_id
            LIMIT 1
        """)
        self.assertIsNotNone(row, "Must find raw lot connected downstream to delivery")
        raw_lot_id = row["material_lot_id"]
        
        result = self.service.trace(raw_lot_id, direction="downstream")
        node_types = {n["type"] for n in result["nodes"]}
        self.assertIn("RAW_LOT", node_types)
        self.assertIn("PRODUCTION_ORDER", node_types)
        self.assertIn("FINISHED_LOT", node_types)
        self.assertIn("SHIPMENT_DELIVERY", node_types)
        self.assertIn("CUSTOMER", node_types)

    def test_upstream_trace_delivery_to_raw_materials(self):
        """
        Traces a customer delivery backward to finished lot, production order, and input raw lots.
        """
        deliv = self.db.fetch_one("SELECT delivery_id, finished_lot_id FROM deliveries LIMIT 1")
        self.assertIsNotNone(deliv)
        del_id = deliv["delivery_id"]
        
        result = self.service.trace(del_id, direction="upstream")
        node_types = {n["type"] for n in result["nodes"]}
        self.assertIn("DELIVERY", node_types)
        self.assertIn("FINISHED_LOT", node_types)
        self.assertIn("PRODUCTION_ORDER", node_types)
        self.assertIn("RAW_LOT", node_types)
        self.assertIn("SUPPLIER", node_types)

    def test_production_order_multi_input_multi_output(self):
        """
        Tests a production order that consumes multiple raw lots and creates multiple finished lots.
        """
        row = self.db.fetch_one("""
            SELECT po.production_order_id, count(DISTINCT c.material_lot_id) as raw_count, count(DISTINCT fl.finished_lot_id) as fin_count
            FROM production_orders po
            JOIN production_order_lot_consumptions c ON po.production_order_id = c.production_order_id
            JOIN finished_lots fl ON po.production_order_id = fl.production_order_id
            GROUP BY po.production_order_id
            HAVING raw_count > 1 AND fin_count > 1
            LIMIT 1
        """)
        if not row:
            self.skipTest("No 1:N PO with multiple inputs found in dataset")
        wo_id = row["production_order_id"]
        
        # Trace upstream from one finished lot
        fl = self.db.fetch_one("SELECT finished_lot_id FROM finished_lots WHERE production_order_id = ? LIMIT 1", (wo_id,))
        result = self.service.trace(fl["finished_lot_id"], direction="upstream")
        raw_nodes = [n for n in result["nodes"] if n["type"] == "RAW_LOT"]
        self.assertGreaterEqual(len(raw_nodes), 2, "Upstream traversal must capture all consumed input raw lots")

    def test_genealogy_lot_without_downstream_deliveries(self):
        """
        Checks genealogy traversal when a finished lot or raw lot has no downstream deliveries.
        """
        # Create or find a lot with zero deliveries
        row = self.db.fetch_one("""
            SELECT finished_lot_id FROM finished_lots
            WHERE finished_lot_id NOT IN (SELECT DISTINCT finished_lot_id FROM deliveries)
            LIMIT 1
        """)
        if row:
            fl_id = row["finished_lot_id"]
            res = self.service.trace(fl_id, direction="downstream")
            # Downstream from an undelivered lot should gracefully terminate
            self.assertEqual(res["root_id"], fl_id)
        else:
            # If all lots have deliveries, test with an isolated hypothetical ID
            res = self.service.trace("FINLOT-ISOLATED-001", direction="downstream")
            self.assertEqual(res["nodes"], [])

if __name__ == "__main__":
    unittest.main()
