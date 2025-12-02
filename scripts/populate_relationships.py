"""Script to populate Neo4j knowledge graph with relationships.

This script creates all relationships between nodes in the ad-rewriter knowledge graph.
Run this after populate_kg.py to add rich domain knowledge relationships.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add parent directory to path to import agent modules
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from agent.kg_service import execute_query


def create_platform_audience_relationships():
    """Create Platform TARGETS Audience relationships."""
    print("Creating Platform → Audience relationships...")
    
    relationships = [
        # Instagram targets Gen-Z and Millennials heavily
        ("instagram", "gen-z", 0.85),
        ("instagram", "millennials", 0.80),
        ("instagram", "gen-x", 0.40),
        ("instagram", "parents", 0.50),
        ("instagram", "students", 0.70),
        
        # LinkedIn targets B2B professionals primarily
        ("linkedin", "b2b professionals", 0.95),
        ("linkedin", "millennials", 0.60),
        ("linkedin", "gen-x", 0.70),
        
        # TikTok targets Gen-Z heavily
        ("tiktok", "gen-z", 0.90),
        ("tiktok", "millennials", 0.65),
        ("tiktok", "students", 0.75),
        
        # Facebook targets broader demographics
        ("facebook", "millennials", 0.75),
        ("facebook", "gen-x", 0.80),
        ("facebook", "seniors", 0.70),
        ("facebook", "parents", 0.85),
        
        # Google Ads targets everyone (search-based)
        ("google", "millennials", 0.70),
        ("google", "gen-x", 0.75),
        ("google", "b2b professionals", 0.80),
        ("google", "parents", 0.70),
        
        # Twitter targets professionals and Gen-Z
        ("twitter", "b2b professionals", 0.70),
        ("twitter", "gen-z", 0.65),
        ("twitter", "millennials", 0.75),
        
        # YouTube targets everyone
        ("youtube", "gen-z", 0.80),
        ("youtube", "millennials", 0.85),
        ("youtube", "gen-x", 0.75),
        ("youtube", "parents", 0.70),
        
        # Pinterest targets parents and Millennials
        ("pinterest", "millennials", 0.80),
        ("pinterest", "gen-x", 0.70),
        ("pinterest", "parents", 0.85),
    ]
    
    for platform, audience, weight in relationships:
        query = """
        MATCH (p:Platform {name: $platform})
        MATCH (a:Audience {name: $audience})
        MERGE (p)-[r:TARGETS {weight: $weight}]->(a)
        SET r.weight = $weight
        """
        execute_query(query, {"platform": platform, "audience": audience, "weight": weight})
    
    print(f"✓ Created {len(relationships)} Platform → Audience relationships")


def create_platform_creativetype_relationships():
    """Create Platform SUPPORTS CreativeType relationships."""
    print("Creating Platform → CreativeType relationships...")
    
    relationships = [
        # Instagram supports various formats
        ("instagram", "image", 0.95),
        ("instagram", "carousel", 0.90),
        ("instagram", "story", 0.85),
        ("instagram", "reel", 0.90),
        ("instagram", "video", 0.75),
        ("instagram", "poll", 0.60),
        
        # LinkedIn supports professional formats
        ("linkedin", "image", 0.80),
        ("linkedin", "video", 0.85),
        ("linkedin", "text-only", 0.90),
        ("linkedin", "carousel", 0.70),
        
        # TikTok is video-first
        ("tiktok", "video", 0.98),
        ("tiktok", "reel", 0.95),
        ("tiktok", "live", 0.70),
        
        # Facebook supports everything
        ("facebook", "image", 0.90),
        ("facebook", "video", 0.85),
        ("facebook", "carousel", 0.80),
        ("facebook", "text-only", 0.75),
        ("facebook", "live", 0.70),
        
        # Google Ads is text-focused
        ("google", "text-only", 0.95),
        ("google", "image", 0.80),
        ("google", "video", 0.70),
        
        # Twitter is text and image
        ("twitter", "text-only", 0.90),
        ("twitter", "image", 0.85),
        ("twitter", "video", 0.70),
        ("twitter", "poll", 0.75),
        
        # YouTube is video-only
        ("youtube", "video", 0.98),
        ("youtube", "live", 0.85),
        
        # Pinterest is image-focused
        ("pinterest", "image", 0.95),
        ("pinterest", "carousel", 0.90),
        ("pinterest", "video", 0.60),
    ]
    
    for platform, creative_type, score in relationships:
        query = """
        MATCH (p:Platform {name: $platform})
        MATCH (ct:CreativeType {name: $creative_type})
        MERGE (p)-[r:SUPPORTS {score: $score}]->(ct)
        SET r.score = $score
        """
        execute_query(query, {"platform": platform, "creative_type": creative_type, "score": score})
    
    print(f"✓ Created {len(relationships)} Platform → CreativeType relationships")


def create_platform_style_relationships():
    """Create Platform PREFERS_STYLE relationships."""
    print("Creating Platform → ContentStyle relationships...")
    
    relationships = [
        # Instagram prefers visual and fun styles
        ("instagram", "visual", 0.95),
        ("instagram", "fun", 0.90),
        ("instagram", "energetic", 0.85),
        ("instagram", "casual", 0.80),
        ("instagram", "inspirational", 0.75),
        
        # LinkedIn prefers professional styles
        ("linkedin", "professional", 0.95),
        ("linkedin", "educational", 0.85),
        ("linkedin", "neutral", 0.80),
        ("linkedin", "conversational", 0.70),
        
        # TikTok prefers energetic and fun
        ("tiktok", "energetic", 0.95),
        ("tiktok", "fun", 0.90),
        ("tiktok", "humorous", 0.85),
        ("tiktok", "casual", 0.80),
        
        # Facebook prefers conversational
        ("facebook", "conversational", 0.90),
        ("facebook", "friendly", 0.85),
        ("facebook", "casual", 0.80),
        ("facebook", "inspirational", 0.75),
        
        # Google prefers concise and neutral
        ("google", "concise", 0.95),
        ("google", "neutral", 0.90),
        ("google", "professional", 0.75),
        
        # Twitter prefers conversational and bold
        ("twitter", "conversational", 0.85),
        ("twitter", "bold", 0.80),
        ("twitter", "professional", 0.75),
        ("twitter", "humorous", 0.70),
        
        # YouTube prefers educational
        ("youtube", "educational", 0.90),
        ("youtube", "professional", 0.85),
        ("youtube", "conversational", 0.80),
        
        # Pinterest prefers visual and inspirational
        ("pinterest", "visual", 0.95),
        ("pinterest", "inspirational", 0.90),
        ("pinterest", "casual", 0.80),
    ]
    
    for platform, style, score in relationships:
        query = """
        MATCH (p:Platform {name: $platform})
        MATCH (cs:ContentStyle {name: $style})
        MERGE (p)-[r:PREFERS_STYLE {score: $score}]->(cs)
        SET r.score = $score
        """
        execute_query(query, {"platform": platform, "style": style, "score": score})
    
    print(f"✓ Created {len(relationships)} Platform → ContentStyle relationships")


def create_platform_sharing_relationships():
    """Create Platform SHARES_AUDIENCE_WITH Platform relationships."""
    print("Creating Platform → Platform (audience overlap) relationships...")
    
    relationships = [
        # Instagram and TikTok share Gen-Z audience
        ("instagram", "tiktok", 0.75),
        ("instagram", "snapchat", 0.70),
        
        # LinkedIn and Twitter share professional audience
        ("linkedin", "twitter", 0.65),
        
        # Facebook overlaps with many platforms
        ("facebook", "instagram", 0.60),
        ("facebook", "youtube", 0.55),
        
        # YouTube overlaps with many
        ("youtube", "instagram", 0.65),
        ("youtube", "tiktok", 0.60),
        
        # Pinterest and Instagram share visual audience
        ("pinterest", "instagram", 0.70),
    ]
    
    for platform1, platform2, overlap in relationships:
        # Create bidirectional relationship
        query = """
        MATCH (p1:Platform {name: $platform1})
        MATCH (p2:Platform {name: $platform2})
        MERGE (p1)-[r:SHARES_AUDIENCE_WITH {overlap_pct: $overlap}]->(p2)
        SET r.overlap_pct = $overlap
        """
        execute_query(query, {"platform1": platform1, "platform2": platform2, "overlap": overlap})
        
        # Also create reverse relationship
        query = """
        MATCH (p1:Platform {name: $platform1})
        MATCH (p2:Platform {name: $platform2})
        MERGE (p2)-[r:SHARES_AUDIENCE_WITH {overlap_pct: $overlap}]->(p1)
        SET r.overlap_pct = $overlap
        """
        execute_query(query, {"platform1": platform1, "platform2": platform2, "overlap": overlap})
    
    print(f"✓ Created {len(relationships) * 2} Platform → Platform relationships")


def create_audience_style_relationships():
    """Create Audience PREFERS_STYLE relationships."""
    print("Creating Audience → ContentStyle relationships...")
    
    relationships = [
        # Gen-Z prefers energetic and fun styles
        ("gen-z", "energetic", 0.90),
        ("gen-z", "fun", 0.85),
        ("gen-z", "humorous", 0.80),
        ("gen-z", "visual", 0.85),
        ("gen-z", "casual", 0.75),
        
        # Millennials prefer balanced styles
        ("millennials", "conversational", 0.85),
        ("millennials", "casual", 0.80),
        ("millennials", "visual", 0.75),
        ("millennials", "inspirational", 0.70),
        
        # Gen-X prefers professional but approachable
        ("gen-x", "professional", 0.80),
        ("gen-x", "conversational", 0.75),
        ("gen-x", "educational", 0.70),
        ("gen-x", "neutral", 0.75),
        
        # B2B professionals prefer professional
        ("b2b professionals", "professional", 0.95),
        ("b2b professionals", "educational", 0.85),
        ("b2b professionals", "neutral", 0.80),
        ("b2b professionals", "conversational", 0.70),
        
        # Seniors prefer traditional styles
        ("seniors", "professional", 0.85),
        ("seniors", "neutral", 0.80),
        ("seniors", "conversational", 0.75),
        
        # Parents prefer trustworthy styles
        ("parents", "conversational", 0.85),
        ("parents", "inspirational", 0.80),
        ("parents", "professional", 0.75),
        ("parents", "casual", 0.70),
        
        # Students prefer fun and casual
        ("students", "fun", 0.85),
        ("students", "casual", 0.80),
        ("students", "energetic", 0.75),
        ("students", "humorous", 0.70),
    ]
    
    for audience, style, score in relationships:
        query = """
        MATCH (a:Audience {name: $audience})
        MATCH (cs:ContentStyle {name: $style})
        MERGE (a)-[r:PREFERS_STYLE {preference_score: $score}]->(cs)
        SET r.preference_score = $score
        """
        execute_query(query, {"audience": audience, "style": style, "score": score})
    
    print(f"✓ Created {len(relationships)} Audience → ContentStyle relationships")


def create_intent_style_relationships():
    """Create UserIntent REQUIRES_STYLE relationships."""
    print("Creating UserIntent → ContentStyle relationships...")
    
    relationships = [
        # Awareness requires engaging styles
        ("awareness", "visual", 0.90),
        ("awareness", "energetic", 0.85),
        ("awareness", "fun", 0.80),
        ("awareness", "inspirational", 0.75),
        
        # Consideration requires informative styles
        ("consideration", "educational", 0.90),
        ("consideration", "professional", 0.85),
        ("consideration", "conversational", 0.80),
        
        # Purchase requires direct styles
        ("purchase", "professional", 0.85),
        ("purchase", "concise", 0.90),
        ("purchase", "bold", 0.80),
        ("purchase", "neutral", 0.75),
        
        # Retention requires engaging styles
        ("retention", "conversational", 0.85),
        ("retention", "inspirational", 0.80),
        ("retention", "fun", 0.75),
        
        # Engagement requires interactive styles
        ("engagement", "fun", 0.90),
        ("engagement", "humorous", 0.85),
        ("engagement", "energetic", 0.80),
        ("engagement", "conversational", 0.75),
    ]
    
    for intent, style, strength in relationships:
        query = """
        MATCH (ui:UserIntent {name: $intent})
        MATCH (cs:ContentStyle {name: $style})
        MERGE (ui)-[r:REQUIRES_STYLE {strength: $strength}]->(cs)
        SET r.strength = $strength
        """
        execute_query(query, {"intent": intent, "style": style, "strength": strength})
    
    print(f"✓ Created {len(relationships)} UserIntent → ContentStyle relationships")


def create_intent_creativetype_relationships():
    """Create UserIntent WORKS_WITH CreativeType relationships."""
    print("Creating UserIntent → CreativeType relationships...")
    
    relationships = [
        # Awareness works with visual formats
        ("awareness", "video", 0.90),
        ("awareness", "image", 0.85),
        ("awareness", "reel", 0.80),
        
        # Consideration works with informative formats
        ("consideration", "carousel", 0.85),
        ("consideration", "video", 0.80),
        ("consideration", "text-only", 0.75),
        
        # Purchase works with direct formats
        ("purchase", "text-only", 0.90),
        ("purchase", "image", 0.80),
        ("purchase", "carousel", 0.75),
        
        # Retention works with engaging formats
        ("retention", "video", 0.85),
        ("retention", "story", 0.80),
        ("retention", "live", 0.75),
        
        # Engagement works with interactive formats
        ("engagement", "poll", 0.90),
        ("engagement", "story", 0.85),
        ("engagement", "video", 0.80),
    ]
    
    for intent, creative_type, compatibility in relationships:
        query = """
        MATCH (ui:UserIntent {name: $intent})
        MATCH (ct:CreativeType {name: $creative_type})
        MERGE (ui)-[r:WORKS_WITH {compatibility: $compatibility}]->(ct)
        SET r.compatibility = $compatibility
        """
        execute_query(query, {"intent": intent, "creative_type": creative_type, "compatibility": compatibility})
    
    print(f"✓ Created {len(relationships)} UserIntent → CreativeType relationships")


def create_category_platform_relationships():
    """Create ProductCategory SUITABLE_FOR Platform relationships."""
    print("Creating ProductCategory → Platform relationships...")
    
    relationships = [
        # Tech products
        ("tech", "linkedin", 0.90),
        ("tech", "twitter", 0.85),
        ("tech", "youtube", 0.80),
        ("tech", "google", 0.95),
        
        # Fashion products
        ("fashion", "instagram", 0.95),
        ("fashion", "pinterest", 0.90),
        ("fashion", "tiktok", 0.85),
        ("fashion", "facebook", 0.75),
        
        # Food products
        ("food", "instagram", 0.90),
        ("food", "facebook", 0.85),
        ("food", "tiktok", 0.80),
        ("food", "pinterest", 0.75),
        
        # Services
        ("services", "linkedin", 0.85),
        ("services", "google", 0.90),
        ("services", "facebook", 0.80),
        
        # B2B products
        ("b2b", "linkedin", 0.95),
        ("b2b", "twitter", 0.85),
        ("b2b", "google", 0.90),
        
        # Healthcare
        ("healthcare", "facebook", 0.85),
        ("healthcare", "google", 0.90),
        ("healthcare", "linkedin", 0.75),
        
        # Education
        ("education", "youtube", 0.95),
        ("education", "linkedin", 0.85),
        ("education", "facebook", 0.80),
        
        # Finance
        ("finance", "linkedin", 0.90),
        ("finance", "google", 0.95),
        ("finance", "facebook", 0.75),
    ]
    
    for category, platform, score in relationships:
        query = """
        MATCH (pc:ProductCategory {name: $category})
        MATCH (p:Platform {name: $platform})
        MERGE (pc)-[r:SUITABLE_FOR {suitability_score: $score}]->(p)
        SET r.suitability_score = $score
        """
        execute_query(query, {"category": category, "platform": platform, "score": score})
    
    print(f"✓ Created {len(relationships)} ProductCategory → Platform relationships")


def create_category_creativetype_relationships():
    """Create ProductCategory WORKS_BEST_WITH CreativeType relationships."""
    print("Creating ProductCategory → CreativeType relationships...")
    
    relationships = [
        # Tech works with video and carousel
        ("tech", "video", 0.90),
        ("tech", "carousel", 0.85),
        ("tech", "text-only", 0.80),
        
        # Fashion works with image and carousel
        ("fashion", "image", 0.95),
        ("fashion", "carousel", 0.90),
        ("fashion", "video", 0.85),
        ("fashion", "reel", 0.80),
        
        # Food works with image and video
        ("food", "image", 0.95),
        ("food", "video", 0.90),
        ("food", "reel", 0.85),
        ("food", "story", 0.80),
        
        # Services work with text and video
        ("services", "text-only", 0.85),
        ("services", "video", 0.80),
        ("services", "image", 0.75),
        
        # B2B works with text and video
        ("b2b", "text-only", 0.90),
        ("b2b", "video", 0.85),
        ("b2b", "carousel", 0.75),
        
        # Healthcare works with image and video
        ("healthcare", "image", 0.85),
        ("healthcare", "video", 0.80),
        ("healthcare", "text-only", 0.75),
        
        # Education works with video
        ("education", "video", 0.95),
        ("education", "image", 0.80),
        ("education", "carousel", 0.75),
        
        # Finance works with text and image
        ("finance", "text-only", 0.90),
        ("finance", "image", 0.80),
        ("finance", "video", 0.75),
    ]
    
    for category, creative_type, effectiveness in relationships:
        query = """
        MATCH (pc:ProductCategory {name: $category})
        MATCH (ct:CreativeType {name: $creative_type})
        MERGE (pc)-[r:WORKS_BEST_WITH {effectiveness: $effectiveness}]->(ct)
        SET r.effectiveness = $effectiveness
        """
        execute_query(query, {"category": category, "creative_type": creative_type, "effectiveness": effectiveness})
    
    print(f"✓ Created {len(relationships)} ProductCategory → CreativeType relationships")


def create_creativetype_platform_relationships():
    """Create CreativeType WORKS_BEST_ON Platform relationships."""
    print("Creating CreativeType → Platform relationships...")
    
    relationships = [
        # Video works best on video platforms
        ("video", "youtube", 0.98),
        ("video", "tiktok", 0.95),
        ("video", "instagram", 0.85),
        ("video", "facebook", 0.80),
        ("video", "linkedin", 0.75),
        
        # Image works best on visual platforms
        ("image", "instagram", 0.95),
        ("image", "pinterest", 0.95),
        ("image", "facebook", 0.85),
        ("image", "twitter", 0.80),
        
        # Carousel works best on Instagram
        ("carousel", "instagram", 0.95),
        ("carousel", "facebook", 0.80),
        ("carousel", "pinterest", 0.75),
        
        # Story works best on Instagram and Facebook
        ("story", "instagram", 0.90),
        ("story", "facebook", 0.85),
        ("story", "snapchat", 0.90),
        
        # Reel works best on Instagram and TikTok
        ("reel", "instagram", 0.95),
        ("reel", "tiktok", 0.90),
        
        # Text-only works best on Twitter and LinkedIn
        ("text-only", "twitter", 0.95),
        ("text-only", "linkedin", 0.90),
        ("text-only", "google", 0.85),
        
        # Poll works best on Instagram and Twitter
        ("poll", "instagram", 0.85),
        ("poll", "twitter", 0.90),
        ("poll", "facebook", 0.80),
        
        # Live works best on Instagram, Facebook, YouTube
        ("live", "instagram", 0.85),
        ("live", "facebook", 0.85),
        ("live", "youtube", 0.90),
        ("live", "tiktok", 0.80),
    ]
    
    for creative_type, platform, effectiveness in relationships:
        query = """
        MATCH (ct:CreativeType {name: $creative_type})
        MATCH (p:Platform {name: $platform})
        MERGE (ct)-[r:WORKS_BEST_ON {effectiveness: $effectiveness}]->(p)
        SET r.effectiveness = $effectiveness
        """
        execute_query(query, {"creative_type": creative_type, "platform": platform, "effectiveness": effectiveness})
    
    print(f"✓ Created {len(relationships)} CreativeType → Platform relationships")


def main():
    """Main function to populate all relationships."""
    print("=" * 60)
    print("Populating Neo4j Knowledge Graph Relationships")
    print("=" * 60)
    print()
    
    create_platform_audience_relationships()
    create_platform_creativetype_relationships()
    create_platform_style_relationships()
    create_platform_sharing_relationships()
    create_audience_style_relationships()
    create_intent_style_relationships()
    create_intent_creativetype_relationships()
    create_category_platform_relationships()
    create_category_creativetype_relationships()
    create_creativetype_platform_relationships()
    
    print("\n" + "=" * 60)
    print("Relationship population complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Run scripts/populate_examples.py to add example nodes")
    print("2. Verify relationships in Neo4j Browser")
    print("\nExample query to test:")
    print("MATCH (p:Platform {name: 'instagram'})-[:TARGETS]->(a:Audience)")
    print("RETURN p.name, a.name, a.age_range")


if __name__ == "__main__":
    main()

