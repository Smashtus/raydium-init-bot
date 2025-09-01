from __future__ import annotations
from typing import Dict, Any
from solders.pubkey import Pubkey
from solana.system_program import TransferParams, transfer
from solana.transaction import Transaction
from tenacity import retry, stop_after_attempt, wait_exponential_jitter
from src.models.plan import Plan
from src.core.solana import Rpc
from src.core.tx import with_compute_budget


@retry(stop=stop_after_attempt(5), wait=wait_exponential_jitter(min=0.2, max=2.0))
async def _transfer(rpc: Rpc, from_kp, to_pub: str, lamports: int, cu_limit: int | None, cu_price_micro: int | None) -> str:
    tx = Transaction()
    with_compute_budget(tx, cu_limit, cu_price_micro)
    tx.add(transfer(TransferParams(from_pubkey=from_kp.pubkey(), to_pubkey=Pubkey.from_string(to_pub), lamports=lamports)))
    tx.recent_blockhash = await rpc.recent_blockhash()
    return await rpc.send_and_confirm(tx, from_kp)


async def run(rpc: Rpc, seed_kp, wallet_map: Dict[str, Any], plan: Plan, cu_limit: int | None, cu_price_micro: int | None) -> Dict[str, Any]:
    funded = []
    for w in plan.wallets:
        if w.role == "SEED":
            continue
        pub = wallet_map[w.wallet_id]["pub"]
        # Idempotent: if already funded >= target, skip
        bal = await rpc.get_balance(pub)
        if bal >= w.funding.total_lamports:
            funded.append({"wallet_id": w.wallet_id, "skipped": True, "reason": "already_funded"})
            continue
        sig = await _transfer(rpc, seed_kp, pub, w.funding.total_lamports - bal, cu_limit, cu_price_micro)
        funded.append({"wallet_id": w.wallet_id, "lamports": w.funding.total_lamports, "sig": sig})
    return {"funded": funded}
