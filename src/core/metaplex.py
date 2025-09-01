"""Metaplex Token Metadata helpers.

Only a very small subset of the Metaplex program is required for the launcher –
creation of metadata accounts.  The function below constructs the
``create_metadata_account_v3`` instruction (using the DataV2 layout with no
optional fields).  The implementation purposely avoids pulling in the full MPL
Python stack and instead packs the instruction data manually using the Borsh
specification.
"""

from __future__ import annotations

try:  # pragma: no cover - executed only when solana libs are available
    from solders.pubkey import Pubkey
    from solders.instruction import Instruction, AccountMeta
except Exception:  # pragma: no cover - fallback for environments without deps
    Pubkey = object  # type: ignore
    Instruction = AccountMeta = object  # type: ignore


METADATA_PREFIX = b"metadata"
SYS_PROGRAM = "11111111111111111111111111111111"
RENT_SYSVAR = "SysvarRent111111111111111111111111111111111"


def _pack_str(s: str) -> bytes:
    b = s.encode("utf-8")
    return len(b).to_bytes(4, "little") + b


def build_create_metadata_v3(
    *,
    metadata_program: str,
    mint: str,
    mint_authority: str,
    payer: str,
    update_authority: str,
    name: str,
    symbol: str,
    uri: str | None,
) -> Instruction:
    """Build an ``Instruction`` for ``create_metadata_account_v3``.

    Only the minimal subset of fields is supported: ``DataV2`` with all optionals
    set to ``None`` and ``is_mutable`` hard coded to ``True``.
    """

    program_id = Pubkey.from_string(metadata_program)
    mint_pk = Pubkey.from_string(mint)
    seeds = [METADATA_PREFIX, bytes(program_id), bytes(mint_pk)]
    metadata_pda, _ = Pubkey.find_program_address(seeds, program_id)

    accounts = [
        AccountMeta(metadata_pda, is_signer=False, is_writable=True),
        AccountMeta(mint_pk, is_signer=False, is_writable=False),
        AccountMeta(Pubkey.from_string(mint_authority), is_signer=True, is_writable=False),
        AccountMeta(Pubkey.from_string(payer), is_signer=True, is_writable=True),
        AccountMeta(Pubkey.from_string(update_authority), is_signer=False, is_writable=False),
        AccountMeta(Pubkey.from_string(SYS_PROGRAM), is_signer=False, is_writable=False),
        AccountMeta(Pubkey.from_string(RENT_SYSVAR), is_signer=False, is_writable=False),
    ]

    data = bytearray()
    data.append(33)  # Instruction discriminator for CreateMetadataAccountV3
    data += _pack_str(name)
    data += _pack_str(symbol)
    data += _pack_str(uri or "")
    data += (0).to_bytes(2, "little")  # seller_fee_basis_points
    data.append(0)  # creators Option::None
    data.append(0)  # collection Option::None
    data.append(0)  # uses Option::None
    data.append(1)  # is_mutable = true
    data.append(0)  # collection_details Option::None

    return Instruction(program_id, accounts, bytes(data))

