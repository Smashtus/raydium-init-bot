class _Dummy:
    def to_bytes(self) -> bytes:
        return b""

def set_compute_unit_limit(limit: int) -> _Dummy:
    return _Dummy()

def set_compute_unit_price(price: int) -> _Dummy:
    return _Dummy()
