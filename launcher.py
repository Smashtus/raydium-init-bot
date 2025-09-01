from __future__ import annotations
import argparse
from pathlib import Path
from rich.console import Console
from rich.table import Table
from src.io.jsonio import load_plan
from src.util.logging import setup_logging, log
from src.util.config import load_config
from src.util.planhash import sha256_file
from src.exec.orchestrator import execute, RunConfig

console = Console()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Sol Atomic Launcher (plan-first).")
    p.add_argument("--plan", required=True, help="Path to plan JSON")
    p.add_argument("--seed-keypair", help="Seed keypair JSON file (ed25519)")
    p.add_argument("--seed-ledger", action="store_true", help="Use Ledger device for seed signer")
    p.add_argument("--rpc", help="RPC URL for cluster")
    p.add_argument("--priority-fee", type=int, default=None, help="Compute unit price (micro-lamports)")
    p.add_argument("--tip-lamports", type=int, default=None, help="Jito tip lamports")
    p.add_argument("--dry-run", action="store_true", help="Summary only, no step execution")
    p.add_argument("--resume", action="store_true", help="Resume from last checkpoint")
    p.add_argument("--only", choices=["fund","mint","metadata","lp","buys","all"], default="all")
    p.add_argument("--allow-override", action="store_true", help="Allow plan program id overrides")
    p.add_argument("--out", default="state", help="Output state dir")
    p.add_argument("--config", default="configs/defaults.yaml", help="Path to config YAML")
    return p.parse_args()


def print_plan_summary(plan_path: Path, cfg: dict) -> None:
    plan = load_plan(plan_path)
    t = Table(title="Plan & Config Summary", show_header=True, header_style="bold")
    t.add_column("Field"); t.add_column("Value")
    t.add_row("version", plan.version)
    t.add_row("model", plan.model)
    t.add_row("network", plan.network)
    t.add_row("plan_id", plan.plan_id)
    t.add_row("token.symbol", plan.token.symbol)
    t.add_row("dex.variant", plan.dex.variant)
    t.add_row("dex.program_id (plan)", plan.dex.program_id)
    t.add_row("program_ids.raydium_v4_amm (cfg)", str(cfg.get("program_ids", {}).get("raydium_v4_amm")))
    t.add_row("schedule.len", str(len(plan.schedule)))
    t.add_row("wallets.len", str(len(plan.wallets)))
    console.print(t)


def main() -> None:
    setup_logging()
    args = parse_args()
    plan_path = Path(args.plan)
    cfg = load_config(Path(args.config))
    plan_hash = sha256_file(plan_path)

    log.info("load_plan_start", path=str(plan_path), plan_hash=plan_hash)
    plan = load_plan(plan_path)
    log.info("load_plan_ok", symbol=plan.token.symbol, schedule_len=len(plan.schedule), wallets=len(plan.wallets))

    if args.dry_run:
        print_plan_summary(plan_path, cfg)
        console.print("[bold green]Dry-run OK[/bold green] — plan structure accepted.")
        return

    only_norm = "lp_init" if args.only == "lp" else args.only
    rc = RunConfig(out_dir=Path(args.out), resume=args.resume, only=only_norm, plan_hash=plan_hash)

    # Persist executed plan for audit
    out_plan = Path(args.out) / "plan.json"
    out_plan.parent.mkdir(parents=True, exist_ok=True)
    out_plan.write_bytes(plan_path.read_bytes())

    execute(plan, rc)
    console.print(f"[bold green]Done.[/bold green] Receipts: {args.out}/receipts  |  Artifacts: {args.out}/artifacts.json")


if __name__ == "__main__":
    main()

