"""Core per-platform rewriting agent with retrieval, KG constraints, and validation."""

from __future__ import annotations

import json
import os
import re
import shutil
import string
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.language_models import BaseLanguageModel
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
EXAMPLES_PATH = DATA_DIR / "examples.json"
KG_PATH = DATA_DIR / "kg.json"
DEFAULT_CHROMA_DIR = Path(os.getenv("CHROMA_DIR", BASE_DIR / "chroma_db"))
CHROMA_COLLECTION = "ad_examples"
EMBED_MODEL = os.getenv("EMBED_MODEL_NAME", "all-MiniLM-L6-v2")
LLM_MODEL = os.getenv("LLM_MODEL_NAME", "gpt-5-mini")

_kg_cache: Dict[str, Any] = {}
_embeddings: Optional[HuggingFaceEmbeddings] = None
_vectorstore: Optional[Chroma] = None
_embeddings_lock = threading.Lock()
_vectorstore_lock = threading.Lock()

PROFANITY_LIST = {"damn", "hell", "shit"}
CTA_REGEX = re.compile(r"\b(buy|shop|order|get|book|reserve|save|claim)\b", re.IGNORECASE)
DISCOUNT_REGEX = re.compile(r"(?<!\w)(\d{1,2}%|half off|bogo)(?!\w)", re.IGNORECASE)
PRODUCT_REGEX = re.compile(r"(?:\bfor\s+)([A-Za-z ]+)")
# This is a regex pattern that matches any single Unicode character in the range from U+263A (☺) to U+1F645 (🙅‍♂️), which includes a wide set of emoji characters.
EMOJI_REGEX = re.compile(r"[\u263a-\U0001f645]")


def _load_kg() -> Dict[str, Any]:
    global _kg_cache
    if _kg_cache:
        return _kg_cache
    with open(KG_PATH, "r", encoding="utf-8") as f:
        _kg_cache = json.load(f)
    return _kg_cache


def _get_embeddings() -> HuggingFaceEmbeddings:
    global _embeddings
    if _embeddings is None:
        with _embeddings_lock:
            # Double-check pattern to avoid race condition
            if _embeddings is None:
                _embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
    return _embeddings


def ensure_vectorstore_ready() -> None:
    if not DEFAULT_CHROMA_DIR.exists() or not any(DEFAULT_CHROMA_DIR.iterdir()):
        raise RuntimeError(
            f"Chroma store missing at {DEFAULT_CHROMA_DIR}. Run `python -m agent.platform_agent --ingest` first."
        )


def _get_vectorstore() -> Chroma:
    global _vectorstore
    if _vectorstore is None:
        with _vectorstore_lock:
            # Double-check pattern to avoid race condition
            if _vectorstore is None:
                ensure_vectorstore_ready()
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


def sanitize_text(text: str) -> Tuple[str, List[str]]:
    issues = []
    sanitized = text.strip()
    words = sanitized.split()
    for idx, word in enumerate(words):
        clean = word.strip(string.punctuation).lower()
        if clean in PROFANITY_LIST:
            issues.append("PROFANITY_MASKED")
            words[idx] = word[0] + "*" * max(len(word) - 1, 1)
    sanitized = " ".join(words)
    return sanitized, issues


def extract_entities(text: str) -> Dict[str, Optional[str]]:
    return {
        "cta": CTA_REGEX.search(text).group(0) if CTA_REGEX.search(text) else None,
        "discount": DISCOUNT_REGEX.search(text).group(0) if DISCOUNT_REGEX.search(text) else None,
        "product": PRODUCT_REGEX.search(text).group(1).strip() if PRODUCT_REGEX.search(text) else None,
    }


def retrieve_examples(query: str, platform: str, k: int = 3) -> List[Dict[str, Any]]:
    vectorstore = _get_vectorstore()
    docs = vectorstore.similarity_search(
        query,
        k=k,
        filter={"platform": platform},
    )
    return [{"text": d.page_content, **(d.metadata or {})} for d in docs]


def get_llm() -> BaseLanguageModel:
    return ChatOpenAI(model=LLM_MODEL, temperature=0.6)


REWRITE_PROMPT = PromptTemplate.from_template(
    """
You rewrite ads for specific platforms.
Input JSON:
{{
  "platform": "{platform}",
  "tone": "{tone}",
  "input_text": "{input_text}",
  "entities": {entities},
  "kg_rules": {kg_rules},
  "examples": {examples}
}}

Respond only in JSON with keys:
platform, rewritten_text, explanation
"""
)


def execute_llm_chain(input_text: str, platform: str, tone: str, entities: Dict[str, Optional[str]], kg_rules: Dict[str, Any], examples: List[Dict[str, Any]]) -> Dict[str, Any]:
    llm = get_llm()
    chain = REWRITE_PROMPT | llm
    result = chain.invoke(
        {
            "platform": platform,
            "tone": tone,
            "input_text": input_text,
            "entities": json.dumps(entities),
            "kg_rules": json.dumps(kg_rules),
            "examples": json.dumps(examples[:3]),
        }
    )
    # Newer LangChain chat models return a BaseMessage; fall back to string if needed.
    response = getattr(result, "content", str(result))
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        return {
            "platform": platform,
            "rewritten_text": response.strip(),
            "explanation": "Model returned non-JSON, raw text forwarded.",
        }


