# sol-atomic-launcher (plan-first)

Goal: Accept a plan JSON and orchestrate a token launch (funding → mint → metadata → Raydium v4 initialize2 → buys).
This patch focuses only on schema compatibility + CLI dry-run.

## Quick start

```bash
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt

mkdir -p plans
cp downstream_plan_mainnet-beta_10000000mint_16.00pctLP_1.0SOL_99pct_3buys.json plans/

python launcher.py --plan plans/downstream_plan_mainnet-beta_10000000mint_16.00pctLP_1.0SOL_99pct_3buys.json --dry-run
```
## Execution scaffold (no chain ops yet)

This patch adds a resumable orchestrator that produces receipts for each step. It does **not** submit transactions yet.

Run end-to-end scaffold:

```bash
python launcher.py \
  --plan plans/downstream_plan_mainnet-beta_10000000mint_16.00pctLP_1.0SOL_99pct_3buys.json \
  --out state
```
## Hardening & Resumability

This patch:
- Adds package `__init__.py` files,
- Persists `artifacts.json` across steps,
- Versioned receipts with `schema_version`, `plan_hash`, `created_ms`,
- Saves a copy of the executed plan to `state/plan.json`,
- Loads config from `configs/defaults.yaml`,
- Implements true resume: steps are skipped when their receipt exists and artifacts contain required fields.

Run:
```bash
python launcher.py --plan plans/downstream_plan_mainnet-beta_10000000mint_16.00pctLP_1.0SOL_99pct_3buys.json --out state
```
