from __future__ import annotations
from typing import Dict, Any
from solana.transaction import Transaction
from src.core.metaplex import build_create_metadata_v3
from src.core.tx import with_compute_budget
from src.core.solana import Rpc


async def run(rpc: Rpc, metadata_program: str, mint: str, mint_authority_kp, payer_kp, update_authority: str, name: str, symbol: str, uri: str | None, cu_limit: int | None, cu_price_micro: int | None, simulate: bool = False) -> Dict[str, Any]:
    ix = build_create_metadata_v3(metadata_program=metadata_program, mint=mint, mint_authority=str(mint_authority_kp.pubkey()), payer=str(payer_kp.pubkey()), update_authority=update_authority, name=name, symbol=symbol, uri=uri or "")
    tx = Transaction()
    with_compute_budget(tx, cu_limit, cu_price_micro)
    tx.add(ix)
    tx.recent_blockhash = await rpc.recent_blockhash()
    if simulate:
        sim = await rpc.simulate(tx, payer_kp, mint_authority_kp)
        return {"simulated": True, "logs": sim.get("logs")}
    sig = await rpc.send_and_confirm(tx, payer_kp, mint_authority_kp)
    return {"tx_sig": sig}
