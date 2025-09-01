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
