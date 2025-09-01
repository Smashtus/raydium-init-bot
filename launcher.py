from __future__ import annotations
import argparse
from pathlib import Path
from rich.console import Console
from rich.table import Table
from src.io.jsonio import load_plan
from src.util.logging import setup_logging, log
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
    p.add_argument("--dry-run", action="store_true", help="Simulate/parse only (summary), no step execution")
    p.add_argument("--resume", action="store_true", help="Resume from last checkpoint")
    p.add_argument("--only", choices=["fund","mint","metadata","lp","buys","all"], default="all")
    p.add_argument("--allow-override", action="store_true", help="Allow plan program id overrides")
    p.add_argument("--out", default="state", help="Output state dir")
    return p.parse_args()

def print_plan_summary(plan_path: Path) -> None:
    plan = load_plan(plan_path)
    t = Table(title="Plan Summary", show_header=True, header_style="bold")
    t.add_column("Field"); t.add_column("Value")
    t.add_row("version", plan.version)
    t.add_row("model", plan.model)
    t.add_row("network", plan.network)
    t.add_row("plan_id", plan.plan_id)
    t.add_row("created_at", plan.created_at)
    t.add_row("token.symbol", plan.token.symbol)
    t.add_row("token.decimals", str(plan.token.decimals))
    t.add_row("token.total_mint", str(plan.token.total_mint))
    t.add_row("token.lp_tokens", str(plan.token.lp_tokens))
    t.add_row("dex.variant", plan.dex.variant)
    t.add_row("dex.program_id", plan.dex.program_id)
    t.add_row("schedule.len", str(len(plan.schedule)))
    t.add_row("wallets.len", str(len(plan.wallets)))
    console.print(t)
    role_table = Table(title="Wallet Roles")
    role_table.add_column("wallet_id"); role_table.add_column("role"); role_table.add_column("total_lamports")
    for w in plan.wallets:
        role_table.add_row(w.wallet_id, w.role, str(w.funding.total_lamports))
    console.print(role_table)

def main() -> None:
    setup_logging()
    args = parse_args()
    plan_path = Path(args.plan)
    log.info("load_plan_start", path=str(plan_path))
    plan = load_plan(plan_path)
    log.info("load_plan_ok", symbol=plan.token.symbol, schedule_len=len(plan.schedule), wallets=len(plan.wallets))

    if args.dry_run:
        print_plan_summary(plan_path)
        console.print("[bold green]Dry-run OK[/bold green] — plan structure accepted.")
        return

    cfg = RunConfig(out_dir=Path(args.out), resume=args.resume, only=("lp" if args.only=="lp" else args.only))
    execute(plan, cfg)
    console.print(f"[bold green]Done.[/bold green] Receipts at: {args.out}/receipts")

if __name__ == "__main__":
    main()
