"""Minimal Metaplex Token Metadata helpers.

This module intentionally implements only the tiny subset of the MPL Token
Metadata program that is required for the launcher: creation of a new metadata
account via the ``CreateMetadataAccountV3`` instruction.  Pulling in the full
MPL python stack would add a significant dependency footprint, therefore the
instruction data is packed manually according to the program's Borsh
specification.
"""

from __future__ import annotations

from solders.pubkey import Pubkey
from solders.instruction import Instruction, AccountMeta

METADATA_PREFIX = b"metadata"
SYS_PROGRAM = "11111111111111111111111111111111"
RENT_SYSVAR = "SysvarRent111111111111111111111111111111111"
TOKEN_PROGRAM = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"


def _pack_str(s: str) -> bytes:
    b = s.encode("utf-8")
    return len(b).to_bytes(4, "little") + b


def find_metadata_pda(mint: str, program: str) -> str:
    """Return the PDA for the metadata account of ``mint``."""

    program_id = Pubkey.from_string(program)
    mint_pk = Pubkey.from_string(mint)
    seeds = [METADATA_PREFIX, program_id.to_bytes(), mint_pk.to_bytes()]
    (pda, _bump) = Pubkey.find_program_address(seeds, program_id)
    return str(pda)


def build_create_metadata_v3(
    *,
    metadata_program: str,
    mint: str,
    mint_authority: str,
    payer: str,
    update_authority: str,
    name: str,
    symbol: str,
    uri: str,
) -> Instruction:
    """Create an ``Instruction`` for ``CreateMetadataAccountV3``.

    Only a minimal ``DataV2`` layout is supported: all optional fields are set to
    ``None`` and ``is_mutable`` defaults to ``True``.  ``seller_fee_basis_points``
    is fixed to ``0`` as the launcher never configures secondary royalties.
    """

    program_id = Pubkey.from_string(metadata_program)
    mint_pk = Pubkey.from_string(mint)
    metadata_pda = Pubkey.from_string(find_metadata_pda(mint, metadata_program))

    accounts = [
        AccountMeta(metadata_pda, is_signer=False, is_writable=True),
        AccountMeta(mint_pk, is_signer=False, is_writable=False),
        AccountMeta(Pubkey.from_string(mint_authority), is_signer=True, is_writable=False),
        AccountMeta(Pubkey.from_string(payer), is_signer=True, is_writable=True),
        AccountMeta(Pubkey.from_string(update_authority), is_signer=False, is_writable=False),
        AccountMeta(Pubkey.from_string(SYS_PROGRAM), is_signer=False, is_writable=False),
        AccountMeta(Pubkey.from_string(RENT_SYSVAR), is_signer=False, is_writable=False),
        AccountMeta(Pubkey.from_string(TOKEN_PROGRAM), is_signer=False, is_writable=False),
    ]

    data = bytearray()
    data.append(33)  # discriminator for CreateMetadataAccountV3
    data += _pack_str(name)
    data += _pack_str(symbol)
    data += _pack_str(uri)
    data += (0).to_bytes(2, "little")  # seller_fee_basis_points
    data.append(0)  # creators Option::None
    data.append(0)  # collection Option::None
    data.append(0)  # uses Option::None
    data.append(1)  # is_mutable = True
    data.append(0)  # collection_details Option::None

    return Instruction(program_id, accounts, bytes(data))

