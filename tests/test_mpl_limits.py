import pytest
from src.core.metaplex import build_create_metadata_v3


def _parse_str(data: bytes, offset: int):
    length = int.from_bytes(data[offset:offset+4], "little")
    start = offset + 4
    end = start + length
    return data[start:end].decode("utf-8"), end


def test_mpl_limits_truncate():
    long_name = "n" * 64
    long_symbol = "s" * 30
    long_uri = "u" * 400
    ix = build_create_metadata_v3(
        metadata_program="11111111111111111111111111111111",
        mint="So11111111111111111111111111111111111111112",
        mint_authority="11111111111111111111111111111111",
        payer="11111111111111111111111111111111",
        update_authority="11111111111111111111111111111111",
        name=long_name,
        symbol=long_symbol,
        uri=long_uri,
    )
    data = bytes(ix.data)
    assert data[0] == 33  # discriminator
    name, off = _parse_str(data, 1)
    symbol, off = _parse_str(data, off)
    uri, _ = _parse_str(data, off)
    assert len(name) == 32
    assert len(symbol) == 10
    assert len(uri) == 200
