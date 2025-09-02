from __future__ import annotations

import os
from dataclasses import dataclass
from .pubkey import Pubkey

@dataclass
class Keypair:
    _data: bytes

    def __init__(self, data: bytes | None = None):
        self._data = data or os.urandom(64)

    @classmethod
    def from_bytes(cls, b: bytes) -> 'Keypair':
        return cls(bytes(b))

    def pubkey(self) -> Pubkey:
        return Pubkey(self._data[:32])

    def __bytes__(self) -> bytes:
        return self._data
