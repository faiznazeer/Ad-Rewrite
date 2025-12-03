"""Script to populate Neo4j knowledge graph with example ad copy.

This script loads examples from examples.json, creates Example nodes,
and links them to platforms, styles, audiences, and intents.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path
from typing import Dict, List

# Add parent directory to path to import agent modules
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from agent.kg_service import execute_query


# Mapping from example.json "tone" values to ContentStyle names
TONE_TO_STYLE_MAP = {
    "fun": "fun",
    "playful": "fun",
    "bold": "bold",
    "visual": "visual",
    "energetic": "energetic",
    "professional": "professional",
    "neutral": "neutral",
    "formal": "professional",
    "concise": "concise",
    "informative": "educational",
    "edgy": "bold",
    "friendly": "conversational",
    "casual": "casual",
    "humorous": "humorous",
    "inspirational": "inspirational",
    "conversational": "conversational",
    "upbeat": "energetic",
    "informal": "casual",
    "quirky": "humorous",
}


def load_existing_examples() -> List[Dict]:
    """Load existing examples from examples.json."""
    examples_path = BASE_DIR / "data" / "examples.json"
    with open(examples_path, "r", encoding="utf-8") as f:
        return json.load(f)


def create_example_node(example: Dict, performance_score: float = None) -> None:
    """Create an Example node in Neo4j."""
    if performance_score is None:
        # Generate realistic performance score (0.6-0.95)
        performance_score = round(random.uniform(0.6, 0.95), 2)
    
    # Generate engagement rate (0.02-0.15)
    engagement_rate = round(random.uniform(0.02, 0.15), 4)
    
    query = """
    MERGE (e:Example {id: $id})
    SET e.text = $text,
        e.platform = $platform,
        e.tone = $tone,
        e.performance_score = $performance_score,
        e.engagement_rate = $engagement_rate,
        e.created_at = datetime()
    """
    execute_query(query, {
        "id": example["id"],
        "text": example["text"],
        "platform": example["platform"],
        "tone": example.get("tone", ""),
        "performance_score": performance_score,
        "engagement_rate": engagement_rate,
    })


def link_example_to_platform(example_id: str, platform: str) -> None:
    """Link Example to Platform."""
    query = """
    MATCH (e:Example {id: $example_id})
    MATCH (p:Platform {name: $platform})
    MERGE (e)-[:DEMONSTRATES]->(p)
    """
    execute_query(query, {"example_id": example_id, "platform": platform.lower()})


def link_example_to_style(example_id: str, style: str) -> None:
    """Link Example to ContentStyle."""
    query = """
    MATCH (e:Example {id: $example_id})
    MATCH (cs:ContentStyle {name: $style})
    MERGE (e)-[:USES_STYLE]->(cs)
    """
    execute_query(query, {"example_id": example_id, "style": style.lower()})


def link_example_to_audience(example_id: str, audience: str) -> None:
    """Link Example to Audience (optional, inferred)."""
    query = """
    MATCH (e:Example {id: $example_id})
    MATCH (a:Audience {name: $audience})
    MERGE (e)-[:TARGETS]->(a)
    """
    execute_query(query, {"example_id": example_id, "audience": audience.lower()})


def link_example_to_intent(example_id: str, intent: str) -> None:
    """Link Example to UserIntent (optional, inferred)."""
    query = """
    MATCH (e:Example {id: $example_id})
    MATCH (ui:UserIntent {name: $intent})
    MERGE (e)-[:FOR_INTENT]->(ui)
    """
    execute_query(query, {"example_id": example_id, "intent": intent.lower()})


def infer_audience_for_platform(platform: str) -> str:
    """Infer primary audience for a platform."""
    audience_map = {
        "instagram": "gen-z",
        "tiktok": "gen-z",
        "linkedin": "b2b professionals",
        "facebook": "millennials",
        "google": "millennials",
        "twitter": "millennials",
        "youtube": "millennials",
        "pinterest": "millennials",
    }
    return audience_map.get(platform.lower(), "millennials")


def infer_intent_from_text(text: str) -> str:
    """Infer user intent from example text."""
    text_lower = text.lower()
    
    # Purchase intent keywords
    if any(word in text_lower for word in ["buy", "shop", "order", "get", "save", "sale", "discount", "deal"]):
        return "purchase"
    
    # Engagement intent keywords
    if any(word in text_lower for word in ["tag", "share", "vote", "duet", "remix", "challenge"]):
        return "engagement"
    
    # Consideration intent keywords
    if any(word in text_lower for word in ["learn", "discover", "explore", "try", "download", "webinar"]):
        return "consideration"
    
    # Awareness intent keywords
    if any(word in text_lower for word in ["announcing", "introducing", "new", "launch"]):
        return "awareness"
    
    # Default to engagement
    return "engagement"


def populate_examples():
    """Load and populate examples from examples.json."""
    print("Loading examples from examples.json...")
    examples = load_existing_examples()
    print(f"Found {len(examples)} examples")
    
    print("Creating Example nodes and relationships...")
    for i, example in enumerate(examples, 1):
        if i % 50 == 0:
            print(f"  Processed {i}/{len(examples)} examples...")
        
        # Create example node
        create_example_node(example)
        
        # Link to platform
        platform = example["platform"].lower()
        link_example_to_platform(example["id"], platform)
        
        # Link to style
        tone = example.get("tone", "").lower()
        style = TONE_TO_STYLE_MAP.get(tone, "casual")
        link_example_to_style(example["id"], style)
        
        # Infer and link audience
        audience = infer_audience_for_platform(platform)
        link_example_to_audience(example["id"], audience)
        
        # Infer and link intent
        intent = infer_intent_from_text(example["text"])
        link_example_to_intent(example["id"], intent)
    
    print(f"✓ Created {len(examples)} Example nodes with relationships")


def main():
    """Main function to populate examples."""
    print("=" * 60)
    print("Populating Neo4j Knowledge Graph with Examples")
    print("=" * 60)
    print()
    
    # Populate examples from examples.json
    populate_examples()
    
    # Get total count
    result = execute_query("MATCH (e:Example) RETURN count(e) as total")
    total = result[0]["total"] if result else 0
    
    print("\n" + "=" * 60)
    print(f"Example population complete! Total examples: {total}")
    print("=" * 60)
    print("\nNote: All examples are loaded from data/examples.json")
    print("To add more examples, edit data/examples.json and re-run this script.")
    print("\nExample queries:")
    print("MATCH (e:Example)-[:DEMONSTRATES]->(p:Platform {name: 'instagram'})")
    print("RETURN e.text LIMIT 5")
    print("\nMATCH (e:Example)-[:USES_STYLE]->(s:ContentStyle {name: 'fun'})")
    print("RETURN e.text LIMIT 5")


if __name__ == "__main__":
    main()

