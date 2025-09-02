import json
from types import SimpleNamespace
from pathlib import Path

from solders.keypair import Keypair

from src.io.jsonio import load_plan
from src.core import keys
from src.exec import orchestrator
from src.exec.orchestrator import RunConfig


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


def test_decrypt_on_resume(tmp_path, monkeypatch):
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

    cfg = make_cfg(outdir)
    orchestrator.execute(plan, cfg, seed_keypair_path="")

    art = json.loads((outdir / "artifacts.json").read_text())
    buys_done = art.get("buys_done", {})
    # All wallets in the plan schedule should now be marked as swapped
    assert all(buys_done.get(wid) for wid in plan.schedule)
