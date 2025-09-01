"""Token mint creation and initial distribution."""

from __future__ import annotations

from typing import Any, Dict

from src.core.ata import ata
from src.core.spl_token import create_mint_and_mint_to
from src.core.solana import Rpc


async def run(
    rpc: Rpc,
    payer_kp,
    lp_creator_pub: str,
    decimals: int,
    amount: int,
) -> Dict[str, Any]:
    """Create a new SPL mint and mint ``amount`` tokens to ``lp_creator_pub``."""

    client = rpc.client
    mint, lp_creator_ata, _ = await create_mint_and_mint_to(
        client,
        payer_kp,
        decimals,
        lp_creator_pub,
        lp_creator_pub,
        amount,
    )
    return {
        "mint": mint,
        "lp_creator_ata": lp_creator_ata,
        "minted_tokens": amount,
    }

