from __future__ import annotations
from src.models.plan import Plan

def assert_plan_invariants(plan: Plan) -> None:
    # Plan.validate() already enforces invariants. Keep a separate hook for runtime checks.
    plan.validate()
