"""Top level orchestration of plan execution.

The real project executes a series of on‑chain operations such as funding
wallets, minting tokens and creating pools.  In the educational setting we keep
the dry‑run behaviour used in the unit tests while also providing an optional
"live" path that delegates to the modules implemented in this patch.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.models.plan import Plan
from src.util.state import State, StepReceipt
from src.exec.invariants import assert_plan_invariants


STEPS_ORDER = ["funding", "mint", "metadata", "lp_init", "buys"]


@dataclass
class RunConfig:
    out_dir: Path
    resume: bool
    only: str  # one of STEPS_ORDER or "all"
    plan_hash: str | None = None


def _selected(step: str, only: str) -> bool:
    return only == "all" or (only == "lp" and step == "lp_init") or (only == step)


def _execute_stub(plan: Plan, cfg: RunConfig) -> None:
    """Reproduce the deterministic behaviour of the original stubs.

    This path is used for dry‑run unit tests.  No Solana libraries are required
    and no network calls are performed.
    """

    state = State(cfg.out_dir)
    assert_plan_invariants(plan)

    # FUNDING
    if _selected("funding", cfg.only):
        if not (cfg.resume and state.done("funding")):
            summary = []
            for w in plan.wallets:
                if w.role == "SEED":
                    continue
                summary.append(
                    {
                        "wallet_id": w.wallet_id,
                        "role": w.role,
                        "funded_lamports": w.funding.total_lamports,
                        "tx_sig": f"FAKE_SIG_{w.wallet_id}",
                    }
                )
            f_out = {"funded": summary, "seed_wallet": next(w.wallet_id for w in plan.wallets if w.role == "SEED")}
            state.mark(
                "funding",
                StepReceipt(
                    step="funding",
                    ok=True,
                    inputs={"wallets": len(plan.wallets)},
                    outputs=f_out,
                    plan_hash=cfg.plan_hash,
                ),
            )
            state.merge_artifacts({"funding": f_out})

    # MINT
    if _selected("mint", cfg.only):
        if cfg.resume and state.done("mint") and "mint" in state.artifacts:
            m_out = state.artifacts["mint"]
        else:
            fake_mint = f"MINT_{plan.plan_id}"
            lp_creator = next(w for w in plan.wallets if w.role == "LP_CREATOR").wallet_id
            m_out = {
                "mint": fake_mint,
                "lp_creator_ata": f"ATA_{fake_mint}_{lp_creator}",
                "minted_tokens": plan.token.lp_tokens,
                "tx_sig": f"FAKE_SIG_MINT_{plan.plan_id}",
            }
            state.mark(
                "mint",
                StepReceipt(
                    step="mint",
                    ok=True,
                    inputs={"lp_tokens": plan.token.lp_tokens},
                    outputs=m_out,
                    plan_hash=cfg.plan_hash,
                ),
            )
            state.merge_artifacts({"mint": m_out})
    else:
        m_out = state.artifacts.get("mint", {})

    # METADATA
    if _selected("metadata", cfg.only):
        if not (cfg.resume and state.done("metadata")):
            md = {
                "name": plan.token.name,
                "symbol": plan.token.symbol,
                "uri": plan.token.uri,
                "tx_sig": f"FAKE_SIG_META_{plan.plan_id}",
            }
            state.mark(
                "metadata",
                StepReceipt(
                    step="metadata",
                    ok=True,
                    inputs={"mint": m_out.get("mint")},
                    outputs=md,
                    plan_hash=cfg.plan_hash,
                ),
            )
            state.merge_artifacts({"metadata": md})

    # LP INIT
    if _selected("lp_init", cfg.only):
        if cfg.resume and state.done("lp_init") and "lp_init" in state.artifacts:
            lp = state.artifacts["lp_init"]
        else:
            pool_id = f"POOL_{plan.plan_id}"
            lp = {
                "pool": pool_id,
                "vault_base": f"VAULT_BASE_{pool_id}",
                "vault_quote": f"VAULT_QUOTE_{pool_id}",
                "lp_mint": f"LP_{pool_id}",
                "tx_sig": f"FAKE_SIG_POOL_{pool_id}",
                "tokens_to_lp": plan.token.lp_tokens,
            }
            state.mark(
                "lp_init",
                StepReceipt(
                    step="lp_init",
                    ok=True,
                    inputs={"mint": m_out.get("mint")},
                    outputs=lp,
                    plan_hash=cfg.plan_hash,
                ),
            )
            state.merge_artifacts({"lp_init": lp})

    # BUYS
    if _selected("buys", cfg.only):
        if not (cfg.resume and state.done("buys")):
            results = []
            idx = 0
            for wid in plan.schedule:
                w = next(w for w in plan.wallets if w.wallet_id == wid)
                if not w.action or w.action.type not in ("SWAP_BUY", "SWAP_BUY_SOL"):
                    continue
                idx += 1
                results.append(
                    {
                        "order": idx,
                        "wallet_id": w.wallet_id,
                        "role": w.role,
                        "in_sol": w.action.effective_base_sol,
                        "min_out_tokens": w.action.min_out_tokens,
                        "received_tokens": max(w.action.min_out_tokens, 1),
                        "slippage_bps": w.action.slippage_bps,
                        "atomic": bool(w.action.atomic),
                        "tx_sig": f"FAKE_SIG_SWAP_{idx}",
                    }
                )
            b = {"swaps": results}
            state.mark(
                "buys",
                StepReceipt(
                    step="buys",
                    ok=True,
                    inputs={"schedule_len": len(plan.schedule)},
                    outputs=b,
                    plan_hash=cfg.plan_hash,
                ),
            )
            state.merge_artifacts({"buys": b})


async def _execute_live(plan: Plan, cfg: RunConfig, rpc, seed_kp=None) -> None:
    """Execute the plan against the network using real RPC calls."""

    from src.core.keys import derive_fresh_wallets, pubkey_str
    from src.exec import funding, minting, metadata, pool_init, swaps

    state = State(cfg.out_dir)
    assert_plan_invariants(plan)

    # Wallet preparation – derive transient wallets for each defined wallet id
    wallet_map: dict[str, Any] = {}
    for w in plan.wallets:
        if w.role == "SEED":
            wallet_map[w.wallet_id] = {
                "kp": seed_kp,
                "pub": pubkey_str(seed_kp) if seed_kp else w.wallet_id,
            }
        else:
            kp = derive_fresh_wallets(w.wallet_id, 1)[0]
            wallet_map[w.wallet_id] = {"kp": kp, "pub": pubkey_str(kp)}

    seed_info = wallet_map[next(w.wallet_id for w in plan.wallets if w.role == "SEED")]

    # FUNDING
    if (
        _selected("funding", cfg.only)
        and not (cfg.resume and state.done("funding"))
        and seed_info["kp"] is not None
    ):
        f_out = await funding.run(rpc, seed_info["kp"], wallet_map, plan)
        state.mark(
            "funding",
            StepReceipt(
                step="funding",
                ok=True,
                inputs={"wallets": len(plan.wallets)},
                outputs=f_out,
                plan_hash=cfg.plan_hash,
            ),
        )
        state.merge_artifacts({"funding": f_out})

    # MINT
    if _selected("mint", cfg.only) and not (cfg.resume and state.done("mint")):
        lp_creator = next(w for w in plan.wallets if w.role == "LP_CREATOR")
        payer_kp = wallet_map[lp_creator.wallet_id]["kp"]
        m_out = await minting.run(
            rpc,
            payer_kp=payer_kp,
            lp_creator_pub=wallet_map[lp_creator.wallet_id]["pub"],
            decimals=plan.token.decimals,
            amount=plan.token.total_mint,
        )
        state.mark(
            "mint",
            StepReceipt(
                step="mint",
                ok=True,
                inputs={"lp_tokens": plan.token.lp_tokens},
                outputs=m_out,
                plan_hash=cfg.plan_hash,
            ),
        )
        state.merge_artifacts({"mint": m_out})
    else:
        m_out = state.artifacts.get("mint")

    # METADATA
    if _selected("metadata", cfg.only) and not (cfg.resume and state.done("metadata")):
        lp_creator = next(w for w in plan.wallets if w.role == "LP_CREATOR")
        payer_kp = wallet_map[lp_creator.wallet_id]["kp"]
        md = await metadata.run(
            rpc,
            metadata_program=plan.token.authorities.get("metadata_program", ""),
            mint=m_out["mint"],
            mint_authority_kp=payer_kp,
            payer_kp=payer_kp,
            update_authority=wallet_map[lp_creator.wallet_id]["pub"],
            name=plan.token.name,
            symbol=plan.token.symbol,
            uri=plan.token.uri,
        )
        state.mark(
            "metadata",
            StepReceipt(
                step="metadata",
                ok=True,
                inputs={"mint": m_out["mint"]},
                outputs=md,
                plan_hash=cfg.plan_hash,
            ),
        )
        state.merge_artifacts({"metadata": md})

    # LP INIT
    if _selected("lp_init", cfg.only) and not (cfg.resume and state.done("lp_init")):
        lp_creator = next(w for w in plan.wallets if w.role == "LP_CREATOR")
        payer_kp = wallet_map[lp_creator.wallet_id]["kp"]
        lp = await pool_init.run(
            rpc,
            program_id=plan.dex.program_id,
            base_mint=m_out["mint"],
            quote_mint=plan.dex.quote_mint,
            tokens_to_lp=plan.token.lp_tokens,
            lp_creator_kp=payer_kp,
        )
        state.mark(
            "lp_init",
            StepReceipt(
                step="lp_init",
                ok=True,
                inputs={"mint": m_out["mint"]},
                outputs=lp,
                plan_hash=cfg.plan_hash,
            ),
        )
        state.merge_artifacts({"lp_init": lp})

    # BUYS
    if _selected("buys", cfg.only) and not (cfg.resume and state.done("buys")):
        b = await swaps.run(
            rpc,
            plan,
            wallet_map,
            base_mint=m_out["mint"],
            quote_mint=plan.dex.quote_mint,
        )
        state.mark(
            "buys",
            StepReceipt(
                step="buys",
                ok=True,
                inputs={"schedule_len": len(plan.schedule)},
                outputs=b,
                plan_hash=cfg.plan_hash,
            ),
        )
        state.merge_artifacts({"buys": b})


def execute(plan: Plan, cfg: RunConfig, rpc=None, seed_kp=None) -> None:
    """Entry point used by ``launcher.py``.

    When ``rpc`` is ``None`` the deterministic stub behaviour is used.  When a
    real :class:`~src.core.solana.Rpc` instance is supplied the plan is executed
    against the network.
    """

    if rpc is None:
        _execute_stub(plan, cfg)
    else:
        asyncio.run(_execute_live(plan, cfg, rpc, seed_kp))

