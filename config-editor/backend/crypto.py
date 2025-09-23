import os
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet

SALT_SIZE = 16
# In a real app, the number of iterations should be higher,
# but we keep it low here for speed in a testing environment.
ITERATIONS = 100_000

def derive_key(password: str, salt: bytes) -> bytes:
    """Derives a 32-byte key from a password and salt using PBKDF2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=ITERATIONS,
        backend=default_backend()
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))

def encrypt(data: bytes, password: str) -> bytes:
    """
    Encrypts data with a password. The salt is randomly generated
    and prepended to the ciphertext.
    """
    salt = os.urandom(SALT_SIZE)
    key = derive_key(password, salt)
    f = Fernet(key)
    encrypted_data = f.encrypt(data)
    # Prepend the salt to the encrypted data for use in decryption.
    return salt + encrypted_data

def decrypt(token: bytes, password: str) -> bytes:
    """
    Decrypts a token using a password. The salt is extracted from the
    beginning of the token.
    """
    salt = token[:SALT_SIZE]
    encrypted_data = token[SALT_SIZE:]
    key = derive_key(password, salt)
    f = Fernet(key)
    return f.decrypt(encrypted_data)
