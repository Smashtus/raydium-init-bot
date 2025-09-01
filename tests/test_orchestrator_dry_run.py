from pathlib import Path
from src.io.jsonio import load_plan
from src.exec.orchestrator import execute, RunConfig

def test_orchestrator_writes_receipts(tmp_path):
    plan = load_plan(Path("plans/downstream_plan_mainnet-beta_10000000mint_16.00pctLP_1.0SOL_99pct_3buys.json"))
    outdir = tmp_path / "state"
    cfg = RunConfig(out_dir=outdir, resume=False, only="all")
    execute(plan, cfg)
    # check receipts
    rec = outdir / "receipts"
    assert (rec / "funding.json").exists()
    assert (rec / "mint.json").exists()
    assert (rec / "metadata.json").exists()
    assert (rec / "lp_init.json").exists()
    assert (rec / "buys.json").exists()
