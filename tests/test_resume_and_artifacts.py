import json
from types import SimpleNamespace
from pathlib import Path
from src.io.jsonio import load_plan
from src.exec import orchestrator
from src.exec.orchestrator import execute, RunConfig


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


def test_resume_and_artifacts(tmp_path, monkeypatch):
    plan = load_plan(Path("plans/downstream_plan_mainnet-beta_10000000mint_16.00pctLP_1.0SOL_99pct_3buys.json"))
    outdir = tmp_path / "state"
    outdir.mkdir()
    (outdir / "artifacts.json").write_text(json.dumps({"mint": {"mint": "So11111111111111111111111111111111111111112"}}))
    monkeypatch.setattr(orchestrator, "Rpc", lambda cfg: FakeRpc())
    monkeypatch.setattr(orchestrator, "load_seed_from_file", lambda path: SimpleNamespace(kp=orchestrator.Keypair()))
    cfg = RunConfig(out_dir=outdir, resume=False, only="buys", plan_hash="TESTHASH", rpc_url="http://", cu_limit=None, cu_price_micro=None, simulate=True)
    execute(plan, cfg)
    receipts1 = sorted((outdir / "receipts").glob("*.json"))
    assert {p.name for p in receipts1} == {"buys.json"}
    assert (outdir / "artifacts.json").exists()

    cfg2 = RunConfig(out_dir=outdir, resume=True, only="buys", plan_hash="TESTHASH", rpc_url="http://", cu_limit=None, cu_price_micro=None, simulate=True)
    execute(plan, cfg2)
    receipts2 = sorted((outdir / "receipts").glob("*.json"))
    assert [p.name for p in receipts1] == [p.name for p in receipts2]

