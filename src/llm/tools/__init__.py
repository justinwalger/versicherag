"""Contains all relevant llm tools for the insurance chat agent."""

TOOL_REGISTRY = {}


def register_tool(key: str):
    """Decorator to register a tool in the global registry, so `get_all_tools()`
    picks it up automatically without changing the agent wiring."""

    def decorator(cls):
        TOOL_REGISTRY[key] = cls
        return cls

    return decorator


def get_all_tools() -> list:
    """Get all tools for the chat agent."""
    return list(TOOL_REGISTRY.values())


# Imported for their side effect of registering tools via @register_tool.
# Must come after register_tool is defined above, since this module imports it.
from src.llm.tools import retrieval  # noqa: F401
