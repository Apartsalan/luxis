"""Tool registry — maps tool names to handlers and JSON schemas for Claude API."""

from __future__ import annotations

import logging
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ToolDefinition:
    """A single tool available to the AI agent."""

    name: str
    description: str
    input_schema: dict[str, Any]
    handler: Callable[..., Coroutine[Any, Any, dict]]


class ToolRegistry:
    """Registry of all AI agent tools.

    Usage:
        registry = ToolRegistry()
        registry.register("case_get", "Haal dossierdetails op", schema, handler_fn)
        tools = registry.get_claude_tools()  # For Claude API tools= parameter
        handler = registry.get_handler("case_get")
    """

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(
        self,
        name: str,
        description: str,
        input_schema: dict[str, Any],
        handler: Callable[..., Coroutine[Any, Any, dict]],
    ) -> None:
        """Register a tool with its schema and handler."""
        if name in self._tools:
            logger.warning("Tool '%s' already registered, overwriting", name)
        self._tools[name] = ToolDefinition(
            name=name,
            description=description,
            input_schema=input_schema,
            handler=handler,
        )

    def get_handler(self, name: str) -> Callable[..., Coroutine[Any, Any, dict]] | None:
        """Get the handler function for a tool by name."""
        tool = self._tools.get(name)
        return tool.handler if tool else None

    def get_claude_tools(self) -> list[dict[str, Any]]:
        """Get tool definitions in Claude API format.

        Returns a list of dicts compatible with anthropic client.messages.create(tools=...).
        """
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
            }
            for tool in self._tools.values()
        ]

    def list_tools(self) -> list[str]:
        """List all registered tool names."""
        return list(self._tools.keys())

    def get_definition(self, name: str) -> ToolDefinition | None:
        """Get full tool definition by name."""
        return self._tools.get(name)

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools
