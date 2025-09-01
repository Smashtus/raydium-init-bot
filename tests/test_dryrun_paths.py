import json
import subprocess
import sys
from pathlib import Path


def run_cli(args):
    cmd = [sys.executable, 'launcher.py'] + args
    return subprocess.check_output(cmd, text=True)
def test_cli_dry_run(tmp_path):
    plan = Path('plans/sample_plan.json')
    seed = tmp_path / 'seed.json'
    seed.write_text(json.dumps(list(range(64))))
    output = run_cli([
        '--plan', str(plan),
        '--seed-keypair', str(seed),
        '--rpc', 'https://example.com',
        '--dry-run',
    ])
    assert 'Dry-run OK' in output
