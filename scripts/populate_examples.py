"""Script to populate Neo4j knowledge graph with example ad copy.

This script loads existing examples from examples.json, creates Example nodes,
links them to platforms and styles, and generates additional examples to reach 500+.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path
from typing import Dict, List, Tuple

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


def generate_additional_examples() -> List[Dict]:
    """Generate additional examples to reach 500+ total."""
    platforms = ["instagram", "linkedin", "tiktok", "facebook", "google", "twitter", "youtube", "pinterest"]
    styles = ["fun", "professional", "energetic", "visual", "casual", "educational", "conversational", "humorous", "inspirational", "bold"]
    intents = ["awareness", "consideration", "purchase", "engagement"]
    categories = ["tech", "fashion", "food", "services", "b2b", "healthcare", "education"]
    
    # Template examples by platform and style
    templates = {
        "instagram": {
            "fun": [
                "New collection dropping Friday—early access for followers! 🎉",
                "Swipe to see our summer edit—which look is your vibe?",
                "Weekend mood: fresh blooms + iced lattes. Tag us!",
            ],
            "visual": [
                "Golden hour vibes ✨ Shop the look in bio",
                "Before & after glow—this serum changed everything.",
                "Mood board Monday: dreamy pastels and soft textures.",
            ],
            "energetic": [
                "Rooftop yoga at sunrise—who's in? 🧘‍♀️",
                "Flash sale ends tonight! 50% off everything.",
                "New drop alert: limited edition collab is live!",
            ],
        },
        "linkedin": {
            "professional": [
                "We're excited to share our Q3 results and strategic initiatives.",
                "Join our upcoming webinar on digital transformation best practices.",
                "Case study: How we helped clients reduce operational costs by 30%.",
            ],
            "educational": [
                "5 key trends shaping the future of remote work in 2024.",
                "Download our latest industry report on AI adoption.",
                "Expert insights: Building resilient supply chains.",
            ],
            "neutral": [
                "We're hiring! Open positions across engineering and product.",
                "Q3 earnings call scheduled for next Tuesday.",
                "Partnership announcement: Expanding our platform capabilities.",
            ],
        },
        "tiktok": {
            "energetic": [
                "POV: You found the perfect summer fit 🎬",
                "This hack changed my life—try it and tag me!",
                "30-second tutorial: Get this look in 3 steps.",
            ],
            "fun": [
                "Rate my outfit 1-10 👀",
                "Tell me I'm wrong—this is the best snack combo.",
                "POV: You're the main character energy ✨",
            ],
            "humorous": [
                "Me trying to be aesthetic vs reality 😂",
                "When you finally find the perfect filter",
                "Plot twist: This actually works!",
            ],
        },
        "facebook": {
            "conversational": [
                "What's your favorite way to unwind after work? Share below!",
                "We love hearing from our community—what would you like to see next?",
                "Weekend plans? We've got some ideas for you!",
            ],
            "friendly": [
                "Happy Friday! Here's what's new this week.",
                "Thank you to everyone who joined us at our event!",
                "We're grateful for your continued support.",
            ],
            "inspirational": [
                "Small steps lead to big changes. What's your goal this week?",
                "Celebrating our community's achievements—you inspire us!",
                "Together we can make a difference. Join us!",
            ],
        },
        "google": {
            "concise": [
                "Free shipping on orders over $50. Shop now.",
                "Same-day delivery available. Order by 2pm.",
                "Limited time: 20% off all items. Use code SAVE20.",
            ],
            "neutral": [
                "Book your appointment online in minutes.",
                "Expert service at competitive prices.",
                "Trusted by thousands of satisfied customers.",
            ],
        },
        "twitter": {
            "conversational": [
                "What's trending in your industry today?",
                "Quick poll: What's your biggest challenge this quarter?",
                "Thread: 5 things we learned building our product.",
            ],
            "bold": [
                "Hot take: This changes everything.",
                "Unpopular opinion: Here's why this matters.",
                "Breaking: Major update coming next week.",
            ],
        },
        "youtube": {
            "educational": [
                "Full tutorial: Master this skill in 10 minutes.",
                "Deep dive: Understanding the fundamentals.",
                "Step-by-step guide: Everything you need to know.",
            ],
            "professional": [
                "Expert interview: Industry insights and trends.",
                "Case study analysis: What worked and what didn't.",
                "Best practices: How to succeed in this field.",
            ],
        },
        "pinterest": {
            "visual": [
                "50+ ideas for your next project. Save for later!",
                "Dream home inspiration: Modern meets cozy.",
                "DIY tutorial: Transform your space on a budget.",
            ],
            "inspirational": [
                "Create the life you want, one pin at a time.",
                "Endless inspiration for your next adventure.",
                "Your vision board starts here.",
            ],
        },
    }
    
    new_examples = []
    example_id_counter = 1000  # Start after existing examples
    
    # Generate examples from templates
    for platform in platforms:
        platform_templates = templates.get(platform, {})
        for style, template_texts in platform_templates.items():
            for template in template_texts:
                new_examples.append({
                    "id": f"{platform[:3]}_gen_{example_id_counter}",
                    "platform": platform,
                    "tone": style,
                    "text": template,
                })
                example_id_counter += 1
    
    # Generate random combinations to fill remaining slots
    target_total = 500
    remaining = target_total - len(new_examples)
    
    for i in range(remaining):
        platform = random.choice(platforms)
        style = random.choice(styles)
        
        # Generate text based on platform and style
        text = generate_example_text(platform, style)
        
        new_examples.append({
            "id": f"{platform[:3]}_gen_{example_id_counter}",
            "platform": platform,
            "tone": style,
            "text": text,
        })
        example_id_counter += 1
    
    return new_examples


def generate_example_text(platform: str, style: str) -> str:
    """Generate example text based on platform and style."""
    # Simple text generation based on patterns
    patterns = {
        "instagram": {
            "fun": ["New drop alert! 🎉", "Swipe to see more ✨", "Tag your bestie! 💕"],
            "visual": ["Shop the look in bio", "Before & after transformation", "Mood board inspo"],
            "energetic": ["Flash sale ends tonight!", "Limited edition—get yours!", "Don't miss out!"],
        },
        "linkedin": {
            "professional": ["We're excited to announce...", "Join our upcoming webinar", "Case study: How we..."],
            "educational": ["5 key trends in...", "Download our latest report", "Expert insights on..."],
            "neutral": ["We're hiring!", "Partnership announcement", "Q3 results"],
        },
        "tiktok": {
            "energetic": ["POV: You found...", "This hack changed my life", "30-second tutorial"],
            "fun": ["Rate this 1-10", "Tell me I'm wrong", "POV: Main character energy"],
            "humorous": ["Plot twist!", "Me trying to be aesthetic", "When you finally..."],
        },
    }
    
    platform_patterns = patterns.get(platform, {})
    style_patterns = platform_patterns.get(style, [])
    
    if style_patterns:
        return random.choice(style_patterns)
    
    # Fallback generic text
    return f"Check out our latest {style} content on {platform}!"


def populate_existing_examples():
    """Load and populate existing examples from examples.json."""
    print("Loading existing examples from examples.json...")
    existing_examples = load_existing_examples()
    print(f"Found {len(existing_examples)} existing examples")
    
    print("Creating Example nodes and relationships...")
    for i, example in enumerate(existing_examples, 1):
        if i % 50 == 0:
            print(f"  Processed {i}/{len(existing_examples)} examples...")
        
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
    
    print(f"✓ Created {len(existing_examples)} Example nodes with relationships")


def populate_generated_examples():
    """Generate and populate additional examples."""
    print("Generating additional examples...")
    new_examples = generate_additional_examples()
    print(f"Generated {len(new_examples)} new examples")
    
    print("Creating Example nodes and relationships...")
    for i, example in enumerate(new_examples, 1):
        if i % 100 == 0:
            print(f"  Processed {i}/{len(new_examples)} examples...")
        
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
    
    print(f"✓ Created {len(new_examples)} new Example nodes with relationships")


def main():
    """Main function to populate examples."""
    print("=" * 60)
    print("Populating Neo4j Knowledge Graph with Examples")
    print("=" * 60)
    print()
    
    # Populate existing examples
    populate_existing_examples()
    print()
    
    # Generate and populate additional examples
    populate_generated_examples()
    
    # Get total count
    result = execute_query("MATCH (e:Example) RETURN count(e) as total")
    total = result[0]["total"] if result else 0
    
    print("\n" + "=" * 60)
    print(f"Example population complete! Total examples: {total}")
    print("=" * 60)
    print("\nExample queries:")
    print("MATCH (e:Example)-[:DEMONSTRATES]->(p:Platform {name: 'instagram'})")
    print("RETURN e.text LIMIT 5")
    print("\nMATCH (e:Example)-[:USES_STYLE]->(s:ContentStyle {name: 'fun'})")
    print("RETURN e.text LIMIT 5")


if __name__ == "__main__":
    main()

