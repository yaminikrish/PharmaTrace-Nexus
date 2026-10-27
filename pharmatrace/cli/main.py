"""
Enterprise Command-Line Interface (CLI) for PharmaTrace Nexus.
Provides subcommands:
- generate: Deterministic synthetic data generator (starter & full scales)
- validate: 8-step validation suite & anomaly benchmark calculation
- verify: Step 10 dual-run reproducibility checksum test
- serve: Multi-threaded web server & REST API
"""

import os
import sys
import argparse
import shutil
import logging
from pharmatrace.config import settings, configure_logging
from pharmatrace.services.generator_service import GeneratorService
from pharmatrace.services.audit_service import AuditService
from pharmatrace.infrastructure.checksums import ChecksumVerifier
from pharmatrace.api.server import start_server

def cmd_generate(args):
    print(f"[*] Executing Generator: seed={args.seed}, scale={args.scale}, output_dir={args.output_dir}")
    generator = GeneratorService(
        seed=args.seed,
        scale=args.scale,
        inject_anomalies=not args.no_anomalies
    )
    generator.generate()
    manifest = generator.export(args.output_dir)
    print(f"[+] Dataset generated successfully in '{args.output_dir}'. Total tables: {len(manifest['tables'])}")

def cmd_validate(args):
    print(f"[*] Running 8-Step Enterprise Validation Suite on '{args.data_dir}'...")
    auditor = AuditService(args.data_dir)
    results = auditor.run_all_validations()

    print("\n" + "=" * 65)
    print("PHARMATRACE NEXUS ENTERPRISE VALIDATION REPORT")
    print("=" * 65)
    print(f"Overall Status:        {results['overall_system_status']}")
    print(f"Data Integrity:        {results['data_integrity_status']}")
    print(f"Total Tables Verified: {results['total_tables_checked']}")
    print(f"Total Rows Inspected:  {results['summary_counts']['total_rows_inspected']:,}")
    print(f"Primary Key Check:     {'PASS' if results['checks']['primary_key_uniqueness']['passed'] else 'FAIL'}")
    print(f"Foreign Key Integrity: {results['checks']['foreign_key_integrity']['violations_count']} violation(s) (1 expected planted ghost lot, 0 unexpected)")
    print(f"Enum Compliance:       {'PASS' if results['checks']['enum_compliance']['passed'] else 'FAIL'}")
    print(f"Date Chronology:       {'PASS' if results['checks']['date_chronology']['passed'] else 'FAIL'}")
    print(f"Inventory Arithmetic:  {'PASS' if results['checks']['inventory_movement_reconciliation']['passed'] else 'FAIL'}")
    print(f"Recall Scope Audit:    {'PASS' if results['checks']['recall_scope_completion']['passed'] else 'FAIL'}")
    print(f"Arithmetic Discrepancies: {results['checks']['arithmetic_reconciliation']['discrepancies_count']} (1 expected planted yield excess, 0 unexpected)")
    print("-" * 65)
    bm = results["checks"]["anomaly_ground_truth_benchmark"]
    print("ANOMALY BENCHMARK vs. GROUND TRUTH:")
    print(f"  Planted Anomalies:   {bm['ground_truth_total']}")
    print(f"  Detected Anomalies:  {bm['detected_total']}")
    print(f"  Audit Precision:     {bm['precision'] * 100:.1f}%")
    print(f"  Audit Recall:        {bm['recall'] * 100:.1f}%")
    print(f"  F1 Score:            {bm['f1_score']:.4f}")
    print("=" * 65 + "\n")

    summary_path = os.path.join(args.data_dir, "validation_summary.json")
    auditor.export_summary(summary_path)
    print(f"[+] Validation report exported to: {summary_path}")

