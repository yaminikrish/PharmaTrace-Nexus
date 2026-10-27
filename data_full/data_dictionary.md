# Master Data Dictionary & Schema Specification

Complete data dictionary for enterprise pharmaceutical & medical device lot traceability.

## Entity: `Supplier`
**Description**: Master record of external raw material and packaging vendors.  
**Primary Key**: `supplier_id`  
**Relationships**:
- Foreign Key: `None` -> `None` (Cardinality: 1:N to MaterialLot)

| Field Name | Type | Required | Unique | Allowed / Sample Values | Validation Rule |
|---|---|---|---|---|---|
| `supplier_id` | `VARCHAR(24)` | YES | YES | SUP-00001 to SUP-99999 | Format matches ^SUP-\d{5}$ |
| `name` | `VARCHAR(128)` | YES | NO | String | Non-empty string |
| `tier` | `VARCHAR(16)` | YES | NO | ['TIER_1', 'TIER_2', 'TIER_3'] | Must be valid SupplierTier enum |
| `country` | `VARCHAR(3)` | YES | NO | ISO-3166 alpha-3 (e.g. USA, CHE, DEU, JPN, GBR) | 3 uppercase letters |
| `contact_email` | `VARCHAR(128)` | YES | NO | Email address | Contains @ and valid domain |
| `status` | `VARCHAR(16)` | YES | NO | ['QUALIFIED', 'CONDITIONAL', 'SUSPENDED'] | Must be valid SupplierStatus enum |
| `created_at` | `DATETIME` | YES | NO | ISO-8601 string | Valid past timestamp |

## Entity: `Product`
**Description**: Master catalog of raw ingredients, intermediate materials, and finished goods.  
**Primary Key**: `product_id`  
**Relationships**:
- Foreign Key: `None` -> `None` (Cardinality: 1:N to MaterialLot, 1:N to BOM, 1:N to FinishedLot)

| Field Name | Type | Required | Unique | Allowed / Sample Values | Validation Rule |
|---|---|---|---|---|---|
| `product_id` | `VARCHAR(24)` | YES | YES | PRD-RAW-0001.. or PRD-FIN-0001.. | Format matches ^PRD-(RAW\|FIN)-\d{4}$ |
| `sku` | `VARCHAR(32)` | YES | YES | SKU identifier | Alphanumeric string |
| `name` | `VARCHAR(128)` | YES | NO | String | Product commercial name |
| `category` | `VARCHAR(20)` | YES | NO | ['RAW_MATERIAL', 'INTERMEDIATE', 'FINISHED_GOOD'] | Valid ProductCategory enum |
| `unit_of_measure` | `VARCHAR(10)` | YES | NO | ['KG', 'LITER', 'UNIT', 'VIAL', 'BOX'] | Standard metric/packaging unit |
| `shelf_life_days` | `INTEGER` | YES | NO | 30 to 1825 | Positive integer in days |
| `created_at` | `DATETIME` | YES | NO | ISO-8601 string | Valid timestamp |

## Entity: `BOM`
**Description**: Bill of Materials specification defining recipe required to produce a finished product.  
**Primary Key**: `bom_id`  
**Relationships**:
- Foreign Key: `finished_product_id` -> `Product.product_id` (Cardinality: N:1)
- Foreign Key: `None` -> `None` (Cardinality: 1:N to BOMItem, 1:N to ProductionOrder)

| Field Name | Type | Required | Unique | Allowed / Sample Values | Validation Rule |
|---|---|---|---|---|---|
| `bom_id` | `VARCHAR(24)` | YES | YES | BOM-2026-0001.. | Format matches ^BOM-2026-\d{4}$ |
| `finished_product_id` | `VARCHAR(24)` | YES | NO | Valid Product.product_id with category=FINISHED_GOOD | FK integrity to Product |
| `version` | `VARCHAR(8)` | YES | NO | v1.0, v1.1, v2.0 | Version string |
| `effective_from` | `DATE` | YES | NO | YYYY-MM-DD | ISO-8601 date <= effective_to |
| `effective_to` | `DATE` | YES | NO | YYYY-MM-DD | ISO-8601 date >= effective_from |
| `status` | `VARCHAR(16)` | YES | NO | ['ACTIVE', 'SUPERSEDED', 'DRAFT'] | Lifecycle state |

