from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class Token:
    total_mint: int
    lp_tokens: int
    name: str
    symbol: str
    decimals: int
    authorities: Dict[str, str] = field(default_factory=dict)
    uri: Optional[str] = None


@dataclass
class Inputs:
    B_total: int
    T0: int
    q_atomic: int
    n_buys: int
    follow_ratio: float
    fee: int
    mm_pct: float
    buffer_pct: float
    snap_lamports: bool = False


@dataclass
class Dex:
    variant: str
    program_id: str
    pool_type: str
    quote_mint: str
    quote_decimals: int


@dataclass
class Funding:
    total_lamports: int
    base_lamports: int = 0
    buffer_lamports: int = 0


@dataclass
class Action:
    type: str
    effective_base_sol: Optional[int] = None
    min_out_tokens: Optional[int] = None
    slippage_bps: Optional[int] = None


@dataclass
class Wallet:
    wallet_id: str
    role: str
    funding: Funding
    action: Optional[Action] = None


@dataclass
class Invariants:
    sum_non_seed_lamports: int
    seed_lamports: int
    expected_equalities: List[str] = field(default_factory=list)


@dataclass
class TxDefaults:
    compute_unit_limit: int
    compute_unit_price_micro_lamports: int
    jito_tip_lamports: int


@dataclass
class Plan:
    version: str
    model: str
    network: str
    plan_id: str
    created_at: datetime
    token: Token
    inputs: Inputs
    dex: Dex
    schedule: List[str]
    wallets: List[Wallet]
    invariants: Invariants
    tx_defaults: TxDefaults

    @staticmethod
    def from_dict(raw: Dict) -> "Plan":
        token = Token(**raw["token"])
        inputs = Inputs(**raw["inputs"])
        dex = Dex(**raw["dex"])
        wallets: List[Wallet] = []
        for w in raw["wallets"]:
            funding = Funding(**w["funding"])
            action = Action(**w["action"]) if w.get("action") else None
            wallets.append(Wallet(wallet_id=w["wallet_id"], role=w["role"], funding=funding, action=action))
        invariants = Invariants(**raw["invariants"])
        tx_defaults = TxDefaults(**raw["tx_defaults"])
        plan = Plan(
            version=raw["version"],
            model=raw["model"],
            network=raw["network"],
            plan_id=raw["plan_id"],
            created_at=datetime.fromisoformat(raw["created_at"].replace("Z", "+00:00")),
            token=token,
            inputs=inputs,
            dex=dex,
            schedule=list(raw["schedule"]),
            wallets=wallets,
            invariants=invariants,
            tx_defaults=tx_defaults,
        )
        plan.validate()
        return plan

    def validate(self) -> None:
        if self.token.lp_tokens != self.inputs.T0:
            raise ValueError("token.lp_tokens must equal inputs.T0")
        non_seed = sum(w.funding.total_lamports for w in self.wallets if w.role != "SEED")
        if non_seed != self.invariants.sum_non_seed_lamports:
            raise ValueError("sum_non_seed_lamports mismatch")
        tol = 1 if self.inputs.snap_lamports else 0
        if abs(non_seed - self.invariants.seed_lamports) > tol:
            raise ValueError("seed lamports invariant violated")
        ids = [w.wallet_id for w in self.wallets]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate wallet_id in wallets")
        missing = set(self.schedule) - set(ids)
        if missing:
            raise ValueError(f"schedule references unknown wallet ids: {missing}")


__all__ = ["Plan", "Plan.from_dict"]
