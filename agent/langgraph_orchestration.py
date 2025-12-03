"""LangGraph orchestration for parallel platform-specific rewrites."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from agent.platform_agent import create_platform_chain

from typing_extensions import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.runtime import Runtime


def _results_reducer(a: List[Any], b: Any) -> List[Any]:
    if  b is None or isinstance(b, list):
        return a
    
    if not isinstance(b, dict):
        raise TypeError(f"Expected dict from node, got {type(b).__name__}: {b}")
    
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
    top_k: int


def _make_platform_node(platform: str):
    """Create LangGraph node that executes platform-specific chain.
    
    Args:
        platform: Platform identifier
        
    Returns:
        LangGraph node function
    """
    def node(state: State, runtime: Runtime[Context]) -> Dict[str, Any]:
        ctx = getattr(runtime, "context", None) or {}
        text = ctx.get("text")
        audience = ctx.get("audience")
        user_intent = ctx.get("user_intent")
        product_category = ctx.get("product_category")
        tone_map = ctx.get("tone_map") or {}
        top_k = ctx.get("top_k", 3)
        
        chain = create_platform_chain(
            platform=platform,
            tone=tone_map.get(platform),
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
    top_k: int = 3,
) -> List[Dict[str, Any]]:
    """Run parallel rewrites for multiple platforms using LangGraph.
    
    Args:
        text: Input text to rewrite
        target_platforms: List of platform keys
        audience: (Optional) target audience
        user_intent: (Optional) user intent
        product_category: (Optional) product category
        tone_map: (Optional) per-platform tone overrides
        top_k: Number of examples to retrieve
        
    Returns:
        List of per-platform output dicts with rewritten_text, explanation, etc.
    """
    tone_map = tone_map or {}

    graph = StateGraph(state_schema=State, context_schema=Context)

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
        "top_k": top_k,
    }

    # Invoke without stream_mode to get final state directly
    final_state = compiled.invoke(init_state, context=context)
    
    # Extract results from final state
    if isinstance(final_state, dict) and "results" in final_state:
        results = final_state["results"]
        # Ensure results is a list of dicts
        if isinstance(results, list):
            return results
    return []


__all__ = ["run_parallel_rewrites"]