from pwdlib import PasswordHash

from user_microservice.interfaces import AbstractHasherClass

_hasher = PasswordHash.recommended()

class PassHash(AbstractHasherClass):

    def hash_password(self, password: str):
        return _hasher.hash(password)

    def verify_password(self, password_plain: str, password_hashed: str):
        return _hasher.verify(password_plain, password_hashed)

passhash = PassHash()