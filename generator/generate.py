"""
Deterministic Synthetic Data Generator for Lot Traceability & Recall Simulation.
Delegates to pharmatrace.services.generator_service.GeneratorService.
"""

import os
import sys
import argparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from pharmatrace.services.generator_service import GeneratorService

class DataGenerator:
    def __init__(self, seed: int = 20261022, scale: str = "starter", inject_anomalies: bool = True):
        self.svc = GeneratorService(seed=seed, scale=scale, inject_anomalies=inject_anomalies)

    def generate_all(self):
        return self.svc.generate()

    def export_data(self, output_dir: str):
        return self.svc.export(output_dir)

def main():
    parser = argparse.ArgumentParser(description="Deterministic Synthetic Data Generator for Lot Traceability & Recall Simulation.")
    parser.add_argument("--seed", type=int, default=20261022, help="Fixed random seed (default: 20261022)")
    parser.add_argument("--scale", choices=["starter", "full"], default="starter", help="Dataset volume scale: 'starter' (fast) or 'full'")
    parser.add_argument("--output-dir", type=str, default="data", help="Output directory path")
    parser.add_argument("--no-anomalies", action="store_true", help="Disable planted negative edge case injection")

    args = parser.parse_args()

    generator = DataGenerator(
        seed=args.seed,
        scale=args.scale,
        inject_anomalies=not args.no_anomalies
    )
    generator.generate_all()
    generator.export_data(args.output_dir)

if __name__ == "__main__":
    main()
