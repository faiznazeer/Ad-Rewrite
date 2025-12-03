"""Test script to verify Neo4j knowledge graph setup with example queries.

This script runs various queries to test the knowledge graph structure,
relationships, and data integrity before refactoring the main code.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add parent directory to path to import agent modules
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from agent.kg_service import execute_query, verify_connection, get_platform_data_batch_cached


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_results(results: list, limit: int = 5):
    """Print query results in a readable format."""
    if not results:
        print("  No results found.")
        return
    
    for i, result in enumerate(results[:limit], 1):
        print(f"  {i}. {result}")
    
    if len(results) > limit:
        print(f"  ... and {len(results) - limit} more")


def test_connection():
    """Test Neo4j connection."""
    print_section("Testing Neo4j Connection")
    
    if verify_connection():
        print("  ✓ Successfully connected to Neo4j")
        return True
    else:
        print("  ✗ Failed to connect to Neo4j")
        print("  Please check your connection settings in .env")
        return False


def test_node_counts():
    """Test that all node types were created."""
    print_section("Node Counts")
    
    node_types = [
        "Platform",
        "Audience",
        "UserIntent",
        "CreativeType",
        "ContentStyle",
        "ProductCategory",
        "Constraint",
        "Example",
    ]
    
    for node_type in node_types:
        query = f"MATCH (n:{node_type}) RETURN count(n) as count"
        result = execute_query(query)
        count = result[0]["count"] if result else 0
        status = "✓" if count > 0 else "✗"
        print(f"  {status} {node_type}: {count} nodes")


def test_platform_constraints():
    """Test platform constraints retrieval."""
    print_section("Platform Constraints")
    
    platforms = ["instagram", "linkedin", "tiktok", "facebook", "google"]
    
    for platform in platforms:
        strategy = get_platform_data_batch_cached(platform)
        constraints = strategy.get("constraints", {})
        if constraints:
            print(f"\n  {platform.upper()}:")
            for key, value in constraints.items():
                print(f"    - {key}: {value}")
        else:
            print(f"  ✗ No constraints found for {platform}")


def test_platform_relationships():
    """Test platform relationships."""
    print_section("Platform → Audience Relationships")
    
    query = """
    MATCH (p:Platform)-[r:TARGETS]->(a:Audience)
    RETURN p.name as platform, a.name as audience, r.weight as weight
    ORDER BY p.name, r.weight DESC
    LIMIT 10
    """
    results = execute_query(query)
    
    print("  Top platform-audience relationships:")
    for result in results:
        print(f"    {result['platform']} → {result['audience']} (weight: {result['weight']:.2f})")


def test_platform_creativetypes():
    """Test platform creative type support."""
    print_section("Platform → CreativeType Relationships")
    
    query = """
    MATCH (p:Platform {name: 'instagram'})-[r:SUPPORTS]->(ct:CreativeType)
    RETURN ct.name as creative_type, r.score as score
    ORDER BY r.score DESC
    """
    results = execute_query(query)
    
    print("  Instagram supports:")
    for result in results:
        print(f"    - {result['creative_type']} (score: {result['score']:.2f})")


def test_platform_styles():
    """Test platform style preferences."""
    print_section("Platform → ContentStyle Relationships")
    
    query = """
    MATCH (p:Platform {name: 'linkedin'})-[r:PREFERS_STYLE]->(cs:ContentStyle)
    RETURN cs.name as style, r.score as score
    ORDER BY r.score DESC
    """
    results = execute_query(query)
    
    print("  LinkedIn prefers styles:")
    for result in results:
        print(f"    - {result['style']} (score: {result['score']:.2f})")


def test_audience_preferences():
    """Test audience style preferences."""
    print_section("Audience → ContentStyle Preferences")
    
    query = """
    MATCH (a:Audience {name: 'gen-z'})-[r:PREFERS_STYLE]->(cs:ContentStyle)
    RETURN cs.name as style, r.preference_score as score
    ORDER BY r.preference_score DESC
    LIMIT 5
    """
    results = execute_query(query)
    
    print("  Gen-Z prefers styles:")
    for result in results:
        print(f"    - {result['style']} (score: {result['score']:.2f})")


def test_intent_requirements():
    """Test user intent style requirements."""
    print_section("UserIntent → ContentStyle Requirements")
    
    query = """
    MATCH (ui:UserIntent {name: 'purchase'})-[r:REQUIRES_STYLE]->(cs:ContentStyle)
    RETURN cs.name as style, r.strength as strength
    ORDER BY r.strength DESC
    """
    results = execute_query(query)
    
    print("  Purchase intent requires styles:")
    for result in results:
        print(f"    - {result['style']} (strength: {result['strength']:.2f})")


def test_category_platform_suitability():
    """Test product category platform suitability."""
    print_section("ProductCategory → Platform Suitability")
    
    query = """
    MATCH (pc:ProductCategory {name: 'tech'})-[r:SUITABLE_FOR]->(p:Platform)
    RETURN p.name as platform, r.suitability_score as score
    ORDER BY r.suitability_score DESC
    """
    results = execute_query(query)
    
    print("  Tech products suitable for platforms:")
    for result in results:
        print(f"    - {result['platform']} (score: {result['score']:.2f})")


def test_examples():
    """Test example nodes and relationships."""
    print_section("Example Nodes")
    
    # Count examples
    query = "MATCH (e:Example) RETURN count(e) as total"
    result = execute_query(query)
    total = result[0]["total"] if result else 0
    print(f"  Total examples: {total}")
    
    # Get sample examples
    query = """
    MATCH (e:Example)-[:DEMONSTRATES]->(p:Platform {name: 'instagram'})
    RETURN e.text as text, e.performance_score as score
    ORDER BY e.performance_score DESC
    LIMIT 3
    """
    results = execute_query(query)
    
    print("\n  Sample Instagram examples:")
    for i, result in enumerate(results, 1):
        print(f"    {i}. {result['text']}")
        print(f"       Performance score: {result['score']:.2f}")


def test_example_relationships():
    """Test example relationships."""
    print_section("Example Relationships")
    
    query = """
    MATCH (e:Example)-[:DEMONSTRATES]->(p:Platform)
    MATCH (e)-[:USES_STYLE]->(cs:ContentStyle)
    MATCH (e)-[:TARGETS]->(a:Audience)
    RETURN p.name as platform, cs.name as style, a.name as audience, count(e) as count
    ORDER BY count DESC
    LIMIT 5
    """
    results = execute_query(query)
    
    print("  Example relationship patterns:")
    for result in results:
        print(f"    {result['platform']} + {result['style']} + {result['audience']}: {result['count']} examples")


def test_cross_platform_insights():
    """Test cross-platform audience sharing."""
    print_section("Cross-Platform Audience Sharing")
    
    query = """
    MATCH (p1:Platform {name: 'instagram'})-[r:SHARES_AUDIENCE_WITH]->(p2:Platform)
    RETURN p2.name as platform, r.overlap_pct as overlap
    ORDER BY r.overlap_pct DESC
    """
    results = execute_query(query)
    
    print("  Platforms sharing audience with Instagram:")
    for result in results:
        print(f"    - {result['platform']} ({result['overlap']*100:.0f}% overlap)")


def test_complex_query():
    """Test a complex multi-hop query."""
    print_section("Complex Multi-Hop Query")
    
    query = """
    MATCH (pc:ProductCategory {name: 'tech'})-[:SUITABLE_FOR]->(p:Platform)
    MATCH (p)-[:PREFERS_STYLE]->(cs:ContentStyle)
    MATCH (p)-[:SUPPORTS]->(ct:CreativeType)
    RETURN DISTINCT p.name as platform, 
           collect(DISTINCT cs.name)[0..3] as styles,
           collect(DISTINCT ct.name)[0..3] as creative_types
    ORDER BY p.name
    LIMIT 3
    """
    results = execute_query(query)
    
    print("  Tech products: Recommended platforms, styles, and creative types:")
    for result in results:
        print(f"\n    Platform: {result['platform']}")
        print(f"      Styles: {', '.join(result['styles'])}")
        print(f"      Creative Types: {', '.join(result['creative_types'])}")


def test_kg_service_functions():
    """Test kg_service.py functions."""
    print_section("Testing kg_service.py Functions")
    
    # Test get_platform_data_batch_cached (constraints)
    print("\n  1. get_platform_data_batch_cached('instagram') - constraints:")
    strategy = get_platform_data_batch_cached("instagram")
    constraints = strategy.get("constraints", {})
    print(f"     {constraints}")
    
    # Test get_platform_data_batch_cached (full strategy)
    print("\n  2. get_platform_data_batch_cached('linkedin', audience='b2b professionals', intent='purchase'):")
    strategy = get_platform_data_batch_cached(
        platform="linkedin",
        audience="b2b professionals",
        intent="purchase",
    )
    print(f"     Constraints: {strategy.get('constraints', {})}")
    print(f"     Preferred Styles: {strategy.get('preferred_styles', [])[:3]}")
    print(f"     Recommended Creative Types: {strategy.get('recommended_creative_types', [])[:3]}")


def main():
    """Run all test queries."""
    print("\n" + "=" * 70)
    print("  Neo4j Knowledge Graph Test Queries")
    print("=" * 70)
    
    # Test connection first
    if not test_connection():
        print("\n  Please fix connection issues before running other tests.")
        return
    
    # Run all tests
    test_node_counts()
    test_platform_constraints()
    test_platform_relationships()
    test_platform_creativetypes()
    test_platform_styles()
    test_audience_preferences()
    test_intent_requirements()
    test_category_platform_suitability()
    test_examples()
    test_example_relationships()
    test_cross_platform_insights()
    test_complex_query()
    test_kg_service_functions()
    
    print("\n" + "=" * 70)
    print("  All tests complete!")
    print("=" * 70)
    print("\n  If all tests passed, you're ready to refactor the code to use Neo4j.")
    print("  If any tests failed, check:")
    print("    1. All population scripts ran successfully")
    print("    2. Neo4j is running and accessible")
    print("    3. Data was populated correctly")


if __name__ == "__main__":
    main()

