"""Tests for AI Agent serialize() utility."""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from app.ai_agent.tools import serialize


class TestSerializePrimitives:
    def test_none(self):
        assert serialize(None) is None

    def test_string(self):
        assert serialize("hello") == "hello"

    def test_empty_string(self):
        assert serialize("") == ""

    def test_bool_true(self):
        result = serialize(True)
        assert result is True

    def test_bool_false(self):
        result = serialize(False)
        assert result is False

    def test_int(self):
        assert serialize(42) == 42

    def test_float(self):
        assert serialize(3.14) == 3.14


class TestSerializeUUID:
    def test_uuid(self):
        uid = uuid.UUID("12345678-1234-5678-1234-567812345678")
        assert serialize(uid) == "12345678-1234-5678-1234-567812345678"

    def test_uuid4(self):
        uid = uuid.uuid4()
        result = serialize(uid)
        assert isinstance(result, str)
        assert result == str(uid)


class TestSerializeDecimal:
    def test_decimal(self):
        assert serialize(Decimal("1500.00")) == "1500.00"

    def test_decimal_precision(self):
        assert serialize(Decimal("0.01")) == "0.01"

    def test_decimal_large(self):
        assert serialize(Decimal("999999999.99")) == "999999999.99"

    def test_decimal_zero(self):
        assert serialize(Decimal("0.00")) == "0.00"


class TestSerializeDatetime:
    def test_date(self):
        d = date(2026, 3, 11)
        assert serialize(d) == "2026-03-11"

    def test_datetime_naive(self):
        dt = datetime(2026, 3, 11, 14, 30, 0)
        assert serialize(dt) == "2026-03-11T14:30:00"

    def test_datetime_utc(self):
        dt = datetime(2026, 3, 11, 14, 30, 0, tzinfo=timezone.utc)
        result = serialize(dt)
        assert "2026-03-11" in result
        assert "14:30:00" in result


class TestSerializeCollections:
    def test_dict(self):
        result = serialize({"key": "value"})
        assert result == {"key": "value"}

    def test_dict_with_uuid_values(self):
        uid = uuid.uuid4()
        result = serialize({"id": uid, "name": "test"})
        assert result == {"id": str(uid), "name": "test"}

    def test_dict_with_decimal_values(self):
        result = serialize({"amount": Decimal("100.50"), "tax": Decimal("21.00")})
        assert result == {"amount": "100.50", "tax": "21.00"}

    def test_list(self):
        result = serialize([1, 2, 3])
        assert result == [1, 2, 3]

    def test_list_with_mixed_types(self):
        uid = uuid.uuid4()
        result = serialize([uid, Decimal("10.00"), date(2026, 1, 1), "text"])
        assert result == [str(uid), "10.00", "2026-01-01", "text"]

    def test_tuple(self):
        result = serialize((1, 2))
        assert result == [1, 2]

    def test_empty_dict(self):
        assert serialize({}) == {}

    def test_empty_list(self):
        assert serialize([]) == []


class TestSerializeNested:
    def test_nested_dict(self):
        uid = uuid.uuid4()
        data = {
            "case": {
                "id": uid,
                "principal": Decimal("5000.00"),
                "opened": date(2026, 1, 15),
            },
            "payments": [
                {"amount": Decimal("1000.00"), "date": date(2026, 2, 1)},
            ],
        }
        result = serialize(data)
        assert result["case"]["id"] == str(uid)
        assert result["case"]["principal"] == "5000.00"
        assert result["case"]["opened"] == "2026-01-15"
        assert result["payments"][0]["amount"] == "1000.00"
        assert result["payments"][0]["date"] == "2026-02-01"

    def test_list_of_dicts(self):
        items = [
            {"id": uuid.uuid4(), "value": Decimal("1.00")},
            {"id": uuid.uuid4(), "value": Decimal("2.00")},
        ]
        result = serialize(items)
        assert len(result) == 2
        assert isinstance(result[0]["id"], str)
        assert result[1]["value"] == "2.00"

    def test_deeply_nested(self):
        data = {"a": {"b": {"c": {"d": Decimal("42.00")}}}}
        result = serialize(data)
        assert result["a"]["b"]["c"]["d"] == "42.00"


class TestSerializePydanticModel:
    def test_pydantic_model(self):
        """Objects with model_dump() should be serialized via that method."""
        class FakeModel:
            def model_dump(self):
                return {"id": uuid.uuid4(), "amount": Decimal("100.00")}

        result = serialize(FakeModel())
        assert isinstance(result["id"], str)
        assert result["amount"] == "100.00"


class TestSerializeFallback:
    def test_unknown_type_becomes_str(self):
        """Unknown types should fall back to str()."""

        class Custom:
            def __str__(self):
                return "custom_value"

        assert serialize(Custom()) == "custom_value"
