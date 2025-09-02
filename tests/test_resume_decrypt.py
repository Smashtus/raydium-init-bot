import json
from pathlib import Path
from types import SimpleNamespace

from solders.keypair import Keypair

from src.io.jsonio import load_plan
from src.exec import orchestrator
from src.exec.orchestrator import RunConfig
from src.core import keys


class FakeRpc:
    async def recent_blockhash(self):
        return "HASH"

    async def simulate(self, tx, *signers):
        return {"logs": []}

    async def send_and_confirm(self, tx, *signers):
        return "SIG"

    async def account_exists(self, pubkey):
        return False

    async def get_balance(self, pubkey):
        return 0

    async def close(self):
        return None


def make_cfg(outdir) -> RunConfig:
    return RunConfig(
        out_dir=outdir,
        resume=True,
        only="buys",
        plan_hash="HASH",
        rpc_url="http://localhost",
        cu_limit=None,
        cu_price_micro=None,
        simulate=True,
    )


def test_resume_decrypt(tmp_path, monkeypatch):
    plan = load_plan(Path("plans/downstream_plan_mainnet-beta_10000000mint_16.00pctLP_1.0SOL_99pct_3buys.json"))
    outdir = tmp_path / "state"
    wallet_dir = outdir / "wallets"
    wallet_dir.mkdir(parents=True, exist_ok=True)

    wallets_art = {}
    for w in plan.wallets:
        if w.role == "SEED":
            continue
        kp = Keypair()
        path = keys.save_encrypted(wallet_dir, w.wallet_id, kp)
        wallets_art[w.wallet_id] = {"pub": keys.pubkey_str(kp), "path": path}

    (outdir / "artifacts.json").write_text(
        json.dumps({"wallets": wallets_art, "mint": {"mint": "So11111111111111111111111111111111111111112"}})
    )

    monkeypatch.setattr(orchestrator, "Rpc", lambda cfg: FakeRpc())
    monkeypatch.setattr(orchestrator, "load_seed_from_file", lambda path: SimpleNamespace(kp=Keypair()))

    captured = {}

    async def fake_run(rpc, plan, wallet_map, **kwargs):
        captured.update(wallet_map)
        return {"swaps": []}

    monkeypatch.setattr(orchestrator.swaps, "run", fake_run)

    cfg = make_cfg(outdir)
    orchestrator.execute(plan, cfg, seed_keypair_path="")

    assert captured and all(isinstance(v.get("kp"), Keypair) for v in captured.values())