## Entity: `BOMItem`
**Description**: Bill of Materials component items detailing quantity of raw material needed per finished unit.  
**Primary Key**: `bom_item_id`  
**Relationships**:
- Foreign Key: `bom_id` -> `BOM.bom_id` (Cardinality: N:1)
- Foreign Key: `raw_product_id` -> `Product.product_id` (Cardinality: N:1)

| Field Name | Type | Required | Unique | Allowed / Sample Values | Validation Rule |
|---|---|---|---|---|---|
| `bom_item_id` | `VARCHAR(28)` | YES | YES | BOMI-2026-000001.. | Format matches ^BOMI-2026-\d{6}$ |
| `bom_id` | `VARCHAR(24)` | YES | NO | Valid BOM.bom_id | FK integrity to BOM |
| `raw_product_id` | `VARCHAR(24)` | YES | NO | Valid Product.product_id with category=RAW_MATERIAL | FK integrity to Product |
| `quantity_per_unit` | `DECIMAL(10,4)` | YES | NO | 0.01 to 500.0 | Positive decimal number |

## Entity: `MaterialLot`
**Description**: Inbound raw material batches received from certified suppliers.  
**Primary Key**: `material_lot_id`  
**Relationships**:
- Foreign Key: `supplier_id` -> `Supplier.supplier_id` (Cardinality: N:1)
- Foreign Key: `product_id` -> `Product.product_id` (Cardinality: N:1)
- Foreign Key: `None` -> `None` (Cardinality: 1:N to ProductionOrderLotConsumption)

| Field Name | Type | Required | Unique | Allowed / Sample Values | Validation Rule |
|---|---|---|---|---|---|
| `material_lot_id` | `VARCHAR(40)` | YES | YES | RAWLOT-<supplier-id>-2026-000001 | Format matches ^RAWLOT-SUP-\d{5}-2026-\d{6}$ |
| `supplier_id` | `VARCHAR(24)` | YES | NO | Valid Supplier.supplier_id | FK integrity to Supplier |
| `product_id` | `VARCHAR(24)` | YES | NO | Valid Product.product_id (category=RAW_MATERIAL) | FK integrity to Product |
| `supplier_batch_no` | `VARCHAR(32)` | YES | NO | Vendor batch code | Alphanumeric string |
| `initial_qty` | `DECIMAL(12,2)` | YES | NO | 50.0 to 10000.0 | Positive decimal |
| `consumed_qty` | `DECIMAL(12,2)` | YES | NO | 0.0 to initial_qty | Must be <= initial_qty |
| `available_qty` | `DECIMAL(12,2)` | YES | NO | initial_qty - consumed_qty | Arithmetic reconciliation: initial_qty - consumed_qty |
| `unit` | `VARCHAR(10)` | YES | NO | ['KG', 'LITER', 'UNIT'] | Matches product unit |
| `received_date` | `DATE` | YES | NO | YYYY-MM-DD | Valid reception date |
| `expiry_date` | `DATE` | YES | NO | YYYY-MM-DD | Must be > received_date |
| `qc_status` | `VARCHAR(16)` | YES | NO | ['RELEASED', 'QUARANTINED', 'REJECTED', 'RECALLED'] | Valid LotQCStatus enum |
| `quarantine_status` | `BOOLEAN` | YES | NO | [True, False] | True if under active quarantine hold |

## Entity: `ProductionOrder`
**Description**: Manufacturing batch work orders transforming raw material lots into finished products.  
**Primary Key**: `production_order_id`  
**Relationships**:
- Foreign Key: `bom_id` -> `BOM.bom_id` (Cardinality: N:1)
- Foreign Key: `product_id` -> `Product.product_id` (Cardinality: N:1)
- Foreign Key: `None` -> `None` (Cardinality: 1:N to ProductionOrderLotConsumption, 1:N to FinishedLot)

