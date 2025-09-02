"""Minimal Metaplex Token Metadata helpers."""

from __future__ import annotations

from solders.pubkey import Pubkey
from solders.instruction import Instruction, AccountMeta

from .mpl_builders import encode_create_metadata_v3

SYSTEM_PROGRAM = "11111111111111111111111111111111"
TOKEN_PROGRAM = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
SYSVAR_RENT = "SysvarRent111111111111111111111111111111111"


def find_metadata_pda(mint: str, metadata_program: str) -> str:
    """Derive the PDA for the metadata account of ``mint``."""

    seeds = [
        b"metadata",
        Pubkey.from_string(metadata_program).to_bytes(),
        Pubkey.from_string(mint).to_bytes(),
    ]
    (pda, _bump) = Pubkey.find_program_address(seeds, Pubkey.from_string(metadata_program))
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
    """Return a ``CreateMetadataAccountV3`` instruction for the given ``mint``.

    The instruction uses a minimal ``DataV2`` layout without creators, collection
    or uses and sets ``seller_fee_basis_points`` to ``0``.  ``is_mutable`` is
    always ``True`` for newly minted tokens in this launcher.
    """

    metadata_pda = Pubkey.from_string(find_metadata_pda(mint, metadata_program))
    keys = [
        AccountMeta(pubkey=metadata_pda, is_signer=False, is_writable=True),
        AccountMeta(pubkey=Pubkey.from_string(mint), is_signer=False, is_writable=False),
        AccountMeta(pubkey=Pubkey.from_string(mint_authority), is_signer=True, is_writable=False),
        AccountMeta(pubkey=Pubkey.from_string(payer), is_signer=True, is_writable=True),
        AccountMeta(pubkey=Pubkey.from_string(update_authority), is_signer=False, is_writable=False),
        AccountMeta(pubkey=Pubkey.from_string(SYSTEM_PROGRAM), is_signer=False, is_writable=False),
        AccountMeta(pubkey=Pubkey.from_string(SYSVAR_RENT), is_signer=False, is_writable=False),
        AccountMeta(pubkey=Pubkey.from_string(TOKEN_PROGRAM), is_signer=False, is_writable=False),
    ]
    data = encode_create_metadata_v3(
        name=name,
        symbol=symbol,
        uri=uri,
        seller_fee_bps=0,
        is_mutable=True,
    )
    return Instruction(program_id=Pubkey.from_string(metadata_program), accounts=keys, data=data)
