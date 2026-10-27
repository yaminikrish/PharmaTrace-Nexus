"""
Enterprise Configuration and Settings Module.
Provides centralized, strongly-typed settings with environment variable overrides
and structured logging configuration.
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class AppSettings:
    """Enterprise Application Configuration."""
    app_name: str = "PharmaTrace Nexus"
    app_version: str = "2.4.0"
    environment: str = os.getenv("PHARMATRACE_ENV", "production")
    debug: bool = os.getenv("PHARMATRACE_DEBUG", "false").lower() in ("true", "1")
    
    # Paths
    base_dir: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir: str = os.getenv("PHARMATRACE_DATA_DIR", os.path.join(base_dir, "data"))
    data_full_dir: str = os.path.join(base_dir, "data_full")
    frontend_dir: str = os.path.join(base_dir, "frontend")
    
    # Database
    db_name: str = "traceability.db"
    
    # Generator defaults
    default_seed: int = int(os.getenv("PHARMATRACE_SEED", "20261022"))
    default_scale: str = os.getenv("PHARMATRACE_SCALE", "starter")
    
    # Server settings
    host: str = os.getenv("PHARMATRACE_HOST", "0.0.0.0")
    port: int = int(os.getenv("PHARMATRACE_PORT", "8080"))

    @property
    def db_path(self) -> str:
        return os.path.join(self.data_dir, self.db_name)

    @property
    def ground_truth_json_path(self) -> str:
        return os.path.join(self.data_dir, "ground_truth.json")

    @property
    def ground_truth_csv_path(self) -> str:
        return os.path.join(self.data_dir, "ground_truth.csv")

    @property
    def manifest_path(self) -> str:
        return os.path.join(self.data_dir, "source_manifest.json")

    @property
    def validation_summary_path(self) -> str:
        return os.path.join(self.data_dir, "validation_summary.json")

def configure_logging(level: int = logging.INFO):
    """Configures enterprise structured logging."""
    logging.basicConfig(
        level=level,
        format="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

settings = AppSettings()
