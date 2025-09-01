from __future__ import annotations
from pathlib import Path
from typing import Dict, Any
from src.util.planhash import sha256_file
from src.core.solana import Rpc


async def preflight(rpc: Rpc, plan_path: Path, cfg: Dict[str, Any]) -> Dict[str, Any]:
    plan_hash = sha256_file(plan_path)
    # Basic RPC call
    _ = await rpc.recent_blockhash()
    # Check presence of configured program IDs (if provided)
    checks = {}
    for k, v in (cfg.get("program_ids") or {}).items():
        if not v:
            continue
        ok = await rpc.account_exists(v)
        checks[k] = bool(ok)
    return {"plan_hash": plan_hash, "program_checks": checks}
