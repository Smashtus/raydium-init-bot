class AsyncClient:
    def __init__(self, url: str, timeout: int, commitment=None):
        self.url = url
        self.timeout = timeout
        self.commitment = commitment

    async def close(self):
        return None

    async def get_latest_blockhash(self):
        class _Resp:
            class value:
                blockhash = "HASH"
        return _Resp()

    async def simulate_transaction(self, tx):
        return type("Sim", (), {"value": {}})()

    async def send_transaction(self, tx, *signers, opts=None):
        class _Resp:
            value = "SIG"
        return _Resp()

    async def confirm_transaction(self, signature, commitment=None):
        return None

    async def get_account_info(self, pubkey):
        class _Resp:
            value = None
        return _Resp()

    async def get_balance(self, pubkey):
        class _Resp:
            value = 0
        return _Resp()
