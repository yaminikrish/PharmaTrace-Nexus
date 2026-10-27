"""
Enterprise Genealogy Traversal Service.
Executes high-performance forward downstream tracing and reverse upstream
root-cause analysis across multi-tier supply chain entities.
"""

from typing import Dict, List, Any, Optional
from pharmatrace.infrastructure.database import DatabaseRepository

class GenealogyService:
    def __init__(self, db_repo: Optional[DatabaseRepository] = None):
        self.db = db_repo or DatabaseRepository()

    def trace(self, node_id: str, direction: str = "downstream") -> Dict[str, Any]:
        """
        Traces multi-tier genealogy either forward downstream or reverse upstream.
        """
        if not node_id:
            row = self.db.fetch_one("SELECT material_lot_id FROM material_lots LIMIT 1")
            node_id = row["material_lot_id"] if row else ""

        nodes = []
        links = []

        if direction == "downstream":
            nodes, links = self._trace_downstream(node_id)
        else:
            nodes, links = self._trace_upstream(node_id)

        unique_nodes = list({n["id"]: n for n in nodes}.values())

        return {
            "root_id": node_id,
            "direction": direction,
            "nodes": unique_nodes,
            "links": links
        }

    def _trace_downstream(self, node_id: str):
        nodes = []
        links = []

        if node_id.startswith("SUP-"):
            supp = self.db.fetch_one("SELECT * FROM suppliers WHERE supplier_id = ?", (node_id,))
            if supp:
                nodes.append({"id": supp["supplier_id"], "label": supp["name"], "type": "SUPPLIER", "status": supp["status"]})
            raw_lots = self.db.fetch_all("SELECT * FROM material_lots WHERE supplier_id = ? LIMIT 5", (node_id,))
            for r in raw_lots:
                nodes.append({"id": r["material_lot_id"], "label": r["material_lot_id"], "type": "RAW_LOT", "status": r["qc_status"], "qty": r["initial_qty"]})
                links.append({"source": node_id, "target": r["material_lot_id"], "label": "Supplies"})
            raw_id = raw_lots[0]["material_lot_id"] if raw_lots else None
        else:
            raw_id = node_id
            r = self.db.fetch_one("SELECT * FROM material_lots WHERE material_lot_id = ?", (raw_id,))
            if r:
                supp = self.db.fetch_one("SELECT * FROM suppliers WHERE supplier_id = ?", (r["supplier_id"],))
                if supp:
                    nodes.append({"id": supp["supplier_id"], "label": supp["name"], "type": "SUPPLIER", "status": supp["status"]})
                    links.append({"source": supp["supplier_id"], "target": r["material_lot_id"], "label": "Procured"})
                nodes.append({"id": r["material_lot_id"], "label": r["material_lot_id"], "type": "RAW_LOT", "status": r["qc_status"], "qty": r["initial_qty"], "product": r["product_id"]})

        if raw_id:
            wos = self.db.fetch_all("""
                SELECT c.consumed_qty, po.* 
                FROM production_order_lot_consumptions c
                JOIN production_orders po ON c.production_order_id = po.production_order_id
                WHERE c.material_lot_id = ?
            """, (raw_id,))

            for wo in wos:
                wo_id = wo["production_order_id"]
                nodes.append({"id": wo_id, "label": wo_id, "type": "PRODUCTION_ORDER", "status": wo["status"], "target_qty": wo["target_qty"], "line": wo["production_line"]})
                links.append({"source": raw_id, "target": wo_id, "label": f"Consumed {wo['consumed_qty']} units"})

                flots = self.db.fetch_all("SELECT * FROM finished_lots WHERE production_order_id = ?", (wo_id,))
                for fl in flots:
                    fl_id = fl["finished_lot_id"]
                    nodes.append({"id": fl_id, "label": fl_id, "type": "FINISHED_LOT", "status": fl["status"], "produced_qty": fl["produced_qty"], "warehouse_qty": fl["warehouse_qty"]})
                    links.append({"source": wo_id, "target": fl_id, "label": "Manufactured"})

                    dels = self.db.fetch_all("""
                        SELECT d.*, c.name as customer_name, c.region as customer_region, s.carrier_name, s.status as shipment_status
                        FROM deliveries d
                        JOIN customers c ON d.customer_id = c.customer_id
                        JOIN shipments s ON d.shipment_id = s.shipment_id
                        WHERE d.finished_lot_id = ? LIMIT 8
                    """, (fl_id,))
                    for d in dels:
                        del_id = d["delivery_id"]
                        cust_id = d["customer_id"]
                        nodes.append({"id": del_id, "label": f"{del_id} ({d['carrier_name']})", "type": "SHIPMENT_DELIVERY", "status": d["status"], "qty": d["delivered_qty"]})
                        links.append({"source": fl_id, "target": del_id, "label": f"Dispatched {d['delivered_qty']}"})

                        nodes.append({"id": cust_id, "label": d["customer_name"], "type": "CUSTOMER", "region": d["customer_region"], "status": "ACTIVE"})
                        links.append({"source": del_id, "target": cust_id, "label": "Delivered"})

        return nodes, links

    def _trace_upstream(self, node_id: str):
        nodes = []
        links = []
        target_fl_id = None

        if node_id.startswith("DEL-"):
            deliv = self.db.fetch_one("SELECT * FROM deliveries WHERE delivery_id = ?", (node_id,))
            if deliv:
                target_fl_id = deliv["finished_lot_id"]
                nodes.append({"id": deliv["delivery_id"], "label": deliv["delivery_id"], "type": "DELIVERY", "status": deliv["status"], "qty": deliv["delivered_qty"]})
        elif node_id.startswith("FINLOT-"):
            target_fl_id = node_id

        if target_fl_id:
            fl = self.db.fetch_one("SELECT * FROM finished_lots WHERE finished_lot_id = ?", (target_fl_id,))
            if fl:
                nodes.append({"id": fl["finished_lot_id"], "label": fl["finished_lot_id"], "type": "FINISHED_LOT", "status": fl["status"], "produced_qty": fl["produced_qty"]})
                wo_id = fl["production_order_id"]
                wo = self.db.fetch_one("SELECT * FROM production_orders WHERE production_order_id = ?", (wo_id,))
                if wo:
                    nodes.append({"id": wo["production_order_id"], "label": wo["production_order_id"], "type": "PRODUCTION_ORDER", "status": wo["status"]})
                    links.append({"source": fl["finished_lot_id"], "target": wo["production_order_id"], "label": "Produced by"})

                    raw_cons = self.db.fetch_all("""
                        SELECT c.*, m.supplier_id, m.qc_status, m.product_id as raw_prod_id
                        FROM production_order_lot_consumptions c
                        LEFT JOIN material_lots m ON c.material_lot_id = m.material_lot_id
                        WHERE c.production_order_id = ?
                    """, (wo["production_order_id"],))

                    for rc in raw_cons:
                        raw_lot_id = rc["material_lot_id"]
                        nodes.append({"id": raw_lot_id, "label": raw_lot_id, "type": "RAW_LOT", "status": rc.get("qc_status", "UNKNOWN"), "qty": rc["consumed_qty"]})
                        links.append({"source": wo["production_order_id"], "target": raw_lot_id, "label": f"Consumed {rc['consumed_qty']}"})

                        if rc.get("supplier_id"):
                            supp = self.db.fetch_one("SELECT * FROM suppliers WHERE supplier_id = ?", (rc["supplier_id"],))
                            if supp:
                                nodes.append({"id": supp["supplier_id"], "label": supp["name"], "type": "SUPPLIER", "status": supp["status"]})
                                links.append({"source": raw_lot_id, "target": supp["supplier_id"], "label": "Supplied by"})

        return nodes, links
