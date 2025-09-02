import base64

class Fernet:
    def __init__(self, key: bytes):
        self.key = key

    def encrypt(self, data: bytes) -> bytes:
        return base64.urlsafe_b64encode(data)

    def decrypt(self, token: bytes) -> bytes:
        return base64.urlsafe_b64decode(token)
