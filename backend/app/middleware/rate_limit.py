"""Rate limiting middleware — protects auth endpoints from brute-force attacks."""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
