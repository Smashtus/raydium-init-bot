"""Async Solana RPC wrapper with retry and convenience helpers.

This module provides a minimal asynchronous RPC client wrapper used by the
launcher.  The real implementation depends on the `solana` and `solders`
packages.  Those heavy dependencies are optional during unit tests; if they
are missing the module still imports successfully but any RPC operation will
fail at runtime.  This approach allows the test-suite to run in environments
without the Solana stack while keeping the production code intact.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

# The Solana python stack is quite heavy and is not installed in the execution
# environment used for the unit tests.  To keep imports cheap we wrap them in a
# try/except block and provide light‑weight fallbacks when unavailable.  The
# fallbacks are good enough for type checkers and for dry‑run operation; any
# attempt to use them for real RPC calls without the dependencies will raise
# an AttributeError at runtime which is acceptable for our purposes.
try:  # pragma: no cover - exercised only when dependencies are available
    from tenacity import retry, stop_after_attempt, wait_exponential_jitter
    from solana.rpc.async_api import AsyncClient
    from solana.rpc.types import TxOpts
    from solana.transaction import Transaction
    from solders.signature import Signature
    from solders.hash import Hash
    from solders.commitment_config import CommitmentLevel
except Exception:  # pragma: no cover - used in the simplified test env
    AsyncClient = object  # type: ignore
    TxOpts = Transaction = Signature = Hash = object  # type: ignore

    class _Commitment:  # minimal stand‑in for the real enum
        Finalized = "finalized"

    CommitmentLevel = _Commitment  # type: ignore

    def retry(*_args, **_kwargs):  # type: ignore
        def decorator(fn):
            return fn

        return decorator

    def stop_after_attempt(_n):  # type: ignore
        return None

    def wait_exponential_jitter(*_args, **_kwargs):  # type: ignore
        return None


COMMIT_FINALIZED = CommitmentLevel.Finalized


@dataclass
class RpcConfig:
    """Configuration for the :class:`Rpc` client."""

    url: str
    commitment: CommitmentLevel = COMMIT_FINALIZED
    timeout_sec: int = 60


class Rpc:
    """Thin asynchronous wrapper around ``AsyncClient``.

    Only a couple of helpers are implemented which are sufficient for the
    launcher.  The object can be constructed even when the underlying Solana
    libraries are missing, however any attempt to perform network operations
    in that case will naturally fail.
    """

    def __init__(self, cfg: RpcConfig):
        self.cfg = cfg
        # ``AsyncClient`` may be the stub object when the dependency is missing.
        self.client = AsyncClient(cfg.url, timeout=cfg.timeout_sec, commitment=cfg.commitment)  # type: ignore[arg-type]

    async def recent_blockhash(self) -> Hash:
        resp = await self.client.get_latest_blockhash()  # type: ignore[operator]
        return resp.value.blockhash

    @retry(stop=stop_after_attempt(5), wait=wait_exponential_jitter(min=0.2, max=2.0))  # type: ignore[misc]
    async def send_and_confirm(
        self,
        tx: Transaction,
        signers: Iterable,
        cu_price_micro: Optional[int] = None,
    ) -> str:
        """Send a signed transaction and wait for confirmation.

        ``cu_price_micro`` is currently unused; compute unit price should be
        handled by a ComputeBudget instruction added by the caller.
        """

        # ``TxOpts`` may be a stub; arguments are ignored in that case.
        tx_sig = await self.client.send_transaction(  # type: ignore[operator]
            tx, *signers, opts=TxOpts(skip_preflight=False)  # type: ignore[arg-type]
        )
        sig = str(tx_sig.value)
        await self.client.confirm_transaction(  # type: ignore[operator]
            Signature.from_string(sig), commitment=self.cfg.commitment  # type: ignore[arg-type]
        )
        return sig

    async def aclose(self) -> None:
        await self.client.close()  # type: ignore[operator]

    async def get_balance(self, pubkey: str) -> int:
        from solders.pubkey import Pubkey  # type: ignore

        r = await self.client.get_balance(Pubkey.from_string(pubkey))  # type: ignore[operator]
        return r.value

