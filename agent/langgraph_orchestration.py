"""Orchestration layer to run per-platform rewrites in parallel using LangGraph

This implementation uses the `StateGraph` API: each platform is a node that
writes its result into a shared `results` list using a reducer. The graph is
compiled and invoked with an initial state and a runtime context containing
the input text and per-platform overrides.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from agent.platform_agent import rewrite_for_platform

from typing_extensions import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.runtime import Runtime


def _results_reducer(a: List[Any], b: Any) -> List[Any]:
    if a is None:
        a = []
    if b is None:
        return a
    return a + [b]


class State(TypedDict):
    results: Annotated[List[Any], _results_reducer]


class Context(TypedDict, total=False):
    text: str
    target_platforms: List[str]
    tone_map: Dict[str, str]
    length_map: Dict[str, int]
    top_k: int


def _make_platform_node(platform: str):
    def node(state: State, runtime: Runtime[Context]) -> Dict[str, Any]:
        ctx = getattr(runtime, "context", None) or {}
        text = ctx.get("text")
        tone_map = ctx.get("tone_map") or {}
        length_map = ctx.get("length_map") or {}
        top_k = ctx.get("top_k", 3)
        out = rewrite_for_platform(
            text=text,
            platform=platform,
            tone=tone_map.get(platform),
            length_pref=length_map.get(platform),
            top_k=top_k,
        )
        # return an element to be reduced into `results`
        return {"results": out}

    return node


def run_parallel_rewrites(
    text: str,
    target_platforms: List[str],
    tone_map: Optional[Dict[str, str]] = None,
    length_map: Optional[Dict[str, int]] = None,
    top_k: int = 3,
) -> List[Dict[str, Any]]:
    """Run rewrites for multiple platforms using LangGraph StateGraph.

    Args:
        text: Input text to rewrite.
        target_platforms: List of platform keys to run.
        tone_map: Optional per-platform tone overrides.
        length_map: Optional per-platform length prefs.
        top_k: Number of examples to retrieve (passed to platform agent).

    Returns:
        A list of per-platform output dicts produced by `rewrite_for_platform`.
    """
    tone_map = tone_map or {}
    length_map = length_map or {}

    graph = StateGraph(state_schema=State, context_schema=Context)

    # add nodes and edges
    for p in target_platforms:
        node = _make_platform_node(p)
        graph.add_node(f"run_{p}", node)
        graph.add_edge(START, f"run_{p}")
        # mark node as a finish point so the graph can terminate after nodes run
        graph.set_finish_point(f"run_{p}")

    compiled = graph.compile()

    init_state: State = {"results": []}
    context: Context = {
        "text": text,
        "target_platforms": target_platforms,
        "tone_map": tone_map,
        "length_map": length_map,
        "top_k": top_k,
    }

    out = compiled.invoke(init_state, context=context, stream_mode="values")
    # compiled.invoke with stream_mode="values" should return the latest state dict
    if isinstance(out, dict):
        return out.get("results", [])
    # fallback: if a list of chunks is returned, try to find a dict with 'results'
    if isinstance(out, list):
        for chunk in out[::-1]:
            if isinstance(chunk, dict) and "results" in chunk:
                return chunk.get("results", [])
    return []


__all__ = ["run_parallel_rewrites"]