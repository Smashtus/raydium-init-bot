from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from src.models.plan import Plan
from src.util.state import State, StepReceipt
from src.exec.invariants import assert_plan_invariants
from src.exec import funding, minting, pool_init, swaps

STEPS_ORDER = ["funding","mint","metadata","lp_init","buys"]


@dataclass
class RunConfig:
    out_dir: Path
    resume: bool
    only: str  # one of STEPS_ORDER or "all"
    plan_hash: str | None = None


def _selected(step: str, only: str) -> bool:
    return only == "all" or (only == "lp" and step == "lp_init") or (only == step)


def execute(plan: Plan, cfg: RunConfig) -> None:
    state = State(cfg.out_dir)
    assert_plan_invariants(plan)

    # FUNDING
    if _selected("funding", cfg.only):
        if not (cfg.resume and state.done("funding")):
            f_out = funding.run(plan)  # stubbed, deterministic
            state.mark("funding", StepReceipt(step="funding", ok=True, inputs={"wallets": len(plan.wallets)}, outputs=f_out, plan_hash=cfg.plan_hash))
            state.merge_artifacts({"funding": f_out})

    # MINT
    if _selected("mint", cfg.only):
        if cfg.resume and state.done("mint") and "mint" in state.artifacts:
            m_out = state.artifacts["mint"]
        else:
            m_out = minting.run(plan)
            state.mark("mint", StepReceipt(step="mint", ok=True, inputs={"lp_tokens": plan.token.lp_tokens}, outputs=m_out, plan_hash=cfg.plan_hash))
            state.merge_artifacts({"mint": m_out})
    else:
        m_out = state.artifacts.get("mint", minting.run(plan))
        state.merge_artifacts({"mint": m_out})

    # METADATA
    if _selected("metadata", cfg.only):
        if not (cfg.resume and state.done("metadata")):
            md = {"name": plan.token.name, "symbol": plan.token.symbol, "uri": plan.token.uri, "tx_sig": f"FAKE_SIG_META_{plan.plan_id}"}
            state.mark("metadata", StepReceipt(step="metadata", ok=True, inputs={"mint": m_out["mint"]}, outputs=md, plan_hash=cfg.plan_hash))
            state.merge_artifacts({"metadata": md})

    # LP INIT
    if _selected("lp_init", cfg.only):
        if cfg.resume and state.done("lp_init") and "lp_init" in state.artifacts:
            lp = state.artifacts["lp_init"]
        else:
            lp = pool_init.run(plan, mint_addr=m_out["mint"])
            state.mark("lp_init", StepReceipt(step="lp_init", ok=True, inputs={"mint": m_out["mint"]}, outputs=lp, plan_hash=cfg.plan_hash))
            state.merge_artifacts({"lp_init": lp})

    # BUYS
    if _selected("buys", cfg.only):
        if not (cfg.resume and state.done("buys")):
            b = swaps.run(plan)
            state.mark("buys", StepReceipt(step="buys", ok=True, inputs={"schedule_len": len(plan.schedule)}, outputs=b, plan_hash=cfg.plan_hash))
            state.merge_artifacts({"buys": b})

