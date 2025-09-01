"""Create Metaplex token metadata."""

from __future__ import annotations

from typing import Any, Dict

from solana.transaction import Transaction

from src.core.metaplex import build_create_metadata_v3
from src.core.solana import Rpc


async def run(
    rpc: Rpc,
    metadata_program: str,
    mint: str,
    mint_authority_kp,
    payer_kp,
    update_authority: str,
    name: str,
    symbol: str,
    uri: str | None,
) -> Dict[str, Any]:
    """Create metadata for ``mint`` using the Metaplex Token Metadata program."""

    ix = build_create_metadata_v3(
        metadata_program=metadata_program,
        mint=mint,
        mint_authority=str(mint_authority_kp.pubkey()),
        payer=str(payer_kp.pubkey()),
        update_authority=update_authority,
        name=name,
        symbol=symbol,
        uri=uri or "",
    )
    tx = Transaction()
    tx.add(ix)
    tx.recent_blockhash = await rpc.recent_blockhash()
    tx.sign(payer_kp, mint_authority_kp)
    sig = await rpc.send_and_confirm(tx, [payer_kp, mint_authority_kp])
    return {"tx_sig": sig}

