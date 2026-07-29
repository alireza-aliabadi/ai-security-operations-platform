"""SSE-friendly streaming helpers for the investigation graph."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

from aisoc.agents.graph import (
    SequentialInvestigationPipeline,
    build_investigation_graph,
)
from aisoc.agents.nodes import NODE_FUNCS, NODE_ORDER
from aisoc.agents.state import InvestigationState, initial_state


def _event(
    event_type: str,
    *,
    agent: str = "",
    content: str = "",
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "type": event_type,
        "agent": agent,
        "content": content,
        "data": data or {},
    }


async def stream_investigation(
    query: str,
    *,
    investigation_id: str = "",
    interrupt_before_export: bool = False,
) -> AsyncIterator[dict[str, Any]]:
    """Yield SSE-friendly events while running the investigation graph."""
    state = initial_state(
        query,
        investigation_id=investigation_id,
        interrupt_before_export=interrupt_before_export,
    )
    yield _event("started", agent="graph", content="Investigation started", data={"query": query})

    graph = build_investigation_graph(interrupt_before_export=interrupt_before_export)

    # Prefer native astream when present (LangGraph or our pipeline)
    if hasattr(graph, "astream"):
        final_state: InvestigationState | None = None
        try:
            async for chunk in graph.astream(state):
                if isinstance(chunk, dict) and "type" in chunk and "agent" in chunk:
                    # Our SequentialInvestigationPipeline format
                    if chunk.get("type") == "completed":
                        final_state = chunk.get("data", {}).get("state")  # type: ignore[assignment]
                    yield chunk
                    continue

                # LangGraph stream_mode=updates yields {node_name: partial_state}
                if isinstance(chunk, dict):
                    for agent, partial in chunk.items():
                        if agent in ("__start__", "__end__"):
                            continue
                        content = f"{agent} updated"
                        data: dict[str, Any] = {}
                        if isinstance(partial, dict):
                            data = {
                                "keywords": partial.get("keywords"),
                                "severity": partial.get("severity"),
                                "confidence": partial.get("confidence"),
                                "trace_tail": (partial.get("agent_trace") or [])[-1:],
                            }
                            # Merge into running state for final event
                            state = {**state, **partial}  # type: ignore[misc]
                            final_state = state
                        yield _event("agent_update", agent=str(agent), content=content, data=data)
            yield _event(
                "completed",
                agent="graph",
                content="Investigation completed",
                data={"state": final_state or state},
            )
            return
        except TypeError:
            # Some langgraph versions require stream_mode kwarg differently
            pass
        except Exception as exc:  # noqa: BLE001
            yield _event("error", agent="graph", content=str(exc))

    # Manual sequential streaming fallback
    pipeline = SequentialInvestigationPipeline(
        [(name, NODE_FUNCS[name]) for name in NODE_ORDER],
        interrupt_before=["reporter"] if interrupt_before_export else None,
    )
    async for event in pipeline.astream(state):
        yield event


def format_sse(event: dict[str, Any]) -> str:
    """Format a dict as an SSE data frame."""
    return f"data: {json.dumps(event, default=str)}\n\n"
