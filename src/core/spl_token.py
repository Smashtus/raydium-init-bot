"""Helpers for interacting with the SPL Token program.

The functions here perform common mint / ATA operations.  They are thin
wrappers over the ``spl.token`` helpers but are written in an asynchronous
style to match the rest of the launcher.  As with other modules in this patch
the imports are optional so that unit tests can execute without pulling in the
entire Solana python stack.
"""

from __future__ import annotations

from typing import Tuple

try:  # pragma: no cover - exercised only when solana dependencies are available
    from solders.pubkey import Pubkey
    from spl.token.client import Token
    from spl.token.constants import (
        TOKEN_PROGRAM_ID,
        ASSOCIATED_TOKEN_ACCOUNT_PROGRAM_ID,
    )
    from solana.rpc.async_api import AsyncClient
    from solana.transaction import Transaction
    from spl.token.instructions import (
        create_associated_token_account,
        mint_to,
        initialize_mint,
    )
except Exception:  # pragma: no cover - fallback stubs for test environment
    Pubkey = object  # type: ignore
    Token = object  # type: ignore
    TOKEN_PROGRAM_ID = ASSOCIATED_TOKEN_ACCOUNT_PROGRAM_ID = object  # type: ignore
    AsyncClient = Transaction = object  # type: ignore

    def create_associated_token_account(*_a, **_k):  # type: ignore
        raise RuntimeError("spl.token library not available")

    def mint_to(*_a, **_k):  # type: ignore
        raise RuntimeError("spl.token library not available")

    def initialize_mint(*_a, **_k):  # type: ignore
        raise RuntimeError("spl.token library not available")


async def create_mint_and_mint_to(
    client: AsyncClient,
    payer_kp,
    decimals: int,
    mint_authority: str,
    dest_owner: str,
    amount: int,
) -> Tuple[str, str, Transaction]:
    """Create a new SPL mint and mint ``amount`` tokens to ``dest_owner``.

    Returns a tuple ``(mint_pub, ata, tx)`` where ``tx`` contains the minting
    instruction so that callers can inspect or modify the transaction if
    necessary.
    """

    token = await Token.create_mint(
        client,
        payer_kp,
        Pubkey.from_string(mint_authority),
        None,
        decimals,
        TOKEN_PROGRAM_ID,
    )
    mint_pub = token.pubkey
    ata = await token.create_associated_token_account(Pubkey.from_string(dest_owner))
    tx = Transaction()
    await token.mint_to(ata, Pubkey.from_string(mint_authority), payer_kp, amount)
    return str(mint_pub), str(ata), tx


async def wrap_sol(
    client: AsyncClient, payer_kp, owner: str, amount: int
) -> Tuple[str, Transaction]:
    """Wrap lamports into a temporary WSOL account owned by ``owner``."""

    from solana.transaction import Transaction
    from solana.system_program import transfer, TransferParams

    wsol_account = Pubkey.create_with_seed(
        Pubkey.from_string(owner),
        "wsol",
        TOKEN_PROGRAM_ID,
    )
    tx = Transaction()
    tx.add(
        transfer(
            TransferParams(
                from_pubkey=payer_kp.pubkey(),
                to_pubkey=wsol_account,
                lamports=amount,
            )
        )
    )
    return str(wsol_account), tx