| Field Name | Type | Required | Unique | Allowed / Sample Values | Validation Rule |
|---|---|---|---|---|---|
| `production_order_id` | `VARCHAR(24)` | YES | YES | WO-2026-000001 | Format matches ^WO-2026-\d{6}$ |
| `bom_id` | `VARCHAR(24)` | YES | NO | Valid BOM.bom_id | FK integrity to BOM |
| `product_id` | `VARCHAR(24)` | YES | NO | Valid Product.product_id | FK integrity to Product |
| `target_qty` | `DECIMAL(12,2)` | YES | NO | 50.0 to 5000.0 | Target planned quantity |
| `produced_qty` | `DECIMAL(12,2)` | YES | NO | target_qty * yield_factor (95%-102%) | Derived output mass |
| `start_date` | `DATETIME` | YES | NO | ISO-8601 string | Timestamp >= all consumed lots received_date |
| `completion_date` | `DATETIME` | YES | NO | ISO-8601 string | Timestamp >= start_date |
| `status` | `VARCHAR(16)` | YES | NO | ['PLANNED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED'] | Valid ProductionOrderStatus enum |
| `production_line` | `VARCHAR(16)` | YES | NO | ['LINE-A', 'LINE-B', 'LINE-C', 'LINE-D'] | Valid facility line |

## Entity: `ProductionOrderLotConsumption`
**Description**: Genealogy bridge record detailing exact raw material lots consumed into each production order.  
**Primary Key**: `consumption_id`  
**Relationships**:
- Foreign Key: `production_order_id` -> `ProductionOrder.production_order_id` (Cardinality: N:1)
- Foreign Key: `material_lot_id` -> `MaterialLot.material_lot_id` (Cardinality: N:1)

| Field Name | Type | Required | Unique | Allowed / Sample Values | Validation Rule |
|---|---|---|---|---|---|
| `consumption_id` | `VARCHAR(28)` | YES | YES | CON-2026-000001.. | Format matches ^CON-2026-\d{6}$ |
| `production_order_id` | `VARCHAR(24)` | YES | NO | Valid ProductionOrder.production_order_id | FK integrity to ProductionOrder |
| `material_lot_id` | `VARCHAR(40)` | YES | NO | Valid MaterialLot.material_lot_id | FK integrity to MaterialLot |
| `consumed_qty` | `DECIMAL(12,2)` | YES | NO | > 0.0 | Positive decimal quantity |
| `consumed_date` | `DATETIME` | YES | NO | ISO-8601 string | Between order start_date and completion_date |

## Entity: `Warehouse`
**Description**: Logistics and manufacturing warehouse storage facilities holding lot inventories.  
**Primary Key**: `warehouse_id`  
**Relationships**:
- Foreign Key: `None` -> `None` (Cardinality: 1:N to FinishedLot, 1:N to Shipment, 1:N to InventoryMovement)

| Field Name | Type | Required | Unique | Allowed / Sample Values | Validation Rule |
|---|---|---|---|---|---|
| `warehouse_id` | `VARCHAR(24)` | YES | YES | WH-0001 to WH-9999 | Format matches ^WH-\d{4}$ |
| `name` | `VARCHAR(128)` | YES | NO | Warehouse name | Non-empty string |
| `location` | `VARCHAR(64)` | YES | NO | City / Metro area | Non-empty string |
| `country` | `VARCHAR(3)` | YES | NO | ISO-3166 alpha-3 | 3 uppercase letters |
| `facility_type` | `VARCHAR(32)` | YES | NO | ['DISTRIBUTION_CENTER', 'MANUFACTURING_WAREHOUSE', 'CENTRAL_DEPOT'] | Valid facility type |
| `status` | `VARCHAR(16)` | YES | NO | ['ACTIVE', 'INACTIVE'] | Status string |

## Entity: `FinishedLot`
**Description**: Finished product lots produced from manufacturing work orders.  
**Primary Key**: `finished_lot_id`  
**Relationships**:
- Foreign Key: `production_order_id` -> `ProductionOrder.production_order_id` (Cardinality: N:1)
- Foreign Key: `product_id` -> `Product.product_id` (Cardinality: N:1)
- Foreign Key: `warehouse_id` -> `Warehouse.warehouse_id` (Cardinality: N:1)
- Foreign Key: `None` -> `None` (Cardinality: 1:N to Delivery, 1:N to InventoryMovement)

