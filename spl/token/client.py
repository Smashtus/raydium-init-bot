from dataclasses import dataclass
from solders.pubkey import Pubkey

@dataclass
class _Token:
    pubkey: Pubkey

    async def create_associated_token_account(self, owner: Pubkey) -> Pubkey:
        return Pubkey.from_string("ata")

    async def mint_to(self, ata: Pubkey, owner: Pubkey, signer, amount: int):
        return None

class Token:
    @staticmethod
    async def create_mint(client, payer_kp, mint_authority: Pubkey, freeze_authority, decimals: int, program_id) -> _Token:
        return _Token(pubkey=Pubkey.from_string("mint"))
