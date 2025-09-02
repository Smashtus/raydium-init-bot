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
    """Verify on-chain state for artifacts in ``out_dir``."""

    art_path = out_dir / "artifacts.json"
    artifacts = json.loads(art_path.read_text()) if art_path.exists() else {}
    cfg = load_config(cfg_path)
    rpc = Rpc(RpcConfig(url=rpc_url))

    checks = {}

    mint = artifacts.get("mint", {}).get("mint")
    if mint:
        checks["mint_exists"] = await rpc.account_exists(mint)
        mp = cfg.get("program_ids", {}).get("metaplex_token_metadata")
        if mp:
            md_pda = find_metadata_pda(mint, mp)
            checks["metadata_exists"] = await rpc.account_exists(md_pda)

    if artifacts.get("lp_init", {}).get("pool"):
        pool = artifacts["lp_init"]["pool"]
        checks["pool_exists"] = await rpc.account_exists(pool)

    out = {"checks": checks, "ok": all(checks.values()) if checks else False}
    (out_dir / "verify.json").write_text(json.dumps(out, indent=2))

    t = Table(title="Verify")
    t.add_column("Check")
    t.add_column("Value")
    for k, v in checks.items():
        t.add_row(k, str(v))
    console.print(t)

    await rpc.close()
    return out


if __name__ == "__main__":  # pragma: no cover
    import asyncio, argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="state")
    ap.add_argument("--rpc", required=True)
    ap.add_argument("--config", default="configs/defaults.yaml")
    a = ap.parse_args()
    asyncio.run(verify(Path(a.out), a.rpc, Path(a.config)))

