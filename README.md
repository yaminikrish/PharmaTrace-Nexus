# PharmaTrace Nexus — Multi-Tier Lot Traceability & Recall Simulation Suite

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/Status-Traceability%20%26%20Recall%20Simulation%20Prototype-blue.svg)]()
[![Seed](https://img.shields.io/badge/Reproducibility-Seed%2020261022%20(Bitwise%20Identical)-blueviolet.svg)]()
[![F1-Score](https://img.shields.io/badge/Audit%20F1--Score-1.000-success.svg)]()

> **Pharmaceutical traceability and recall simulation prototype for tracing affected lots through suppliers, production orders, warehouses, and customer deliveries, then simulating recall blast radius, quarantine containment, and recovery velocity.**

---

## 1. Executive Summary & System Scope

In life science supply chain modeling and incident response training, identifying contaminated lots and simulating containment strategies is critical. **PharmaTrace Nexus** is an enterprise pharmaceutical traceability and recall simulation prototype designed to model and evaluate multi-tier supply chain lineage and recall responses (simulating cGMP and FDA 21 CFR Part 7 workflows):
- Maintains strict bidirectional multi-tier genealogy (from Tier-1/2/3 chemical suppliers & raw material lots, through BOM consumption, work orders, finished good lots, warehouse inventory holds, transit shipments, to hospital/pharmacy deliveries).
- Simulates Class I, Class II, and Class III recall incidents with real-time blast radius mapping, warehouse quarantine hold locks, customer notification dispatch, and 14-day recovery velocity tracking.
- Implements an automated anomaly auditor benchmarked against an isolated, uncorrupted ground-truth dataset (`ground_truth.json`), achieving **100.0% Precision**, **100.0% Recall**, and an **F1-Score of 1.000** through exact incident matching (verifying issue type, affected entity ID, and violating values).
- Guarantees 100% deterministic bitwise reproducibility under fixed seed `20261022`, verified via dual-run SHA-256 cryptographic checksum matching across all tables.

---

## 2. Core Entities & Relational Architecture

The system models **15 normalized entities and bridge tables**, adhering to strict primary key constraints, foreign key referential integrity, and domain lifecycles:

```
[Supplier] ──1:N──> [MaterialLot] ──N:1──> [Product (Raw)]
   │                     │
   │                     └──N:M──> [ProductionOrderLotConsumption]
   │                                           │
   │                                           ▼
[Product (Finished)] <──N:1── [BOM] ──1:N──> [ProductionOrder]
   ▲                                           │
   │                                           ▼ (1:N)
   └───────────────────────────── [FinishedLot] <──N:1── [Warehouse]
                                        │                      │
                                        ├──1:N──> [InventoryMovement]
                                        │                      │
                                        └──1:N──> [Delivery] ──N:1──> [Shipment]
                                                     │
                                                     └──N:1──> [Customer]
[RecallCase] ──1:N──> [RecallAction] (Immutable Event Dispatch Log)
```

### Relational Entities Summary Table

| Entity | Primary Key | Foreign Keys / Bridges | Cardinality | Key Business Lifecycle States |
|---|---|---|---|---|
| **Supplier** | `supplier_id` | None | `1:N` to MaterialLot | `QUALIFIED`, `CONDITIONAL`, `SUSPENDED` |
| **Product** | `product_id` | None | `1:N` to MaterialLot/FinishedLot | `RAW_MATERIAL`, `INTERMEDIATE`, `FINISHED_GOOD` |
| **BOM** | `bom_id` | `finished_product_id` &rarr; `Product` | `1:N` to BOMItem, `1:N` to ProductionOrder | `ACTIVE`, `SUPERSEDED`, `DRAFT` |
| **BOMItem** | `bom_item_id` | `bom_id` &rarr; `BOM`, `raw_product_id` &rarr; `Product` | `N:1` to BOM, `N:1` to Product | Component ingredient ratio per unit |
| **Warehouse** | `warehouse_id` | None | `1:N` to FinishedLot, `1:N` to Shipment, `1:N` to InventoryMovement | `ACTIVE`, `INACTIVE` |
| **MaterialLot** | `material_lot_id` | `supplier_id`, `product_id` | `1:N` to Consumption | `RELEASED`, `QUARANTINED`, `REJECTED`, `RECALLED` |
| **ProductionOrder** | `production_order_id` | `bom_id`, `product_id` | `1:N` to Consumption, `1:N` to FinishedLot | `PLANNED`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED` |
| **ProductionOrderLotConsumption** | `consumption_id` | `production_order_id`, `material_lot_id` | Bridge (`N:M` raw lots to work orders) | Immutable genealogy consumption event |
| **FinishedLot** | `finished_lot_id` | `production_order_id`, `product_id`, `warehouse_id` | `N:1` to ProductionOrder, `1:N` to Delivery, `1:N` to InventoryMovement | `AVAILABLE`, `IN_TRANSIT`, `DELIVERED`, `QUARANTINED`, `RECALLED` |
| **InventoryMovement** | `movement_id` | `finished_lot_id`, `warehouse_id` | `N:1` to FinishedLot, `N:1` to Warehouse | Stock movements (`PRODUCTION_RECEIPT`, `SHIPMENT_DISPATCH`, etc.) |
| **Shipment** | `shipment_id` | `origin_warehouse` &rarr; `Warehouse` | `1:N` to Delivery | `PREPARING`, `DISPATCHED`, `IN_TRANSIT`, `DELIVERED`, `INTERCEPTED` |
| **Customer** | `customer_id` | None | `1:N` to Delivery | `HOSPITAL`, `PHARMACY_CHAIN`, `REGIONAL_DISTRIBUTOR` |
| **Delivery** | `delivery_id` | `shipment_id`, `customer_id`, `finished_lot_id` | `N:1` to Shipment, FinishedLot, Customer | `IN_TRANSIT`, `RECEIVED`, `ACCEPTED`, `REJECTED`, `RECALLED` |
| **RecallCase** | `recall_case_id` | Trigger Entity ID | `1:N` to RecallAction | `INITIATED`, `SCOPE_DETERMINED`, `QUARANTINE_IN_EFFECT`, `RECONCILED` |
| **RecallAction** | `action_id` | `recall_case_id` &rarr; `RecallCase` | Immutable audit action log | `PENDING`, `IN_PROGRESS`, `COMPLETED`, `FAILED` |

---

## 3. Deterministic ID Nomenclature

All synthetic identifiers follow strict, zero-padded, immutable enterprise conventions:
- **Warehouse**: `WH-0001`
- **Raw Material Lot**: `RAWLOT-<supplier-id>-2026-000001` (e.g. `RAWLOT-SUP-00018-2026-000001`)
- **Work Order**: `WO-2026-000001`
- **Finished Lot**: `FINLOT-2026-000001`
- **Inventory Movement**: `MOV-2026-000001`
- **Shipment**: `SHP-2026-000001`
- **Customer Delivery**: `DEL-2026-000001`
- **Recall Case**: `REC-2026-000001`
- **Recall Action**: `ACT-2026-000001`

---

## 4. Planted Negative Edge Cases & Isolated Ground Truth

To thoroughly test audit resilience and exception handling, 4 deliberate negative edge cases were planted with zero leakage into the input feature files. The ground truth is stored isolated in [`data/ground_truth.json`](file:///c:/Users/ASSIMILATE/Desktop/task/data/ground_truth.json):

```json
[
  {
    "issue_type": "MISSING_INPUT_LOT",
    "entity_type": "ProductionOrderLotConsumption",
    "entity_id": "CON-2026-999999",
    "parent_id": "WO-2026-000001",
    "violating_value": "RAWLOT-SUP-99999-2026-999999",
    "expected_condition": "Referenced material_lot_id must exist in MaterialLot master table",
    "severity": "CRITICAL"
  },
  {
    "issue_type": "DELIVERED_EXCEEDS_PRODUCED",
    "entity_type": "Delivery",
    "entity_id": "DEL-2026-000122",
    "parent_id": "FINLOT-2026-000002",
    "violating_value": "1137.11",
    "expected_condition": "Delivered quantity must be <= produced quantity (758.07)",
    "severity": "HIGH"
  },
  {
    "issue_type": "RECALL_MISSED_CUSTOMER",
    "entity_type": "RecallCase",
    "entity_id": "REC-2026-000002",
    "parent_id": "DEL-2026-000186",
    "violating_value": "CUST-00068",
    "expected_condition": "Customer received recalled lot but received no notification dispatch action",
    "severity": "CRITICAL"
  },
  {
    "issue_type": "RECALLED_INVENTORY_AVAILABLE",
    "entity_type": "FinishedLot",
    "entity_id": "FINLOT-2026-000003",
    "parent_id": "REC-2026-BREACH-01",
    "violating_value": "status=AVAILABLE, warehouse_qty=500.0, quarantine_qty=0.0",
    "expected_condition": "Recalled finished lot inventory must have status=RECALLED/QUARANTINED and warehouse_qty quarantined",
    "severity": "CRITICAL"
  }
]
```

### Anomaly Auditor Benchmark Results (Exact Incident Verification)
The audit service evaluates detected anomalies using exact matching across:
1. `issue_type` (category)
2. `entity_id` (exact affected record ID)
3. `violating_value` (violating quantity / status values)

- **Planted Anomalies**: `4`
- **Detected Anomalies**: `4`
- **False Positives**: `0`
- **False Negatives**: `0`
- **Precision**: `100.0%`
- **Recall**: `100.0%`
- **F1-Score**: `1.0000`

---

## 5. Step 10: Reproducibility Proof (Dual-Run Checksum Matching)

The system enforces 100% deterministic generation using a fixed seed (`20261022`). Running `reproducibility_test.py` generates the entire dataset twice into isolated directories and compares row counts and SHA-256 cryptographic hashes:

```
======================================================================
STEP 10 REPRODUCIBILITY TEST: Dual-Run Bitwise Verification (Seed=20261022)
======================================================================
Artifact File                       | Run 1 Rows | Run 2 Rows | Status    
----------------------------------------------------------------------
bom_items.csv                       | 44         | 44         | MATCH (IDENTICAL)
boms.csv                            | 15         | 15         | MATCH (IDENTICAL)
customers.csv                       | 80         | 80         | MATCH (IDENTICAL)
deliveries.csv                      | 500        | 500        | MATCH (IDENTICAL)
finished_lots.csv                   | 200        | 200        | MATCH (IDENTICAL)
inventory_movements.csv             | 771        | 771        | MATCH (IDENTICAL)
material_lots.csv                   | 300        | 300        | MATCH (IDENTICAL)
production_order_lot_consumptions.csv | 450        | 450        | MATCH (IDENTICAL)
production_orders.csv               | 150        | 150        | MATCH (IDENTICAL)
products.csv                        | 35         | 35         | MATCH (IDENTICAL)
recall_actions.csv                  | 88         | 88         | MATCH (IDENTICAL)
recall_cases.csv                    | 9          | 9          | MATCH (IDENTICAL)
shipments.csv                       | 120        | 120        | MATCH (IDENTICAL)
suppliers.csv                       | 50         | 50         | MATCH (IDENTICAL)
warehouses.csv                      | 5          | 5          | MATCH (IDENTICAL)
ground_truth.json                   | -          | -          | MATCH (IDENTICAL)
traceability.db                     | -          | -          | MATCH (IDENTICAL)
----------------------------------------------------------------------
[SUCCESS] 100% BITWISE REPRODUCIBILITY VERIFIED ACROSS BOTH RUNS!
======================================================================
```

---

## 6. Dataset Scale & Volume Coverage

The generator supports both a snappy starter scale and the full enterprise baseline volume:

| Entity / Dimension | Starter Scale (Fast / UI Demo) | Full Baseline Scale |
|---|---|---|
| **Suppliers** | 50 | **500** |
| **Raw Material Lots** | 300 | **10,000** |
| **BOMs & BOM Items** | 15 / 44 | **50 / 148** |
| **Production Orders (WOs)** | 150 | **5,000** |
| **Lot Consumptions** | 450 | **14,797** |
| **Finished Lots** | 200 | **8,000** |
| **Warehouses & Movements** | 5 / 771 | **5 / 28,141** |
| **Shipments & Deliveries** | 120 / 500 | **4,500 / 20,000** |
| **Customers** | 80 | **1,200** |
| **Recall Cases & Actions** | 9 / 88 | **31 / 198** |
| **Total Inspected Rows (15 Tables)** | **2,817 rows** | **92,720 rows** |
| **Generation Runtime** | < 1 second | ~14 seconds |

---

## 7. Command-Line Interface (CLI) Guide

### Quick Start: Run Entire Application With One Command

To execute the entire end-to-end pipeline (data validation, reproducibility verification, test suite, and launch the interactive web application):

```bash
python run.py
```
*(or via CLI: `python main.py run-all`)*

This single command will:
1. Verify / generate the required synthetic supply chain datasets.
2. Run the 8-step enterprise validation suite and calculate the ground truth anomaly benchmark (**F1 = 1.000**).
3. Execute the Step 10 dual-run checksum reproducibility test (**100% bitwise verified**).
4. Run the automated enterprise test suite (**5/5 tests OK**).
5. Launch the multi-threaded web application server and open **`http://localhost:8080`** in your browser.

---

### Individual Subcommands (`main.py`)

```bash
# Display help and available subcommands
python main.py --help

# Generate Starter Scale Dataset
python main.py generate --seed 20261022 --scale starter --output-dir data

# Generate Full Baseline Volume (500 suppliers, 10,000 raw lots, 5,000 WOs, 8,000 finished lots, 20,000 deliveries)
python main.py generate --seed 20261022 --scale full --output-dir data_full

# Run 8-Step Enterprise Validation Suite & Anomaly Benchmark
python main.py validate --data-dir data

# Execute Step 10 Dual-Run Checksum Reproducibility Verification
python main.py verify

# Launch Web Application Server & REST API
python main.py serve --port 8080
```

### 2. Run Enterprise Automated Test Suite

```bash
python -m unittest discover tests
```

---

## 8. Enterprise Layered Architecture & Directory Structure

The codebase is structured according to **Clean Architecture / Domain-Driven Design (DDD)** principles:

```
c:\Users\ASSIMILATE\Desktop\task\
├── pharmatrace/                        # Core Enterprise Python Package
│   ├── config.py                      # Strongly-typed configuration, settings & logging
│   ├── core/                          # Domain Layer (Zero external framework dependencies)
│   │   ├── enums.py                   # Domain enums (SupplierTier, LotQCStatus, RecallHazardClass, etc.)
│   │   ├── models.py                  # Domain entities & strongly-typed dataclasses
│   │   ├── exceptions.py              # Domain-specific custom exceptions
│   │   └── dictionary.py              # Master schema specification & validation rules
│   ├── services/                      # Application / Use Case Layer
│   │   ├── genealogy_service.py       # Multi-tier bidirectional DAG traversal service
│   │   ├── recall_service.py          # Recall blast radius, containment & timeline simulation
│   │   ├── audit_service.py           # 8-step validation suite & anomaly benchmarking
│   │   └── generator_service.py       # Deterministic synthetic data generator (starter & full scales)
│   ├── infrastructure/                # Infrastructure & External Adapters Layer
│   │   ├── database.py                # SQLite repository, schema initialization & indexing
│   │   ├── exporters.py               # Exporters for CSV, JSON, SQLite, Markdown & manifests
│   │   └── checksums.py               # SHA-256 verifiers & reproducibility dual-run executor
│   ├── api/                           # Interface / Presentation Layer
│   │   └── server.py                  # Multi-threaded ThreadingHTTPServer & REST API handlers
│   └── cli/                           # Command-Line Interface Layer
│       └── main.py                    # Unified CLI with generate, validate, verify, serve subcommands
├── tests/                             # Comprehensive Automated Unit & Integration Test Suite
│   ├── test_genealogy.py              # Tests bidirectional multi-tier traversal
│   ├── test_recall_simulation.py      # Tests blast radius and containment % calculation
│   ├── test_validation.py             # Tests 8-step validation suite & anomaly benchmark
│   └── test_reproducibility.py        # Tests Step 10 dual-run checksum determinism
├── data/                              # Generated starter scale dataset (2,817 rows across 15 tables)
├── data_full/                         # Generated full baseline dataset (92,720 rows across 15 tables)
├── frontend/                          # High-aesthetic dark glassmorphic web application
│   ├── index.html                     # HTML5 UI shell with 5 main views
│   ├── styles.css                     # Modern design system with micro-animations
│   └── app.js                         # DAG visualizer, timeline stepper, and actor portals
├── main.py                            # Root CLI entrypoint
├── server.py                          # Backwards-compatible server launcher
├── pyproject.toml                     # Enterprise package & build configuration
└── README.md                          # Comprehensive system documentation
```
