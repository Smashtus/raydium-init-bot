from __future__ import annotations

from dataclasses import dataclass
from typing import List
from .pubkey import Pubkey

@dataclass
class AccountMeta:
    pubkey: Pubkey
    is_signer: bool
    is_writable: bool

class Instruction:
    def __init__(self, program_id: Pubkey, accounts: List[AccountMeta], data: bytes):
        self.program_id = program_id
        self.accounts = accounts
        self.data = data

    @classmethod
    def from_bytes(cls, data: bytes) -> 'Instruction':
        return cls(Pubkey(b'\0' * 32), [], data)
