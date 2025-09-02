from dataclasses import dataclass
from solders.pubkey import Pubkey
from solders.instruction import Instruction, AccountMeta

@dataclass
class TransferParams:
    from_pubkey: Pubkey
    to_pubkey: Pubkey
    lamports: int

def transfer(params: TransferParams) -> Instruction:
    return Instruction(
        program_id=Pubkey.from_string("system"),
        accounts=[
            AccountMeta(params.from_pubkey, True, True),
            AccountMeta(params.to_pubkey, False, True),
        ],
        data=b"",
    )
