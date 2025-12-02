"""Neo4j Knowledge Graph service for querying platform constraints, styles, and relationships."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

# Neo4j connection settings
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

_driver: Optional[GraphDatabase.driver] = None


def get_driver() -> GraphDatabase.driver:
    """Get or create Neo4j driver instance with connection pooling."""
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD),
            max_connection_lifetime=30 * 60,  # 30 minutes
            max_connection_pool_size=50,
            connection_acquisition_timeout=2 * 60,  # 2 minutes
        )
    return _driver


def close_driver() -> None:
    """Close Neo4j driver connection."""
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None


def execute_query(query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Execute a Cypher query and return results.
    
    Args:
        query: Cypher query string
        parameters: Optional query parameters
        
    Returns:
        List of result records as dictionaries
    """
    driver = get_driver()
    with driver.session() as session:
        result = session.run(query, parameters or {})
        return [dict(record) for record in result]


def platform_exists(platform: str) -> bool:
    """Check if a platform exists in the knowledge graph.
    
    Args:
        platform: Platform name (e.g., 'instagram', 'linkedin')
        
    Returns:
        True if platform exists, False otherwise
    """
    query = """
    MATCH (p:Platform {name: $platform})
    RETURN count(p) as count
    """
    results = execute_query(query, {"platform": platform.lower()})
    return results[0]["count"] > 0 if results else False


def get_platform_constraints(platform: str) -> Dict[str, Any]:
    """Get all constraints (validation rules) for a platform.
    
    Args:
        platform: Platform name (e.g., 'instagram', 'linkedin')
        
    Returns:
        Dictionary with constraint names as keys and values
        Example: {'max_length_chars': 2200, 'allow_emojis': True, 'cta_required': False}
        Returns empty dict if platform has no constraints (but platform exists)
    """
    query = """
    MATCH (p:Platform {name: $platform})-[:HAS_CONSTRAINT]->(c:Constraint)
    RETURN c.name as name, c.value as value, c.type as type
    """
    results = execute_query(query, {"platform": platform.lower()})
    
    constraints = {}
    for record in results:
        name = record["name"]
        value = record["value"]
        # Convert string values to appropriate types
        if record.get("type") == "boolean":
            value = value.lower() == "true" if isinstance(value, str) else bool(value)
        elif record.get("type") == "integer":
            value = int(value)
        constraints[name] = value
    
    return constraints


def get_default_constraints(platform: str) -> Dict[str, Any]:
    """Get default constraints for platforms that don't have explicit constraints in KG.
    
    Args:
        platform: Platform name
        
    Returns:
        Dictionary with default constraint values
    """
    # Default constraints by platform type/characteristics
    defaults = {
        "twitter": {
            "max_length_chars": 280,  # Twitter/X character limit
            "allow_emojis": True,
            "cta_required": False,
        },
        "youtube": {
            "max_length_chars": 5000,  # YouTube description limit
            "allow_emojis": True,
            "cta_required": True,
        },
        "pinterest": {
            "max_length_chars": 500,  # Pinterest description limit
            "allow_emojis": True,
            "cta_required": False,
        },
    }
    
    # Return platform-specific defaults or generic defaults
    if platform.lower() in defaults:
        return defaults[platform.lower()]
    
    # Generic fallback defaults
    return {
        "max_length_chars": 2000,
        "allow_emojis": True,
        "cta_required": False,
    }


def get_platform_preferred_styles(platform: str) -> List[str]:
    """Get preferred content styles for a platform.
    
    Args:
        platform: Platform name
        
    Returns:
        List of preferred style names, ordered by preference score
    """
    query = """
    MATCH (p:Platform {name: $platform})-[r:PREFERS_STYLE]->(s:ContentStyle)
    RETURN s.name as style, r.score as score
    ORDER BY r.score DESC
    """
    results = execute_query(query, {"platform": platform.lower()})
    return [record["style"] for record in results]


