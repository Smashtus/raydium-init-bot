from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Iterable, Any
from tenacity import retry, stop_after_attempt, wait_exponential_jitter
from solana.rpc.async_api import AsyncClient
from solana.rpc.types import TxOpts
from solana.transaction import Transaction
from solders.signature import Signature
from solders.commitment_config import CommitmentLevel
from solders.hash import Hash
import asyncio

COMMIT_FINALIZED = CommitmentLevel.Finalized

@dataclass
class RpcConfig:
    url: str
    commitment: CommitmentLevel = COMMIT_FINALIZED
    timeout_sec: int = 60

class Rpc:
    def __init__(self, cfg: RpcConfig):
        self.cfg = cfg
        self.client = AsyncClient(cfg.url, timeout=cfg.timeout_sec, commitment=cfg.commitment)

    async def close(self):
        await self.client.close()

    async def recent_blockhash(self) -> Hash:
        resp = await self.client.get_latest_blockhash()
        return resp.value.blockhash

    async def simulate(self, tx: Transaction, *signers: Any) -> dict:
        # NOTE: preflight simulate; signers used to sign the tx first
        if signers:
            tx.sign(*signers)
        sim = await self.client.simulate_transaction(tx)
        return sim.value.__dict__ if hasattr(sim, "value") else {}

    @retry(stop=stop_after_attempt(5), wait=wait_exponential_jitter(min=0.2, max=2.0))
    async def send_and_confirm(self, tx: Transaction, *signers: Any) -> str:
        if signers:
            tx.sign(*signers)
        resp = await self.client.send_transaction(tx, *signers, opts=TxOpts(skip_preflight=False))
        sig = str(resp.value)
        await self.client.confirm_transaction(Signature.from_string(sig), commitment=self.cfg.commitment)
        return sig

    # Minimal helpers for idempotency checks
    async def account_exists(self, pubkey: str) -> bool:
        from solders.pubkey import Pubkey
        info = await self.client.get_account_info(Pubkey.from_string(pubkey))
        return info.value is not None

    async def get_balance(self, pubkey: str) -> int:
        from solders.pubkey import Pubkey
        r = await self.client.get_balance(Pubkey.from_string(pubkey))
        return r.value
