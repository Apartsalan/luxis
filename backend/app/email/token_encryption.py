"""Token encryption — Fernet symmetric encryption for OAuth tokens at rest.

Uses TOKEN_ENCRYPTION_KEY if set, otherwise falls back to SECRET_KEY.
A separate key allows SECRET_KEY rotation without breaking OAuth tokens.

NOTE: Changing the active key invalidates all stored tokens.
Users will need to re-connect their OAuth email accounts.
"""

import base64
import hashlib

from cryptography.fernet import Fernet

from app.config import settings

_key_source = settings.token_encryption_key or settings.secret_key
_raw = hashlib.sha256(_key_source.encode()).digest()
_fernet_key = base64.urlsafe_b64encode(_raw)
_fernet = Fernet(_fernet_key)


def encrypt_token(plaintext: str) -> bytes:
    """Encrypt a token string, returning encrypted bytes for DB storage."""
    return _fernet.encrypt(plaintext.encode())


def decrypt_token(ciphertext: bytes) -> str:
    """Decrypt stored bytes back to the original token string."""
    return _fernet.decrypt(ciphertext).decode()
