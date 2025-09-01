"""Transfer lamports from the seed wallet to sub‑wallets.

This module implements the live funding step.  The heavy Solana imports are
kept inside the functions so the module can be imported without the Solana
Python stack installed – useful for unit tests and dry‑run execution.
"""

from __future__ import annotations

from typing import Any, Dict

from tenacity import retry, stop_after_attempt, wait_exponential_jitter

from src.models.plan import Plan
from src.core.solana import Rpc


@retry(stop=stop_after_attempt(5), wait=wait_exponential_jitter(min=0.2, max=2.0))
async def _transfer(rpc: Rpc, from_kp, to_pub: str, lamports: int) -> str:
    from solders.pubkey import Pubkey
    from solana.system_program import TransferParams, transfer
    from solana.transaction import Transaction

    tx = Transaction()
    tx.add(
        transfer(
            TransferParams(
                from_pubkey=from_kp.pubkey(),
                to_pubkey=Pubkey.from_string(to_pub),
                lamports=lamports,
            )
        )
    )
    tx.recent_blockhash = await rpc.recent_blockhash()
    tx.sign(from_kp)
    return await rpc.send_and_confirm(tx, [from_kp])


async def run(rpc: Rpc, seed_kp, subwallets: Dict[str, Any], plan: Plan) -> Dict[str, Any]:
    """Fund all non-seed wallets defined in ``plan`` from ``seed_kp``."""

    funded = []
    for w in plan.wallets:
        if w.role == "SEED":
            continue
        pub = subwallets[w.wallet_id]["pub"]
        sig = await _transfer(rpc, seed_kp, pub, w.funding.total_lamports)
        funded.append(
            {
                "wallet_id": w.wallet_id,
                "lamports": w.funding.total_lamports,
                "sig": sig,
            }
        )
    return {"funded": funded}

