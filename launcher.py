from __future__ import annotations
import argparse, asyncio, json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from src.io.jsonio import load_plan
from src.util.logging import setup_logging, log
from src.util.config import load_config
from src.util.planhash import sha256_file
from src.exec.orchestrator import execute_async, RunConfig
from src.util import preflight as preflight_mod
from scripts.verify import verify as verify_script
from src.core.solana import Rpc, RpcConfig

console = Console()

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Sol Atomic Launcher (plan-first, prod-safe).")
    sub = p.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="Execute a plan")
    run.add_argument("--plan", required=True, help="Path to plan JSON")
    run.add_argument("--seed-keypair", required=False, help="Seed keypair JSON file (ed25519)")
    run.add_argument("--rpc", required=True, help="RPC URL for cluster")
    run.add_argument("--priority-fee", type=int, default=None, help="Compute unit price (micro-lamports)")
    run.add_argument("--cu-limit", type=int, default=1_000_000, help="Compute unit limit per tx")
    run.add_argument("--simulate", action="store_true", help="Simulate each tx before send")
    run.add_argument("--resume", action="store_true", help="Resume from last checkpoint")
    run.add_argument("--only", choices=["fund","mint","metadata","lp","lp_init","buys","all"], default="all")
    run.add_argument("--out", default="state", help="Output state dir")
    run.add_argument("--config", default="configs/defaults.yaml", help="Path to config YAML")

    pre = sub.add_parser("preflight", help="Dry-run planners and verify configuration")
    pre.add_argument("--plan", required=True, help="Path to plan JSON")
    pre.add_argument("--rpc", required=True, help="RPC URL for cluster")
    pre.add_argument("--config", default="configs/defaults.yaml", help="Path to config YAML")
    pre.add_argument("--out", default="state", help="Output state dir")

    ver = sub.add_parser("verify", help="Verify on-chain state against artifacts")
    ver.add_argument("--out", default="state", help="State directory with artifacts")
    ver.add_argument("--rpc", required=True, help="RPC URL for cluster")
    ver.add_argument("--config", default="configs/defaults.yaml", help="Path to config YAML")

    return p

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
    parser = build_parser()
    args = parser.parse_args()

    if args.cmd == "preflight":
        plan_path = Path(args.plan)
        cfg = load_config(Path(args.config))
        plan = load_plan(plan_path)
        rpc = Rpc(RpcConfig(url=args.rpc))
        res = asyncio.run(preflight_mod.preflight(rpc, plan_path, cfg, plan))
        out = Path(args.out) / "preflight.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(res, indent=2))
        t = Table(title="Preflight")
        t.add_column("Check")
        t.add_column("Value")
        for k, v in res["program_checks"].items():
            t.add_row(k, str(v))
        t.add_row("simulate_metadata_ok", str(res["simulate_metadata_ok"]))
        t.add_row("simulate_init_ok", str(res["simulate_init_ok"]))
        console.print(t)
        return

    if args.cmd == "verify":
        asyncio.run(verify_script(Path(args.out), args.rpc, Path(args.config)))
        return

    # run subcommand
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
        only=("lp_init" if args.only in ("lp", "lp_init") else args.only),
        plan_hash=plan_hash,
        rpc_url=args.rpc,
        cu_limit=args.cu_limit,
        cu_price_micro=args.priority_fee,
        simulate=args.simulate,
    )

    # Persist executed plan for audit
    out_plan = Path(args.out) / "plan.json"
    out_plan.parent.mkdir(parents=True, exist_ok=True)
    out_plan.write_bytes(plan_path.read_bytes())

    asyncio.run(execute_async(plan, rc, seed_keypair_path=args.seed_keypair or "", config_yaml=cfg_yaml))
    console.print(f"[bold green]Done.[/bold green] Receipts: {args.out}/receipts  |  Artifacts: {args.out}/artifacts.json")

if __name__ == "__main__":
    main()