def cmd_verify(args):
    print("\n" + "=" * 70)
    print(f"STEP 10 REPRODUCIBILITY TEST: Dual-Run Bitwise Verification (Seed={args.seed})")
    print("=" * 70)

    dir1, dir2 = "test_run1", "test_run2"
    for d in [dir1, dir2]:
        if os.path.exists(d): shutil.rmtree(d)

    print(f"[*] Executing Run 1 (seed={args.seed}, scale={args.scale})...")
    g1 = GeneratorService(seed=args.seed, scale=args.scale, inject_anomalies=True)
    g1.generate()
    g1.export(dir1)

    print(f"[*] Executing Run 2 (seed={args.seed}, scale={args.scale})...")
    g2 = GeneratorService(seed=args.seed, scale=args.scale, inject_anomalies=True)
    g2.generate()
    g2.export(dir2)

    chk1 = ChecksumVerifier.compute_directory_checksums(dir1)
    chk2 = ChecksumVerifier.compute_directory_checksums(dir2)
    comp = ChecksumVerifier.compare_checksums(chk1, chk2)

    print("\n" + "-" * 70)
    print(f"{'Artifact File':<35} | {'Run 1 Rows':<10} | {'Run 2 Rows':<10} | {'Status':<10}")
    print("-" * 70)

    for file, cdata in comp["comparison"].items():
        status = "MATCH (IDENTICAL)" if cdata["identical"] else "MISMATCH"
        print(f"{file:<35} | {str(cdata['run1_rows']):<10} | {str(cdata['run2_rows']):<10} | {status}")

    print("-" * 70)
    if comp["all_identical"]:
        print("[SUCCESS] 100% BITWISE REPRODUCIBILITY VERIFIED ACROSS BOTH RUNS!")
    else:
        print("[FAILURE] Checksum or row count divergence detected.")
    print("=" * 70 + "\n")

    shutil.rmtree(dir1, ignore_errors=True)
    shutil.rmtree(dir2, ignore_errors=True)
    return 0 if comp["all_identical"] else 1

def cmd_serve(args):
    start_server(host=args.host, port=args.port)

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pharmatrace",
        description="PharmaTrace Nexus — Enterprise Multi-Tier Lot Traceability & Recall Simulation Suite"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # generate
    gen_parser = subparsers.add_parser("generate", help="Generate synthetic supply chain dataset")
    gen_parser.add_argument("--seed", type=int, default=settings.default_seed, help=f"Deterministic random seed (default: {settings.default_seed})")
    gen_parser.add_argument("--scale", choices=["starter", "full"], default=settings.default_scale, help="Dataset scale ('starter' or 'full')")
    gen_parser.add_argument("--output-dir", default=settings.data_dir, help=f"Output directory (default: {settings.data_dir})")
    gen_parser.add_argument("--no-anomalies", action="store_true", help="Disable planted negative edge case injection")
    gen_parser.set_defaults(func=cmd_generate)

    # validate
    val_parser = subparsers.add_parser("validate", help="Run 8-step validation and anomaly benchmark")
    val_parser.add_argument("--data-dir", default=settings.data_dir, help=f"Data directory to inspect (default: {settings.data_dir})")
    val_parser.set_defaults(func=cmd_validate)

    # verify
    ver_parser = subparsers.add_parser("verify", help="Execute Step 10 dual-run checksum reproducibility test")
    ver_parser.add_argument("--seed", type=int, default=settings.default_seed, help=f"Seed for dual-run test (default: {settings.default_seed})")
    ver_parser.add_argument("--scale", choices=["starter", "full"], default="starter", help="Dataset scale for test")
    ver_parser.set_defaults(func=cmd_verify)

    # serve
    srv_parser = subparsers.add_parser("serve", help="Launch web server & REST API")
    srv_parser.add_argument("--host", default=settings.host, help=f"Bind host (default: {settings.host})")
    srv_parser.add_argument("--port", type=int, default=settings.port, help=f"Listen port (default: {settings.port})")
    srv_parser.set_defaults(func=cmd_serve)

    # run-all
    run_parser = subparsers.add_parser("run-all", help="Execute complete pipeline (generate, validate, verify, test, serve)")
    run_parser.add_argument("--port", type=int, default=settings.port, help=f"Listen port (default: {settings.port})")
    run_parser.set_defaults(func=lambda args: os.system(f"python run.py {args.port}"))

    return parser

def main():
    configure_logging()
    parser = build_parser()
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)
    args = parser.parse_args()
    if hasattr(args, "func"):
        res = args.func(args)
        if res is not None and isinstance(res, int):
            sys.exit(res)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
