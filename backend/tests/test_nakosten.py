"""Tests for nakosten (post-judgment costs) calculation."""

from decimal import Decimal

from app.collections.nakosten import calculate_nakosten


def test_nakosten_zonder_betekening():
    assert calculate_nakosten("zonder_betekening") == Decimal("189.00")


def test_nakosten_met_betekening():
    assert calculate_nakosten("met_betekening") == Decimal("287.00")


def test_nakosten_none():
    assert calculate_nakosten(None) == Decimal("0.00")


def test_nakosten_empty_string():
    assert calculate_nakosten("") == Decimal("0.00")
