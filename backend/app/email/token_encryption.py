"""Token encryption — Fernet symmetric encryption for OAuth tokens at rest.

Uses the app's SECRET_KEY to derive a Fernet key via SHA-256.
This ensures tokens stored in the database are never in plaintext.

NOTE: Changing SECRET_KEY invalidates all stored tokens.
Users will need to re-connect their OAuth email accounts.
"""

import base64
import hashlib

from cryptography.fernet import Fernet

from app.config import settings

# Derive a stable Fernet key from the app's secret_key.
# Fernet requires exactly 32 url-safe base64-encoded bytes.
_raw = hashlib.sha256(settings.secret_key.encode()).digest()
_fernet_key = base64.urlsafe_b64encode(_raw)
_fernet = Fernet(_fernet_key)


def encrypt_token(plaintext: str) -> bytes:
    """Encrypt a token string, returning encrypted bytes for DB storage."""
    return _fernet.encrypt(plaintext.encode())


def decrypt_token(ciphertext: bytes) -> str:
    """Decrypt stored bytes back to the original token string."""
    return _fernet.decrypt(ciphertext).decode()
