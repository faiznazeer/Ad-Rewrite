"""Script to populate Neo4j knowledge graph with domain knowledge.

This script creates all nodes and relationships for the ad-rewriter knowledge graph.
Run this after setting up Neo4j to initialize the graph with all domain knowledge.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Add parent directory to path to import agent modules
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from agent.kg_service import get_driver, execute_query, verify_connection


def create_constraints_and_indexes():
    """Create all constraints and indexes for the graph schema."""
    print("Creating constraints and indexes...")
    
    constraints = [
        "CREATE CONSTRAINT platform_name IF NOT EXISTS FOR (p:Platform) REQUIRE p.name IS UNIQUE",
        "CREATE CONSTRAINT audience_name IF NOT EXISTS FOR (a:Audience) REQUIRE a.name IS UNIQUE",
        "CREATE CONSTRAINT intent_name IF NOT EXISTS FOR (ui:UserIntent) REQUIRE ui.name IS UNIQUE",
        "CREATE CONSTRAINT creativetype_name IF NOT EXISTS FOR (ct:CreativeType) REQUIRE ct.name IS UNIQUE",
        "CREATE CONSTRAINT contentstyle_name IF NOT EXISTS FOR (cs:ContentStyle) REQUIRE cs.name IS UNIQUE",
        "CREATE CONSTRAINT productcategory_name IF NOT EXISTS FOR (pc:ProductCategory) REQUIRE pc.name IS UNIQUE",
        "CREATE CONSTRAINT constraint_name IF NOT EXISTS FOR (c:Constraint) REQUIRE c.name IS UNIQUE",
        "CREATE CONSTRAINT example_id IF NOT EXISTS FOR (e:Example) REQUIRE e.id IS UNIQUE",
    ]
    
    indexes = [
        "CREATE INDEX platform_name_index IF NOT EXISTS FOR (p:Platform) ON (p.name)",
        "CREATE INDEX audience_name_index IF NOT EXISTS FOR (a:Audience) ON (a.name)",
        "CREATE INDEX intent_name_index IF NOT EXISTS FOR (ui:UserIntent) ON (ui.name)",
        "CREATE INDEX creativetype_name_index IF NOT EXISTS FOR (ct:CreativeType) ON (ct.name)",
        "CREATE INDEX contentstyle_name_index IF NOT EXISTS FOR (cs:ContentStyle) ON (cs.name)",
        "CREATE INDEX productcategory_name_index IF NOT EXISTS FOR (pc:ProductCategory) ON (pc.name)",
        "CREATE INDEX constraint_name_index IF NOT EXISTS FOR (c:Constraint) ON (c.name)",
        "CREATE INDEX example_id_index IF NOT EXISTS FOR (e:Example) ON (e.id)",
    ]
    
    for constraint in constraints:
        try:
            execute_query(constraint)
        except Exception as e:
            print(f"Warning: {e}")
    
    for index in indexes:
        try:
            execute_query(index)
        except Exception as e:
            print(f"Warning: {e}")
    
    print("✓ Constraints and indexes created")


def create_platforms():
    """Create Platform nodes."""
    print("Creating Platform nodes...")
    
    platforms = [
        {"name": "instagram", "description": "Visual-first social platform", "type": "social"},
        {"name": "linkedin", "description": "Professional networking platform", "type": "professional"},
        {"name": "tiktok", "description": "Short-form video platform", "type": "social"},
        {"name": "facebook", "description": "Social networking platform", "type": "social"},
        {"name": "google", "description": "Search and display ads", "type": "advertising"},
        {"name": "twitter", "description": "Real-time social platform", "type": "social"},
        {"name": "youtube", "description": "Video sharing platform", "type": "video"},
        {"name": "pinterest", "description": "Visual discovery platform", "type": "social"},
    ]
    
    for platform in platforms:
        query = """
        MERGE (p:Platform {name: $name})
        SET p.description = $description, p.type = $type
        """
        execute_query(query, platform)
    
    print(f"✓ Created {len(platforms)} Platform nodes")


def create_audiences():
    """Create Audience nodes."""
    print("Creating Audience nodes...")
    
    audiences = [
        {"name": "gen-z", "age_range": "18-27", "demographics": "Digital natives, value authenticity"},
        {"name": "millennials", "age_range": "28-43", "demographics": "Tech-savvy, value experiences"},
        {"name": "gen-x", "age_range": "44-59", "demographics": "Independent, value quality"},
        {"name": "b2b professionals", "age_range": "25-55", "demographics": "Decision makers, value efficiency"},
        {"name": "seniors", "age_range": "60+", "demographics": "Traditional, value trust"},
        {"name": "parents", "age_range": "25-50", "demographics": "Family-focused, value safety"},
        {"name": "students", "age_range": "18-25", "demographics": "Budget-conscious, value deals"},
    ]
    
    for audience in audiences:
        query = """
        MERGE (a:Audience {name: $name})
        SET a.age_range = $age_range, a.demographics = $demographics
        """
        execute_query(query, audience)
    
    print(f"✓ Created {len(audiences)} Audience nodes")


def create_user_intents():
    """Create UserIntent nodes."""
    print("Creating UserIntent nodes...")
    
    intents = [
        {"name": "awareness", "funnel_stage": "top", "description": "Building brand awareness"},
        {"name": "consideration", "funnel_stage": "middle", "description": "Evaluating options"},
        {"name": "purchase", "funnel_stage": "bottom", "description": "Ready to buy"},
        {"name": "retention", "funnel_stage": "post", "description": "Keeping customers engaged"},
        {"name": "engagement", "funnel_stage": "any", "description": "Driving interactions"},
    ]
    
    for intent in intents:
        query = """
        MERGE (ui:UserIntent {name: $name})
        SET ui.funnel_stage = $funnel_stage, ui.description = $description
        """
        execute_query(query, intent)
    
    print(f"✓ Created {len(intents)} UserIntent nodes")


def create_creative_types():
    """Create CreativeType nodes."""
    print("Creating CreativeType nodes...")
    
    creative_types = [
        {"name": "video", "format": "moving", "description": "Video content"},
        {"name": "image", "format": "static", "description": "Static image"},
        {"name": "carousel", "format": "interactive", "description": "Multiple images in sequence"},
        {"name": "story", "format": "ephemeral", "description": "24-hour story format"},
        {"name": "reel", "format": "short-video", "description": "Short-form video"},
        {"name": "text-only", "format": "text", "description": "Text-based content"},
        {"name": "poll", "format": "interactive", "description": "Interactive poll"},
        {"name": "live", "format": "real-time", "description": "Live streaming"},
    ]
    
    for ct in creative_types:
        query = """
        MERGE (ct:CreativeType {name: $name})
        SET ct.format = $format, ct.description = $description
        """
        execute_query(query, ct)
    
    print(f"✓ Created {len(creative_types)} CreativeType nodes")


def create_content_styles():
    """Create ContentStyle nodes."""
    print("Creating ContentStyle nodes...")
    
    styles = [
        {"name": "professional", "tone": "formal", "description": "Business-focused, authoritative"},
        {"name": "casual", "tone": "relaxed", "description": "Friendly, approachable"},
        {"name": "energetic", "tone": "high-energy", "description": "Exciting, dynamic"},
        {"name": "visual", "tone": "aesthetic", "description": "Image-focused, visually appealing"},
        {"name": "educational", "tone": "informative", "description": "Informative, helpful"},
        {"name": "conversational", "tone": "chatty", "description": "Friendly, dialogue-like"},
        {"name": "humorous", "tone": "funny", "description": "Witty, entertaining"},
        {"name": "inspirational", "tone": "uplifting", "description": "Motivational, aspirational"},
        {"name": "fun", "tone": "playful", "description": "Light-hearted, enjoyable"},
        {"name": "bold", "tone": "confident", "description": "Strong, assertive"},
        {"name": "neutral", "tone": "balanced", "description": "Objective, unbiased"},
        {"name": "concise", "tone": "brief", "description": "Short, to-the-point"},
    ]
    
    for style in styles:
        query = """
        MERGE (cs:ContentStyle {name: $name})
        SET cs.tone = $tone, cs.description = $description
        """
        execute_query(query, style)
    
    print(f"✓ Created {len(styles)} ContentStyle nodes")


def create_product_categories():
    """Create ProductCategory nodes."""
    print("Creating ProductCategory nodes...")
    
    categories = [
        {"name": "tech", "industry": "technology", "description": "Technology products and services"},
        {"name": "fashion", "industry": "retail", "description": "Fashion and apparel"},
        {"name": "food", "industry": "food & beverage", "description": "Food and dining"},
        {"name": "services", "industry": "services", "description": "Professional services"},
        {"name": "b2b", "industry": "business", "description": "Business-to-business"},
        {"name": "healthcare", "industry": "health", "description": "Healthcare and wellness"},
        {"name": "education", "industry": "education", "description": "Educational services"},
        {"name": "finance", "industry": "financial", "description": "Financial services"},
    ]
    
    for category in categories:
        query = """
        MERGE (pc:ProductCategory {name: $name})
        SET pc.industry = $industry, pc.description = $description
        """
        execute_query(query, category)
    
    print(f"✓ Created {len(categories)} ProductCategory nodes")


def create_constraints():
    """Create Constraint nodes and link them to platforms."""
    print("Creating Constraint nodes...")
    
    # Constraints from current kg.json
    platform_constraints = {
        "instagram": [
            {"name": "max_length_chars", "type": "integer", "value": 2200},
            {"name": "allow_emojis", "type": "boolean", "value": True},
            {"name": "cta_required", "type": "boolean", "value": False},
        ],
        "linkedin": [
            {"name": "max_length_chars", "type": "integer", "value": 1300},
            {"name": "allow_emojis", "type": "boolean", "value": False},
            {"name": "cta_required", "type": "boolean", "value": True},
        ],
        "facebook": [
            {"name": "max_length_chars", "type": "integer", "value": 2000},
            {"name": "allow_emojis", "type": "boolean", "value": True},
            {"name": "cta_required", "type": "boolean", "value": True},
        ],
        "google": [
            {"name": "max_length_chars", "type": "integer", "value": 150},
            {"name": "allow_emojis", "type": "boolean", "value": False},
            {"name": "cta_required", "type": "boolean", "value": True},
        ],
        "tiktok": [
            {"name": "max_length_chars", "type": "integer", "value": 2200},
            {"name": "allow_emojis", "type": "boolean", "value": True},
            {"name": "cta_required", "type": "boolean", "value": False},
        ],
    }
    
    for platform, constraints in platform_constraints.items():
        for constraint in constraints:
            # Create constraint node
            query = """
            MERGE (c:Constraint {name: $name})
            SET c.type = $type, c.value = $value
            """
            execute_query(query, constraint)
            
            # Link to platform
            query = """
            MATCH (p:Platform {name: $platform})
            MATCH (c:Constraint {name: $name})
            MERGE (p)-[:HAS_CONSTRAINT {value: $value}]->(c)
            """
            execute_query(query, {"platform": platform, **constraint})
    
    print(f"✓ Created Constraint nodes and linked to platforms")


def main():
    """Main function to populate the knowledge graph."""
    print("=" * 60)
    print("Populating Neo4j Knowledge Graph")
    print("=" * 60)
    
    if not verify_connection():
        print("ERROR: Cannot connect to Neo4j. Please check your connection settings.")
        print(f"URI: {os.getenv('NEO4J_URI', 'bolt://localhost:7687')}")
        return
    
    print("✓ Connected to Neo4j\n")
    
    # Clear existing data (optional - comment out if you want to keep existing data)
    print("Clearing existing data...")
    execute_query("MATCH (n) DETACH DELETE n")
    print("✓ Cleared existing data\n")
    
    # Create schema
    create_constraints_and_indexes()
    print()
    
    # Create nodes
    create_platforms()
    create_audiences()
    create_user_intents()
    create_creative_types()
    create_content_styles()
    create_product_categories()
    create_constraints()
    
    print("\n" + "=" * 60)
    print("Knowledge graph population complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Run scripts/populate_relationships.py to add relationships")
    print("2. Run scripts/populate_examples.py to add example nodes")


if __name__ == "__main__":
    main()

