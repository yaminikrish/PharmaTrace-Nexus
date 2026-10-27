"""
Strongly-Typed Domain Entities and Data Transfer Objects (DTOs).
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from datetime import datetime
from pharmatrace.core.enums import (
    SupplierTier, SupplierStatus, ProductCategory, LotQCStatus,
    ProductionOrderStatus, FinishedLotStatus, ShipmentStatus,
    CustomerType, DeliveryStatus, RecallHazardClass, RecallStatus,
    RecallActionType, ActionStatus, EdgeCaseType
)

@dataclass
class Supplier:
    supplier_id: str
    name: str
    tier: str
    country: str
    contact_email: str
    status: str
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class Product:
    product_id: str
    sku: str
    name: str
    category: str
    unit_of_measure: str
    shelf_life_days: int
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class BOM:
    bom_id: str
    finished_product_id: str
    version: str
    effective_from: str
    effective_to: str
    status: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class BOMItem:
    bom_item_id: str
    bom_id: str
    raw_product_id: str
    quantity_per_unit: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class MaterialLot:
    material_lot_id: str
    supplier_id: str
    product_id: str
    supplier_batch_no: str
    initial_qty: float
    consumed_qty: float
    available_qty: float
    unit: str
    received_date: str
    expiry_date: str
    qc_status: str
    quarantine_status: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class ProductionOrder:
    production_order_id: str
    bom_id: str
    product_id: str
    target_qty: float
    produced_qty: float
    start_date: str
    completion_date: str
    status: str
    production_line: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class ProductionOrderLotConsumption:
    consumption_id: str
    production_order_id: str
    material_lot_id: str
    consumed_qty: float
    consumed_date: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class Warehouse:
    warehouse_id: str
    name: str
    location: str
    country: str
    facility_type: str
    status: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class FinishedLot:
    finished_lot_id: str
    production_order_id: str
    product_id: str
    warehouse_id: str
    produced_qty: float
    warehouse_qty: float
    shipped_qty: float
    quarantine_qty: float
    manufacture_date: str
    expiry_date: str
    status: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class InventoryMovement:
    movement_id: str
    finished_lot_id: str
    warehouse_id: str
    movement_type: str
    quantity: float
    source_status: str
    target_status: str
    reference_id: str
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class Shipment:
    shipment_id: str
    origin_warehouse: str
    carrier_name: str
    tracking_number: str
    ship_date: str
    est_arrival_date: str
    actual_arrival_date: Optional[str]
    status: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class Customer:
    customer_id: str
    name: str
    type: str
    region: str
    contact_email: str
    phone: str
    compliance_tier: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class Delivery:
    delivery_id: str
    shipment_id: str
    customer_id: str
    finished_lot_id: str
    delivered_qty: float
    delivery_date: str
    customer_ack_status: str
    status: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class RecallCase:
    recall_case_id: str
    trigger_entity_type: str
    trigger_entity_id: str
    hazard_classification: str
    root_cause: str
    initiation_date: str
    closure_target_date: str
    status: str
    affected_raw_lots_count: int
    affected_finished_lots_count: int
    total_affected_qty: float
    total_recovered_qty: float
    containment_rate_pct: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class RecallAction:
    action_id: str
    recall_case_id: str
    action_type: str
    target_entity_type: str
    target_entity_id: str
    actor_role: str
    target_qty: float
    recovered_qty: float
    action_status: str
    action_timestamp: str
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class GroundTruthAnomaly:
    issue_type: str
    entity_type: str
    entity_id: str
    parent_id: str
    violating_value: str
    expected_condition: str
    severity: str
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
