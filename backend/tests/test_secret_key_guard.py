"""Tests for the SECRET_KEY startup guard (AUDIT-B1).

A weak/placeholder SECRET_KEY lets an attacker forge valid JWTs. The guard
must refuse to start in production AND in any environment that is not an
explicit dev/test env (default-secure: an unset/misspelled APP_ENV is treated
as production). Dev/test/CI may boot on a weak key but must be flagged.
"""

from app.config import (
    MIN_SECRET_KEY_LENGTH,
    SECRET_KEY_BLACKLIST,
    secret_key_status,
)

STRONG_KEY = "x" * MIN_SECRET_KEY_LENGTH  # exactly the minimum length


def test_placeholder_in_production_is_weak_and_enforced():
    weak, enforced = secret_key_status(
        "change-this-to-a-random-string-in-production", "production"
    )
    assert weak is True
    assert enforced is True  # -> startup must exit


def test_placeholder_in_development_warns_but_boots():
    weak, enforced = secret_key_status(
        "change-this-to-a-random-string-in-production", "development"
    )
    assert weak is True
    assert enforced is False  # dev is tolerated (warning only)


def test_strong_key_in_production_is_accepted():
    weak, enforced = secret_key_status(STRONG_KEY, "production")
    assert weak is False
    assert enforced is True


def test_short_key_is_weak():
    weak, _ = secret_key_status("short", "production")
    assert weak is True


def test_key_one_char_below_minimum_is_weak():
    weak, _ = secret_key_status("y" * (MIN_SECRET_KEY_LENGTH - 1), "production")
    assert weak is True


def test_all_blacklisted_keys_are_weak():
    for key in SECRET_KEY_BLACKLIST:
        weak, _ = secret_key_status(key, "production")
        assert weak is True, f"{key!r} should be flagged weak"


def test_unset_app_env_is_enforced():
    """An empty/unset APP_ENV must be treated as production (default-secure)."""
    _, enforced = secret_key_status(STRONG_KEY, "")
    assert enforced is True


def test_misspelled_production_env_is_enforced():
    """A typo'd APP_ENV must NOT silently disable the guard."""
    _, enforced = secret_key_status("change-this-to-a-random-string-in-production", "prodction")
    assert enforced is True


def test_known_dev_envs_are_not_enforced():
    for env in ["development", "dev", "test", "testing", "local", "ci", "  DEV  "]:
        _, enforced = secret_key_status(STRONG_KEY, env)
        assert enforced is False, f"{env!r} should be a non-enforced dev env"
