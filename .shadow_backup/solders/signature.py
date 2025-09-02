class Signature(str):
    @classmethod
    def from_string(cls, s: str) -> 'Signature':
        return cls(s)