| Field Name | Type | Required | Unique | Allowed / Sample Values | Validation Rule |
|---|---|---|---|---|---|
| `finished_lot_id` | `VARCHAR(28)` | YES | YES | FINLOT-2026-000001 | Format matches ^FINLOT-2026-\d{6}$ |
| `production_order_id` | `VARCHAR(24)` | YES | NO | Valid ProductionOrder.production_order_id | FK integrity to ProductionOrder |
| `product_id` | `VARCHAR(24)` | YES | NO | Valid Product.product_id | Matches production order product_id |
| `warehouse_id` | `VARCHAR(24)` | YES | NO | Valid Warehouse.warehouse_id | FK integrity to Warehouse |
| `produced_qty` | `DECIMAL(12,2)` | YES | NO | Matches production order produced_qty | Mass balance check |
| `warehouse_qty` | `DECIMAL(12,2)` | YES | NO | produced_qty - shipped_qty | Derived: produced_qty - shipped_qty |
| `shipped_qty` | `DECIMAL(12,2)` | YES | NO | Sum of related delivery quantities | Derived: sum(Delivery.delivered_qty) |
| `quarantine_qty` | `DECIMAL(12,2)` | YES | NO | Quantity held in quarantine | 0.0 or warehouse_qty if quarantined |
| `manufacture_date` | `DATETIME` | YES | NO | ISO-8601 string | Matches work order completion_date |
| `expiry_date` | `DATE` | YES | NO | YYYY-MM-DD | manufacture_date + product.shelf_life_days |
| `status` | `VARCHAR(20)` | YES | NO | ['AVAILABLE', 'IN_TRANSIT', 'DELIVERED', 'QUARANTINED', 'RECALLED', 'SCRAPPED'] | Valid FinishedLotStatus enum |

## Entity: `InventoryMovement`
**Description**: Immutable ledger of finished lot inventory transitions between available, quarantined, shipped, and recovered states across warehouses.  
**Primary Key**: `movement_id`  
**Relationships**:
- Foreign Key: `finished_lot_id` -> `FinishedLot.finished_lot_id` (Cardinality: N:1)
- Foreign Key: `warehouse_id` -> `Warehouse.warehouse_id` (Cardinality: N:1)

| Field Name | Type | Required | Unique | Allowed / Sample Values | Validation Rule |
|---|---|---|---|---|---|
| `movement_id` | `VARCHAR(28)` | YES | YES | MOV-2026-000001.. | Format matches ^MOV-2026-\d{6}$ |
| `finished_lot_id` | `VARCHAR(28)` | YES | NO | Valid FinishedLot.finished_lot_id | FK integrity to FinishedLot |
| `warehouse_id` | `VARCHAR(24)` | YES | NO | Valid Warehouse.warehouse_id | FK integrity to Warehouse |
| `movement_type` | `VARCHAR(32)` | YES | NO | ['PRODUCTION_RECEIPT', 'SHIPMENT_DISPATCH', 'QUARANTINE_HOLD', 'RECALL_RECOVERY'] | Valid movement type |
| `quantity` | `DECIMAL(12,2)` | YES | NO | > 0.0 | Quantity transferred |
| `source_status` | `VARCHAR(20)` | YES | NO | ['IN_PRODUCTION', 'AVAILABLE', 'SHIPPED', 'QUARANTINED', 'RECALLED'] | Origin inventory status |
| `target_status` | `VARCHAR(20)` | YES | NO | ['AVAILABLE', 'SHIPPED', 'QUARANTINED', 'RECOVERED'] | Target inventory status |
| `reference_id` | `VARCHAR(32)` | YES | NO | Reference transaction ID (WO, SHP, REC, ACT) | Transaction reference |
| `timestamp` | `DATETIME` | YES | NO | ISO-8601 string | Valid timestamp |

## Entity: `Shipment`
**Description**: Logistics transit records moving finished lots from warehouse to customer facilities.  
**Primary Key**: `shipment_id`  
**Relationships**:
- Foreign Key: `origin_warehouse` -> `Warehouse.warehouse_id` (Cardinality: N:1)
- Foreign Key: `None` -> `None` (Cardinality: 1:N to Delivery)

