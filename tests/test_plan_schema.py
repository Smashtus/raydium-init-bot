from pathlib import Path

from src.io.jsonio import load_plan


def test_load_sample_plan():
    plan = load_plan(Path('plans/sample_plan.json'))
    assert plan.token.lp_tokens == plan.inputs.T0
    assert len(plan.wallets) == 3
    assert plan.schedule == ['w1', 'w2']
