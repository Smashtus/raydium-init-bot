from __future__ import annotations
import argparse, asyncio
from pathlib import Path
from rich.console import Console
from rich.table import Table
from src.io.jsonio import load_plan
from src.util.logging import setup_logging, log
from src.util.config import load_config
from src.util.planhash import sha256_file
from src.exec.orchestrator import execute_async, RunConfig

console = Console()

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Sol Atomic Launcher (plan-first, prod-safe).")
    p.add_argument("--plan", required=True, help="Path to plan JSON")
    p.add_argument("--seed-keypair", required=False, help="Seed keypair JSON file (ed25519)")
    p.add_argument("--rpc", required=True, help="RPC URL for cluster")
    p.add_argument("--priority-fee", type=int, default=None, help="Compute unit price (micro-lamports)")
    p.add_argument("--cu-limit", type=int, default=1_000_000, help="Compute unit limit per tx")
    p.add_argument("--simulate", action="store_true", help="Simulate each tx before send")
    p.add_argument("--resume", action="store_true", help="Resume from last checkpoint")
    p.add_argument("--only", choices=["fund","mint","metadata","lp","lp_init","buys","all"], default="all")
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
    cfg_yaml = Path(args.config)
    cfg_yaml.parent.mkdir(parents=True, exist_ok=True)
    cfg = load_config(cfg_yaml)
    plan_hash = sha256_file(plan_path)

    log.info("load_plan_start", path=str(plan_path), plan_hash=plan_hash)
    plan = load_plan(plan_path)
    log.info("load_plan_ok", symbol=plan.token.symbol, schedule_len=len(plan.schedule), wallets=len(plan.wallets))

    rc = RunConfig(
        out_dir=Path(args.out),
        resume=args.resume,
        only=("lp_init" if args.only in ("lp","lp_init") else args.only),
        plan_hash=plan_hash,
        rpc_url=args.rpc,
        cu_limit=args.cu_limit,
        cu_price_micro=args.priority_fee,
        simulate=args.simulate
    )

    # Persist executed plan for audit
    out_plan = Path(args.out) / "plan.json"
    out_plan.parent.mkdir(parents=True, exist_ok=True)
    out_plan.write_bytes(plan_path.read_bytes())

    asyncio.run(execute_async(plan, rc, seed_keypair_path=args.seed_keypair or "", config_yaml=cfg_yaml))
    console.print(f"[bold green]Done.[/bold green] Receipts: {args.out}/receipts  |  Artifacts: {args.out}/artifacts.json")

if __name__ == "__main__":
    main()
