from __future__ import annotations

"""Helper encoders for Metaplex Token Metadata program."""

from typing import Optional


def _pack_str(s: str) -> bytes:
    b = s.encode("utf-8")
    return len(b).to_bytes(4, "little") + b


def encode_create_metadata_v3(
    *,
    name: str,
    symbol: str,
    uri: str,
    seller_fee_bps: int,
    is_mutable: bool,
) -> bytes:
    """Encode a minimal ``CreateMetadataAccountV3`` instruction payload.

    Only the subset of ``DataV2`` used by the launcher is supported.  Creators,
    collection and uses are all set to ``None``; ``collection_details`` is not
    provided.  ``seller_fee_bps`` and ``is_mutable`` are configurable to match the
    token being minted.
    """

    data = bytearray()
    data.append(33)  # discriminator for CreateMetadataAccountV3
    data += _pack_str(name)
    data += _pack_str(symbol)
    data += _pack_str(uri)
    data += int(seller_fee_bps).to_bytes(2, "little")
    data.append(0)  # creators Option::None
    data.append(0)  # collection Option::None
    data.append(0)  # uses Option::None
    data.append(1 if is_mutable else 0)
    data.append(0)  # collection_details Option::None
    return bytes(data)
