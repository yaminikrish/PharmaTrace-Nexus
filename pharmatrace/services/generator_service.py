"""
Enterprise Synthetic Data Generator Service.
Orchestrates master data, warehouses, production order consumption genealogy,
chronologically consistent shipments & deliveries, controlled edge case injection,
and derived mass-balance reconciliation.
"""

import os
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from pharmatrace.core.enums import (
    SupplierTier, SupplierStatus, ProductCategory, LotQCStatus,
    ProductionOrderStatus, FinishedLotStatus, ShipmentStatus,
    CustomerType, DeliveryStatus, RecallHazardClass, RecallStatus,
    RecallActionType, ActionStatus, EdgeCaseType,
    WarehouseFacilityType, InventoryMovementType
)
from pharmatrace.infrastructure.exporters import DataExporter

logger = logging.getLogger(__name__)

SCALE_CONFIGS = {
    "starter": {
        "suppliers_count": 50,
        "raw_products_count": 20,
        "finished_products_count": 15,
        "raw_lots_count": 300,
        "production_orders_count": 150,
        "finished_lots_count": 200,
        "customers_count": 80,
        "shipments_count": 120,
        "deliveries_count": 500,
        "recall_cases_count": 8
    },
    "full": {
        "suppliers_count": 500,
        "raw_products_count": 100,
        "finished_products_count": 50,
        "raw_lots_count": 10000,
        "production_orders_count": 5000,
        "finished_lots_count": 8000,
        "customers_count": 1200,
        "shipments_count": 4500,
        "deliveries_count": 20000,
        "recall_cases_count": 30
    }
}

COUNTRY_CODES = ["USA", "CHE", "DEU", "JPN", "GBR", "FRA", "CAN", "IRL", "SGP", "DNK"]
CARRIERS = ["DHL Supply Chain", "FedEx Freight", "UPS Supply Chain", "Kuehne+Nagel", "Maersk Logistics"]
REGIONS = ["NA_EAST", "NA_WEST", "NA_CENTRAL", "EU_WEST", "EU_CENTRAL", "APAC"]
PRODUCTION_LINES = ["LINE-A", "LINE-B", "LINE-C", "LINE-D"]

WAREHOUSES_DEF = [
    {"warehouse_id": "WH-0001", "name": "North Central Logistics Hub", "location": "Boston, MA", "country": "USA", "facility_type": WarehouseFacilityType.DISTRIBUTION_CENTER.value, "status": "ACTIVE"},
    {"warehouse_id": "WH-0002", "name": "Mid-Atlantic Distribution Center", "location": "Philadelphia, PA", "country": "USA", "facility_type": WarehouseFacilityType.DISTRIBUTION_CENTER.value, "status": "ACTIVE"},
    {"warehouse_id": "WH-0003", "name": "Western Regional Cold-Chain Depot", "location": "Reno, NV", "country": "USA", "facility_type": WarehouseFacilityType.DISTRIBUTION_CENTER.value, "status": "ACTIVE"},
    {"warehouse_id": "WH-0004", "name": "Great Lakes Manufacturing Depot", "location": "Chicago, IL", "country": "USA", "facility_type": WarehouseFacilityType.CENTRAL_DEPOT.value, "status": "ACTIVE"},
    {"warehouse_id": "WH-0005", "name": "European Central Logistics Terminal", "location": "Basel", "country": "CHE", "facility_type": WarehouseFacilityType.DISTRIBUTION_CENTER.value, "status": "ACTIVE"}
]

