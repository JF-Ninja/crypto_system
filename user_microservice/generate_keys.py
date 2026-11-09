import os
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


def safe_generate_keys():
    private_path = "private.pem"
    public_path = "public.pem"

    if os.path.exists(private_path) or os.path.exists(public_path):
        return

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    with open(private_path, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))

    public_key = private_key.public_key()
    with open(public_path, "wb") as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))

if __name__ == "__main__":
    safe_generate_keys()