def get_platform_data_batch(
    platform: str,
    audience: Optional[str] = None,
    intent: Optional[str] = None,
    product_category: Optional[str] = None,
) -> Dict[str, Any]:
    """Get all platform data in a single batched query (replaces 8-11 separate queries).
    
    Args:
        platform: Platform name
        audience: Optional audience segment
        intent: Optional user intent
        product_category: Optional product category
        
    Returns:
        Dictionary with constraints, preferred_styles, recommended_creative_types,
        target_audiences, and optional audience/intent/category-specific data.
    """
    query = """
    MATCH (p:Platform {name: $platform})
    
    // Get constraints
    OPTIONAL MATCH (p)-[:HAS_CONSTRAINT]->(c:Constraint)
    WITH p, collect(DISTINCT {name: c.name, value: c.value, type: c.type}) as constraints
    
    // Get preferred styles
    OPTIONAL MATCH (p)-[r1:PREFERS_STYLE]->(s1:ContentStyle)
    WITH p, constraints, collect(DISTINCT {style: s1.name, score: r1.score}) as platform_styles
    
    // Get creative types
    OPTIONAL MATCH (p)-[r2:SUPPORTS]->(ct:CreativeType)
    WITH p, constraints, platform_styles, collect(DISTINCT {name: ct.name, score: r2.score}) as creative_types
    
    // Get target audiences
    OPTIONAL MATCH (p)-[r3:TARGETS]->(a:Audience)
    WITH p, constraints, platform_styles, creative_types, collect(DISTINCT {name: a.name, weight: r3.weight}) as audiences
    
    // Get audience preferences if audience specified (use conditional OPTIONAL MATCH)
    OPTIONAL MATCH (a2:Audience {name: $audience})-[r4:PREFERS_STYLE]->(s2:ContentStyle)
    WITH p, constraints, platform_styles, creative_types, audiences, 
         CASE WHEN $audience IS NOT NULL THEN collect(DISTINCT {style: s2.name, score: r4.preference_score}) ELSE [] END as audience_styles
    
    // Get intent requirements if intent specified
    OPTIONAL MATCH (ui:UserIntent {name: $intent})-[r5:REQUIRES_STYLE]->(s3:ContentStyle)
    WITH p, constraints, platform_styles, creative_types, audiences, audience_styles,
         CASE WHEN $intent IS NOT NULL THEN collect(DISTINCT {style: s3.name, strength: r5.strength}) ELSE [] END as intent_styles
    
    // Get category suitability if category specified
    OPTIONAL MATCH (pc:ProductCategory {name: $category})-[r6:SUITABLE_FOR]->(p)
    WITH constraints, platform_styles, creative_types, audiences, audience_styles, intent_styles,
         CASE WHEN $category IS NOT NULL AND r6 IS NOT NULL THEN r6.suitability_score ELSE null END as category_score
    
    RETURN constraints, platform_styles, creative_types, audiences, 
           audience_styles, intent_styles, category_score
    """
    
    results = execute_query(query, {
        "platform": platform.lower(),
        "audience": audience.lower() if audience else None,
        "intent": intent.lower() if intent else None,
        "category": product_category.lower() if product_category else None,
    })
    
    if not results:
        # Platform doesn't exist or no data
        return {}
    
    result = results[0]
    
    # Process constraints
    constraints = {}
    for c in result.get("constraints", []):
        if c.get("name"):  # Skip None values
            name = c["name"]
            value = c["value"]
            if c.get("type") == "boolean":
                value = value.lower() == "true" if isinstance(value, str) else bool(value)
            elif c.get("type") == "integer":
                value = int(value)
            constraints[name] = value
    
    # Process platform styles (sort by score)
    platform_styles_data = result.get("platform_styles", [])
    platform_styles = sorted(
        [s["style"] for s in platform_styles_data if s.get("style")],
        key=lambda x: next((s["score"] for s in platform_styles_data if s.get("style") == x), 0),
        reverse=True
    )
    
    # Process creative types (sort by score)
    creative_types_data = result.get("creative_types", [])
    creative_types = sorted(
        [ct["name"] for ct in creative_types_data if ct.get("name")],
        key=lambda x: next((ct["score"] for ct in creative_types_data if ct.get("name") == x), 0),
        reverse=True
    )
    
    # Process audiences (sort by weight)
    audiences_data = result.get("audiences", [])
    audiences = sorted(
        [a["name"] for a in audiences_data if a.get("name")],
        key=lambda x: next((a["weight"] for a in audiences_data if a.get("name") == x), 0),
        reverse=True
    )
    
    # Build strategy dict
    strategy = {
        "constraints": constraints if constraints else get_default_constraints(platform),
        "preferred_styles": platform_styles,
        "recommended_creative_types": creative_types,
        "target_audiences": audiences,
    }
    
    # Add audience-specific styles if available
    if result.get("audience_styles"):
        audience_styles_data = result["audience_styles"]
        strategy["audience_preferred_styles"] = sorted(
            [s["style"] for s in audience_styles_data if s.get("style")],
            key=lambda x: next((s["score"] for s in audience_styles_data if s.get("style") == x), 0),
            reverse=True
        )[:5]
    
    # Add intent-specific styles if available
    if result.get("intent_styles"):
        intent_styles_data = result["intent_styles"]
        strategy["intent_required_styles"] = sorted(
            [s["style"] for s in intent_styles_data if s.get("style")],
            key=lambda x: next((s["strength"] for s in intent_styles_data if s.get("style") == x), 0),
            reverse=True
        )[:5]
    
    # Add category suitability score if available
    if result.get("category_score") is not None:
        strategy["category_suitability_score"] = result["category_score"]
    
    return strategy


