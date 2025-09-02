from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any
import asyncio
from solders.keypair import Keypair
from src.models.plan import Plan
from src.util.state import State, StepReceipt
from src.util.telemetry import Telemetry
from src.util.config import load_config
from src.core.solana import Rpc, RpcConfig
from src.core.keys import (
    load_seed_from_file,
    gen_subwallets,
    save_encrypted,
    pubkey_str,
    load_encrypted,
)
from src.exec import funding, minting, metadata, pool_init, swaps
from src.core.metaplex import find_metadata_pda
from src.dex.raydium_v4 import derive_pool_accounts, probe_pool_exists
from src.exec.invariants import assert_plan_invariants, assert_runtime_bounds

STEPS_ORDER = ["funding","mint","metadata","lp_init","buys"]

@dataclass
class RunConfig:
    out_dir: Path
    resume: bool
    only: str
    plan_hash: str
    rpc_url: str
    cu_limit: int | None
    cu_price_micro: int | None
    tip_to: str | None = None
    tip_lamports: int | None = None
    simulate: bool = False
    max_buys: int | None = None

async def execute_async(plan: Plan, cfg: RunConfig, seed_keypair_path: str, config_yaml: Path) -> None:
    assert_plan_invariants(plan)
    assert_runtime_bounds(plan)
    state = State(cfg.out_dir)
    telem = Telemetry(cfg.out_dir / "telemetry.ndjson")
    rpc = Rpc(RpcConfig(url=cfg.rpc_url))

    # Subwallet keypairs (fresh) persisted if not present
    wallet_ids = [w.wallet_id for w in plan.wallets if w.role != "SEED"]
    wallet_dir = cfg.out_dir / "wallets"
    if "wallets" not in state.artifacts:
        sub = gen_subwallets(wallet_ids)
        pubmap = {wid: {"kp": kp, "pub": pubkey_str(kp), "path": save_encrypted(wallet_dir, wid, kp)} for wid, kp in sub.items()}
        state.merge_artifacts({"wallets": {wid: {"pub": v["pub"], "path": v["path"]} for wid, v in pubmap.items()}})
        # keep Keypair objects in memory map for this run
        wallet_map: Dict[str, Any] = {wid: {"kp": sub[wid], "pub": pubmap[wid]["pub"]} for wid in wallet_ids}
    else:
        wallet_map = {}
        for wid, info in state.artifacts.get("wallets", {}).items():
            p = info.get("path")
            if p and p.endswith(".enc"):
                kp = load_encrypted(p)
                wallet_map[wid] = {"kp": kp, "pub": pubkey_str(kp)}
            elif info.get("pub"):
                wallet_map[wid] = {"pub": info.get("pub")}

    # Load seed
    seed = load_seed_from_file(seed_keypair_path).kp

    # FUNDING
    if cfg.only in ("all","funding") and not (cfg.resume and state.done("funding")):
        fout = await funding.run(rpc, seed, wallet_map or state.artifacts.get("wallets", {}), plan, cfg.cu_limit, cfg.cu_price_micro)
        state.mark("funding", StepReceipt(step="funding", ok=True, inputs={"wallets": len(plan.wallets)}, outputs=fout, plan_hash=cfg.plan_hash))
        state.merge_artifacts({"funding": fout})
        telem.emit({"event":"funding_complete","wallets":len(plan.wallets)})

    # MINT
    mint_art = state.artifacts.get("mint")
    if cfg.only in ("all", "mint"):
        if mint_art and await rpc.account_exists(mint_art.get("mint")):
            state.mark(
                "mint",
                StepReceipt(
                    step="mint",
                    ok=True,
                    inputs={},
                    outputs={"skipped": True, "reason": "mint_exists"},
                    plan_hash=cfg.plan_hash,
                ),
            )
        elif not (cfg.resume and state.done("mint") and mint_art):
            lp_creator = next(w for w in plan.wallets if w.role == "LP_CREATOR")
            lp_pub = (wallet_map.get(lp_creator.wallet_id) or state.artifacts["wallets"][lp_creator.wallet_id])["pub"]
            mout = await minting.run(rpc, seed, lp_pub, plan.token.decimals, plan.token.lp_tokens)
            state.mark("mint", StepReceipt(step="mint", ok=True, inputs={"lp_tokens": plan.token.lp_tokens}, outputs=mout, plan_hash=cfg.plan_hash))
            state.merge_artifacts({"mint": mout})
            telem.emit({"event": "mint_complete", "mint": mout["mint"]})
        mint_art = state.artifacts.get("mint")

    # METADATA
    if cfg.only in ("all", "metadata"):
        mp = load_config(config_yaml).get("program_ids", {}).get("metaplex_token_metadata")
        md_pda = find_metadata_pda(mint_art["mint"], mp)
        if await rpc.account_exists(md_pda):
            state.mark(
                "metadata",
                StepReceipt(
                    step="metadata",
                    ok=True,
                    inputs={"mint": mint_art["mint"]},
                    outputs={"skipped": True, "reason": "metadata_exists"},
                    plan_hash=cfg.plan_hash,
                ),
            )
        elif not (cfg.resume and state.done("metadata")):
            md = await metadata.run(
                rpc,
                mp,
                mint_art["mint"],
                seed,
                seed,
                update_authority=str(seed.pubkey()),
                name=plan.token.name,
                symbol=plan.token.symbol,
                uri=plan.token.uri,
                cu_limit=cfg.cu_limit,
                cu_price_micro=cfg.cu_price_micro,
                simulate=cfg.simulate,
            )
            state.mark(
                "metadata",
                StepReceipt(step="metadata", ok=True, inputs={"mint": mint_art["mint"]}, outputs=md, plan_hash=cfg.plan_hash),
            )
            state.merge_artifacts({"metadata": md})
            telem.emit({"event": "metadata_complete", "mint": mint_art["mint"]})

    # LP INIT
    if cfg.only in ("all", "lp_init", "lp"):
        rpid = load_config(config_yaml).get("program_ids", {}).get("raydium_v4_amm")
        wsol = load_config(config_yaml).get("mints", {}).get("wrapped_sol")
        accounts = derive_pool_accounts(mint_art["mint"], wsol, rpid)
        if await probe_pool_exists(rpc, accounts):
            state.mark(
                "lp_init",
                StepReceipt(
                    step="lp_init",
                    ok=True,
                    inputs={"mint": mint_art["mint"]},
                    outputs={"skipped": True, "reason": "pool_exists", "pool": accounts.pool},
                    plan_hash=cfg.plan_hash,
                ),
            )
            state.merge_artifacts({"lp_init": {"pool": accounts.pool}})
        elif not (cfg.resume and state.done("lp_init") and state.artifacts.get("lp_init")):
            lp_creator = next(w for w in plan.wallets if w.role == "LP_CREATOR")
            lp_kp = (wallet_map.get(lp_creator.wallet_id) or {}).get("kp", seed)
            lp = await pool_init.run(
                rpc,
                rpid,
                base_mint=mint_art["mint"],
                quote_mint=wsol,
                tokens_to_lp=plan.token.lp_tokens,
                lp_creator_kp=lp_kp,
                cu_limit=cfg.cu_limit,
                cu_price_micro=cfg.cu_price_micro,
                simulate=cfg.simulate,
            )
            state.mark(
                "lp_init",
                StepReceipt(
                    step="lp_init",
                    ok=True,
                    inputs={"mint": mint_art["mint"]},
                    outputs=lp,
                    plan_hash=cfg.plan_hash,
                ),
            )
            state.merge_artifacts({"lp_init": lp})
            telem.emit({"event": "lp_init_complete", "pool": lp.get("pool")})

    # BUYS
    if cfg.only in ("all", "buys"):
        wsol = load_config(config_yaml).get("mints", {}).get("wrapped_sol")
        rpid = load_config(config_yaml).get("program_ids", {}).get("raydium_v4_amm")
        buys_done = state.artifacts.get("buys_done", {})
        b = await swaps.run(
            rpc,
            plan,
            wallet_map or state.artifacts.get("wallets", {}),
            base_mint=mint_art["mint"],
            quote_mint=wsol,
            program_id=rpid,
            cu_limit=cfg.cu_limit,
            cu_price_micro=cfg.cu_price_micro,
            simulate=cfg.simulate,
            buys_done=buys_done,
            max_buys=cfg.max_buys,
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
        state.merge_artifacts({"buys": b, "buys_done": buys_done})
        telem.emit({"event": "buys_complete", "count": len([s for s in b.get("swaps", []) if not s.get("skipped")])})

    await rpc.close()


def execute(plan: Plan, cfg: RunConfig, seed_keypair_path: str = "", config_yaml: Path | None = None, **_unused: Any) -> None:
    """Synchronous helper used by tests and CLI wrappers."""
    asyncio.run(execute_async(plan, cfg, seed_keypair_path, config_yaml or Path("configs/defaults.yaml")))
