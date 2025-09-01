# sol-atomic-launcher

Prototype launcher for orchestrating Solana token mints and Raydium pools
based on a declarative plan file.  This repository contains only a minimal
subset of the functionality described in the specification.  The focus of this
prototype is the **plan schema** and a small CLI that loads the plan and prints
a summary.

The long term goal is to provide a single command that can mint a token,
initialise a Raydium pool and execute a series of swaps according to a plan.
This repository lays out the project structure and provides the first building
blocks so that additional functionality can be implemented in future patches.

## Usage

```bash
pip install -r requirements.txt
python launcher.py --plan plans/sample_plan.json --seed-keypair path/to/seed.json --rpc https://example.com --dry-run
```

Running the above command will parse the plan file and print a short summary in
**dry run** mode.

## Tests

Run the unit tests with:

```bash
pytest
```

## Caveats

The majority of the features from the full specification have not yet been
implemented.  Many modules contain placeholders for future work and the CLI
performs only minimal validation.  Use this code for development and testing
only.
