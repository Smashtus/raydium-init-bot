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
    plan_hash: str | None = None


def _should_run(step: str, cfg: RunConfig) -> bool:
    if cfg.only == "all":
        return True
    alias = "lp_init" if cfg.only == "lp" else cfg.only
    return alias == step


def execute(plan: Plan, cfg: RunConfig) -> None:
    state = State(cfg.out_dir)
    assert_plan_invariants(plan)

    # FUNDING
    if _should_run("funding", cfg) and (not cfg.resume or not state.done("funding")):
        f_out = funding.run(plan)
        state.mark("funding", StepReceipt(step="funding", ok=True, inputs={"wallets": len(plan.wallets)}, outputs=f_out, plan_hash=cfg.plan_hash))
        state.merge_artifacts({"funding": f_out})

    # MINT
    mint_out = state.artifacts.get("mint")
    if not mint_out and _should_run("mint", cfg) and (not cfg.resume or not state.done("mint")):
        mint_out = minting.run(plan)
        state.mark("mint", StepReceipt(step="mint", ok=True, inputs={"lp_tokens": plan.token.lp_tokens}, outputs=mint_out, plan_hash=cfg.plan_hash))
        state.merge_artifacts({"mint": mint_out})
    elif not mint_out:
        # compute but also persist for downstream steps to read
        mint_out = minting.run(plan)
        state.merge_artifacts({"mint": mint_out})

    # METADATA
    if _should_run("metadata", cfg) and (not cfg.resume or not state.done("metadata")):
        md = {"name": plan.token.name, "symbol": plan.token.symbol, "uri": plan.token.uri, "tx_sig": f"FAKE_SIG_META_{plan.plan_id}"}
        state.mark("metadata", StepReceipt(step="metadata", ok=True, inputs={"mint": mint_out["mint"]}, outputs=md, plan_hash=cfg.plan_hash))
        state.merge_artifacts({"metadata": md})

    # LP INIT
    lp_out = state.artifacts.get("lp_init")
    if not lp_out and _should_run("lp_init", cfg) and (not cfg.resume or not state.done("lp_init")):
        lp_out = pool_init.run(plan, mint_addr=mint_out["mint"])
        state.mark("lp_init", StepReceipt(step="lp_init", ok=True, inputs={"mint": mint_out["mint"]}, outputs=lp_out, plan_hash=cfg.plan_hash))
        state.merge_artifacts({"lp_init": lp_out})
    elif not lp_out:
        lp_out = pool_init.run(plan, mint_addr=mint_out["mint"])
        state.merge_artifacts({"lp_init": lp_out})

    # BUYS
    if _should_run("buys", cfg) and (not cfg.resume or not state.done("buys")):
        b = swaps.run(plan)
        state.mark("buys", StepReceipt(step="buys", ok=True, inputs={"schedule_len": len(plan.schedule)}, outputs=b, plan_hash=cfg.plan_hash))
        state.merge_artifacts({"buys": b})
