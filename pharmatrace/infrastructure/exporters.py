"""
Enterprise Data Exporters.
Exports datasets to CSV, JSON, SQLite, and formatted Markdown specifications,
and generates cryptographic source manifests.
"""

import os
import csv
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Any
from pharmatrace.core.dictionary import DATA_DICTIONARY
from pharmatrace.infrastructure.database import DatabaseRepository

class DataExporter:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.csv_dir = os.path.join(output_dir, "csv")
        self.json_dir = os.path.join(output_dir, "json")
        self.db_path = os.path.join(output_dir, "traceability.db")

    def export_all(self, datasets: Dict[str, List[Dict[str, Any]]], ground_truth: List[Dict[str, Any]], seed: int, scale: str) -> Dict[str, Any]:
        os.makedirs(self.csv_dir, exist_ok=True)
        os.makedirs(self.json_dir, exist_ok=True)

        # 1. Export Ground Truth strictly isolated
        gt_json_path = os.path.join(self.output_dir, "ground_truth.json")
        gt_csv_path = os.path.join(self.output_dir, "ground_truth.csv")
        
        with open(gt_json_path, "w", encoding="utf-8") as f:
            json.dump(ground_truth, f, indent=2)

        if ground_truth:
            with open(gt_csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(ground_truth[0].keys()))
                writer.writeheader()
                writer.writerows(ground_truth)

        # 2. Export Relational Tables (CSV & JSON)
        manifest = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "seed": seed,
            "scale": scale,
            "tables": {}
        }

        for table_name, rows in datasets.items():
            csv_path = os.path.join(self.csv_dir, f"{table_name}.csv")
            json_path = os.path.join(self.json_dir, f"{table_name}.json")

            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(rows, f, indent=2)

            if rows:
                with open(csv_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                    writer.writeheader()
                    writer.writerows(rows)

            with open(csv_path, "rb") as f:
                sha256 = hashlib.sha256(f.read()).hexdigest()

            model_name = self._table_to_model(table_name)
            manifest["tables"][table_name] = {
                "row_count": len(rows),
                "csv_sha256": sha256,
                "primary_key": DATA_DICTIONARY.get(model_name, {}).get("primary_key", "id")
            }

        # 3. Export SQLite Database
        db_repo = DatabaseRepository(self.db_path)
        db_repo.initialize_schema_and_indices(datasets)
        with open(self.db_path, "rb") as f:
            manifest["sqlite_sha256"] = hashlib.sha256(f.read()).hexdigest()

        # 4. Export Manifest & Data Dictionaries
        manifest_path = os.path.join(self.output_dir, "source_manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        dict_json_path = os.path.join(self.output_dir, "data_dictionary.json")
        with open(dict_json_path, "w", encoding="utf-8") as f:
            json.dump(DATA_DICTIONARY, f, indent=2)

        self._export_markdown_dictionary(os.path.join(self.output_dir, "data_dictionary.md"))
        return manifest

    def _table_to_model(self, table_name: str) -> str:
        mapping = {
            "suppliers": "Supplier",
            "products": "Product",
            "boms": "BOM",
            "bom_items": "BOMItem",
            "warehouses": "Warehouse",
            "material_lots": "MaterialLot",
            "production_orders": "ProductionOrder",
            "production_order_lot_consumptions": "ProductionOrderLotConsumption",
            "finished_lots": "FinishedLot",
            "customers": "Customer",
            "shipments": "Shipment",
            "deliveries": "Delivery",
            "recall_cases": "RecallCase",
            "recall_actions": "RecallAction",
            "inventory_movements": "InventoryMovement"
        }
        return mapping.get(table_name, table_name)

    def _export_markdown_dictionary(self, filepath: str):
        lines = [
            "# Master Data Dictionary & Schema Specification",
            "",
            "Complete data dictionary for enterprise pharmaceutical & medical device lot traceability.",
            ""
        ]

        for entity, info in DATA_DICTIONARY.items():
            lines.append(f"## Entity: `{entity}`")
            lines.append(f"**Description**: {info['description']}  ")
            lines.append(f"**Primary Key**: `{info['primary_key']}`  ")
            if info["relationships"]:
                lines.append("**Relationships**:")
                for r in info["relationships"]:
                    lines.append(f"- Foreign Key: `{r['foreign_key']}` -> `{r['references']}` (Cardinality: {r['cardinality']})")
            lines.append("")
            lines.append("| Field Name | Type | Required | Unique | Allowed / Sample Values | Validation Rule |")
            lines.append("|---|---|---|---|---|---|")
            for field, fspec in info["fields"].items():
                req = "YES" if fspec["required"] else "NO"
                uniq = "YES" if fspec["unique"] else "NO"
                allowed = str(fspec["allowed_values"]).replace("|", "\\|")
                rule = str(fspec["validation_rule"]).replace("|", "\\|")
                lines.append(f"| `{field}` | `{fspec['type']}` | {req} | {uniq} | {allowed} | {rule} |")
            lines.append("")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
