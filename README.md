# Raydium Init Bot — Atomic Launcher

End-to-end permissionless token launch workflow driven by a JSON “plan”.
From one Seed keypair it funds wallets, mints tokens, creates metadata,
initializes a Raydium v4 pool, and executes buys — all idempotent,
resumable, and receipt-tracked.

---

## 1. Requirements

Ubuntu 20.04+ or Debian-based system.

Install system deps:
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git

Clone repo:
git clone https://github.com/<YOUR_REPO>/raydium-init-bot.git
cd raydium-init-bot

Set up venv:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

---

## 2. Config & Secrets

1. Wallet passphrase for encrypted subwallets:
export LAUNCHER_WALLET_PASS="choose-a-strong-passphrase"

2. Seed keypair file (JSON array of 64 ints). Place under:
keys/seed.json

3. Config YAML: see configs/defaults.yaml. It must contain:
program_ids:
  metaplex_token_metadata: <MPL_PROGRAM_ID>
  raydium_v4_amm: <RAYDIUM_PROGRAM_ID>
mints:
  wrapped_sol: So11111111111111111111111111111111111111112
fees:
  compute_unit_limit: 1000000
  compute_unit_price_micro_lamports: 150000

---

## 3. Plan

Place your plan JSON under plans/.
Example: plans/downstream_plan_mainnet-beta.json

---

## 4. Quick Commands

4.1 Dry summary (no network)
python launcher.py run --plan plans/downstream_plan_mainnet-beta.json --rpc https://api.mainnet-beta.solana.com --dry-run

4.2 Preflight (simulate, no submit)
python launcher.py preflight --plan plans/downstream_plan_mainnet-beta.json --rpc https://api.mainnet-beta.solana.com --config configs/defaults.yaml --out state --strict
Exits code 0 if all checks/simulations OK, else 1.

4.3 Full run (all steps, resumable)
python launcher.py run --plan plans/downstream_plan_mainnet-beta.json --seed-keypair keys/seed.json --rpc https://api.mainnet-beta.solana.com --config configs/defaults.yaml --out state --priority-fee 150000 --cu-limit 1000000

4.4 Resume run (skip finished steps)
python launcher.py run --plan plans/downstream_plan_mainnet-beta.json --rpc https://api.mainnet-beta.solana.com --config configs/defaults.yaml --out state --resume

4.5 Limit buys (testing safety)
python launcher.py run --plan plans/downstream_plan_mainnet-beta.json --rpc https://api.mainnet-beta.solana.com --config configs/defaults.yaml --out state --max-buys 2

4.6 Verify after run (read-only checks)
python launcher.py verify --out state --rpc https://api.mainnet-beta.solana.com --config configs/defaults.yaml
Exits code 0 if mint, metadata PDA, and pool exist; else 1.

---

## 5. Outputs

- Receipts: state/receipts/*.json (one per step)
- Artifacts: state/artifacts.json (merged state)
- Telemetry: state/telemetry.ndjson (append-only events)
- Encrypted wallets: state/wallets/*.enc

---

## 6. Safety Features

- Idempotency: steps skip if already done on-chain
- Resume: re-run with --resume to continue after interruption
- Per-wallet swap guards: no duplicate buys
- Runtime bounds: decimals 0–9; slippage ≤ 5000 bps; positive LP tokens
- Exit codes: preflight --strict and verify exit non-zero if checks fail
- Max buys: optional --max-buys N cap for test runs

---

## 7. Test Ladder

1. Offline unit tests:
pytest -q

2. Preflight (safe):
python launcher.py preflight --plan plans/downstream_plan_mainnet-beta.json --rpc https://api.mainnet-beta.solana.com --config configs/defaults.yaml --out state --strict

3. Controlled run (limit buys):
python launcher.py run --plan plans/downstream_plan_mainnet-beta.json --rpc https://api.mainnet-beta.solana.com --config configs/defaults.yaml --out state --max-buys 1

4. Resume run:
python launcher.py run --plan plans/downstream_plan_mainnet-beta.json --rpc https://api.mainnet-beta.solana.com --config configs/defaults.yaml --out state --resume

5. Verify after run:
python launcher.py verify --out state --rpc https://api.mainnet-beta.solana.com --config configs/defaults.yaml

---

## 8. Notes

- Do not commit or log seed keypairs
- Use a private RPC with sufficient CU budget support
- Always preflight before a live run

---

End of README.md replacement.

