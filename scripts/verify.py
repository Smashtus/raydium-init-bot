from __future__ import annotations

import json
from pathlib import Path
from typing import Tuple, Dict, Any, List

from rich.console import Console

from src.core.solana import Rpc, RpcConfig
from src.core.metaplex import find_metadata_pda
from src.dex.raydium_v4 import derive_pool_accounts, probe_pool_exists
from src.util.config import load_config
from src.util.planhash import sha256_file


console = Console()


async def verify(out_dir: Path, rpc_url: str, cfg_path: Path) -> Tuple[Dict[str, Any], bool]:
    """Verify on-chain state for the current deployment.

    The function is intentionally read-only and cross references the persisted
    ``artifacts.json`` with on-chain data.  Missing artifacts or network errors
    simply result in ``False`` checks allowing tests to exercise the happy and
    unhappy paths deterministically.
    """

    art_path = out_dir / "artifacts.json"
    artifacts = json.loads(art_path.read_text()) if art_path.exists() else {}
    cfg = load_config(cfg_path)
    rpc = Rpc(RpcConfig(url=rpc_url))

    mint: str = artifacts.get("mint", {}).get("mint", "")
    metadata_pda = ""
    pool_addr = ""
    if mint:
        mint_exists = await rpc.account_exists(mint)
        md_prog = cfg["program_ids"]["metaplex_token_metadata"]
        metadata_pda = find_metadata_pda(mint, md_prog)
        metadata_exists = await rpc.account_exists(metadata_pda)

        accs = derive_pool_accounts(
            mint, cfg["mints"]["wrapped_sol"], cfg["program_ids"]["raydium_v4_amm"]
        )
        pool_addr = accs.pool
        pool_exists = await probe_pool_exists(rpc, accs)
    else:
        mint_exists = metadata_exists = pool_exists = False

    swaps: List[Dict[str, Any]] = []
    for s in artifacts.get("buys", {}).get("swaps", []):
        sig = s.get("sig")
        if not sig:
            continue
        wid = s.get("wallet_id", "")
        present = False
        try:
            from solders.signature import Signature

            tx = await rpc.client.get_transaction(Signature.from_string(sig))
            present = tx.value is not None
        except Exception:
            present = False
        swaps.append({"wallet_id": wid, "sig": sig, "tx_present": present})

    plan_path = out_dir / "plan.json"
    plan_hash = sha256_file(plan_path) if plan_path.exists() else ""

    result: Dict[str, Any] = {
        "schema_version": "1.0.0",
        "plan_hash": plan_hash,
        "mint": mint,
        "metadata_pda": metadata_pda,
        "pool": pool_addr,
        "checks": {
            "mint_exists": mint_exists,
            "metadata_exists": metadata_exists,
            "pool_exists": pool_exists,
        },
        "swaps": swaps,
    }

    (out_dir / "verify.json").write_text(json.dumps(result, indent=2))

    present = sum(1 for s in swaps if s["tx_present"])
    console.print("VERIFY RESULT")
    console.print(f"- mint_exists: {'OK' if mint_exists else 'FAIL'}")
    console.print(f"- metadata_exists: {'OK' if metadata_exists else 'FAIL'}")
    console.print(f"- pool_exists: {'OK' if pool_exists else 'FAIL'}")
    console.print(f"- swaps (present/total): {present}/{len(swaps)}")

    ok = mint_exists and metadata_exists and pool_exists
    await rpc.close()
    return result, ok


if __name__ == "__main__":  # pragma: no cover
    import asyncio, argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="state")
    ap.add_argument("--rpc", required=True)
    ap.add_argument("--config", default="configs/defaults.yaml")
    a = ap.parse_args()
    asyncio.run(verify(Path(a.out), a.rpc, Path(a.config)))