# Cache platform data for better performance (platform data rarely changes)
@lru_cache(maxsize=128)
def _get_platform_data_batch_cached(
    platform: str,
    audience: Optional[str],
    intent: Optional[str],
    category: Optional[str],
) -> Dict[str, Any]:
    """Cached version - use tuple for cache key (lru_cache requires hashable args)."""
    return get_platform_data_batch(platform, audience, intent, category)


def get_platform_data_batch_cached(
    platform: str,
    audience: Optional[str] = None,
    intent: Optional[str] = None,
    product_category: Optional[str] = None,
) -> Dict[str, Any]:
    """Get platform data with LRU caching (128 entries)."""
    return _get_platform_data_batch_cached(
        platform.lower(),
        audience.lower() if audience else None,
        intent.lower() if intent else None,
        product_category.lower() if product_category else None,
    )


def get_platform_strategy(
    platform: str,
    audience: Optional[str] = None,
    intent: Optional[str] = None,
    product_category: Optional[str] = None,
) -> Dict[str, Any]:
    """Get comprehensive strategy recommendations for a platform.
    
    Args:
        platform: Platform name
        audience: Optional audience segment
        intent: Optional user intent
        product_category: Optional product category
        
    Returns:
        Dictionary with constraints, preferred_styles, recommended_creative_types,
        target_audiences, and optional audience/intent/category-specific data.
    """
    # Use the optimized batched query instead of multiple separate queries
    return get_platform_data_batch_cached(platform, audience, intent, product_category)


def get_similar_platforms(platform: str, limit: int = 3) -> List[Dict[str, str]]:
    """Get platforms that share audiences with the given platform.
    
    Args:
        platform: Platform name
        limit: Maximum number of similar platforms to return
        
    Returns:
        List of dictionaries with platform names and overlap percentages
    """
    query = """
    MATCH (p1:Platform {name: $platform})-[r:SHARES_AUDIENCE_WITH]->(p2:Platform)
    RETURN p2.name as platform, r.overlap_pct as overlap
    ORDER BY r.overlap_pct DESC
    LIMIT $limit
    """
    results = execute_query(query, {"platform": platform.lower(), "limit": limit})
    return [{"platform": record["platform"], "overlap": record.get("overlap", 0)} for record in results]


def get_recommended_styles(
    platform: str,
    audience: Optional[str] = None,
    intent: Optional[str] = None,
) -> List[str]:
    """Get recommended content styles based on platform, audience, and intent.
    
    This function now uses the optimized batched query for better performance.
    
    Args:
        platform: Platform name
        audience: Optional audience segment
        intent: Optional user intent
        
    Returns:
        List of recommended style names
    """
    # Use the optimized batched query to get all data at once
    strategy = get_platform_data_batch_cached(platform, audience, intent, None)
    
    # Start with platform preferred styles
    styles = strategy.get("preferred_styles", [])
    
    # If audience specified, prioritize audience preferences
    if audience and "audience_preferred_styles" in strategy:
        audience_styles = strategy["audience_preferred_styles"]
        # Merge and deduplicate, prioritizing audience preferences
        styles = list(dict.fromkeys(audience_styles + styles))
    
    # If intent specified, prioritize intent requirements
    if intent and "intent_required_styles" in strategy:
        intent_styles = strategy["intent_required_styles"]
        # Merge and deduplicate, prioritizing intent requirements
        styles = list(dict.fromkeys(intent_styles + styles))
    
    return styles[:10]  # Return top 10


def get_creative_recommendations(platform: str, product_category: Optional[str] = None) -> List[str]:
    """Get recommended creative types for a platform.
    
    Args:
        platform: Platform name
        product_category: Optional product category
        
    Returns:
        List of recommended creative type names
    """
    query = """
    MATCH (p:Platform {name: $platform})-[r:SUPPORTS]->(ct:CreativeType)
    RETURN ct.name as name, r.score as score
    ORDER BY r.score DESC
    """
    results = execute_query(query, {"platform": platform.lower()})
    return [record["name"] for record in results]


def verify_connection() -> bool:
    """Verify Neo4j connection is working.
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        driver = get_driver()
        driver.verify_connectivity()
        return True
    except Exception as e:
        print(f"Neo4j connection error: {e}")
        return False


__all__ = [
    "get_driver",
    "close_driver",
    "execute_query",
    "platform_exists",
    "get_platform_constraints",
    "get_default_constraints",
    "get_platform_preferred_styles",
    "get_platform_strategy",
    "get_platform_data_batch",
    "get_platform_data_batch_cached",
    "get_similar_platforms",
    "get_recommended_styles",
    "get_creative_recommendations",
    "verify_connection",
]


