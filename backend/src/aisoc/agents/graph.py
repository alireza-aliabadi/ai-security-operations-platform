"""Investigation graph builder (LangGraph with sequential fallback)."""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable, Awaitable
from typing import Any

from aisoc.agents.nodes import NODE_FUNCS, NODE_ORDER
from aisoc.agents.state import InvestigationState, initial_state
from aisoc.core.logging import get_logger

logger = get_logger(__name__)

NodeFn = Callable[[InvestigationState], Awaitable[InvestigationState]]


class SequentialInvestigationPipeline:
    """Simple async pipeline that mimics a compiled graph (ainvoke + astream)."""

    def __init__(
        self,
        nodes: list[tuple[str, NodeFn]] | None = None,
        *,
        interrupt_before: list[str] | None = None,
    ) -> None:
        self.nodes = nodes or [(name, NODE_FUNCS[name]) for name in NODE_ORDER]
        self.interrupt_before = set(interrupt_before or [])

    async def ainvoke(
        self,
        state: InvestigationState,
        *,
        config: dict[str, Any] | None = None,
    ) -> InvestigationState:
        _ = config
        current = dict(state)
        for name, fn in self.nodes:
            if name in self.interrupt_before and current.get("interrupt_before_export"):
                approvals = list(current.get("approvals_needed") or [])
                approvals.append(
                    {
                        "action": f"continue_before_{name}",
                        "reason": f"Graph interrupted before {name}",
                    }
                )
                current["approvals_needed"] = approvals
                current["agent_trace"] = list(current.get("agent_trace") or []) + [
                    {
                        "agent": "graph",
                        "content": f"Interrupted before {name}",
                        "data": {"interrupt_before": name},
                    }
                ]
                break
            try:
                current = dict(await fn(current))  # type: ignore[arg-type]
            except Exception as exc:  # noqa: BLE001
                errors = list(current.get("errors") or [])
                errors.append(f"{name}: {exc}")
                current["errors"] = errors
                logger.exception("agent_node_failed", agent=name)
        return current  # type: ignore[return-value]

    async def astream(
        self,
        state: InvestigationState,
        *,
        config: dict[str, Any] | None = None,
        stream_mode: str = "updates",
    ) -> AsyncIterator[dict[str, Any]]:
        _ = config, stream_mode
        current = dict(state)
        for name, fn in self.nodes:
            if name in self.interrupt_before and current.get("interrupt_before_export"):
                yield {
                    "type": "interrupt",
                    "agent": name,
                    "content": f"Interrupted before {name}",
                    "data": {"state": current},
                }
                break
            try:
                updated = dict(await fn(current))  # type: ignore[arg-type]
                current = updated
                yield {
                    "type": "agent_update",
                    "agent": name,
                    "content": f"{name} completed",
                    "data": {
                        "trace_tail": (updated.get("agent_trace") or [])[-1:],
                        "severity": updated.get("severity"),
                        "confidence": updated.get("confidence"),
                        "keywords": updated.get("keywords"),
                    },
                }
            except Exception as exc:  # noqa: BLE001
                errors = list(current.get("errors") or [])
                errors.append(f"{name}: {exc}")
                current["errors"] = errors
                yield {
                    "type": "error",
                    "agent": name,
                    "content": str(exc),
                    "data": {},
                }
        yield {
            "type": "completed",
            "agent": "graph",
            "content": "Investigation pipeline completed",
            "data": {"state": current},
        }


def _try_build_langgraph(*, interrupt_before_export: bool):
    try:
        from langgraph.graph import END, START, StateGraph
    except Exception as exc:  # noqa: BLE001
        logger.warning("langgraph_unavailable", error=str(exc))
        return None

    graph: Any = StateGraph(InvestigationState)
    for name, fn in NODE_FUNCS.items():
        graph.add_node(name, fn)

    # Linear chain
    order = NODE_ORDER
    graph.add_edge(START, order[0])
    for left, right in zip(order, order[1:], strict=False):
        graph.add_edge(left, right)
    graph.add_edge(order[-1], END)

    interrupt_before = ["reporter"] if interrupt_before_export else None
    try:
        return graph.compile(interrupt_before=interrupt_before)
    except TypeError:
        # Older/newer langgraph may not accept interrupt_before the same way
        return graph.compile()


def build_investigation_graph(*, interrupt_before_export: bool = False) -> Any:
    """Build a LangGraph graph when available; otherwise a sequential pipeline."""
    compiled = _try_build_langgraph(interrupt_before_export=interrupt_before_export)
    if compiled is not None:
        logger.info("investigation_graph_backend", backend="langgraph")
        return compiled

    logger.info("investigation_graph_backend", backend="sequential")
    return SequentialInvestigationPipeline(
        interrupt_before=["reporter"] if interrupt_before_export else None
    )


async def run_investigation(
    query: str,
    *,
    investigation_id: str = "",
    interrupt_before_export: bool = False,
) -> InvestigationState:
    graph = build_investigation_graph(interrupt_before_export=interrupt_before_export)
    state = initial_state(
        query,
        investigation_id=investigation_id,
        interrupt_before_export=interrupt_before_export,
    )
    if hasattr(graph, "ainvoke"):
        result = await graph.ainvoke(state)
        return result  # type: ignore[return-value]
    # Extremely defensive fallback
    pipeline = SequentialInvestigationPipeline()
    return await pipeline.ainvoke(state)
