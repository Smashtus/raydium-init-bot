from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any

LAMPORTS_PER_SOL = 1_000_000_000

@dataclass
class Token:
    total_mint: int
    lp_tokens: int
    name: str
    symbol: str
    decimals: int
    authorities: Dict[str, str] = field(default_factory=dict)
    uri: Optional[str] = None
    mint_metadata: Optional[str] = None

@dataclass
class Inputs:
    B_total: float
    T0: float
    q_atomic: float
    n_buys: int
    follow_ratio: float
    fee: float
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
    network: Optional[str] = None
    deps: Dict[str, Any] = field(default_factory=dict)
    openbook_params: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Funding:
    total_lamports: int
    base_lamports: int
    buffer_lamports: int

    @staticmethod
    def _sol2lam(x: float | int | None) -> Optional[int]:
        if x is None:
            return None
        return int(round(float(x) * LAMPORTS_PER_SOL))

    @staticmethod
    def from_dict(raw: Dict[str, Any]) -> "Funding":
        tl = raw.get("total_lamports")
        bl = raw.get("base_lamports")
        bufl = raw.get("buffer_lamports")
        if tl is None and "total_sol" in raw:
            tl = Funding._sol2lam(raw.get("total_sol"))
        if bl is None:
            bl = raw.get("base_lamports")
            if bl is None and "base_sol" in raw:
                bl = Funding._sol2lam(raw.get("base_sol"))
            if bl is None: bl = 0
        if bufl is None:
            bufl = raw.get("buffer_lamports")
            if bufl is None and "buffer_sol" in raw:
                bufl = Funding._sol2lam(raw.get("buffer_sol"))
            if bufl is None: bufl = 0
        if tl is None:
            tl = int(bl) + int(bufl)
        return Funding(total_lamports=int(tl), base_lamports=int(bl), buffer_lamports=int(bufl))

@dataclass
class Action:
    type: str
    effective_base_sol: float = 0.0
    min_out_tokens: int = 0
    slippage_bps: int = 50
    atomic: bool = False
    gross_base_sol: Optional[float] = None
    tokens_to_lp: Optional[int] = None
    raydium_program_id: Optional[str] = None
    quote_mint: Optional[str] = None
    pool_init_slippage_bps: Optional[int] = None

@dataclass
class Wallet:
    wallet_id: str
    role: str
    funding: Funding
    action: Optional[Action] = None
    index: Optional[int] = None
    name: Optional[str] = None
    actions: List[Action] = field(default_factory=list)

@dataclass
class Invariants:
    sum_non_seed_lamports: int
    seed_lamports: int
    expected_equalities: List[str] = field(default_factory=list)
    atomic_tokens: Optional[int] = None

@dataclass
class Plan:
    version: str
    model: str
    network: str
    plan_id: str
    created_at: str
    token: Token
    inputs: Inputs
    dex: Dex
    schedule: List[str]
    wallets: List[Wallet]
    invariants: Invariants
    tx_defaults: Dict[str, int]

    @staticmethod
    def from_dict(raw: Dict[str, Any]) -> "Plan":
        tok = dict(raw["token"])
        if tok.get("mint_metadata") and not tok.get("uri"):
            tok["uri"] = tok["mint_metadata"]
        token = Token(**tok)
        inputs = Inputs(**raw["inputs"])
        dex = Dex(**raw["dex"])
        wallets: List[Wallet] = []
        for w in raw["wallets"]:
            funding = Funding.from_dict(w["funding"])
            action = Action(**w["action"]) if w.get("action") else None
            actions = [Action(**a) for a in w.get("actions", [])]
            wallets.append(Wallet(wallet_id=w["wallet_id"], role=w["role"], funding=funding, action=action, actions=actions, index=w.get("index"), name=w.get("name")))
        inv = Invariants(**raw["invariants"])
        plan = Plan(version=raw["version"], model=raw["model"], network=raw["network"], plan_id=raw["plan_id"], created_at=raw["created_at"], token=token, inputs=inputs, dex=dex, schedule=raw["schedule"], wallets=wallets, invariants=inv, tx_defaults=raw["tx_defaults"])
        plan.validate()
        return plan

    def validate(self) -> None:
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
        if self.token.lp_tokens != int(self.inputs.T0):
            raise ValueError("token.lp_tokens must equal inputs.T0")
        lpw = next((w for w in self.wallets if w.role == "LP_CREATOR"), None)
        if not lpw:
            raise ValueError("missing LP_CREATOR wallet")
        has_create_lp = (lpw.action and lpw.action.type == "CREATE_LP") or any(a.type == "CREATE_LP" for a in lpw.actions)
        if not has_create_lp:
            raise ValueError("LP_CREATOR must contain a CREATE_LP action")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
