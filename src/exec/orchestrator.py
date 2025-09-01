from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
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

def _should_run(step: str, cfg: RunConfig) -> bool:
    if cfg.only == "all":
        return True
    return cfg.only == step or (cfg.only == "buys" and step == "buys")

def execute(plan: Plan, cfg: RunConfig) -> None:
    state = State(cfg.out_dir)
    assert_plan_invariants(plan)

    # FUNDING
    if _should_run("funding", cfg) and (cfg.resume is False or not state.done("funding")):
        f_out = funding.run(plan)
        state.mark("funding", StepReceipt(step="funding", ok=True, inputs={"wallets": len(plan.wallets)}, outputs=f_out))

    # MINT
    if _should_run("mint", cfg) and (cfg.resume is False or not state.done("mint")):
        m_out = minting.run(plan)
        state.mark("mint", StepReceipt(step="mint", ok=True, inputs={"lp_tokens": plan.token.lp_tokens}, outputs=m_out))
    else:
        # If resuming, try to read the mint from prior artifacts (not implemented yet). For now, recompute.
        m_out = minting.run(plan)

    # METADATA
    if _should_run("metadata", cfg) and (cfg.resume is False or not state.done("metadata")):
        md = {
            "name": plan.token.name,
            "symbol": plan.token.symbol,
            "uri": plan.token.uri,
            "tx_sig": f"FAKE_SIG_META_{plan.plan_id}",
        }
        state.mark("metadata", StepReceipt(step="metadata", ok=True, inputs={"mint": m_out["mint"]}, outputs=md))

    # LP INIT
    if _should_run("lp_init", cfg) and (cfg.resume is False or not state.done("lp_init")):
        lp = pool_init.run(plan, mint_addr=m_out["mint"])
        state.mark("lp_init", StepReceipt(step="lp_init", ok=True, inputs={"mint": m_out["mint"]}, outputs=lp))

    # BUYS
    if _should_run("buys", cfg) and (cfg.resume is False or not state.done("buys")):
        b = swaps.run(plan)
        state.mark("buys", StepReceipt(step="buys", ok=True, inputs={"schedule_len": len(plan.schedule)}, outputs=b))
