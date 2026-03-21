"""Token encryption — Fernet symmetric encryption for OAuth tokens at rest.

Uses the app's SECRET_KEY to derive a Fernet key via PBKDF2-HMAC-SHA256
with a fixed salt and 600 000 iterations (OWASP 2023 recommendation).

NOTE: Changing SECRET_KEY or FERNET_SALT invalidates all stored tokens.
Users will need to re-connect their OAuth email accounts.
"""

import base64
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.config import settings

# Salt: read from env var, or use a fixed default.
# Changing this invalidates all encrypted tokens — that's OK,
# users just re-connect OAuth.
_salt = os.environ.get("FERNET_SALT", "luxis-fernet-v2-salt-2026").encode()

_kdf = PBKDF2HMAC(
    algorithm=hashes.SHA256(),
    length=32,
    salt=_salt,
    iterations=600_000,
)
_raw = _kdf.derive(settings.secret_key.encode())
_fernet_key = base64.urlsafe_b64encode(_raw)
_fernet = Fernet(_fernet_key)


def encrypt_token(plaintext: str) -> bytes:
    """Encrypt a token string, returning encrypted bytes for DB storage."""
    return _fernet.encrypt(plaintext.encode())


def decrypt_token(ciphertext: bytes) -> str:
    """Decrypt stored bytes back to the original token string."""
    return _fernet.decrypt(ciphertext).decode()
