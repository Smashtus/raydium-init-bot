from __future__ import annotations

import hashlib
from dataclasses import dataclass

@dataclass
class Pubkey:
    _data: bytes

    @classmethod
    def from_string(cls, s: str) -> 'Pubkey':
        b = s.encode('utf-8')[:32]
        return cls(b.ljust(32, b'\0'))

    def to_bytes(self) -> bytes:
        return self._data

    def __str__(self) -> str:
        return self._data.hex()

    @staticmethod
    def find_program_address(seeds: list[bytes], program_id: 'Pubkey'):
        h = hashlib.sha256(b''.join(seeds) + program_id.to_bytes()).digest()
        return Pubkey(h), 255
