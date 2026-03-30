"""Tool executor — executes tool_use blocks from Claude API responses."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_agent.tools import serialize
from app.ai_agent.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class ToolExecutor:
    """Executes AI agent tool calls against the Luxis service layer.

    Takes tool_use blocks from Claude API responses, looks up the handler
    in the registry, calls it with the appropriate context, and serializes
    the result back to JSON-safe format.
    """

    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry

    async def execute(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        *,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Execute a single tool call.

        Args:
            tool_name: Name of the tool to execute.
            tool_input: Parameters from Claude's tool_use block.
            db: Async database session.
            tenant_id: Current tenant UUID.
            user_id: Current user UUID (for audit trail).

        Returns:
            Serialized result dict (JSON-safe).
        """
        handler = self.registry.get_handler(tool_name)
        if handler is None:
            logger.warning("Unknown tool requested: %s", tool_name)
            return {"error": f"Onbekende tool: {tool_name}"}

        try:
            result = await handler(
                db=db,
                tenant_id=tenant_id,
                user_id=user_id,
                **tool_input,
            )
            return serialize(result)
        except TypeError as e:
            logger.error("Tool '%s' parameter error: %s", tool_name, e)
            return {"error": f"Ongeldige parameters voor {tool_name}: {e}"}
        except ValueError as e:
            logger.error("Tool '%s' value error: %s", tool_name, e)
            return {"error": f"Ongeldige waarde voor {tool_name}: {e}"}
        except Exception:
            logger.exception("Tool '%s' execution failed", tool_name)
            return {"error": f"Uitvoering van {tool_name} mislukt"}
