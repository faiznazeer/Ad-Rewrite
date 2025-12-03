"""Per-platform rewriting agent with Neo4j KG integration and vector retrieval."""

from __future__ import annotations

import json
import os
import shutil
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.language_models import BaseLanguageModel
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from pydantic import BaseModel, Field

from agent.kg_service import (
    get_platform_data_batch_cached,
    get_recommended_styles,
    platform_exists,
)

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
EXAMPLES_PATH = DATA_DIR / "examples.json"
DEFAULT_CHROMA_DIR = Path(os.getenv("CHROMA_DIR", BASE_DIR / "chroma_db"))
CHROMA_COLLECTION = "ad_examples"
EMBED_MODEL = os.getenv("EMBED_MODEL_NAME", "all-MiniLM-L6-v2")
LLM_MODEL = os.getenv("LLM_MODEL_NAME", "gpt-5-mini")

_embeddings: Optional[HuggingFaceEmbeddings] = None
_vectorstore: Optional[Chroma] = None
_embeddings_lock = threading.Lock()
_vectorstore_lock = threading.Lock()


def _get_embeddings() -> HuggingFaceEmbeddings:
    global _embeddings
    if _embeddings is None:
        with _embeddings_lock:
            # Double-check pattern to avoid race condition
            if _embeddings is None:
                _embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
    return _embeddings


def _get_vectorstore() -> Chroma:
    global _vectorstore
    if _vectorstore is None:
        with _vectorstore_lock:
            # Double-check pattern to avoid race condition
            if _vectorstore is None:
                if not DEFAULT_CHROMA_DIR.exists() or not any(DEFAULT_CHROMA_DIR.iterdir()):
                    raise RuntimeError(
                        f"Chroma store missing at {DEFAULT_CHROMA_DIR}. Run `python -m agent.platform_agent --ingest` first."
                    )
                _vectorstore = Chroma(
                    collection_name=CHROMA_COLLECTION,
                    persist_directory=str(DEFAULT_CHROMA_DIR),
                    embedding_function=_get_embeddings(),
                )
    return _vectorstore


def ingest_examples() -> None:
    """Load curated examples and persist them to Chroma."""
    if DEFAULT_CHROMA_DIR.exists():
        shutil.rmtree(DEFAULT_CHROMA_DIR)
    DEFAULT_CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    with open(EXAMPLES_PATH, "r", encoding="utf-8") as f:
        examples = json.load(f)
    ids = [ex["id"] for ex in examples]
    texts = [ex["text"] for ex in examples]
    metadatas = [{"platform": ex["platform"], "tone": ex["tone"]} for ex in examples]
    vectorstore = Chroma(
        collection_name=CHROMA_COLLECTION,
        persist_directory=str(DEFAULT_CHROMA_DIR),
        embedding_function=_get_embeddings(),
    )
    vectorstore.add_texts(texts=texts, metadatas=metadatas, ids=ids)


def retrieve_examples(query: str, platform: str, k: int = 3) -> List[Dict[str, Any]]:
    vectorstore = _get_vectorstore()
    docs = vectorstore.similarity_search(
        query,
        k=k,
        filter={"platform": platform},
    )
    return [{"text": d.page_content, **(d.metadata or {})} for d in docs]


class RewriteOutput(BaseModel):
    """Structured output schema for ad rewrite."""
    platform: str = Field(description="The platform name")
    rewritten_text: str = Field(description="The rewritten ad copy for the platform")
    explanation: str = Field(description="Brief explanation of the rewrite strategy")


def get_llm() -> BaseLanguageModel:
    return ChatOpenAI(model=LLM_MODEL, temperature=0.6)


REWRITE_PROMPT = PromptTemplate.from_template(
    """
You rewrite ads for specific platforms using knowledge graph insights.
Input JSON:
{{
  "platform": "{platform}",
  "tone": "{tone}",
  "input_text": "{input_text}",
  "examples": {examples},
  "strategy_context": {strategy_context}
}}

Strategy Context provides:
- Recommended styles based on platform, audience, and intent
- Creative type recommendations
- Audience preferences and intent requirements

Rewrite the ad copy for the specified platform, adapting it to match the platform's style, audience preferences, and intent requirements.
"""
)


