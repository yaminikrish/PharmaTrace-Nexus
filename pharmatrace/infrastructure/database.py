"""
Enterprise SQLite Database Repository.
Manages database connections, schema migrations, table creation, indexing,
and strongly-typed query execution.
"""

import os
import sqlite3
import logging
from typing import Dict, List, Any, Optional
from pharmatrace.config import settings

logger = logging.getLogger(__name__)

class DatabaseRepository:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.db_path

    def get_connection(self) -> sqlite3.Connection:
        """Returns a configured SQLite connection with row factories."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

TABLE_SCHEMAS: Dict[str, str] = {
    "suppliers": """
        CREATE TABLE IF NOT EXISTS suppliers (
            supplier_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            tier TEXT NOT NULL,
            country TEXT NOT NULL,
            contact_email TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
    """,
    "products": """
        CREATE TABLE IF NOT EXISTS products (
            product_id TEXT PRIMARY KEY,
            sku TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            unit_of_measure TEXT NOT NULL,
            shelf_life_days INTEGER NOT NULL,
            created_at TEXT NOT NULL
        );
    """,
    "boms": """
        CREATE TABLE IF NOT EXISTS boms (
            bom_id TEXT PRIMARY KEY,
            finished_product_id TEXT NOT NULL,
            version TEXT NOT NULL,
            effective_from TEXT NOT NULL,
            effective_to TEXT NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (finished_product_id) REFERENCES products(product_id)
        );
    """,
    "bom_items": """
        CREATE TABLE IF NOT EXISTS bom_items (
            bom_item_id TEXT PRIMARY KEY,
            bom_id TEXT NOT NULL,
            raw_product_id TEXT NOT NULL,
            quantity_per_unit REAL NOT NULL,
            FOREIGN KEY (bom_id) REFERENCES boms(bom_id),
            FOREIGN KEY (raw_product_id) REFERENCES products(product_id)
        );
    """,
    "warehouses": """
        CREATE TABLE IF NOT EXISTS warehouses (
            warehouse_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            location TEXT NOT NULL,
            country TEXT NOT NULL,
            facility_type TEXT NOT NULL,
            status TEXT NOT NULL
        );
    """,
    "material_lots": """
        CREATE TABLE IF NOT EXISTS material_lots (
            material_lot_id TEXT PRIMARY KEY,
            supplier_id TEXT NOT NULL,
            product_id TEXT NOT NULL,
            supplier_batch_no TEXT NOT NULL,
            initial_qty REAL NOT NULL,
            consumed_qty REAL NOT NULL,
            available_qty REAL NOT NULL,
            unit TEXT NOT NULL,
            received_date TEXT NOT NULL,
            expiry_date TEXT NOT NULL,
            qc_status TEXT NOT NULL,
            quarantine_status INTEGER NOT NULL,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        );
    """,
    "production_orders": """
        CREATE TABLE IF NOT EXISTS production_orders (
            production_order_id TEXT PRIMARY KEY,
            bom_id TEXT NOT NULL,
            product_id TEXT NOT NULL,
            target_qty REAL NOT NULL,
            produced_qty REAL NOT NULL,
            start_date TEXT NOT NULL,
            completion_date TEXT NOT NULL,
            status TEXT NOT NULL,
            production_line TEXT NOT NULL,
            FOREIGN KEY (bom_id) REFERENCES boms(bom_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        );
    """,
    "production_order_lot_consumptions": """
        CREATE TABLE IF NOT EXISTS production_order_lot_consumptions (
            consumption_id TEXT PRIMARY KEY,
            production_order_id TEXT NOT NULL,
            material_lot_id TEXT NOT NULL,
            consumed_qty REAL NOT NULL,
            consumed_date TEXT NOT NULL,
            FOREIGN KEY (production_order_id) REFERENCES production_orders(production_order_id),
            FOREIGN KEY (material_lot_id) REFERENCES material_lots(material_lot_id)
        );
    """,
    "finished_lots": """
        CREATE TABLE IF NOT EXISTS finished_lots (
            finished_lot_id TEXT PRIMARY KEY,
            production_order_id TEXT NOT NULL,
            product_id TEXT NOT NULL,
            warehouse_id TEXT NOT NULL,
            produced_qty REAL NOT NULL,
            warehouse_qty REAL NOT NULL,
            shipped_qty REAL NOT NULL,
            quarantine_qty REAL NOT NULL,
            manufacture_date TEXT NOT NULL,
            expiry_date TEXT NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (production_order_id) REFERENCES production_orders(production_order_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id),
            FOREIGN KEY (warehouse_id) REFERENCES warehouses(warehouse_id)
        );
    """,
    "customers": """
        CREATE TABLE IF NOT EXISTS customers (
            customer_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            region TEXT NOT NULL,
            contact_email TEXT NOT NULL,
            phone TEXT NOT NULL,
            compliance_tier TEXT NOT NULL
        );
    """,
    "shipments": """
        CREATE TABLE IF NOT EXISTS shipments (
            shipment_id TEXT PRIMARY KEY,
            origin_warehouse TEXT NOT NULL,
            carrier_name TEXT NOT NULL,
            tracking_number TEXT NOT NULL,
            ship_date TEXT NOT NULL,
            est_arrival_date TEXT NOT NULL,
            actual_arrival_date TEXT,
            status TEXT NOT NULL,
            FOREIGN KEY (origin_warehouse) REFERENCES warehouses(warehouse_id)
        );
    """,
    "deliveries": """
        CREATE TABLE IF NOT EXISTS deliveries (
            delivery_id TEXT PRIMARY KEY,
            shipment_id TEXT NOT NULL,
            customer_id TEXT NOT NULL,
            finished_lot_id TEXT NOT NULL,
            delivered_qty REAL NOT NULL,
            delivery_date TEXT NOT NULL,
            customer_ack_status TEXT NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (shipment_id) REFERENCES shipments(shipment_id),
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
            FOREIGN KEY (finished_lot_id) REFERENCES finished_lots(finished_lot_id)
        );
    """,
    "recall_cases": """
        CREATE TABLE IF NOT EXISTS recall_cases (
            recall_case_id TEXT PRIMARY KEY,
            trigger_entity_type TEXT NOT NULL,
            trigger_entity_id TEXT NOT NULL,
            hazard_classification TEXT NOT NULL,
            root_cause TEXT NOT NULL,
            initiation_date TEXT NOT NULL,
            closure_target_date TEXT NOT NULL,
            status TEXT NOT NULL,
            affected_raw_lots_count INTEGER NOT NULL,
            affected_finished_lots_count INTEGER NOT NULL,
            total_affected_qty REAL NOT NULL,
            total_recovered_qty REAL NOT NULL,
            containment_rate_pct REAL NOT NULL
        );
    """,
    "recall_actions": """
        CREATE TABLE IF NOT EXISTS recall_actions (
            action_id TEXT PRIMARY KEY,
            recall_case_id TEXT NOT NULL,
            action_type TEXT NOT NULL,
            target_entity_type TEXT NOT NULL,
            target_entity_id TEXT NOT NULL,
            actor_role TEXT NOT NULL,
            target_qty REAL NOT NULL,
            recovered_qty REAL NOT NULL,
            action_status TEXT NOT NULL,
            action_timestamp TEXT NOT NULL,
            notes TEXT,
            FOREIGN KEY (recall_case_id) REFERENCES recall_cases(recall_case_id)
        );
    """,
    "inventory_movements": """
        CREATE TABLE IF NOT EXISTS inventory_movements (
            movement_id TEXT PRIMARY KEY,
            finished_lot_id TEXT NOT NULL,
            warehouse_id TEXT NOT NULL,
            movement_type TEXT NOT NULL,
            quantity REAL NOT NULL,
            source_status TEXT NOT NULL,
            target_status TEXT NOT NULL,
            reference_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (finished_lot_id) REFERENCES finished_lots(finished_lot_id),
            FOREIGN KEY (warehouse_id) REFERENCES warehouses(warehouse_id)
        );
    """
}

class DatabaseRepository:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.db_path

    def get_connection(self) -> sqlite3.Connection:
        """Returns a configured SQLite connection with row factories."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize_schema_and_indices(self, datasets: Dict[str, List[Dict[str, Any]]]):
        """Creates strongly-typed relational tables with foreign keys and performance indices."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        # Disable foreign keys during initial load to allow intentional planted edge cases
        cur.execute("PRAGMA foreign_keys = OFF;")

        # Create explicit tables
        for table_name, create_sql in TABLE_SCHEMAS.items():
            cur.execute(create_sql)

        # Insert data
        for table_name, rows in datasets.items():
            if not rows:
                continue
            cols = list(rows[0].keys())
            placeholders = ", ".join(["?"] * len(cols))
            insert_sql = f"INSERT INTO {table_name} ({', '.join(cols)}) VALUES ({placeholders})"
            
            data_tuples = []
            for r in rows:
                row_tuple = []
                for c in cols:
                    val = r.get(c)
                    if isinstance(val, bool):
                        row_tuple.append(1 if val else 0)
                    else:
                        row_tuple.append(val)
                data_tuples.append(tuple(row_tuple))

            cur.executemany(insert_sql, data_tuples)

        # Performance indices
        indices = [
            "CREATE INDEX IF NOT EXISTS idx_matlot_prod ON material_lots(product_id);",
            "CREATE INDEX IF NOT EXISTS idx_matlot_supp ON material_lots(supplier_id);",
            "CREATE INDEX IF NOT EXISTS idx_bom_prod ON boms(finished_product_id);",
            "CREATE INDEX IF NOT EXISTS idx_bomi_bom ON bom_items(bom_id);",
            "CREATE INDEX IF NOT EXISTS idx_bomi_prod ON bom_items(raw_product_id);",
            "CREATE INDEX IF NOT EXISTS idx_po_bom ON production_orders(bom_id);",
            "CREATE INDEX IF NOT EXISTS idx_po_prod ON production_orders(product_id);",
            "CREATE INDEX IF NOT EXISTS idx_con_po ON production_order_lot_consumptions(production_order_id);",
            "CREATE INDEX IF NOT EXISTS idx_con_lot ON production_order_lot_consumptions(material_lot_id);",
            "CREATE INDEX IF NOT EXISTS idx_finlot_po ON finished_lots(production_order_id);",
            "CREATE INDEX IF NOT EXISTS idx_finlot_wh ON finished_lots(warehouse_id);",
            "CREATE INDEX IF NOT EXISTS idx_shp_wh ON shipments(origin_warehouse);",
            "CREATE INDEX IF NOT EXISTS idx_deliv_finlot ON deliveries(finished_lot_id);",
            "CREATE INDEX IF NOT EXISTS idx_deliv_cust ON deliveries(customer_id);",
            "CREATE INDEX IF NOT EXISTS idx_deliv_shp ON deliveries(shipment_id);",
            "CREATE INDEX IF NOT EXISTS idx_rec_act ON recall_actions(recall_case_id);",
            "CREATE INDEX IF NOT EXISTS idx_inv_lot ON inventory_movements(finished_lot_id);",
            "CREATE INDEX IF NOT EXISTS idx_inv_wh ON inventory_movements(warehouse_id);"
        ]
        for idx_sql in indices:
            try:
                cur.execute(idx_sql)
            except sqlite3.OperationalError:
                pass

        conn.commit()
        conn.close()
        logger.info(f"Explicit database schema and indices initialized successfully at '{self.db_path}'")


    def fetch_all(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute(query, params)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute(query, params)
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None