| Field Name | Type | Required | Unique | Allowed / Sample Values | Validation Rule |
|---|---|---|---|---|---|
| `shipment_id` | `VARCHAR(24)` | YES | YES | SHP-2026-000001 | Format matches ^SHP-2026-\d{6}$ |
| `origin_warehouse` | `VARCHAR(32)` | YES | NO | Valid Warehouse.warehouse_id | FK to Warehouse |
| `carrier_name` | `VARCHAR(64)` | YES | NO | ['DHL Supply Chain', 'FedEx Freight', 'UPS Supply Chain', 'Kuehne+Nagel', 'Maersk Logistics'] | Approved carrier |
| `tracking_number` | `VARCHAR(32)` | YES | YES | Carrier tracking identifier | Alphanumeric string |
| `ship_date` | `DATETIME` | YES | NO | ISO-8601 string | Timestamp >= lot manufacture_date |
| `est_arrival_date` | `DATETIME` | YES | NO | ISO-8601 string | ship_date + 1 to 5 days |
| `actual_arrival_date` | `DATETIME` | NO | NO | ISO-8601 string or NULL | Actual arrival date |
| `status` | `VARCHAR(16)` | YES | NO | ['PREPARING', 'DISPATCHED', 'IN_TRANSIT', 'DELIVERED', 'INTERCEPTED'] | Valid ShipmentStatus enum |

## Entity: `Customer`
**Description**: Recipient healthcare organizations, hospital networks, pharmacy chains, and distributors.  
**Primary Key**: `customer_id`  
**Relationships**:
- Foreign Key: `None` -> `None` (Cardinality: 1:N to Delivery)

| Field Name | Type | Required | Unique | Allowed / Sample Values | Validation Rule |
|---|---|---|---|---|---|
| `customer_id` | `VARCHAR(24)` | YES | YES | CUST-00001 to CUST-99999 | Format matches ^CUST-\d{5}$ |
| `name` | `VARCHAR(128)` | YES | NO | Commercial customer name | Non-empty string |
| `type` | `VARCHAR(24)` | YES | NO | ['HOSPITAL', 'PHARMACY_CHAIN', 'REGIONAL_DISTRIBUTOR', 'CLINICAL_CENTER'] | Valid CustomerType enum |
| `region` | `VARCHAR(16)` | YES | NO | ['NA_EAST', 'NA_WEST', 'NA_CENTRAL', 'EU_WEST', 'EU_CENTRAL', 'APAC'] | Geographic sales region |
| `contact_email` | `VARCHAR(128)` | YES | NO | Email address | Valid email format |
| `phone` | `VARCHAR(24)` | YES | NO | E.164 phone string | International phone format |
| `compliance_tier` | `VARCHAR(10)` | YES | NO | ['GOLD', 'SILVER', 'STANDARD'] | SLA compliance level |

## Entity: `Delivery`
**Description**: Customer delivery line item detailing received quantities of finished product lots.  
**Primary Key**: `delivery_id`  
**Relationships**:
- Foreign Key: `shipment_id` -> `Shipment.shipment_id` (Cardinality: N:1)
- Foreign Key: `customer_id` -> `Customer.customer_id` (Cardinality: N:1)
- Foreign Key: `finished_lot_id` -> `FinishedLot.finished_lot_id` (Cardinality: N:1)

| Field Name | Type | Required | Unique | Allowed / Sample Values | Validation Rule |
|---|---|---|---|---|---|
| `delivery_id` | `VARCHAR(28)` | YES | YES | DEL-2026-000001 | Format matches ^DEL-2026-\d{6}$ |
| `shipment_id` | `VARCHAR(24)` | YES | NO | Valid Shipment.shipment_id | FK integrity to Shipment |
| `customer_id` | `VARCHAR(24)` | YES | NO | Valid Customer.customer_id | FK integrity to Customer |
| `finished_lot_id` | `VARCHAR(28)` | YES | NO | Valid FinishedLot.finished_lot_id | FK integrity to FinishedLot |
| `delivered_qty` | `DECIMAL(12,2)` | YES | NO | Positive decimal quantity | Sum of lot deliveries <= lot produced_qty |
| `delivery_date` | `DATETIME` | YES | NO | ISO-8601 string | delivery_date >= shipment.ship_date |
| `customer_ack_status` | `VARCHAR(16)` | YES | NO | ['CONFIRMED', 'PENDING_INSPECTION', 'DISPUTED'] | Customer acknowledgment |
| `status` | `VARCHAR(16)` | YES | NO | ['IN_TRANSIT', 'RECEIVED', 'ACCEPTED', 'REJECTED', 'RECALLED'] | Valid DeliveryStatus enum |

## Entity: `RecallCase`
**Description**: Formal recall incident record tracking trigger, blast radius, actions, and regulatory closure.  
**Primary Key**: `recall_case_id`  
**Relationships**:
- Foreign Key: `None` -> `None` (Cardinality: 1:N to RecallAction)

