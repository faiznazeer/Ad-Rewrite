"""Orchestration layer to run per-platform rewrites in parallel using LangGraph

This implementation uses the `StateGraph` API: each platform gets its own
LangChain chain that is executed in parallel. The graph orchestrates these
chains, with each node creating and invoking a platform-specific chain.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from agent.platform_agent import create_platform_chain

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
    audience: Optional[str]
    user_intent: Optional[str]
    product_category: Optional[str]
    tone_map: Dict[str, str]
    length_map: Dict[str, int]
    top_k: int


def _make_platform_node(platform: str):
    """Create a LangGraph node that executes a platform-specific LangChain chain.
    
    Each platform gets its own chain that handles:
    - Text sanitization and entity extraction
    - Example retrieval
    - LLM-based rewriting with KG context (audience, intent, category)
    - Validation and repair
    
    Args:
        platform: Platform identifier (e.g., 'instagram', 'linkedin')
        
    Returns:
        A LangGraph node function that executes the platform chain.
    """
    def node(state: State, runtime: Runtime[Context]) -> Dict[str, Any]:
        ctx = getattr(runtime, "context", None) or {}
        text = ctx.get("text")
        audience = ctx.get("audience")
        user_intent = ctx.get("user_intent")
        product_category = ctx.get("product_category")
        tone_map = ctx.get("tone_map") or {}
        length_map = ctx.get("length_map") or {}
        top_k = ctx.get("top_k", 3)
        
        # Create the platform-specific chain with KG context
        chain = create_platform_chain(
            platform=platform,
            tone=tone_map.get(platform),
            length_pref=length_map.get(platform),
            audience=audience,
            user_intent=user_intent,
            product_category=product_category,
            top_k=top_k,
        )
        
        # Invoke the chain with the input text
        result = chain.invoke({"text": text})
        
        # return an element to be reduced into `results`
        return {"results": result}

    return node


def run_parallel_rewrites(
    text: str,
    target_platforms: List[str],
    audience: Optional[str] = None,
    user_intent: Optional[str] = None,
    product_category: Optional[str] = None,
    tone_map: Optional[Dict[str, str]] = None,
    length_map: Optional[Dict[str, int]] = None,
    top_k: int = 3,
) -> List[Dict[str, Any]]:
    """Run rewrites for multiple platforms using LangGraph to orchestrate platform chains.

    Each platform gets its own LangChain chain that is executed in parallel via LangGraph.
    The chains leverage Neo4j knowledge graph context (audience, intent, category) to provide
    enhanced, context-aware rewrites.

    Args:
        text: Input text to rewrite.
        target_platforms: List of platform keys to run (e.g., ['instagram', 'linkedin']).
        audience: Optional target audience segment (e.g., 'gen-z', 'b2b professionals').
        user_intent: Optional user intent/funnel stage (e.g., 'awareness', 'purchase').
        product_category: Optional product category (e.g., 'tech', 'fashion', 'b2b').
        tone_map: Optional per-platform tone/style overrides.
        length_map: Optional per-platform length prefs.
        top_k: Number of examples to retrieve for each platform.

    Returns:
        A list of per-platform output dicts, each containing:
        - platform: Platform identifier
        - rewritten_text: Final rewritten text (optimized for audience/intent/category)
        - explanation: LLM explanation
        - examples_used: Retrieved examples
        - validation: Validation results
        - entities: Extracted entities
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
        "audience": audience,
        "user_intent": user_intent,
        "product_category": product_category,
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