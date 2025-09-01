from __future__ import annotations
from solders.instruction import Instruction
from solders.pubkey import Pubkey
from solana.transaction import Transaction
from solana.system_program import TransferParams, transfer
from solders.compute_budget import set_compute_unit_limit, set_compute_unit_price


def with_compute_budget(tx: Transaction, cu_limit: int | None, cu_price_micro: int | None) -> Transaction:
    if cu_limit:
        tx.add(Instruction.from_bytes(set_compute_unit_limit(cu_limit).to_bytes()))
    if cu_price_micro:
        tx.add(Instruction.from_bytes(set_compute_unit_price(cu_price_micro).to_bytes()))
    return tx


def with_tip(tx: Transaction, tip_to: str | None, lamports: int | None, payer_pub: str | None) -> Transaction:
    if tip_to and lamports and lamports > 0 and payer_pub:
        tx.add(transfer(TransferParams(
            from_pubkey=Pubkey.from_string(payer_pub),
            to_pubkey=Pubkey.from_string(tip_to),
            lamports=lamports
        )))
    return tx
