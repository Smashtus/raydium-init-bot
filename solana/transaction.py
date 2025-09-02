class Transaction:
    def __init__(self):
        self.instructions = []
        self.recent_blockhash = None

    def add(self, ix):
        self.instructions.append(ix)
        return self

    def sign(self, *signers):
        return self
