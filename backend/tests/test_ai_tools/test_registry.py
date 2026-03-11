"""Tests for AI Agent ToolRegistry."""

import pytest

from app.ai_agent.tools.registry import ToolDefinition, ToolRegistry


# ── Helpers ──────────────────────────────────────────────────────────────


async def _dummy_handler(**kwargs):
    return {"ok": True}


async def _another_handler(**kwargs):
    return {"result": "data"}


# ── ToolDefinition ───────────────────────────────────────────────────────


class TestToolDefinition:
    def test_dataclass_fields(self):
        td = ToolDefinition(
            name="test_tool",
            description="A test tool",
            input_schema={"type": "object", "properties": {}},
            handler=_dummy_handler,
        )
        assert td.name == "test_tool"
        assert td.description == "A test tool"
        assert td.handler is _dummy_handler


# ── ToolRegistry CRUD ────────────────────────────────────────────────────


class TestRegistryCRUD:
    def test_register_and_len(self):
        registry = ToolRegistry()
        assert len(registry) == 0

        registry.register("tool_a", "Desc A", {"type": "object"}, _dummy_handler)
        assert len(registry) == 1

    def test_contains(self):
        registry = ToolRegistry()
        registry.register("tool_a", "Desc A", {"type": "object"}, _dummy_handler)
        assert "tool_a" in registry
        assert "nonexistent" not in registry

    def test_list_tools(self):
        registry = ToolRegistry()
        registry.register("alpha", "A", {}, _dummy_handler)
        registry.register("beta", "B", {}, _another_handler)
        names = registry.list_tools()
        assert "alpha" in names
        assert "beta" in names
        assert len(names) == 2

    def test_get_handler_returns_handler(self):
        registry = ToolRegistry()
        registry.register("tool_a", "Desc", {}, _dummy_handler)
        handler = registry.get_handler("tool_a")
        assert handler is _dummy_handler

    def test_get_handler_returns_none_for_unknown(self):
        registry = ToolRegistry()
        assert registry.get_handler("nonexistent") is None

    def test_get_definition(self):
        schema = {"type": "object", "properties": {"x": {"type": "string"}}}
        registry = ToolRegistry()
        registry.register("tool_a", "Desc A", schema, _dummy_handler)

        defn = registry.get_definition("tool_a")
        assert defn is not None
        assert defn.name == "tool_a"
        assert defn.description == "Desc A"
        assert defn.input_schema == schema
        assert defn.handler is _dummy_handler

    def test_get_definition_returns_none_for_unknown(self):
        registry = ToolRegistry()
        assert registry.get_definition("nonexistent") is None

    def test_overwrite_existing_tool(self):
        registry = ToolRegistry()
        registry.register("tool_a", "V1", {}, _dummy_handler)
        registry.register("tool_a", "V2", {}, _another_handler)

        assert len(registry) == 1
        defn = registry.get_definition("tool_a")
        assert defn.description == "V2"
        assert defn.handler is _another_handler


# ── get_claude_tools() format ────────────────────────────────────────────


class TestGetClaudeTools:
    def test_output_format(self):
        registry = ToolRegistry()
        schema = {
            "type": "object",
            "properties": {"case_id": {"type": "string"}},
            "required": ["case_id"],
        }
        registry.register("case_get", "Haal dossier op", schema, _dummy_handler)

        tools = registry.get_claude_tools()
        assert len(tools) == 1

        tool = tools[0]
        assert tool["name"] == "case_get"
        assert tool["description"] == "Haal dossier op"
        assert tool["input_schema"] == schema
        # Must NOT contain handler (not serializable)
        assert "handler" not in tool

    def test_multiple_tools(self):
        registry = ToolRegistry()
        registry.register("a", "A", {}, _dummy_handler)
        registry.register("b", "B", {}, _another_handler)
        registry.register("c", "C", {}, _dummy_handler)

        tools = registry.get_claude_tools()
        assert len(tools) == 3
        names = {t["name"] for t in tools}
        assert names == {"a", "b", "c"}

    def test_empty_registry(self):
        registry = ToolRegistry()
        assert registry.get_claude_tools() == []

    def test_claude_tools_have_required_keys(self):
        registry = ToolRegistry()
        registry.register("t", "desc", {"type": "object"}, _dummy_handler)
        tool = registry.get_claude_tools()[0]
        assert set(tool.keys()) == {"name", "description", "input_schema"}


# ── register_all_tools / create_default_registry ─────────────────────────


class TestDefaultRegistry:
    def test_register_all_tools(self):
        from app.ai_agent.tools.definitions import register_all_tools

        registry = ToolRegistry()
        register_all_tools(registry)
        assert len(registry) == 34  # 34 tools defined in definitions.py

    def test_create_default_registry(self):
        from app.ai_agent.tools.definitions import create_default_registry

        registry = create_default_registry()
        assert len(registry) == 34

    def test_all_tools_have_handlers(self):
        from app.ai_agent.tools.definitions import create_default_registry

        registry = create_default_registry()
        for name in registry.list_tools():
            handler = registry.get_handler(name)
            assert handler is not None, f"Tool '{name}' has no handler"
            assert callable(handler), f"Tool '{name}' handler is not callable"

    def test_all_tools_have_schemas(self):
        from app.ai_agent.tools.definitions import create_default_registry

        registry = create_default_registry()
        for name in registry.list_tools():
            defn = registry.get_definition(name)
            assert defn.input_schema is not None, f"Tool '{name}' has no schema"
            assert "type" in defn.input_schema, f"Tool '{name}' schema missing 'type'"

    def test_all_tools_have_descriptions(self):
        from app.ai_agent.tools.definitions import create_default_registry

        registry = create_default_registry()
        for name in registry.list_tools():
            defn = registry.get_definition(name)
            assert defn.description, f"Tool '{name}' has empty description"
            assert len(defn.description) > 10, f"Tool '{name}' description too short"

    def test_claude_tools_format_compatible(self):
        """All tools should produce valid Claude API format."""
        from app.ai_agent.tools.definitions import create_default_registry

        registry = create_default_registry()
        tools = registry.get_claude_tools()
        assert len(tools) == 34

        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "input_schema" in tool
            assert isinstance(tool["name"], str)
            assert isinstance(tool["description"], str)
            assert isinstance(tool["input_schema"], dict)

    def test_no_duplicate_tool_names(self):
        from app.ai_agent.tools.definitions import create_default_registry

        registry = create_default_registry()
        names = registry.list_tools()
        assert len(names) == len(set(names)), "Duplicate tool names found"
