"""Tests for AI Agent ToolExecutor."""

import uuid
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.ai_agent.tools.executor import ToolExecutor
from app.ai_agent.tools.registry import ToolRegistry

# ── Fixtures ─────────────────────────────────────────────────────────────

TENANT_ID = uuid.uuid4()
USER_ID = uuid.uuid4()


def _make_executor(*tools):
    """Create a ToolExecutor with the given (name, handler) pairs registered."""
    registry = ToolRegistry()
    for name, handler in tools:
        registry.register(name, f"Desc for {name}", {"type": "object"}, handler)
    return ToolExecutor(registry)


def _mock_db():
    """Create a mock AsyncSession."""
    return MagicMock()


# ── Successful execution ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_execute_simple_tool():
    """Executing a registered tool should return the handler result."""

    async def handler(**kwargs):
        return {"status": "ok", "case_id": kwargs["case_id"]}

    executor = _make_executor(("case_get", handler))
    result = await executor.execute(
        "case_get",
        {"case_id": "abc-123"},
        db=_mock_db(),
        tenant_id=TENANT_ID,
        user_id=USER_ID,
    )
    assert result == {"status": "ok", "case_id": "abc-123"}


@pytest.mark.asyncio
async def test_execute_passes_context():
    """Handler receives db, tenant_id, user_id plus tool_input kwargs."""
    received = {}

    async def handler(**kwargs):
        received.update(kwargs)
        return {"ok": True}

    executor = _make_executor(("test_tool", handler))
    db = _mock_db()

    await executor.execute(
        "test_tool",
        {"foo": "bar"},
        db=db,
        tenant_id=TENANT_ID,
        user_id=USER_ID,
    )

    assert received["db"] is db
    assert received["tenant_id"] == TENANT_ID
    assert received["user_id"] == USER_ID
    assert received["foo"] == "bar"


# ── Serialization ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_execute_serializes_result():
    """Result should be serialized (UUID -> str, Decimal -> str)."""
    case_id = uuid.uuid4()

    async def handler(**kwargs):
        return {
            "id": case_id,
            "amount": Decimal("1500.00"),
            "items": [{"sub_id": uuid.uuid4()}],
        }

    executor = _make_executor(("test_tool", handler))
    result = await executor.execute(
        "test_tool",
        {},
        db=_mock_db(),
        tenant_id=TENANT_ID,
        user_id=USER_ID,
    )

    assert result["id"] == str(case_id)
    assert result["amount"] == "1500.00"
    assert isinstance(result["items"][0]["sub_id"], str)


# ── Error handling ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_execute_unknown_tool():
    """Unknown tool should return error dict."""
    executor = _make_executor()
    result = await executor.execute(
        "nonexistent_tool",
        {},
        db=_mock_db(),
        tenant_id=TENANT_ID,
        user_id=USER_ID,
    )
    assert "error" in result
    assert "nonexistent_tool" in result["error"]


@pytest.mark.asyncio
async def test_execute_type_error():
    """TypeError from handler should be caught and returned as error."""

    async def bad_handler(**kwargs):
        raise TypeError("missing required argument: 'case_id'")

    executor = _make_executor(("bad_tool", bad_handler))
    result = await executor.execute(
        "bad_tool",
        {},
        db=_mock_db(),
        tenant_id=TENANT_ID,
        user_id=USER_ID,
    )
    assert "error" in result
    assert "bad_tool" in result["error"]


@pytest.mark.asyncio
async def test_execute_value_error():
    """ValueError from handler should be caught and returned as error."""

    async def val_handler(**kwargs):
        raise ValueError("Invalid amount")

    executor = _make_executor(("val_tool", val_handler))
    result = await executor.execute(
        "val_tool",
        {},
        db=_mock_db(),
        tenant_id=TENANT_ID,
        user_id=USER_ID,
    )
    assert "error" in result
    assert "val_tool" in result["error"]


@pytest.mark.asyncio
async def test_execute_generic_exception():
    """Generic exceptions should be caught and return a safe error."""

    async def crash_handler(**kwargs):
        raise RuntimeError("database connection lost")

    executor = _make_executor(("crash_tool", crash_handler))
    result = await executor.execute(
        "crash_tool",
        {},
        db=_mock_db(),
        tenant_id=TENANT_ID,
        user_id=USER_ID,
    )
    assert "error" in result
    assert "crash_tool" in result["error"]
    # Should NOT leak the internal error message
    assert "database connection lost" not in result["error"]


@pytest.mark.asyncio
async def test_execute_empty_input():
    """Tools with no required params should work with empty input."""

    async def no_params(**kwargs):
        return {"count": 5}

    executor = _make_executor(("simple_tool", no_params))
    result = await executor.execute(
        "simple_tool",
        {},
        db=_mock_db(),
        tenant_id=TENANT_ID,
        user_id=USER_ID,
    )
    assert result == {"count": 5}
