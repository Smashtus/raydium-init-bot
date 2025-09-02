from __future__ import annotations

import json
from pathlib import Path
from rich.table import Table
from rich.console import Console

from src.core.solana import Rpc, RpcConfig
from src.core.metaplex import find_metadata_pda
from src.dex.raydium_v4 import derive_pool_accounts, probe_pool_exists
from src.util.config import load_config


console = Console()


async def verify(out_dir: Path, rpc_url: str, cfg_path: Path) -> dict:
    """Verify on‑chain state for the current deployment.

    The function inspects the persisted ``artifacts.json`` file and checks
    whether the expected mint, metadata account and Raydium pool have been
    created.  Network access is read‑only and therefore safe in testing
    environments.
    """

    art_path = out_dir / "artifacts.json"
    artifacts = json.loads(art_path.read_text()) if art_path.exists() else {}
    cfg = load_config(cfg_path)
    rpc = Rpc(RpcConfig(url=rpc_url))

    checks = {
        "mint_exists": False,
        "metadata_exists": False,
        "pool_exists": False,
        "swap_txs": [],
    }

    mint = artifacts.get("mint", {}).get("mint")
    if mint:
        checks["mint_exists"] = await rpc.account_exists(mint)

        mp_prog = cfg.get("program_ids", {}).get("metaplex_token_metadata")
        if mp_prog:
            md_pda = find_metadata_pda(mint, mp_prog)
            checks["metadata_exists"] = await rpc.account_exists(md_pda)

        ray_prog = cfg.get("program_ids", {}).get("raydium_v4_amm")
        wsol = cfg.get("mints", {}).get("wrapped_sol")
        if ray_prog and wsol:
            accs = derive_pool_accounts(base_mint=mint, quote_mint=wsol, program_id=ray_prog)
            checks["pool_exists"] = await probe_pool_exists(rpc, accs)

    # Best-effort check of swap transactions
    swaps = artifacts.get("buys", {}).get("swaps", [])
    for s in swaps:
        sig = s.get("sig")
        if not sig:
            continue
        try:
            from solders.signature import Signature
            tx = await rpc.client.get_transaction(Signature.from_string(sig))
            checks["swap_txs"].append({"sig": sig, "found": tx.value is not None})
        except Exception:
            checks["swap_txs"].append({"sig": sig, "found": False})

    (out_dir / "verify.json").write_text(json.dumps(checks, indent=2))

    t = Table(title="Verify")
    t.add_column("Check")
    t.add_column("Value")
    for k, v in checks.items():
        if k == "swap_txs":
            t.add_row("swap_txs_found", f"{sum(1 for s in v if s['found'])}/{len(v)}")
        else:
            t.add_row(k, str(v))
    console.print(t)

    await rpc.close()
    ok = bool(checks.get("mint_exists")) and bool(checks.get("metadata_exists")) and bool(checks.get("pool_exists"))
    return checks, ok


if __name__ == "__main__":  # pragma: no cover
    import asyncio, argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="state")
    ap.add_argument("--rpc", required=True)
    ap.add_argument("--config", default="configs/defaults.yaml")
    a = ap.parse_args()
    asyncio.run(verify(Path(a.out), a.rpc, Path(a.config)))

