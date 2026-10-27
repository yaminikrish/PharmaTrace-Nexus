"""
Schema definitions, Data Dictionary, and Domain Enums for End-to-End Lot Traceability & Recall Simulation.
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional

# Enums
class SupplierTier:
    TIER_1 = "TIER_1"
    TIER_2 = "TIER_2"
    TIER_3 = "TIER_3"

class SupplierStatus:
    QUALIFIED = "QUALIFIED"
    CONDITIONAL = "CONDITIONAL"
    SUSPENDED = "SUSPENDED"

class ProductCategory:
    RAW_MATERIAL = "RAW_MATERIAL"
    INTERMEDIATE = "INTERMEDIATE"
    FINISHED_GOOD = "FINISHED_GOOD"

class LotQCStatus:
    RELEASED = "RELEASED"
    QUARANTINED = "QUARANTINED"
    REJECTED = "REJECTED"
    RECALLED = "RECALLED"

class ProductionOrderStatus:
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class FinishedLotStatus:
    AVAILABLE = "AVAILABLE"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    QUARANTINED = "QUARANTINED"
    RECALLED = "RECALLED"
    SCRAPPED = "SCRAPPED"

class ShipmentStatus:
    PREPARING = "PREPARING"
    DISPATCHED = "DISPATCHED"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    INTERCEPTED = "INTERCEPTED"

class CustomerType:
    HOSPITAL = "HOSPITAL"
    PHARMACY_CHAIN = "PHARMACY_CHAIN"
    REGIONAL_DISTRIBUTOR = "REGIONAL_DISTRIBUTOR"
    CLINICAL_CENTER = "CLINICAL_CENTER"

class DeliveryStatus:
    IN_TRANSIT = "IN_TRANSIT"
    RECEIVED = "RECEIVED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    RECALLED = "RECALLED"

class RecallHazardClass:
    CLASS_I = "CLASS_I"      # High risk: reasonable probability of severe adverse health consequences or death
    CLASS_II = "CLASS_II"    # Medium risk: temporary or medically reversible adverse health consequences
    CLASS_III = "CLASS_III"  # Low risk: not likely to cause adverse health consequences

class RecallStatus:
    INITIATED = "INITIATED"
    SCOPE_DETERMINED = "SCOPE_DETERMINED"
    NOTIFICATIONS_SENT = "NOTIFICATIONS_SENT"
    QUARANTINE_IN_EFFECT = "QUARANTINE_IN_EFFECT"
    RECOVERY_ACTIVE = "RECOVERY_ACTIVE"
    RECONCILED = "RECONCILED"
    CLOSED = "CLOSED"

class RecallActionType:
    NOTIFICATION_DISPATCH = "NOTIFICATION_DISPATCH"
    WAREHOUSE_QUARANTINE = "WAREHOUSE_QUARANTINE"
    CARRIER_HOLD = "CARRIER_HOLD"
    CUSTOMER_RECALL_NOTICE = "CUSTOMER_RECALL_NOTICE"
    PRODUCT_RETRIEVAL = "PRODUCT_RETRIEVAL"
    DESTRUCTION_VERIFICATION = "DESTRUCTION_VERIFICATION"

class ActionStatus:
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class EdgeCaseType:
    MISSING_INPUT_LOT = "MISSING_INPUT_LOT"
    DELIVERED_EXCEEDS_PRODUCED = "DELIVERED_EXCEEDS_PRODUCED"
    RECALL_MISSED_CUSTOMER = "RECALL_MISSED_CUSTOMER"
    RECALLED_INVENTORY_AVAILABLE = "RECALLED_INVENTORY_AVAILABLE"


# Comprehensive Data Dictionary definition
DATA_DICTIONARY: Dict[str, Dict[str, Any]] = {
    "Supplier": {
        "description": "Master record of external raw material and packaging vendors.",
        "primary_key": "supplier_id",
        "relationships": [
            {"foreign_key": "None", "references": "None", "cardinality": "1:N to MaterialLot"}
        ],
        "fields": {
            "supplier_id": {"type": "VARCHAR(24)", "required": True, "unique": True, "allowed_values": "SUP-00001 to SUP-99999", "validation_rule": "Format matches ^SUP-\\d{5}$"},
            "name": {"type": "VARCHAR(128)", "required": True, "unique": False, "allowed_values": "String", "validation_rule": "Non-empty string"},
            "tier": {"type": "VARCHAR(16)", "required": True, "unique": False, "allowed_values": ["TIER_1", "TIER_2", "TIER_3"], "validation_rule": "Must be valid SupplierTier enum"},
            "country": {"type": "VARCHAR(3)", "required": True, "unique": False, "allowed_values": "ISO-3166 alpha-3 (e.g. USA, CHE, DEU, JPN, GBR)", "validation_rule": "3 uppercase letters"},
            "contact_email": {"type": "VARCHAR(128)", "required": True, "unique": False, "allowed_values": "Email address", "validation_rule": "Contains @ and valid domain"},
            "status": {"type": "VARCHAR(16)", "required": True, "unique": False, "allowed_values": ["QUALIFIED", "CONDITIONAL", "SUSPENDED"], "validation_rule": "Must be valid SupplierStatus enum"},
            "created_at": {"type": "DATETIME", "required": True, "unique": False, "allowed_values": "ISO-8601 string", "validation_rule": "Valid past timestamp"}
        }
    },
    "Product": {
        "description": "Master catalog of raw ingredients, intermediate materials, and finished goods.",
        "primary_key": "product_id",
        "relationships": [
            {"foreign_key": "None", "references": "None", "cardinality": "1:N to MaterialLot, 1:N to BOM, 1:N to FinishedLot"}
        ],
        "fields": {
            "product_id": {"type": "VARCHAR(24)", "required": True, "unique": True, "allowed_values": "PRD-RAW-0001.. or PRD-FIN-0001..", "validation_rule": "Format matches ^PRD-(RAW|FIN)-\\d{4}$"},
            "sku": {"type": "VARCHAR(32)", "required": True, "unique": True, "allowed_values": "SKU identifier", "validation_rule": "Alphanumeric string"},
            "name": {"type": "VARCHAR(128)", "required": True, "unique": False, "allowed_values": "String", "validation_rule": "Product commercial name"},
            "category": {"type": "VARCHAR(20)", "required": True, "unique": False, "allowed_values": ["RAW_MATERIAL", "INTERMEDIATE", "FINISHED_GOOD"], "validation_rule": "Valid ProductCategory enum"},
            "unit_of_measure": {"type": "VARCHAR(10)", "required": True, "unique": False, "allowed_values": ["KG", "LITER", "UNIT", "VIAL", "BOX"], "validation_rule": "Standard metric/packaging unit"},
            "shelf_life_days": {"type": "INTEGER", "required": True, "unique": False, "allowed_values": "30 to 1825", "validation_rule": "Positive integer in days"},
            "created_at": {"type": "DATETIME", "required": True, "unique": False, "allowed_values": "ISO-8601 string", "validation_rule": "Valid timestamp"}
        }
    },
    "BOM": {
        "description": "Bill of Materials specification defining recipe required to produce a finished product.",
        "primary_key": "bom_id",
        "relationships": [
            {"foreign_key": "finished_product_id", "references": "Product.product_id", "cardinality": "N:1"},
            {"foreign_key": "None", "references": "None", "cardinality": "1:N to BOMItem, 1:N to ProductionOrder"}
        ],
        "fields": {
            "bom_id": {"type": "VARCHAR(24)", "required": True, "unique": True, "allowed_values": "BOM-2026-0001..", "validation_rule": "Format matches ^BOM-2026-\\d{4}$"},
            "finished_product_id": {"type": "VARCHAR(24)", "required": True, "unique": False, "allowed_values": "Valid Product.product_id with category=FINISHED_GOOD", "validation_rule": "FK integrity to Product"},
            "version": {"type": "VARCHAR(8)", "required": True, "unique": False, "allowed_values": "v1.0, v1.1, v2.0", "validation_rule": "Version string"},
            "effective_from": {"type": "DATE", "required": True, "unique": False, "allowed_values": "YYYY-MM-DD", "validation_rule": "ISO-8601 date <= effective_to"},
            "effective_to": {"type": "DATE", "required": True, "unique": False, "allowed_values": "YYYY-MM-DD", "validation_rule": "ISO-8601 date >= effective_from"},
            "status": {"type": "VARCHAR(16)", "required": True, "unique": False, "allowed_values": ["ACTIVE", "SUPERSEDED", "DRAFT"], "validation_rule": "Lifecycle state"}
        }
    },
    "BOMItem": {
        "description": "Bill of Materials component items detailing quantity of raw material needed per finished unit.",
        "primary_key": "bom_item_id",
        "relationships": [
            {"foreign_key": "bom_id", "references": "BOM.bom_id", "cardinality": "N:1"},
            {"foreign_key": "raw_product_id", "references": "Product.product_id", "cardinality": "N:1"}
        ],
        "fields": {
            "bom_item_id": {"type": "VARCHAR(28)", "required": True, "unique": True, "allowed_values": "BOMI-2026-000001..", "validation_rule": "Format matches ^BOMI-2026-\\d{6}$"},
            "bom_id": {"type": "VARCHAR(24)", "required": True, "unique": False, "allowed_values": "Valid BOM.bom_id", "validation_rule": "FK integrity to BOM"},
            "raw_product_id": {"type": "VARCHAR(24)", "required": True, "unique": False, "allowed_values": "Valid Product.product_id with category=RAW_MATERIAL", "validation_rule": "FK integrity to Product"},
            "quantity_per_unit": {"type": "DECIMAL(10,4)", "required": True, "unique": False, "allowed_values": "0.01 to 500.0", "validation_rule": "Positive decimal number"}
        }
    },
    "MaterialLot": {
        "description": "Inbound raw material batches received from certified suppliers.",
        "primary_key": "material_lot_id",
        "relationships": [
            {"foreign_key": "supplier_id", "references": "Supplier.supplier_id", "cardinality": "N:1"},
            {"foreign_key": "product_id", "references": "Product.product_id", "cardinality": "N:1"},
            {"foreign_key": "None", "references": "None", "cardinality": "1:N to ProductionOrderLotConsumption"}
        ],
        "fields": {
            "material_lot_id": {"type": "VARCHAR(40)", "required": True, "unique": True, "allowed_values": "RAWLOT-<supplier-id>-2026-000001", "validation_rule": "Format matches ^RAWLOT-SUP-\\d{5}-2026-\\d{6}$"},
            "supplier_id": {"type": "VARCHAR(24)", "required": True, "unique": False, "allowed_values": "Valid Supplier.supplier_id", "validation_rule": "FK integrity to Supplier"},
            "product_id": {"type": "VARCHAR(24)", "required": True, "unique": False, "allowed_values": "Valid Product.product_id (category=RAW_MATERIAL)", "validation_rule": "FK integrity to Product"},
            "supplier_batch_no": {"type": "VARCHAR(32)", "required": True, "unique": False, "allowed_values": "Vendor batch code", "validation_rule": "Alphanumeric string"},
            "initial_qty": {"type": "DECIMAL(12,2)", "required": True, "unique": False, "allowed_values": "50.0 to 10000.0", "validation_rule": "Positive decimal"},
            "consumed_qty": {"type": "DECIMAL(12,2)", "required": True, "unique": False, "allowed_values": "0.0 to initial_qty", "validation_rule": "Must be <= initial_qty"},
            "available_qty": {"type": "DECIMAL(12,2)", "required": True, "unique": False, "allowed_values": "initial_qty - consumed_qty", "validation_rule": "Arithmetic reconciliation: initial_qty - consumed_qty"},
            "unit": {"type": "VARCHAR(10)", "required": True, "unique": False, "allowed_values": ["KG", "LITER", "UNIT"], "validation_rule": "Matches product unit"},
            "received_date": {"type": "DATE", "required": True, "unique": False, "allowed_values": "YYYY-MM-DD", "validation_rule": "Valid reception date"},
            "expiry_date": {"type": "DATE", "required": True, "unique": False, "allowed_values": "YYYY-MM-DD", "validation_rule": "Must be > received_date"},
            "qc_status": {"type": "VARCHAR(16)", "required": True, "unique": False, "allowed_values": ["RELEASED", "QUARANTINED", "REJECTED", "RECALLED"], "validation_rule": "Valid LotQCStatus enum"},
            "quarantine_status": {"type": "BOOLEAN", "required": True, "unique": False, "allowed_values": [True, False], "validation_rule": "True if under active quarantine hold"}
        }
    },
    "ProductionOrder": {
        "description": "Manufacturing batch work orders transforming raw material lots into finished products.",
        "primary_key": "production_order_id",
        "relationships": [
            {"foreign_key": "bom_id", "references": "BOM.bom_id", "cardinality": "N:1"},
            {"foreign_key": "product_id", "references": "Product.product_id", "cardinality": "N:1"},
            {"foreign_key": "None", "references": "None", "cardinality": "1:N to ProductionOrderLotConsumption, 1:N to FinishedLot"}
        ],
        "fields": {
            "production_order_id": {"type": "VARCHAR(24)", "required": True, "unique": True, "allowed_values": "WO-2026-000001", "validation_rule": "Format matches ^WO-2026-\\d{6}$"},
            "bom_id": {"type": "VARCHAR(24)", "required": True, "unique": False, "allowed_values": "Valid BOM.bom_id", "validation_rule": "FK integrity to BOM"},
            "product_id": {"type": "VARCHAR(24)", "required": True, "unique": False, "allowed_values": "Valid Product.product_id", "validation_rule": "FK integrity to Product"},
            "target_qty": {"type": "DECIMAL(12,2)", "required": True, "unique": False, "allowed_values": "50.0 to 5000.0", "validation_rule": "Target planned quantity"},
            "produced_qty": {"type": "DECIMAL(12,2)", "required": True, "unique": False, "allowed_values": "target_qty * yield_factor (typically 95%-102%)", "validation_rule": "Derived output mass"},
            "start_date": {"type": "DATETIME", "required": True, "unique": False, "allowed_values": "ISO-8601 string", "validation_rule": "Timestamp >= all consumed lots received_date"},
            "completion_date": {"type": "DATETIME", "required": True, "unique": False, "allowed_values": "ISO-8601 string", "validation_rule": "Timestamp >= start_date"},
            "status": {"type": "VARCHAR(16)", "required": True, "unique": False, "allowed_values": ["PLANNED", "IN_PROGRESS", "COMPLETED", "CANCELLED"], "validation_rule": "Valid ProductionOrderStatus enum"},
            "production_line": {"type": "VARCHAR(16)", "required": True, "unique": False, "allowed_values": ["LINE-A", "LINE-B", "LINE-C", "LINE-D"], "validation_rule": "Valid facility line"}
        }
    },
    "ProductionOrderLotConsumption": {
        "description": "Genealogy bridge record detailing exact raw material lots consumed into each production order.",
        "primary_key": "consumption_id",
        "relationships": [
            {"foreign_key": "production_order_id", "references": "ProductionOrder.production_order_id", "cardinality": "N:1"},
            {"foreign_key": "material_lot_id", "references": "MaterialLot.material_lot_id", "cardinality": "N:1"}
        ],
        "fields": {
            "consumption_id": {"type": "VARCHAR(28)", "required": True, "unique": True, "allowed_values": "CON-2026-000001..", "validation_rule": "Format matches ^CON-2026-\\d{6}$"},
            "production_order_id": {"type": "VARCHAR(24)", "required": True, "unique": False, "allowed_values": "Valid ProductionOrder.production_order_id", "validation_rule": "FK integrity to ProductionOrder"},
            "material_lot_id": {"type": "VARCHAR(40)", "required": True, "unique": False, "allowed_values": "Valid MaterialLot.material_lot_id", "validation_rule": "FK integrity to MaterialLot (except edge cases)"},
            "consumed_qty": {"type": "DECIMAL(12,2)", "required": True, "unique": False, "allowed_values": "> 0.0", "validation_rule": "Positive decimal quantity"},
            "consumed_date": {"type": "DATETIME", "required": True, "unique": False, "allowed_values": "ISO-8601 string", "validation_rule": "Between order start_date and completion_date"}
        }
    },
    "Warehouse": {
        "description": "Logistics and manufacturing warehouse storage facilities holding lot inventories.",
        "primary_key": "warehouse_id",
        "relationships": [
            {"foreign_key": "None", "references": "None", "cardinality": "1:N to FinishedLot, 1:N to Shipment, 1:N to InventoryMovement"}
        ],
        "fields": {
            "warehouse_id": {"type": "VARCHAR(24)", "required": True, "unique": True, "allowed_values": "WH-0001 to WH-9999", "validation_rule": "Format matches ^WH-\\d{4}$"},
            "name": {"type": "VARCHAR(128)", "required": True, "unique": False, "allowed_values": "Warehouse name", "validation_rule": "Non-empty string"},
            "location": {"type": "VARCHAR(64)", "required": True, "unique": False, "allowed_values": "City / Metro area", "validation_rule": "Non-empty string"},
            "country": {"type": "VARCHAR(3)", "required": True, "unique": False, "allowed_values": "ISO-3166 alpha-3", "validation_rule": "3 uppercase letters"},
            "facility_type": {"type": "VARCHAR(32)", "required": True, "unique": False, "allowed_values": ["DISTRIBUTION_CENTER", "MANUFACTURING_WAREHOUSE", "CENTRAL_DEPOT"], "validation_rule": "Valid facility type"},
            "status": {"type": "VARCHAR(16)", "required": True, "unique": False, "allowed_values": ["ACTIVE", "INACTIVE"], "validation_rule": "Status string"}
        }
    },
    "FinishedLot": {
        "description": "Finished product lots produced from manufacturing work orders.",
        "primary_key": "finished_lot_id",
        "relationships": [
            {"foreign_key": "production_order_id", "references": "ProductionOrder.production_order_id", "cardinality": "N:1"},
            {"foreign_key": "product_id", "references": "Product.product_id", "cardinality": "N:1"},
            {"foreign_key": "warehouse_id", "references": "Warehouse.warehouse_id", "cardinality": "N:1"},
            {"foreign_key": "None", "references": "None", "cardinality": "1:N to Delivery, 1:N to InventoryMovement"}
        ],
        "fields": {
            "finished_lot_id": {"type": "VARCHAR(28)", "required": True, "unique": True, "allowed_values": "FINLOT-2026-000001", "validation_rule": "Format matches ^FINLOT-2026-\\d{6}$"},
            "production_order_id": {"type": "VARCHAR(24)", "required": True, "unique": False, "allowed_values": "Valid ProductionOrder.production_order_id", "validation_rule": "FK integrity to ProductionOrder"},
            "product_id": {"type": "VARCHAR(24)", "required": True, "unique": False, "allowed_values": "Valid Product.product_id", "validation_rule": "Matches production order product_id"},
            "warehouse_id": {"type": "VARCHAR(24)", "required": True, "unique": False, "allowed_values": "Valid Warehouse.warehouse_id", "validation_rule": "FK integrity to Warehouse"},
            "produced_qty": {"type": "DECIMAL(12,2)", "required": True, "unique": False, "allowed_values": "Matches production order produced_qty", "validation_rule": "Mass balance check"},
            "warehouse_qty": {"type": "DECIMAL(12,2)", "required": True, "unique": False, "allowed_values": "produced_qty - shipped_qty", "validation_rule": "Derived: produced_qty - shipped_qty"},
            "shipped_qty": {"type": "DECIMAL(12,2)", "required": True, "unique": False, "allowed_values": "Sum of related delivery quantities", "validation_rule": "Derived: sum(Delivery.delivered_qty)"},
            "quarantine_qty": {"type": "DECIMAL(12,2)", "required": True, "unique": False, "allowed_values": "Quantity held in quarantine", "validation_rule": "0.0 or warehouse_qty if quarantined"},
            "manufacture_date": {"type": "DATETIME", "required": True, "unique": False, "allowed_values": "ISO-8601 string", "validation_rule": "Matches work order completion_date"},
            "expiry_date": {"type": "DATE", "required": True, "unique": False, "allowed_values": "YYYY-MM-DD", "validation_rule": "manufacture_date + product.shelf_life_days"},
            "status": {"type": "VARCHAR(20)", "required": True, "unique": False, "allowed_values": ["AVAILABLE", "IN_TRANSIT", "DELIVERED", "QUARANTINED", "RECALLED", "SCRAPPED"], "validation_rule": "Valid FinishedLotStatus enum"}
        }
    },
    "InventoryMovement": {
        "description": "Immutable ledger of finished lot inventory transitions between available, quarantined, shipped, and recovered states across warehouses.",
        "primary_key": "movement_id",
        "relationships": [
            {"foreign_key": "finished_lot_id", "references": "FinishedLot.finished_lot_id", "cardinality": "N:1"},
            {"foreign_key": "warehouse_id", "references": "Warehouse.warehouse_id", "cardinality": "N:1"}
        ],
        "fields": {
            "movement_id": {"type": "VARCHAR(28)", "required": True, "unique": True, "allowed_values": "MOV-2026-000001..", "validation_rule": "Format matches ^MOV-2026-\\d{6}$"},
            "finished_lot_id": {"type": "VARCHAR(28)", "required": True, "unique": False, "allowed_values": "Valid FinishedLot.finished_lot_id", "validation_rule": "FK integrity to FinishedLot"},
            "warehouse_id": {"type": "VARCHAR(24)", "required": True, "unique": False, "allowed_values": "Valid Warehouse.warehouse_id", "validation_rule": "FK integrity to Warehouse"},
            "movement_type": {"type": "VARCHAR(32)", "required": True, "unique": False, "allowed_values": ["PRODUCTION_RECEIPT", "SHIPMENT_DISPATCH", "QUARANTINE_HOLD", "RECALL_RECOVERY"], "validation_rule": "Valid movement type"},
            "quantity": {"type": "DECIMAL(12,2)", "required": True, "unique": False, "allowed_values": "> 0.0", "validation_rule": "Quantity transferred"},
            "source_status": {"type": "VARCHAR(20)", "required": True, "unique": False, "allowed_values": ["IN_PRODUCTION", "AVAILABLE", "SHIPPED", "QUARANTINED", "RECALLED"], "validation_rule": "Origin inventory status"},
            "target_status": {"type": "VARCHAR(20)", "required": True, "unique": False, "allowed_values": ["AVAILABLE", "SHIPPED", "QUARANTINED", "RECOVERED"], "validation_rule": "Target inventory status"},
            "reference_id": {"type": "VARCHAR(32)", "required": True, "unique": False, "allowed_values": "Reference transaction ID (WO, SHP, REC, ACT)", "validation_rule": "Transaction reference"},
            "timestamp": {"type": "DATETIME", "required": True, "unique": False, "allowed_values": "ISO-8601 string", "validation_rule": "Valid timestamp"}
        }
    },
    "Shipment": {
        "description": "Logistics transit records moving finished lots from warehouse to customer facilities.",
        "primary_key": "shipment_id",
        "relationships": [
            {"foreign_key": "origin_warehouse", "references": "Warehouse.warehouse_id", "cardinality": "N:1"},
            {"foreign_key": "None", "references": "None", "cardinality": "1:N to Delivery"}
        ],
        "fields": {
            "shipment_id": {"type": "VARCHAR(24)", "required": True, "unique": True, "allowed_values": "SHP-2026-000001", "validation_rule": "Format matches ^SHP-2026-\\d{6}$"},
            "origin_warehouse": {"type": "VARCHAR(32)", "required": True, "unique": False, "allowed_values": ["WH-0001", "WH-0002", "WH-0003", "WH-0004", "WH-0005"], "validation_rule": "FK to Warehouse"},
            "carrier_name": {"type": "VARCHAR(64)", "required": True, "unique": False, "allowed_values": ["DHL Supply Chain", "FedEx Freight", "UPS Supply Chain", "Kuehne+Nagel", "Maersk Logistics"], "validation_rule": "Approved carrier"},
            "tracking_number": {"type": "VARCHAR(32)", "required": True, "unique": True, "allowed_values": "Carrier tracking identifier", "validation_rule": "Alphanumeric string"},
            "ship_date": {"type": "DATETIME", "required": True, "unique": False, "allowed_values": "ISO-8601 string", "validation_rule": "Timestamp >= lot manufacture_date"},
            "est_arrival_date": {"type": "DATETIME", "required": True, "unique": False, "allowed_values": "ISO-8601 string", "validation_rule": "ship_date + 1 to 5 days"},
            "actual_arrival_date": {"type": "DATETIME", "required": False, "unique": False, "allowed_values": "ISO-8601 string or NULL", "validation_rule": "Actual arrival date"},
            "status": {"type": "VARCHAR(16)", "required": True, "unique": False, "allowed_values": ["PREPARING", "DISPATCHED", "IN_TRANSIT", "DELIVERED", "INTERCEPTED"], "validation_rule": "Valid ShipmentStatus enum"}
        }
    },
    "Customer": {
        "description": "Recipient healthcare organizations, hospital networks, pharmacy chains, and distributors.",
        "primary_key": "customer_id",
        "relationships": [
            {"foreign_key": "None", "references": "None", "cardinality": "1:N to Delivery"}
        ],
        "fields": {
            "customer_id": {"type": "VARCHAR(24)", "required": True, "unique": True, "allowed_values": "CUST-00001 to CUST-99999", "validation_rule": "Format matches ^CUST-\\d{5}$"},
            "name": {"type": "VARCHAR(128)", "required": True, "unique": False, "allowed_values": "Commercial customer name", "validation_rule": "Non-empty string"},
            "type": {"type": "VARCHAR(24)", "required": True, "unique": False, "allowed_values": ["HOSPITAL", "PHARMACY_CHAIN", "REGIONAL_DISTRIBUTOR", "CLINICAL_CENTER"], "validation_rule": "Valid CustomerType enum"},
            "region": {"type": "VARCHAR(16)", "required": True, "unique": False, "allowed_values": ["NA_EAST", "NA_WEST", "NA_CENTRAL", "EU_WEST", "EU_CENTRAL", "APAC"], "validation_rule": "Geographic sales region"},
            "contact_email": {"type": "VARCHAR(128)", "required": True, "unique": False, "allowed_values": "Email address", "validation_rule": "Valid email format"},
            "phone": {"type": "VARCHAR(24)", "required": True, "unique": False, "allowed_values": "E.164 phone string", "validation_rule": "International phone format"},
            "compliance_tier": {"type": "VARCHAR(10)", "required": True, "unique": False, "allowed_values": ["GOLD", "SILVER", "STANDARD"], "validation_rule": "SLA compliance level"}
        }
    },
    "Delivery": {
        "description": "Customer delivery line item detailing received quantities of finished product lots.",
        "primary_key": "delivery_id",
        "relationships": [
            {"foreign_key": "shipment_id", "references": "Shipment.shipment_id", "cardinality": "N:1"},
            {"foreign_key": "customer_id", "references": "Customer.customer_id", "cardinality": "N:1"},
            {"foreign_key": "finished_lot_id", "references": "FinishedLot.finished_lot_id", "cardinality": "N:1"}
        ],
        "fields": {
            "delivery_id": {"type": "VARCHAR(28)", "required": True, "unique": True, "allowed_values": "DEL-2026-000001", "validation_rule": "Format matches ^DEL-2026-\\d{6}$"},
            "shipment_id": {"type": "VARCHAR(24)", "required": True, "unique": False, "allowed_values": "Valid Shipment.shipment_id", "validation_rule": "FK integrity to Shipment"},
            "customer_id": {"type": "VARCHAR(24)", "required": True, "unique": False, "allowed_values": "Valid Customer.customer_id", "validation_rule": "FK integrity to Customer"},
            "finished_lot_id": {"type": "VARCHAR(28)", "required": True, "unique": False, "allowed_values": "Valid FinishedLot.finished_lot_id", "validation_rule": "FK integrity to FinishedLot"},
            "delivered_qty": {"type": "DECIMAL(12,2)", "required": True, "unique": False, "allowed_values": "Positive decimal quantity", "validation_rule": "Sum of lot deliveries <= lot produced_qty (except edge cases)"},
            "delivery_date": {"type": "DATETIME", "required": True, "unique": False, "allowed_values": "ISO-8601 string", "validation_rule": "delivery_date >= shipment.ship_date"},
            "customer_ack_status": {"type": "VARCHAR(16)", "required": True, "unique": False, "allowed_values": ["CONFIRMED", "PENDING_INSPECTION", "DISPUTED"], "validation_rule": "Customer acknowledgment"},
            "status": {"type": "VARCHAR(16)", "required": True, "unique": False, "allowed_values": ["IN_TRANSIT", "RECEIVED", "ACCEPTED", "REJECTED", "RECALLED"], "validation_rule": "Valid DeliveryStatus enum"}
        }
    },
    "RecallCase": {
        "description": "Formal recall incident record tracking trigger, blast radius, actions, and regulatory closure.",
        "primary_key": "recall_case_id",
        "relationships": [
            {"foreign_key": "None", "references": "None", "cardinality": "1:N to RecallAction"}
        ],
        "fields": {
            "recall_case_id": {"type": "VARCHAR(24)", "required": True, "unique": True, "allowed_values": "REC-2026-000001", "validation_rule": "Format matches ^REC-2026-\\d{6}$"},
            "trigger_entity_type": {"type": "VARCHAR(16)", "required": True, "unique": False, "allowed_values": ["RAW_LOT", "FINISHED_LOT"], "validation_rule": "Entity type that triggered recall"},
            "trigger_entity_id": {"type": "VARCHAR(40)", "required": True, "unique": False, "allowed_values": "Valid MaterialLot.material_lot_id or FinishedLot.finished_lot_id", "validation_rule": "Valid entity key"},
            "hazard_classification": {"type": "VARCHAR(16)", "required": True, "unique": False, "allowed_values": ["CLASS_I", "CLASS_II", "CLASS_III"], "validation_rule": "FDA/EMA hazard tier"},
            "root_cause": {"type": "VARCHAR(256)", "required": True, "unique": False, "allowed_values": "Description (e.g. Microbial Contamination, Impurity Exceedance, Label Error)", "validation_rule": "Documented root cause"},
            "initiation_date": {"type": "DATETIME", "required": True, "unique": False, "allowed_values": "ISO-8601 string", "validation_rule": "Incident trigger timestamp"},
            "closure_target_date": {"type": "DATE", "required": True, "unique": False, "allowed_values": "YYYY-MM-DD", "validation_rule": "initiation_date + 30 to 90 days"},
            "status": {"type": "VARCHAR(24)", "required": True, "unique": False, "allowed_values": ["INITIATED", "SCOPE_DETERMINED", "NOTIFICATIONS_SENT", "QUARANTINE_IN_EFFECT", "RECOVERY_ACTIVE", "RECONCILED", "CLOSED"], "validation_rule": "Valid RecallStatus enum"},
            "affected_raw_lots_count": {"type": "INTEGER", "required": True, "unique": False, "allowed_values": ">= 0", "validation_rule": "Count of traced raw lots"},
            "affected_finished_lots_count": {"type": "INTEGER", "required": True, "unique": False, "allowed_values": ">= 0", "validation_rule": "Count of traced finished lots"},
            "total_affected_qty": {"type": "DECIMAL(12,2)", "required": True, "unique": False, "allowed_values": ">= 0.0", "validation_rule": "Sum of affected units across finished lots"},
            "total_recovered_qty": {"type": "DECIMAL(12,2)", "required": True, "unique": False, "allowed_values": "0.0 to total_affected_qty", "validation_rule": "Derived recovered quantity"},
            "containment_rate_pct": {"type": "DECIMAL(5,2)", "required": True, "unique": False, "allowed_values": "0.00 to 100.00", "validation_rule": "Derived: (total_recovered_qty / total_affected_qty) * 100"}
        }
    },
    "RecallAction": {
        "description": "Immutable lifecycle action log capturing containment notices, quarantine locks, and physical retrievals.",
        "primary_key": "action_id",
        "relationships": [
            {"foreign_key": "recall_case_id", "references": "RecallCase.recall_case_id", "cardinality": "N:1"}
        ],
        "fields": {
            "action_id": {"type": "VARCHAR(24)", "required": True, "unique": True, "allowed_values": "ACT-2026-000001", "validation_rule": "Format matches ^ACT-2026-\\d{6}$"},
            "recall_case_id": {"type": "VARCHAR(24)", "required": True, "unique": False, "allowed_values": "Valid RecallCase.recall_case_id", "validation_rule": "FK integrity to RecallCase"},
            "action_type": {"type": "VARCHAR(32)", "required": True, "unique": False, "allowed_values": ["NOTIFICATION_DISPATCH", "WAREHOUSE_QUARANTINE", "CARRIER_HOLD", "CUSTOMER_RECALL_NOTICE", "PRODUCT_RETRIEVAL", "DESTRUCTION_VERIFICATION"], "validation_rule": "Valid RecallActionType enum"},
            "target_entity_type": {"type": "VARCHAR(24)", "required": True, "unique": False, "allowed_values": ["SUPPLIER", "WAREHOUSE_LOT", "SHIPMENT", "CUSTOMER_DELIVERY"], "validation_rule": "Target system entity"},
            "target_entity_id": {"type": "VARCHAR(40)", "required": True, "unique": False, "allowed_values": "ID of target entity", "validation_rule": "Reference target ID"},
            "actor_role": {"type": "VARCHAR(32)", "required": True, "unique": False, "allowed_values": ["Supplier", "Planner", "Carrier/Warehouse Operator", "Logistics Analyst", "Operations Manager"], "validation_rule": "Must match one of 5 Primary Actors"},
            "target_qty": {"type": "DECIMAL(12,2)", "required": True, "unique": False, "allowed_values": ">= 0.0", "validation_rule": "Quantity affected by action"},
            "recovered_qty": {"type": "DECIMAL(12,2)", "required": True, "unique": False, "allowed_values": ">= 0.0", "validation_rule": "Quantity confirmed quarantined or returned"},
            "action_status": {"type": "VARCHAR(16)", "required": True, "unique": False, "allowed_values": ["PENDING", "IN_PROGRESS", "COMPLETED", "FAILED"], "validation_rule": "Valid ActionStatus enum"},
            "action_timestamp": {"type": "DATETIME", "required": True, "unique": False, "allowed_values": "ISO-8601 string", "validation_rule": "Timestamp >= recall_case initiation_date"},
            "notes": {"type": "VARCHAR(256)", "required": False, "unique": False, "allowed_values": "Text notes", "validation_rule": "Optional operator comment"}
        }
    }
}
