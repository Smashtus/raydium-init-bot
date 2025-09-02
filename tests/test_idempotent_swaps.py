import json
from types import SimpleNamespace
from pathlib import Path

from src.io.jsonio import load_plan
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


def _mk_cfg(outdir, resume: bool) -> RunConfig:
    return RunConfig(
        out_dir=outdir,
        resume=resume,
        only="buys",
        plan_hash="HASH",
        rpc_url="http://localhost",
        cu_limit=None,
        cu_price_micro=None,
        simulate=True,
    )


def test_idempotent_swaps(tmp_path, monkeypatch):
    plan = load_plan(Path("plans/downstream_plan_mainnet-beta_10000000mint_16.00pctLP_1.0SOL_99pct_3buys.json"))
    outdir = tmp_path / "state"
    outdir.mkdir()
    # pre-populate mint artifact so buys step can run
    (outdir / "artifacts.json").write_text(json.dumps({"mint": {"mint": "So11111111111111111111111111111111111111112"}}))

    monkeypatch.setattr(orchestrator, "Rpc", lambda cfg: FakeRpc())
    monkeypatch.setattr(orchestrator, "load_seed_from_file", lambda path: SimpleNamespace(kp=object()))

    cfg1 = _mk_cfg(outdir, resume=False)
    orchestrator.execute(plan, cfg1, seed_keypair_path="")

    cfg2 = _mk_cfg(outdir, resume=True)
    orchestrator.execute(plan, cfg2, seed_keypair_path="")

    art = json.loads((outdir / "artifacts.json").read_text())
    swaps = art.get("buys", {}).get("swaps", [])
    assert swaps and all(s.get("skipped") for s in swaps)
