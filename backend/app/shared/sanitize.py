"""Filename sanitization for Content-Disposition headers (SEC-23).

Prevents header injection via crafted filenames containing quotes,
newlines, or other control characters. Follows RFC 6266.
"""

import re
import unicodedata


def safe_filename(name: str) -> str:
    """Sanitize a filename for use in Content-Disposition headers.

    - Strips control characters (\\r, \\n, \\x00-\\x1f)
    - Removes double quotes
    - Normalizes unicode to NFC
    - Falls back to 'download' if nothing remains
    """
    # Normalize unicode
    name = unicodedata.normalize("NFC", name)
    # Strip control characters and double quotes
    name = re.sub(r'[\x00-\x1f\x7f"\\]', "", name)
    # Strip leading/trailing whitespace and dots (Windows safety)
    name = name.strip(". ")
    return name or "download"


def content_disposition(disposition: str, filename: str) -> str:
    """Build a safe Content-Disposition header value.

    Args:
        disposition: 'inline' or 'attachment'
        filename: the raw filename to sanitize

    Returns:
        A header value like: attachment; filename="safe.pdf"; filename*=UTF-8''safe.pdf
    """
    safe = safe_filename(filename)
    # ASCII-safe version for filename="..."
    ascii_safe = safe.encode("ascii", errors="replace").decode("ascii")
    # UTF-8 encoded version for filename*= (RFC 5987)
    from urllib.parse import quote
    utf8_encoded = quote(safe, safe="")
    return f'{disposition}; filename="{ascii_safe}"; filename*=UTF-8\'\'{utf8_encoded}'
