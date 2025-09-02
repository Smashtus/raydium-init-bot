"""Lightweight stubs for the ``solders`` package used in tests.

These stubs implement just enough of the interfaces used by the project so that
unit tests can run in environments where the real ``solders`` bindings are not
available.  The implementations are intentionally simplistic and are **not**
cryptographically correct.
"""

from .pubkey import Pubkey
from .keypair import Keypair
from .instruction import Instruction, AccountMeta
from .signature import Signature
from .hash import Hash
from .commitment_config import CommitmentLevel
