"""
Enterprise Recall Simulation Service.
Calculates blast radius, containment rate, financial exposure,
and manages multi-stage recall lifecycle execution.
"""

from typing import Dict, List, Any, Optional
from pharmatrace.core.enums import RecallHazardClass
from pharmatrace.infrastructure.database import DatabaseRepository

class RecallService:
    def __init__(self, db_repo: Optional[DatabaseRepository] = None):
        self.db = db_repo or DatabaseRepository()

    def simulate(self, lot_id: str, hazard_class: str = RecallHazardClass.CLASS_I.value, root_cause: str = "Microbial Contamination Detected") -> Dict[str, Any]:
        """
        Simulates recall blast radius, affected customer scope, and 14-day timeline containment.
        """
        affected_raw_ids = set()
        affected_fin_lots = []
        affected_deliveries = []

        if lot_id.startswith("RAWLOT-"):
            affected_raw_ids.add(lot_id)
            affected_fin_lots = self.db.fetch_all("""
                SELECT DISTINCT fl.* 
                FROM production_order_lot_consumptions c
                JOIN finished_lots fl ON c.production_order_id = fl.production_order_id
                WHERE c.material_lot_id = ?
            """, (lot_id,))
        elif lot_id.startswith("FINLOT-"):
            fl = self.db.fetch_one("SELECT * FROM finished_lots WHERE finished_lot_id = ?", (lot_id,))
            if fl:
                affected_fin_lots = [fl]
                raw_cons = self.db.fetch_all("SELECT material_lot_id FROM production_order_lot_consumptions WHERE production_order_id = ?", (fl["production_order_id"],))
                affected_raw_ids.update([r["material_lot_id"] for r in raw_cons])
        else:
            fl = self.db.fetch_one("SELECT * FROM finished_lots LIMIT 1")
            if fl:
                affected_fin_lots = [fl]
                lot_id = fl["finished_lot_id"]

        total_produced_affected = round(sum(float(fl["produced_qty"]) for fl in affected_fin_lots), 2)
        total_warehouse_held = round(sum(float(fl["warehouse_qty"]) for fl in affected_fin_lots), 2)

        for fl in affected_fin_lots:
            dels = self.db.fetch_all("""
                SELECT d.*, c.name as customer_name, c.region as customer_region
                FROM deliveries d
                JOIN customers c ON d.customer_id = c.customer_id
                WHERE d.finished_lot_id = ?
            """, (fl["finished_lot_id"],))
            affected_deliveries.extend(dels)

        total_delivered_affected = round(sum(float(d["delivered_qty"]) for d in affected_deliveries), 2)

        est_customer_recovery = round(total_delivered_affected * (0.92 if hazard_class == RecallHazardClass.CLASS_I.value else 0.85), 2)
        total_recovered_simulated = round(total_warehouse_held + est_customer_recovery, 2)
        containment_rate = round((total_recovered_simulated / total_produced_affected * 100.0), 1) if total_produced_affected > 0 else 100.0

        unit_cost = 185.0
        financial_exposure = round((total_produced_affected * unit_cost) + (250000.0 if hazard_class == RecallHazardClass.CLASS_I.value else 75000.0), 2)

        timeline = [
            {"day": 0, "stage": "INCIDENT_TRIGGER", "label": "Recall Trigger Logged", "actions_count": 1, "status": "COMPLETED", "containment_pct": 0.0},
            {"day": 1, "stage": "REGULATORY_DISPATCH", "label": "FDA / EMA & Supplier Alert", "actions_count": len(affected_raw_ids) + 1, "status": "COMPLETED", "containment_pct": 5.0},
            {"day": 2, "stage": "WAREHOUSE_LOCK", "label": f"Warehouse Physical Quarantine ({total_warehouse_held:,.0f} units)", "actions_count": len(affected_fin_lots), "status": "COMPLETED", "containment_pct": round((total_warehouse_held / max(1, total_produced_affected)) * 100, 1)},
            {"day": 3, "stage": "CUSTOMER_NOTIFICATION", "label": f"Hospital / Pharmacy Bulletins Dispatched ({len(affected_deliveries)} deliveries)", "actions_count": len(affected_deliveries), "status": "IN_PROGRESS", "containment_pct": round(((total_warehouse_held + (est_customer_recovery * 0.4)) / max(1, total_produced_affected)) * 100, 1)},
            {"day": 7, "stage": "RECOVERY_WAVE_1", "label": "In-transit Carrier Intercepts & Hospital Holds", "actions_count": len(affected_deliveries), "status": "PENDING", "containment_pct": round(((total_warehouse_held + (est_customer_recovery * 0.75)) / max(1, total_produced_affected)) * 100, 1)},
            {"day": 14, "stage": "RECONCILIATION", "label": "Destruction Certificates & Regulatory Closure", "actions_count": 2, "status": "PLANNED", "containment_pct": containment_rate}
        ]

        return {
            "simulation_id": f"SIM-{lot_id[-6:]}",
            "target_lot_id": lot_id,
            "hazard_classification": hazard_class,
            "root_cause": root_cause,
            "scope": {
                "affected_raw_lots_count": len(affected_raw_ids),
                "affected_finished_lots_count": len(affected_fin_lots),
                "affected_deliveries_count": len(affected_deliveries),
                "affected_customers_count": len({d["customer_id"] for d in affected_deliveries}),
                "total_produced_affected": total_produced_affected,
                "warehouse_held_qty": total_warehouse_held,
                "delivered_qty": total_delivered_affected,
                "simulated_recovery_qty": total_recovered_simulated,
                "containment_rate_pct": containment_rate,
                "estimated_financial_exposure_usd": financial_exposure
            },
            "timeline": timeline,
            "affected_finished_lots": affected_fin_lots,
            "affected_deliveries_sample": affected_deliveries[:10]
        }