def create_platform_chain(
    platform: str,
    tone: Optional[str] = None,
    audience: Optional[str] = None,
    user_intent: Optional[str] = None,
    product_category: Optional[str] = None,
    top_k: int = 3,
):
    """Create LangChain Runnable chain for platform-specific rewriting.
    
    Chain: retrieve examples → LLM rewrite
    
    Args:
        platform: Platform identifier
        tone: Optional tone/style override
        audience: Optional target audience
        user_intent: Optional user intent
        product_category: Optional product category
        top_k: Number of examples to retrieve
        
    Returns:
        LangChain Runnable chain
    """
    if not platform_exists(platform):
        raise ValueError(f"Unsupported platform {platform} - platform not found in knowledge graph")
    
    strategy = get_platform_data_batch_cached(
        platform=platform,
        audience=audience,
        intent=user_intent,
        product_category=product_category,
    )
    
    recommended_styles = get_recommended_styles(platform=platform, audience=audience, intent=user_intent)
    
    if tone:
        final_tone = tone
    elif recommended_styles:
        final_tone = recommended_styles[0]
    else:
        preferred_styles = strategy.get("preferred_styles", [])
        final_tone = preferred_styles[0] if preferred_styles else "casual"
    
    llm = get_llm()
    structured_llm = llm.with_structured_output(RewriteOutput)
    
    def prepare_context(input_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare context: retrieve examples, build strategy context."""
        text = input_dict["text"].strip()
        examples = retrieve_examples(text, platform, k=top_k)
        
        strategy_context = {
            "recommended_styles": recommended_styles[:5],
            "recommended_creative_types": strategy.get("recommended_creative_types", [])[:5],
        }
        
        if audience:
            strategy_context["audience"] = audience
            if "audience_preferred_styles" in strategy:
                strategy_context["audience_preferred_styles"] = strategy["audience_preferred_styles"]
        
        if user_intent:
            strategy_context["user_intent"] = user_intent
            if "intent_required_styles" in strategy:
                strategy_context["intent_required_styles"] = strategy["intent_required_styles"]
        
        if product_category:
            strategy_context["product_category"] = product_category
            if "category_suitability_score" in strategy:
                strategy_context["category_suitability_score"] = strategy["category_suitability_score"]
        
        return {
            "platform": platform,
            "tone": final_tone,
            "input_text": text,
            "strategy_context": json.dumps(strategy_context),
            "examples": json.dumps(examples[:3]),
            "examples_used": examples,
            "strategy_data": strategy,
        }
    
    def parse_llm_response(input_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Parse structured LLM response and extract rewritten text."""
        llm_result = input_dict.get("llm_result")
        
        if llm_result is None:
            # Fallback: use input text as-is
            rewritten_text = input_dict.get("input_text", "")
            llm_output = {
                "platform": platform,
                "rewritten_text": rewritten_text,
                "explanation": "No response from LLM, using input text.",
            }
        else:
            # Structured output is already a Pydantic model
            if isinstance(llm_result, RewriteOutput):
                llm_output = {
                    "platform": llm_result.platform,
                    "rewritten_text": llm_result.rewritten_text,
                    "explanation": llm_result.explanation,
                }
            else:
                # Fallback for unexpected types
                llm_output = {
                    "platform": platform,
                    "rewritten_text": str(llm_result),
                    "explanation": "Unexpected response format.",
                }
        
        rewritten_text = llm_output.get("rewritten_text", "").strip() or input_dict.get("input_text", "")
        
        return {
            **input_dict,
            "llm_output": llm_output,
            "rewritten_text": rewritten_text,
        }
    
    def finalize(input_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Format final result."""
        return {
            "platform": platform,
            "rewritten_text": input_dict["rewritten_text"],
            "explanation": input_dict["llm_output"].get("explanation", ""),
            "examples_used": input_dict["examples_used"],
            "strategy_data": input_dict.get("strategy_data", {}),
        }
    
    chain = (
        RunnableLambda(prepare_context)
        | RunnablePassthrough.assign(llm_result=REWRITE_PROMPT | structured_llm)
        | RunnableLambda(parse_llm_response)
        | RunnableLambda(finalize)
    )
    
    return chain


def rewrite_for_platform(
    text: str,
    platform: str,
    tone: Optional[str] = None,
    audience: Optional[str] = None,
    user_intent: Optional[str] = None,
    product_category: Optional[str] = None,
    top_k: int = 3,
) -> Dict[str, Any]:
    """Rewrite text for a specific platform using the platform chain with KG context.
    
    This is a convenience wrapper around create_platform_chain, specifically to call from CLI.
    For new code, prefer using create_platform_chain directly.
    
    Args:
        text: Input text to rewrite.
        platform: Platform identifier.
        tone: Optional tone/style override.
        audience: Optional target audience segment (enhances style selection).
        user_intent: Optional user intent (enhances style requirements).
        product_category: Optional product category (provides category-specific insights).
        top_k: Number of examples to retrieve.
        
    Returns:
        Platform-specific rewrite result dictionary.
    """
    chain = create_platform_chain(
        platform=platform,
        tone=tone,
        audience=audience,
        user_intent=user_intent,
        product_category=product_category,
        top_k=top_k,
    )
    return chain.invoke({"text": text})


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Platform agent utilities")
    parser.add_argument("--ingest", action="store_true", help="Ingest curated examples into Chroma")
    parser.add_argument("--text", type=str, help="Sample text to rewrite")
    parser.add_argument("--platform", type=str, help="Platform to target")
    parser.add_argument("--tone", type=str, help="Preferred tone override")
    args = parser.parse_args()

    if args.ingest:
        ingest_examples()
        print("Ingestion complete.")

    if args.text and args.platform:
        output = rewrite_for_platform(args.text, args.platform, tone=args.tone)
        print(json.dumps(output, indent=2))
