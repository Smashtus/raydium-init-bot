from pathlib import Path

import pytest

from src.io.jsonio import load_plan
from src.exec.invariants import assert_runtime_bounds


def test_assert_runtime_bounds_decimals_and_slippage():
    plan = load_plan(Path("plans/sample_plan.json"))

    plan.token.decimals = 10
    with pytest.raises(ValueError):
        assert_runtime_bounds(plan)

    plan.token.decimals = 6
    plan.wallets[2].action.slippage_bps = 6000
    with pytest.raises(ValueError):
        assert_runtime_bounds(plan)

