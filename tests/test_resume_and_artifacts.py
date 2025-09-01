from pathlib import Path
from src.io.jsonio import load_plan
from src.exec.orchestrator import execute, RunConfig


def test_resume_and_artifacts(tmp_path):
    plan = load_plan(Path("plans/downstream_plan_mainnet-beta_10000000mint_16.00pctLP_1.0SOL_99pct_3buys.json"))
    outdir = tmp_path / "state"
    # First run
    execute(plan, RunConfig(out_dir=outdir, resume=False, only="all", plan_hash="TESTHASH"))
    receipts1 = sorted((outdir / "receipts").glob("*.json"))
    assert {p.name for p in receipts1} == {"funding.json","mint.json","metadata.json","lp_init.json","buys.json"}
    assert (outdir / "artifacts.json").exists()

    # Second run (resume): should not create new receipts or change list
    execute(plan, RunConfig(out_dir=outdir, resume=True, only="all", plan_hash="TESTHASH"))
    receipts2 = sorted((outdir / "receipts").glob("*.json"))
    assert [p.name for p in receipts1] == [p.name for p in receipts2]

