#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from src.io.jsonio import load_plan


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Solana atomic launcher prototype")
    parser.add_argument("--plan", required=True, type=Path, help="Path to plan JSON")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--seed-keypair", type=Path, help="Seed keypair file")
    group.add_argument("--seed-ledger", action="store_true", help="Use Ledger for seed signer")
    parser.add_argument("--rpc", required=True, help="RPC URL")
    parser.add_argument("--priority-fee", type=int, default=0, help="Compute unit price override")
    parser.add_argument("--jito-grpc", help="Jito gRPC endpoint")
    parser.add_argument("--tip-lamports", type=int, default=0, help="Jito tip in lamports")
    parser.add_argument("--dry-run", action="store_true", help="Simulate only")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoints")
    parser.add_argument("--only", choices=["fund", "mint", "metadata", "lp", "buys", "all"], default="all")
    parser.add_argument("--allow-override", action="store_true", help="Allow plan program id overrides")
    parser.add_argument("--out", type=Path, default=Path("state"), help="Output state directory")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    plan = load_plan(args.plan)
    print(f"Loaded plan {plan.plan_id} for network {plan.network}")
    print(f"Wallets: {len(plan.wallets)} | Schedule: {plan.schedule}")

    if args.dry_run:
        print("Dry run mode enabled; no transactions will be sent.")


if __name__ == "__main__":
    main()