def validate_text(text: str, platform: str, kg_rules: Dict[str, Any]) -> Dict[str, Any]:
    issues = []
    repaired = text
    if len(text) > kg_rules["max_length_chars"]:
        issues.append("MAX_LENGTH_EXCEEDED")
        repaired = repaired[: kg_rules["max_length_chars"]].rstrip()
    if not kg_rules["allow_emojis"] and EMOJI_REGEX.search(repaired):
        issues.append("EMOJI_NOT_ALLOWED")
        repaired = EMOJI_REGEX.sub("", repaired)
    if kg_rules.get("cta_required") and not CTA_REGEX.search(repaired):
        issues.append("CTA_MISSING")
        repaired = f"{repaired.rstrip(string.punctuation)}. Get yours today."
    profanity_matches = PROFANITY_LIST.intersection({w.lower().strip(string.punctuation) for w in repaired.split()})
    if profanity_matches:
        issues.append("PROFANITY_DETECTED")
    return {
        "ok": not issues,
        "issues": issues,
        "repaired_text": repaired,
    }


def create_platform_chain(
    platform: str,
    tone: Optional[str] = None,
    length_pref: Optional[int] = None,
    top_k: int = 3,
):
    """Create a LangChain Runnable chain for a specific platform.
    
    The chain processes input text through:
    1. Sanitization and entity extraction
    2. Example retrieval
    3. LLM rewriting
    4. Validation and repair
    
    Args:
        platform: Platform identifier (e.g., 'instagram', 'linkedin')
        tone: Optional tone override
        length_pref: Optional length preference override
        top_k: Number of examples to retrieve
        
    Returns:
        A LangChain Runnable chain that takes text input and returns platform-specific rewrite result.
    """
    kg = _load_kg()
    if platform not in kg:
        raise ValueError(f"Unsupported platform {platform}")
    
    kg_rules = dict(kg[platform])
    if length_pref:
        kg_rules["max_length_chars"] = min(length_pref, kg_rules["max_length_chars"])
    final_tone = tone or kg_rules["preferred_styles"][0]
    
    llm = get_llm()
    
    def prepare_context(input_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare context for the LLM chain: sanitize, extract entities, retrieve examples."""
        text = input_dict["text"]
        sanitized_text, sanitize_issues = sanitize_text(text)
        entities = extract_entities(sanitized_text)
        examples = retrieve_examples(sanitized_text, platform, k=top_k)
        
        return {
            "platform": platform,
            "tone": final_tone,
            "input_text": sanitized_text,
            "entities": json.dumps(entities),
            "kg_rules": json.dumps(kg_rules),
            "examples": json.dumps(examples[:3]),
            "sanitize_issues": sanitize_issues,
            "original_entities": entities,
            "examples_used": examples,
        }
    
    def parse_llm_response(input_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Parse LLM response and extract rewritten text."""
        # The LLM result is passed as a message, extract content
        llm_result = input_dict.get("llm_result")
        if llm_result is None:
            # Fallback if structure is different
            response = str(input_dict)
        else:
            response = getattr(llm_result, "content", str(llm_result))
        
        try:
            llm_output = json.loads(response)
        except json.JSONDecodeError:
            llm_output = {
                "platform": platform,
                "rewritten_text": response.strip(),
                "explanation": "Model returned non-JSON, raw text forwarded.",
            }
        
        rewritten_text = llm_output.get("rewritten_text", "").strip() or input_dict.get("input_text", "")
        
        return {
            **input_dict,
            "llm_output": llm_output,
            "rewritten_text": rewritten_text,
        }
    
    def validate_and_finalize(input_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and repair the rewritten text, then format final result."""
        rewritten_text = input_dict["rewritten_text"]
        validation = validate_text(rewritten_text, platform, kg_rules)
        result_text = validation["repaired_text"]
        validation.pop("repaired_text")
        validation["issues"].extend(input_dict["sanitize_issues"])
        
        return {
            "platform": platform,
            "rewritten_text": result_text,
            "explanation": input_dict["llm_output"].get("explanation", ""),
            "examples_used": input_dict["examples_used"],
            "validation": validation,
            "entities": input_dict["original_entities"],
        }
    
    # Build the chain: prepare context -> prompt -> llm -> parse -> validate
    # Use RunnablePassthrough to merge the LLM result with the context
    chain = (
        RunnableLambda(prepare_context)
        | RunnablePassthrough.assign(llm_result=REWRITE_PROMPT | llm)
        | RunnableLambda(parse_llm_response)
        | RunnableLambda(validate_and_finalize)
    )
    
    return chain


def rewrite_for_platform(
    text: str,
    platform: str,
    tone: Optional[str] = None,
    length_pref: Optional[int] = None,
    top_k: int = 3,
) -> Dict[str, Any]:
    """Rewrite text for a specific platform using the platform chain.
    
    This is a convenience wrapper around create_platform_chain for backward compatibility.
    For new code, prefer using create_platform_chain directly.
    
    Args:
        text: Input text to rewrite.
        platform: Platform identifier.
        tone: Optional tone override.
        length_pref: Optional length preference override.
        top_k: Number of examples to retrieve.
        
    Returns:
        Platform-specific rewrite result dictionary.
    """
    chain = create_platform_chain(
        platform=platform,
        tone=tone,
        length_pref=length_pref,
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
