from __future__ import annotations
from typing import Dict, Any
from src.models.plan import Plan
from src.core.solana import Rpc
from src.core.ata import ata
from spl.token.client import Token
from solders.pubkey import Pubkey
from spl.token.constants import TOKEN_PROGRAM_ID


async def run(rpc: Rpc, payer_kp, lp_creator_pub: str, decimals: int, amount: int) -> Dict[str, Any]:
    # If artifacts already contain a mint, caller should pass it and skip
    client = rpc.client
    token = await Token.create_mint(client, payer_kp, Pubkey.from_string(lp_creator_pub), None, decimals, TOKEN_PROGRAM_ID)
    mint_pub = token.pubkey
    ata_addr = await token.create_associated_token_account(Pubkey.from_string(lp_creator_pub))
    await token.mint_to(ata_addr, Pubkey.from_string(lp_creator_pub), payer_kp, amount)
    return {"mint": str(mint_pub), "lp_creator_ata": str(ata_addr), "minted_tokens": amount}