| Field Name | Type | Required | Unique | Allowed / Sample Values | Validation Rule |
|---|---|---|---|---|---|
| `recall_case_id` | `VARCHAR(24)` | YES | YES | REC-2026-000001 | Format matches ^REC-2026-\d{6}$ |
| `trigger_entity_type` | `VARCHAR(16)` | YES | NO | ['RAW_LOT', 'FINISHED_LOT'] | Entity type that triggered recall |
| `trigger_entity_id` | `VARCHAR(40)` | YES | NO | Valid MaterialLot or FinishedLot ID | Valid entity key |
| `hazard_classification` | `VARCHAR(16)` | YES | NO | ['CLASS_I', 'CLASS_II', 'CLASS_III'] | FDA/EMA hazard tier |
| `root_cause` | `VARCHAR(256)` | YES | NO | Description of root cause | Documented root cause |
| `initiation_date` | `DATETIME` | YES | NO | ISO-8601 string | Incident trigger timestamp |
| `closure_target_date` | `DATE` | YES | NO | YYYY-MM-DD | initiation_date + 30 to 90 days |
| `status` | `VARCHAR(24)` | YES | NO | ['INITIATED', 'SCOPE_DETERMINED', 'NOTIFICATIONS_SENT', 'QUARANTINE_IN_EFFECT', 'RECOVERY_ACTIVE', 'RECONCILED', 'CLOSED'] | Valid RecallStatus enum |
| `affected_raw_lots_count` | `INTEGER` | YES | NO | >= 0 | Count of traced raw lots |
| `affected_finished_lots_count` | `INTEGER` | YES | NO | >= 0 | Count of traced finished lots |
| `total_affected_qty` | `DECIMAL(12,2)` | YES | NO | >= 0.0 | Sum of affected units across finished lots |
| `total_recovered_qty` | `DECIMAL(12,2)` | YES | NO | 0.0 to total_affected_qty | Derived recovered quantity |
| `containment_rate_pct` | `DECIMAL(5,2)` | YES | NO | 0.00 to 100.00 | Derived: (total_recovered_qty / total_affected_qty) * 100 |

## Entity: `RecallAction`
**Description**: Immutable lifecycle action log capturing containment notices, quarantine locks, and physical retrievals.  
**Primary Key**: `action_id`  
**Relationships**:
- Foreign Key: `recall_case_id` -> `RecallCase.recall_case_id` (Cardinality: N:1)

| Field Name | Type | Required | Unique | Allowed / Sample Values | Validation Rule |
|---|---|---|---|---|---|
| `action_id` | `VARCHAR(24)` | YES | YES | ACT-2026-000001 | Format matches ^ACT-2026-\d{6}$ |
| `recall_case_id` | `VARCHAR(24)` | YES | NO | Valid RecallCase.recall_case_id | FK integrity to RecallCase |
| `action_type` | `VARCHAR(32)` | YES | NO | ['NOTIFICATION_DISPATCH', 'WAREHOUSE_QUARANTINE', 'CARRIER_HOLD', 'CUSTOMER_RECALL_NOTICE', 'PRODUCT_RETRIEVAL', 'DESTRUCTION_VERIFICATION'] | Valid RecallActionType enum |
| `target_entity_type` | `VARCHAR(24)` | YES | NO | ['SUPPLIER', 'WAREHOUSE_LOT', 'SHIPMENT', 'CUSTOMER_DELIVERY'] | Target system entity |
| `target_entity_id` | `VARCHAR(40)` | YES | NO | ID of target entity | Reference target ID |
| `actor_role` | `VARCHAR(32)` | YES | NO | ['Supplier', 'Planner', 'Carrier/Warehouse Operator', 'Logistics Analyst', 'Operations Manager'] | Must match one of 5 Primary Actors |
| `target_qty` | `DECIMAL(12,2)` | YES | NO | >= 0.0 | Quantity affected by action |
| `recovered_qty` | `DECIMAL(12,2)` | YES | NO | >= 0.0 | Quantity confirmed quarantined or returned |
| `action_status` | `VARCHAR(16)` | YES | NO | ['PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED'] | Valid ActionStatus enum |
| `action_timestamp` | `DATETIME` | YES | NO | ISO-8601 string | Timestamp >= recall_case initiation_date |
| `notes` | `VARCHAR(256)` | NO | NO | Text notes | Optional operator comment |
