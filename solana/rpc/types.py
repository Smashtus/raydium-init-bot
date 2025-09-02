from dataclasses import dataclass

@dataclass
class TxOpts:
    skip_preflight: bool = False