class GeneratorService:
    def __init__(self, seed: int = 20261022, scale: str = "starter", inject_anomalies: bool = True):
        self.seed = seed
        self.scale = scale
        self.cfg = SCALE_CONFIGS[scale]
        self.inject_anomalies = inject_anomalies
        self.rng = random.Random(seed)
        
        self.base_date = datetime(2026, 1, 10, 8, 0, 0)
        self.act_counter = 1
        self.mov_counter = 1
        
        # Entity collections
        self.suppliers: List[Dict[str, Any]] = []
        self.products: List[Dict[str, Any]] = []
        self.boms: List[Dict[str, Any]] = []
        self.bom_items: List[Dict[str, Any]] = []
        self.warehouses: List[Dict[str, Any]] = []
        self.material_lots: List[Dict[str, Any]] = []
        self.production_orders: List[Dict[str, Any]] = []
        self.lot_consumptions: List[Dict[str, Any]] = []
        self.finished_lots: List[Dict[str, Any]] = []
        self.customers: List[Dict[str, Any]] = []
        self.shipments: List[Dict[str, Any]] = []
        self.deliveries: List[Dict[str, Any]] = []
        self.recall_cases: List[Dict[str, Any]] = []
        self.recall_actions: List[Dict[str, Any]] = []
        self.inventory_movements: List[Dict[str, Any]] = []
        self.ground_truth: List[Dict[str, Any]] = []
        
        # Lookups
        self.raw_products_list: List[Dict[str, Any]] = []
        self.fin_products_list: List[Dict[str, Any]] = []
        self.bom_by_fin_product: Dict[str, Dict[str, Any]] = {}
        self.raw_lots_by_product: Dict[str, List[Dict[str, Any]]] = {}

    def generate(self) -> Dict[str, List[Dict[str, Any]]]:
        logger.info(f"Generating synthetic dataset: seed={self.seed}, scale={self.scale}")
        self._generate_master_data()
        self._generate_raw_lots()
        self._generate_manufacturing()
        self._generate_distribution()
        self._generate_recalls()
        if self.inject_anomalies:
            self._inject_edge_cases()
        self._reconcile_mass_balances()

        return self.get_datasets()

    def get_datasets(self) -> Dict[str, List[Dict[str, Any]]]:
        return {
            "suppliers": self.suppliers,
            "products": self.products,
            "boms": self.boms,
            "bom_items": self.bom_items,
            "warehouses": self.warehouses,
            "material_lots": self.material_lots,
            "production_orders": self.production_orders,
            "production_order_lot_consumptions": self.lot_consumptions,
            "finished_lots": self.finished_lots,
            "customers": self.customers,
            "shipments": self.shipments,
            "deliveries": self.deliveries,
            "recall_cases": self.recall_cases,
            "recall_actions": self.recall_actions,
            "inventory_movements": self.inventory_movements
        }

    def export(self, output_dir: str) -> Dict[str, Any]:
        exporter = DataExporter(output_dir)
        return exporter.export_all(self.get_datasets(), self.ground_truth, self.seed, self.scale)

    def _generate_master_data(self):
        # 1. Suppliers
        vendor_names = ["BioPharma Synthetics", "Nordic Chemical Labs", "Apex Polymers", "Kyoto Solvents",
                        "Helvetia Pharma", "Starlight Actives", "Vanguard BioSciences", "Sterling Fine Chem",
                        "Pacific BioAg", "Alps Purifications", "Continental Reagents", "Nova Biochemical"]
        for i in range(1, self.cfg["suppliers_count"] + 1):
            supplier_id = f"SUP-{i:05d}"
            name = f"{self.rng.choice(vendor_names)} {i}"
            tier = self.rng.choices([SupplierTier.TIER_1.value, SupplierTier.TIER_2.value, SupplierTier.TIER_3.value], weights=[0.5, 0.35, 0.15])[0]
            status = self.rng.choices([SupplierStatus.QUALIFIED.value, SupplierStatus.CONDITIONAL.value, SupplierStatus.SUSPENDED.value], weights=[0.85, 0.12, 0.03])[0]
            country = self.rng.choice(COUNTRY_CODES)
            email = f"compliance@{name.lower().replace(' ', '')}.com"
            created_at = (self.base_date - timedelta(days=self.rng.randint(200, 800))).isoformat()
            self.suppliers.append({
                "supplier_id": supplier_id,
                "name": name,
                "tier": tier,
                "country": country,
                "contact_email": email,
                "status": status,
                "created_at": created_at
            })

        # 2. Warehouses (explicit entity master)
        self.warehouses = [dict(w) for w in WAREHOUSES_DEF]

        # 3. Products
        raw_names = ["Microcrystalline Cellulose", "Sodium Stearyl Fumarate", "Povidone K30", "Lactose Monohydrate",
                     "Hydroxypropyl Methylcellulose", "Titanium Dioxide USP", "Magnesium Stearate Pharma", "Croscarmellose Sodium",
                     "Colloidal Silicon Dioxide", "Polyethylene Glycol 3350", "Citric Acid Anhydrous", "Mannitol Fine Granules"]
        for i in range(1, self.cfg["raw_products_count"] + 1):
            pid = f"PRD-RAW-{i:04d}"
            sku = f"SKU-RAW-{i:04d}"
            name = f"{self.rng.choice(raw_names)} Grade-{chr(65 + (i % 6))}"
            uom = self.rng.choice(["KG", "LITER", "UNIT"])
            shelf_life = self.rng.randint(365, 1095)
            prod = {
                "product_id": pid,
                "sku": sku,
                "name": name,
                "category": ProductCategory.RAW_MATERIAL.value,
                "unit_of_measure": uom,
                "shelf_life_days": shelf_life,
                "created_at": (self.base_date - timedelta(days=600)).isoformat()
            }
            self.products.append(prod)
            self.raw_products_list.append(prod)
            self.raw_lots_by_product[pid] = []

        fin_names = ["CardioVasc Infusion Solution", "NeuroSedative Injectable", "ImmunoGlo Max Syringes",
                     "BioPeptide Insulin Extended", "OncoShield Monoclonal Vial", "RespiClear Oral Susp",
                     "Hemostatic Powder 50g", "Antiviral Sterile Suspension", "DermalRegen Hydrogel"]
        for i in range(1, self.cfg["finished_products_count"] + 1):
            pid = f"PRD-FIN-{i:04d}"
            sku = f"SKU-FIN-{i:04d}"
            name = f"{self.rng.choice(fin_names)} {100 + i * 25}mg"
            uom = self.rng.choice(["VIAL", "BOX", "UNIT"])
            shelf_life = self.rng.randint(365, 730)
            prod = {
                "product_id": pid,
                "sku": sku,
                "name": name,
                "category": ProductCategory.FINISHED_GOOD.value,
                "unit_of_measure": uom,
                "shelf_life_days": shelf_life,
                "created_at": (self.base_date - timedelta(days=500)).isoformat()
            }
            self.products.append(prod)
            self.fin_products_list.append(prod)

        # 4. BOMs
        bomi_counter = 1
        for i, fin_prod in enumerate(self.fin_products_list, start=1):
            bom_id = f"BOM-2026-{i:04d}"
            bom = {
                "bom_id": bom_id,
                "finished_product_id": fin_prod["product_id"],
                "version": "v1.0",
                "effective_from": "2026-01-01",
                "effective_to": "2028-12-31",
                "status": "ACTIVE"
            }
            self.boms.append(bom)
            self.bom_by_fin_product[fin_prod["product_id"]] = bom

            sample_count = min(len(self.raw_products_list), self.rng.randint(2, 4))
            chosen_raws = self.rng.sample(self.raw_products_list, sample_count)
            for raw in chosen_raws:
                qty_per_unit = round(self.rng.uniform(0.1, 2.5), 3)
                self.bom_items.append({
                    "bom_item_id": f"BOMI-2026-{bomi_counter:06d}",
                    "bom_id": bom_id,
                    "raw_product_id": raw["product_id"],
                    "quantity_per_unit": qty_per_unit
                })
                bomi_counter += 1

        # 5. Customers
        customer_names = ["Metropolitan General Hospital", "Mercy Health System", "Alliance Care Pharmacy",
                          "Ascension Regional Clinic", "CareFirst Distribution", "OmniCare Medical Center",
                          "Valley Childrens Hospital", "Apex Therapeutics Pharmacy", "Nordic Health Depot",
                          "National Health Trust", "St. Jude Clinical Alliance"]
        for i in range(1, self.cfg["customers_count"] + 1):
            cust_id = f"CUST-{i:05d}"
            name = f"{self.rng.choice(customer_names)} #{i}"
            cust_type = self.rng.choice([CustomerType.HOSPITAL.value, CustomerType.PHARMACY_CHAIN.value, CustomerType.REGIONAL_DISTRIBUTOR.value, CustomerType.CLINICAL_CENTER.value])
            region = self.rng.choice(REGIONS)
            email = f"pharmacy@{cust_id.lower()}.health.org"
            phone = f"+1-800-{self.rng.randint(100, 999):03d}-{self.rng.randint(1000, 9999):04d}"
            compliance = self.rng.choices(["GOLD", "SILVER", "STANDARD"], weights=[0.4, 0.45, 0.15])[0]
            self.customers.append({
                "customer_id": cust_id,
                "name": name,
                "type": cust_type,
                "region": region,
                "contact_email": email,
                "phone": phone,
                "compliance_tier": compliance
            })

    def _generate_raw_lots(self):
        for i in range(1, self.cfg["raw_lots_count"] + 1):
            supp = self.rng.choice(self.suppliers)
            raw_prod = self.rng.choice(self.raw_products_list)
            lot_id = f"RAWLOT-{supp['supplier_id']}-2026-{i:06d}"
            vendor_batch = f"VB-{supp['country']}-{self.rng.randint(10000, 99999)}"
            initial_qty = round(self.rng.uniform(500.0, 5000.0), 2)
            received_dt = self.base_date + timedelta(days=self.rng.randint(0, 120))
            expiry_dt = received_dt + timedelta(days=raw_prod["shelf_life_days"])
            qc_status = self.rng.choices([LotQCStatus.RELEASED.value, LotQCStatus.QUARANTINED.value], weights=[0.97, 0.03])[0]
            quarantine = (qc_status == LotQCStatus.QUARANTINED.value)

            record = {
                "material_lot_id": lot_id,
                "supplier_id": supp["supplier_id"],
                "product_id": raw_prod["product_id"],
                "supplier_batch_no": vendor_batch,
                "initial_qty": initial_qty,
                "consumed_qty": 0.0,
                "available_qty": initial_qty,
                "unit": raw_prod["unit_of_measure"],
                "received_date": received_dt.strftime("%Y-%m-%d"),
                "expiry_date": expiry_dt.strftime("%Y-%m-%d"),
                "qc_status": qc_status,
                "quarantine_status": quarantine
            }
            self.material_lots.append(record)
            self.raw_lots_by_product[raw_prod["product_id"]].append(record)

    def _generate_manufacturing(self):
        con_counter = 1
        fin_counter = 1
        bom_items_by_bom: Dict[str, List[Dict[str, Any]]] = {}
        for item in self.bom_items:
            bom_items_by_bom.setdefault(item["bom_id"], []).append(item)

        for wo_idx in range(1, self.cfg["production_orders_count"] + 1):
            wo_id = f"WO-2026-{wo_idx:06d}"
            fin_prod = self.rng.choice(self.fin_products_list)
            bom = self.bom_by_fin_product[fin_prod["product_id"]]
            req_items = bom_items_by_bom.get(bom["bom_id"], [])

            target_qty = round(self.rng.uniform(200.0, 2000.0), 2)
            yield_factor = self.rng.uniform(0.97, 1.01)
            produced_qty = round(target_qty * yield_factor, 2)

            consumed_lots_for_order = []
            max_received_date = self.base_date
            possible = True

            for req in req_items:
                avail_pool = self.raw_lots_by_product.get(req["raw_product_id"], [])
                candidates = [l for l in avail_pool if l["available_qty"] > 20.0 and l["qc_status"] == LotQCStatus.RELEASED.value]
                if not candidates:
                    candidates = avail_pool
                if candidates:
                    chosen_lot = self.rng.choice(candidates)
                    lot_rx_dt = datetime.strptime(chosen_lot["received_date"], "%Y-%m-%d")
                    if lot_rx_dt > max_received_date:
                        max_received_date = lot_rx_dt
                    needed_qty = round(req["quantity_per_unit"] * target_qty, 2)
                    consumed_lots_for_order.append((chosen_lot, needed_qty))
                else:
                    possible = False
                    break

            if not possible or not consumed_lots_for_order:
                continue

            order_start = max_received_date + timedelta(days=self.rng.randint(2, 20), hours=self.rng.randint(1, 12))
            order_comp = order_start + timedelta(hours=self.rng.randint(12, 48))
            prod_line = self.rng.choice(PRODUCTION_LINES)

            po_record = {
                "production_order_id": wo_id,
                "bom_id": bom["bom_id"],
                "product_id": fin_prod["product_id"],
                "target_qty": target_qty,
                "produced_qty": produced_qty,
                "start_date": order_start.isoformat(),
                "completion_date": order_comp.isoformat(),
                "status": ProductionOrderStatus.COMPLETED.value,
                "production_line": prod_line
            }
            self.production_orders.append(po_record)

            for raw_lot, needed_qty in consumed_lots_for_order:
                actual_consumed = min(raw_lot["available_qty"], needed_qty)
                if actual_consumed <= 0:
                    actual_consumed = round(needed_qty * 0.5, 2)
                raw_lot["consumed_qty"] = round(raw_lot["consumed_qty"] + actual_consumed, 2)
                raw_lot["available_qty"] = max(0.0, round(raw_lot["initial_qty"] - raw_lot["consumed_qty"], 2))

                con_record = {
                    "consumption_id": f"CON-2026-{con_counter:06d}",
                    "production_order_id": wo_id,
                    "material_lot_id": raw_lot["material_lot_id"],
                    "consumed_qty": actual_consumed,
                    "consumed_date": (order_start + timedelta(hours=2)).isoformat()
                }
                self.lot_consumptions.append(con_record)
                con_counter += 1

            if fin_counter <= self.cfg["finished_lots_count"]:
                fin_lot_id = f"FINLOT-2026-{fin_counter:06d}"
                fin_exp = (order_comp + timedelta(days=fin_prod["shelf_life_days"])).strftime("%Y-%m-%d")
                wh = self.rng.choice(self.warehouses)
                
                fin_lot = {
                    "finished_lot_id": fin_lot_id,
                    "production_order_id": wo_id,
                    "product_id": fin_prod["product_id"],
                    "warehouse_id": wh["warehouse_id"],
                    "produced_qty": produced_qty,
                    "warehouse_qty": produced_qty,
                    "shipped_qty": 0.0,
                    "quarantine_qty": 0.0,
                    "manufacture_date": order_comp.isoformat(),
                    "expiry_date": fin_exp,
                    "status": FinishedLotStatus.AVAILABLE.value
                }
                self.finished_lots.append(fin_lot)

                # Record stock intake movement
                self.inventory_movements.append({
                    "movement_id": f"MOV-2026-{self.mov_counter:06d}",
                    "finished_lot_id": fin_lot_id,
                    "warehouse_id": wh["warehouse_id"],
                    "movement_type": InventoryMovementType.PRODUCTION_RECEIPT.value,
                    "quantity": produced_qty,
                    "source_status": "IN_PRODUCTION",
                    "target_status": "AVAILABLE",
                    "reference_id": wo_id,
                    "timestamp": order_comp.isoformat()
                })
                self.mov_counter += 1
                fin_counter += 1

        # Generate additional finished lots for remaining quota (supporting 1:N ProductionOrder -> FinishedLot)
        while fin_counter <= self.cfg["finished_lots_count"] and self.production_orders:
            base_po = self.rng.choice(self.production_orders)
            fin_lot_id = f"FINLOT-2026-{fin_counter:06d}"
            mfg_dt = datetime.fromisoformat(base_po["completion_date"]) + timedelta(days=self.rng.randint(0, 5), hours=self.rng.randint(1, 10))
            fin_exp = (mfg_dt + timedelta(days=365)).strftime("%Y-%m-%d")
            qty = base_po["produced_qty"]
            wh = self.rng.choice(self.warehouses)

            fin_lot = {
                "finished_lot_id": fin_lot_id,
                "production_order_id": base_po["production_order_id"],
                "product_id": base_po["product_id"],
                "warehouse_id": wh["warehouse_id"],
                "produced_qty": qty,
                "warehouse_qty": qty,
                "shipped_qty": 0.0,
                "quarantine_qty": 0.0,
                "manufacture_date": mfg_dt.isoformat(),
                "expiry_date": fin_exp,
                "status": FinishedLotStatus.AVAILABLE.value
            }
            self.finished_lots.append(fin_lot)

            self.inventory_movements.append({
                "movement_id": f"MOV-2026-{self.mov_counter:06d}",
                "finished_lot_id": fin_lot_id,
                "warehouse_id": wh["warehouse_id"],
                "movement_type": InventoryMovementType.PRODUCTION_RECEIPT.value,
                "quantity": qty,
                "source_status": "IN_PRODUCTION",
                "target_status": "AVAILABLE",
                "reference_id": base_po["production_order_id"],
                "timestamp": mfg_dt.isoformat()
            })
            self.mov_counter += 1
            fin_counter += 1

    def _generate_distribution(self):
        """
        Generates shipments and customer deliveries with STRICT chronological consistency:
        finished_lot.manufacture_date <= shipment.ship_date <= delivery.delivery_date <= actual_arrival_date.
        """
        shipments_count = self.cfg["shipments_count"]
        deliveries_count = self.cfg["deliveries_count"]
        base_dels = deliveries_count // shipments_count
        remainder = deliveries_count % shipments_count

        del_counter = 1
        fin_lots_pool = list(self.finished_lots)

        for s_idx in range(1, shipments_count + 1):
            shp_id = f"SHP-2026-{s_idx:06d}"
            origin_wh = self.rng.choice(self.warehouses)["warehouse_id"]
            carrier = self.rng.choice(CARRIERS)
            tracking = f"TRK-{self.rng.randint(10000000, 99999999)}"
            num_dels_for_shp = base_dels + (1 if s_idx <= remainder else 0)

            # Choose lots for this shipment
            assigned_lots = []
            edge_lot_id = self.finished_lots[1]["finished_lot_id"] if len(self.finished_lots) > 1 else ""
            for _ in range(num_dels_for_shp):
                already_has_edge_lot = any(d["finished_lot_id"] == edge_lot_id for d in self.deliveries) or any(l["finished_lot_id"] == edge_lot_id for l in assigned_lots)
                candidates = [l for l in fin_lots_pool if l["warehouse_qty"] >= 5.0 and (not already_has_edge_lot or l["finished_lot_id"] != edge_lot_id)]
                if not candidates:
                    candidates = [l for l in fin_lots_pool if l["warehouse_qty"] > 0.0 and (not already_has_edge_lot or l["finished_lot_id"] != edge_lot_id)]
                if not candidates:
                    candidates = [l for l in fin_lots_pool if not already_has_edge_lot or l["finished_lot_id"] != edge_lot_id]
                if not candidates:
                    candidates = fin_lots_pool
                chosen_lot = self.rng.choice(candidates)
                assigned_lots.append(chosen_lot)

            # Shipment date MUST occur AFTER all lots on this shipment are manufactured
            max_mfg_dt = max(datetime.fromisoformat(l["manufacture_date"]) for l in assigned_lots)
            ship_dt = max_mfg_dt + timedelta(days=self.rng.randint(1, 10), hours=self.rng.randint(2, 12))
            transit_days = self.rng.randint(1, 4)
            est_arr = ship_dt + timedelta(days=transit_days)
            actual_arr = est_arr + timedelta(hours=self.rng.randint(0, 10))

            shp_record = {
                "shipment_id": shp_id,
                "origin_warehouse": origin_wh,
                "carrier_name": carrier,
                "tracking_number": tracking,
                "ship_date": ship_dt.isoformat(),
                "est_arrival_date": est_arr.isoformat(),
                "actual_arrival_date": actual_arr.isoformat(),
                "status": ShipmentStatus.DELIVERED.value
            }
            self.shipments.append(shp_record)

            # Generate deliveries for this shipment
            for lot in assigned_lots:
                del_id = f"DEL-2026-{del_counter:06d}"
                del_counter += 1
                cust = self.rng.choice(self.customers)

                avail = lot["warehouse_qty"]
                if avail >= 10.0:
                    del_qty = round(self.rng.uniform(5.0, min(avail, 250.0)), 2)
                elif avail > 0.0:
                    del_qty = round(avail, 2)
                else:
                    del_qty = 5.0

                lot["warehouse_qty"] = max(0.0, round(lot["warehouse_qty"] - del_qty, 2))
                lot["shipped_qty"] = round(lot["shipped_qty"] + del_qty, 2)

                # Delivery date strictly between shipment ship_date and actual_arrival_date
                del_dt = ship_dt + timedelta(days=self.rng.randint(1, transit_days), hours=self.rng.randint(1, 8))
                if del_dt > actual_arr:
                    actual_arr = del_dt + timedelta(hours=2)
                    shp_record["actual_arrival_date"] = actual_arr.isoformat()

                ack_status = self.rng.choices(["CONFIRMED", "PENDING_INSPECTION"], weights=[0.92, 0.08])[0]

                self.deliveries.append({
                    "delivery_id": del_id,
                    "shipment_id": shp_id,
                    "customer_id": cust["customer_id"],
                    "finished_lot_id": lot["finished_lot_id"],
                    "delivered_qty": del_qty,
                    "delivery_date": del_dt.isoformat(),
                    "customer_ack_status": ack_status,
                    "status": DeliveryStatus.RECEIVED.value
                })

                # Record stock dispatch movement
                self.inventory_movements.append({
                    "movement_id": f"MOV-2026-{self.mov_counter:06d}",
                    "finished_lot_id": lot["finished_lot_id"],
                    "warehouse_id": lot["warehouse_id"],
                    "movement_type": InventoryMovementType.SHIPMENT_DISPATCH.value,
                    "quantity": del_qty,
                    "source_status": "AVAILABLE",
                    "target_status": "SHIPPED",
                    "reference_id": shp_id,
                    "timestamp": ship_dt.isoformat()
                })
                self.mov_counter += 1

    def _generate_recalls(self):
        po_by_raw_lot: Dict[str, List[str]] = {}
        for c in self.lot_consumptions:
            po_by_raw_lot.setdefault(c["material_lot_id"], []).append(c["production_order_id"])

        fin_by_po: Dict[str, List[Dict[str, Any]]] = {}
        for fl in self.finished_lots:
            fin_by_po.setdefault(fl["production_order_id"], []).append(fl)

        del_by_fin: Dict[str, List[Dict[str, Any]]] = {}
        for d in self.deliveries:
            del_by_fin.setdefault(d["finished_lot_id"], []).append(d)

        num_recalls = self.cfg["recall_cases_count"]
        sampled_raw = self.rng.sample(self.material_lots, min(len(self.material_lots), num_recalls // 2))
        sampled_fin = self.rng.sample(self.finished_lots, min(len(self.finished_lots), num_recalls - len(sampled_raw)))

        recall_candidates = [("RAW_LOT", r["material_lot_id"]) for r in sampled_raw] + \
                            [("FINISHED_LOT", f["finished_lot_id"]) for f in sampled_fin]

        root_causes = [
            "Microbial Contamination (Burkholderia cepacia complex detected)",
            "Active Pharmaceutical Ingredient (API) Potency Out of Specification",
            "Particulate Matter Contamination (Subvisible glass particles)",
            "Cross-Contamination with Trace Allergen Excipient",
            "Packaging Seal Integrity Breach resulting in Sterility Loss",
            "Impurity N-Nitrosodimethylamine (NDMA) Exceedance"
        ]

        for idx, (trigger_type, trigger_id) in enumerate(recall_candidates, start=1):
            rec_id = f"REC-2026-{idx:06d}"
            hazard = self.rng.choices(
                [RecallHazardClass.CLASS_I.value, RecallHazardClass.CLASS_II.value, RecallHazardClass.CLASS_III.value],
                weights=[0.45, 0.40, 0.15]
            )[0]
            cause = self.rng.choice(root_causes)

            affected_raw_ids = set()
            affected_fin_lots: List[Dict[str, Any]] = []

            if trigger_type == "RAW_LOT":
                affected_raw_ids.add(trigger_id)
                wos = po_by_raw_lot.get(trigger_id, [])
                for wo in wos:
                    flots = fin_by_po.get(wo, [])
                    affected_fin_lots.extend(flots)
            else:
                fl = next((f for f in self.finished_lots if f["finished_lot_id"] == trigger_id), None)
                if fl:
                    affected_fin_lots.append(fl)
                    wo = fl["production_order_id"]
                    raw_cons = [c["material_lot_id"] for c in self.lot_consumptions if c["production_order_id"] == wo]
                    affected_raw_ids.update(raw_cons)

            unique_fin_map = {f["finished_lot_id"]: f for f in affected_fin_lots}
            affected_fin_lots = list(unique_fin_map.values())

            affected_deliveries: List[Dict[str, Any]] = []
            for fl in affected_fin_lots:
                fl["status"] = FinishedLotStatus.RECALLED.value
                dels = del_by_fin.get(fl["finished_lot_id"], [])
                affected_deliveries.extend(dels)

            total_affected_qty = sum(fl["produced_qty"] for fl in affected_fin_lots)

            # Determine recall initiation timestamp after deliveries & manufacturing
            max_dt = self.base_date + timedelta(days=120)
            for d in affected_deliveries:
                dd = datetime.fromisoformat(d["delivery_date"])
                if dd > max_dt:
                    max_dt = dd
            for fl in affected_fin_lots:
                md = datetime.fromisoformat(fl["manufacture_date"])
                if md > max_dt:
                    max_dt = md
            init_dt = max_dt + timedelta(days=self.rng.randint(2, 10), hours=self.rng.randint(2, 8))
            closure_target = (init_dt + timedelta(days=60)).strftime("%Y-%m-%d")

            # Actions
            for raw_id in affected_raw_ids:
                raw_lot = next((r for r in self.material_lots if r["material_lot_id"] == raw_id), None)
                if raw_lot:
                    raw_lot["qc_status"] = LotQCStatus.RECALLED.value
                    raw_lot["quarantine_status"] = True
                    self.recall_actions.append({
                        "action_id": f"ACT-2026-{self.act_counter:06d}",
                        "recall_case_id": rec_id,
                        "action_type": RecallActionType.NOTIFICATION_DISPATCH.value,
                        "target_entity_type": "SUPPLIER",
                        "target_entity_id": raw_lot["supplier_id"],
                        "actor_role": "Supplier",
                        "target_qty": raw_lot["initial_qty"],
                        "recovered_qty": raw_lot["available_qty"],
                        "action_status": ActionStatus.COMPLETED.value,
                        "action_timestamp": (init_dt + timedelta(hours=2)).isoformat(),
                        "notes": f"Supplier alert sent for contaminated lot {raw_id}. Remaining available quantity quarantined."
                    })
                    self.act_counter += 1

            total_recovered = 0.0
            for fl in affected_fin_lots:
                wh_held = fl["warehouse_qty"]
                fl["quarantine_qty"] = round(fl["quarantine_qty"] + wh_held, 2)
                fl["warehouse_qty"] = 0.0
                total_recovered += wh_held
                self.recall_actions.append({
                    "action_id": f"ACT-2026-{self.act_counter:06d}",
                    "recall_case_id": rec_id,
                    "action_type": RecallActionType.WAREHOUSE_QUARANTINE.value,
                    "target_entity_type": "WAREHOUSE_LOT",
                    "target_entity_id": fl["finished_lot_id"],
                    "actor_role": "Carrier/Warehouse Operator",
                    "target_qty": fl["produced_qty"],
                    "recovered_qty": wh_held,
                    "action_status": ActionStatus.COMPLETED.value,
                    "action_timestamp": (init_dt + timedelta(hours=6)).isoformat(),
                    "notes": f"Warehouse inventory quarantined: {wh_held} units locked in safe holding zone."
                })
                self.act_counter += 1

                if wh_held > 0:
                    self.inventory_movements.append({
                        "movement_id": f"MOV-2026-{self.mov_counter:06d}",
                        "finished_lot_id": fl["finished_lot_id"],
                        "warehouse_id": fl["warehouse_id"],
                        "movement_type": InventoryMovementType.QUARANTINE_HOLD.value,
                        "quantity": wh_held,
                        "source_status": "AVAILABLE",
                        "target_status": "QUARANTINED",
                        "reference_id": rec_id,
                        "timestamp": (init_dt + timedelta(hours=6)).isoformat()
                    })
                    self.mov_counter += 1

            for d in affected_deliveries:
                cust_retrieved = round(d["delivered_qty"] * self.rng.uniform(0.70, 0.95), 2)
                total_recovered += cust_retrieved
                d["status"] = DeliveryStatus.RECALLED.value
                self.recall_actions.append({
                    "action_id": f"ACT-2026-{self.act_counter:06d}",
                    "recall_case_id": rec_id,
                    "action_type": RecallActionType.CUSTOMER_RECALL_NOTICE.value,
                    "target_entity_type": "CUSTOMER_DELIVERY",
                    "target_entity_id": d["delivery_id"],
                    "actor_role": "Logistics Analyst",
                    "target_qty": d["delivered_qty"],
                    "recovered_qty": cust_retrieved,
                    "action_status": ActionStatus.COMPLETED.value,
                    "action_timestamp": (init_dt + timedelta(days=1, hours=4)).isoformat(),
                    "notes": f"Customer notice acknowledged by {d['customer_id']}. Retrieved {cust_retrieved} units."
                })
                self.act_counter += 1

                fl_obj = next((f for f in self.finished_lots if f["finished_lot_id"] == d["finished_lot_id"]), None)
                wh_id = fl_obj["warehouse_id"] if fl_obj else self.warehouses[0]["warehouse_id"]
                self.inventory_movements.append({
                    "movement_id": f"MOV-2026-{self.mov_counter:06d}",
                    "finished_lot_id": d["finished_lot_id"],
                    "warehouse_id": wh_id,
                    "movement_type": InventoryMovementType.RECALL_RECOVERY.value,
                    "quantity": cust_retrieved,
                    "source_status": "SHIPPED",
                    "target_status": "RECOVERED",
                    "reference_id": f"DEL-RET-{d['delivery_id']}",
                    "timestamp": (init_dt + timedelta(days=1, hours=4)).isoformat()
                })
                self.mov_counter += 1

            total_recovered = round(min(total_affected_qty, total_recovered), 2)
            containment_pct = round((total_recovered / total_affected_qty * 100.0), 2) if total_affected_qty > 0 else 100.0
            rec_status = RecallStatus.RECOVERY_ACTIVE.value if containment_pct < 98.0 else RecallStatus.RECONCILED.value

            self.recall_cases.append({
                "recall_case_id": rec_id,
                "trigger_entity_type": trigger_type,
                "trigger_entity_id": trigger_id,
                "hazard_classification": hazard,
                "root_cause": cause,
                "initiation_date": init_dt.isoformat(),
                "closure_target_date": closure_target,
                "status": rec_status,
                "affected_raw_lots_count": len(affected_raw_ids),
                "affected_finished_lots_count": len(affected_fin_lots),
                "total_affected_qty": total_affected_qty,
                "total_recovered_qty": total_recovered,
                "containment_rate_pct": containment_pct
            })

    def _inject_edge_cases(self):
        logger.info("Injecting enterprise negative edge cases with isolated ground truth...")
        
        # Edge Case 1: Missing input lot
        if self.production_orders:
            target_wo = self.production_orders[0]
            ghost_lot_id = "RAWLOT-SUP-99999-2026-999999"
            con_id = f"CON-2026-999999"
            self.lot_consumptions.append({
                "consumption_id": con_id,
                "production_order_id": target_wo["production_order_id"],
                "material_lot_id": ghost_lot_id,
                "consumed_qty": 450.0,
                "consumed_date": target_wo["start_date"]
            })
            self.ground_truth.append({
                "issue_type": EdgeCaseType.MISSING_INPUT_LOT.value,
                "entity_type": "ProductionOrderLotConsumption",
                "entity_id": con_id,
                "parent_id": target_wo["production_order_id"],
                "violating_value": ghost_lot_id,
                "expected_condition": "Referenced material_lot_id must exist in MaterialLot master table",
                "severity": "CRITICAL",
                "description": f"Work order {target_wo['production_order_id']} references ghost input raw lot {ghost_lot_id} not present in MaterialLot table."
            })

        # Edge Case 2: Delivered quantity exceeds produced quantity
        if self.finished_lots and self.deliveries:
            target_fl = self.finished_lots[1]
            fl_dels = [d for d in self.deliveries if d["finished_lot_id"] == target_fl["finished_lot_id"]]
            if fl_dels:
                deliv = fl_dels[0]
                excess_qty = round(target_fl["produced_qty"] * 1.5, 2)
                deliv["delivered_qty"] = excess_qty

                # Sync the corresponding shipment dispatch movement
                for m in self.inventory_movements:
                    if m["finished_lot_id"] == target_fl["finished_lot_id"] and m["movement_type"] == InventoryMovementType.SHIPMENT_DISPATCH.value:
                        m["quantity"] = excess_qty
                        break
                
                self.ground_truth.append({
                    "issue_type": EdgeCaseType.DELIVERED_EXCEEDS_PRODUCED.value,
                    "entity_type": "Delivery",
                    "entity_id": deliv["delivery_id"],
                    "parent_id": target_fl["finished_lot_id"],
                    "violating_value": str(excess_qty),
                    "expected_condition": f"Delivered quantity must be <= produced quantity ({target_fl['produced_qty']})",
                    "severity": "HIGH",
                    "description": f"Delivery {deliv['delivery_id']} delivered quantity ({excess_qty}) exceeds total manufactured lot quantity ({target_fl['produced_qty']})."
                })

        # Edge Case 3: Recall misses a downstream customer
        cust_actions = [a for a in self.recall_actions if a["action_type"] == RecallActionType.CUSTOMER_RECALL_NOTICE.value]
        if cust_actions:
            omitted_action = cust_actions[0]
            self.recall_actions.remove(omitted_action)
            omitted_delivery = next((d for d in self.deliveries if d["delivery_id"] == omitted_action["target_entity_id"]), None)
            cust_id = omitted_delivery["customer_id"] if omitted_delivery else "CUST-OMITTED"
            fl_id = omitted_delivery["finished_lot_id"] if omitted_delivery else "UNKNOWN_LOT"
            rec_id = omitted_action["recall_case_id"]

            self.ground_truth.append({
                "issue_type": EdgeCaseType.RECALL_MISSED_CUSTOMER.value,
                "entity_type": "RecallCase",
                "entity_id": rec_id,
                "parent_id": omitted_action["target_entity_id"],
                "violating_value": cust_id,
                "expected_condition": f"Customer {cust_id} received delivery {omitted_action['target_entity_id']} of recalled lot {fl_id} but received no notification dispatch action",
                "severity": "CRITICAL",
                "description": f"Recall case {rec_id} failed to notify customer {cust_id} on delivery {omitted_action['target_entity_id']}."
            })

        # Edge Case 4: Recalled inventory remains available for sale
        if len(self.finished_lots) > 2:
            breach_lot = self.finished_lots[2]
            breach_lot["status"] = FinishedLotStatus.AVAILABLE.value
            breach_lot["warehouse_qty"] = 500.0
            breach_lot["quarantine_qty"] = 0.0
            
            rec_case_id = "REC-2026-BREACH-01"
            breach_mfg_dt = datetime.fromisoformat(breach_lot["manufacture_date"])
            rec_init_dt = breach_mfg_dt + timedelta(days=self.rng.randint(15, 25), hours=self.rng.randint(2, 8))
            closure_target = (rec_init_dt + timedelta(days=60)).strftime("%Y-%m-%d")

            self.recall_cases.append({
                "recall_case_id": rec_case_id,
                "trigger_entity_type": "FINISHED_LOT",
                "trigger_entity_id": breach_lot["finished_lot_id"],
                "hazard_classification": RecallHazardClass.CLASS_I.value,
                "root_cause": "Critical Impurity Spike - Immediate Containment Required",
                "initiation_date": rec_init_dt.isoformat(),
                "closure_target_date": closure_target,
                "status": RecallStatus.INITIATED.value,
                "affected_raw_lots_count": 2,
                "affected_finished_lots_count": 1,
                "total_affected_qty": breach_lot["produced_qty"],
                "total_recovered_qty": 0.0,
                "containment_rate_pct": 0.0
            })
            
            breach_dels = [d for d in self.deliveries if d["finished_lot_id"] == breach_lot["finished_lot_id"]]
            for b_del in breach_dels:
                self.recall_actions.append({
                    "action_id": f"ACT-2026-{self.act_counter:06d}",
                    "recall_case_id": rec_case_id,
                    "action_type": RecallActionType.CUSTOMER_RECALL_NOTICE.value,
                    "target_entity_type": "CUSTOMER_DELIVERY",
                    "target_entity_id": b_del["delivery_id"],
                    "actor_role": "Logistics Analyst",
                    "target_qty": b_del["delivered_qty"],
                    "recovered_qty": round(b_del["delivered_qty"] * 0.85, 2),
                    "action_status": ActionStatus.COMPLETED.value,
                    "action_timestamp": (rec_init_dt + timedelta(days=1)).isoformat(),
                    "notes": f"Notice delivered to {b_del['customer_id']}."
                })
                self.act_counter += 1

            self.ground_truth.append({
                "issue_type": EdgeCaseType.RECALLED_INVENTORY_AVAILABLE.value,
                "entity_type": "FinishedLot",
                "entity_id": breach_lot["finished_lot_id"],
                "parent_id": rec_case_id,
                "violating_value": "status=AVAILABLE, warehouse_qty=500.0, quarantine_qty=0.0",
                "expected_condition": "Recalled finished lot inventory must have status=RECALLED/QUARANTINED and warehouse_qty quarantined",
                "severity": "CRITICAL",
                "description": f"Finished lot {breach_lot['finished_lot_id']} under active Class I recall {rec_case_id} remains listed as AVAILABLE for sale with 500 units unquarantined."
            })

    def _reconcile_mass_balances(self):
        fl_shipped_map: Dict[str, float] = {}
        for d in self.deliveries:
            fl_shipped_map[d["finished_lot_id"]] = round(fl_shipped_map.get(d["finished_lot_id"], 0.0) + float(d["delivered_qty"]), 2)

        for fl in self.finished_lots:
            is_edge_4 = any(g["issue_type"] == EdgeCaseType.RECALLED_INVENTORY_AVAILABLE.value and g["entity_id"] == fl["finished_lot_id"] for g in self.ground_truth)
            is_edge_2 = any(g["issue_type"] == EdgeCaseType.DELIVERED_EXCEEDS_PRODUCED.value and g["parent_id"] == fl["finished_lot_id"] for g in self.ground_truth)
            
            shipped = fl_shipped_map.get(fl["finished_lot_id"], 0.0)
            fl["shipped_qty"] = shipped
            
            if not is_edge_4 and not is_edge_2:
                if fl["status"] == FinishedLotStatus.RECALLED.value:
                    fl["warehouse_qty"] = 0.0
                else:
                    fl["warehouse_qty"] = max(0.0, round(fl["produced_qty"] - shipped, 2))
