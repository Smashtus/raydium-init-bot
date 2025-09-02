from __future__ import annotations
from pathlib import Path
from typing import Dict, Any
from solana.transaction import Transaction
from src.util.planhash import sha256_file
from src.core.solana import Rpc
from src.core.tx import with_compute_budget
from src.core.metaplex import build_create_metadata_v3, find_metadata_pda
from src.dex.raydium_v4 import derive_pool_accounts, build_initialize2


async def preflight(rpc: Rpc, plan_path: Path, cfg: Dict[str, Any], plan) -> Dict[str, Any]:
    plan_hash = sha256_file(plan_path)
    program_checks: Dict[str, Any] = {}

    # Ensure referenced program IDs exist
    for k, v in (cfg.get("program_ids") or {}).items():
        if not v:
            continue
        program_checks[f"prog_{k}"] = bool(await rpc.account_exists(v))

    # Simulate creation of a dummy metadata account
    meta_prog = cfg["program_ids"]["metaplex_token_metadata"]
    tx1 = Transaction()
    tx1 = with_compute_budget(
        tx1,
        cfg["fees"]["compute_unit_limit"],
        cfg["fees"]["compute_unit_price_micro_lamports"],
    )
    tx1.add(
        build_create_metadata_v3(
            metadata_program=meta_prog,
            mint="So11111111111111111111111111111111111111112",
            mint_authority=str(plan.dex.program_id),
            payer=str(plan.dex.program_id),
            update_authority=str(plan.dex.program_id),
            name="X",
            symbol="X",
            uri="",
        )
    )
    sim_md = await rpc.simulate(tx1)

    # Simulate Raydium pool initialisation
    rpid = cfg["program_ids"]["raydium_v4_amm"]
    wsol = cfg["mints"]["wrapped_sol"]
    acc = derive_pool_accounts(plan.token.symbol + plan.plan_id, wsol, rpid)
    tx2 = Transaction()
    for ix in build_initialize2(
        rpid,
        base_mint=plan.token.symbol + plan.plan_id,
        quote_mint=wsol,
        lp_creator_pub=str(plan.dex.program_id),
        tokens_to_lp=plan.token.lp_tokens,
    ):
        tx2.add(ix)
    sim_init = await rpc.simulate(tx2)

    return {
        "plan_hash": plan_hash,
        "program_checks": program_checks,
        "simulate_metadata_ok": sim_md.get("err") is None,
        "simulate_init_ok": sim_init.get("err") is None,
    }
