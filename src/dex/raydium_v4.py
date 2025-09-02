"""Minimal Raydium v4 CPMM instruction builders.

The real Raydium helper library performs a considerable amount of PDA
derivation and binary packing.  For the purposes of the launcher we only need a
very small subset which is implemented here using the ``solders`` primitives.
The builders are intentionally light‑weight but deterministic so that higher
level orchestration code can be exercised in unit tests without a live Solana
connection.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from solders.pubkey import Pubkey
from solders.instruction import Instruction, AccountMeta


@dataclass
class PoolAccounts:
    pool: str
    authority: str
    lp_mint: str
    vault_base: str
    vault_quote: str
    open_orders: str
    target_orders: str
    amm_config: str


def _pda(seeds: List[bytes], program_id: Pubkey) -> Pubkey:
    (pda, _bump) = Pubkey.find_program_address(seeds, program_id)
    return pda


def derive_pool_accounts(base_mint: str, quote_mint: str, program_id: str) -> PoolAccounts:
    """Derive PDAs for the core Raydium pool accounts."""

    pid = Pubkey.from_string(program_id)
    base = Pubkey.from_string(base_mint)
    quote = Pubkey.from_string(quote_mint)

    pool = _pda([b"amm", base.to_bytes(), quote.to_bytes()], pid)
    authority = _pda([b"authority", pool.to_bytes()], pid)
    lp_mint = _pda([b"lp_mint", pool.to_bytes()], pid)
    vault_base = _pda([b"vault_base", pool.to_bytes()], pid)
    vault_quote = _pda([b"vault_quote", pool.to_bytes()], pid)
    open_orders = _pda([b"open_orders", pool.to_bytes()], pid)
    target_orders = _pda([b"target_orders", pool.to_bytes()], pid)
    amm_config = _pda([b"amm_config", base.to_bytes(), quote.to_bytes()], pid)

    return PoolAccounts(
        pool=str(pool),
        authority=str(authority),
        lp_mint=str(lp_mint),
        vault_base=str(vault_base),
        vault_quote=str(vault_quote),
        open_orders=str(open_orders),
        target_orders=str(target_orders),
        amm_config=str(amm_config),
    )


def build_initialize2(
    program_id: str,
    base_mint: str,
    quote_mint: str,
    lp_creator_pub: str,
    tokens_to_lp: int,
) -> List[Instruction]:
    """Return instructions for Raydium's ``initialize2`` helper."""

    acc = derive_pool_accounts(base_mint, quote_mint, program_id)
    pid = Pubkey.from_string(program_id)
    metas = [
        AccountMeta(Pubkey.from_string(acc.pool), False, True),
        AccountMeta(Pubkey.from_string(acc.authority), False, False),
        AccountMeta(Pubkey.from_string(acc.lp_mint), False, True),
        AccountMeta(Pubkey.from_string(acc.vault_base), False, True),
        AccountMeta(Pubkey.from_string(acc.vault_quote), False, True),
        AccountMeta(Pubkey.from_string(base_mint), False, False),
        AccountMeta(Pubkey.from_string(quote_mint), False, False),
        AccountMeta(Pubkey.from_string(acc.open_orders), False, True),
        AccountMeta(Pubkey.from_string(acc.target_orders), False, True),
        AccountMeta(Pubkey.from_string(acc.amm_config), False, False),
        AccountMeta(Pubkey.from_string(lp_creator_pub), True, True),
    ]

    data = tokens_to_lp.to_bytes(8, "little")
    ix = Instruction(pid, metas, b"\x00" + data)
    return [ix]


def build_swap_SOL_to_base(
    program_id: str,
    accounts: PoolAccounts,
    user_pub: str,
    in_lamports: int,
    min_out: int,
    slippage_bps: int,
) -> List[Instruction]:
    """Construct a direct SOL→base token swap instruction list."""

    pid = Pubkey.from_string(program_id)
    metas = [
        AccountMeta(Pubkey.from_string(accounts.pool), False, True),
        AccountMeta(Pubkey.from_string(accounts.vault_base), False, True),
        AccountMeta(Pubkey.from_string(accounts.vault_quote), False, True),
        AccountMeta(Pubkey.from_string(user_pub), True, True),
    ]
    data = (
        b"\x01" + in_lamports.to_bytes(8, "little") + min_out.to_bytes(8, "little") + slippage_bps.to_bytes(2, "little")
    )
    return [Instruction(pid, metas, data)]


async def probe_pool_exists(rpc, accounts: PoolAccounts) -> bool:
    """Check whether the pool account already exists on chain."""

    return await rpc.account_exists(accounts.pool)

