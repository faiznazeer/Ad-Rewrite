# Neo4j Query Examples

Quick reference guide for testing queries in Neo4j Browser (http://localhost:7474).

## Basic Queries

### View All Platforms
```cypher
MATCH (p:Platform)
RETURN p.name, p.description, p.type
ORDER BY p.name
```

### View All Constraints for a Platform
```cypher
MATCH (p:Platform {name: 'instagram'})-[:HAS_CONSTRAINT]->(c:Constraint)
RETURN c.name, c.type, c.value
```

### Count All Nodes by Type
```cypher
MATCH (n)
RETURN labels(n)[0] as node_type, count(n) as count
ORDER BY count DESC
```

## Platform Queries

### Get Platform Strategy (Constraints + Styles + Creative Types)
```cypher
MATCH (p:Platform {name: 'linkedin'})
OPTIONAL MATCH (p)-[:HAS_CONSTRAINT]->(c:Constraint)
OPTIONAL MATCH (p)-[:PREFERS_STYLE]->(cs:ContentStyle)
OPTIONAL MATCH (p)-[:SUPPORTS]->(ct:CreativeType)
RETURN p.name,
       collect(DISTINCT c.name) as constraints,
       collect(DISTINCT cs.name) as styles,
       collect(DISTINCT ct.name) as creative_types
```

### Find Platforms Targeting Gen-Z
```cypher
MATCH (p:Platform)-[r:TARGETS]->(a:Audience {name: 'gen-z'})
RETURN p.name, r.weight
ORDER BY r.weight DESC
```

### Find Platforms That Share Audience with Instagram
```cypher
MATCH (p1:Platform {name: 'instagram'})-[r:SHARES_AUDIENCE_WITH]->(p2:Platform)
RETURN p2.name as platform, r.overlap_pct as overlap
ORDER BY r.overlap_pct DESC
```

## Style & Creative Type Queries

### Get Recommended Styles for LinkedIn + B2B Audience + Purchase Intent
```cypher
MATCH (p:Platform {name: 'linkedin'})-[:PREFERS_STYLE]->(s1:ContentStyle)
MATCH (a:Audience {name: 'b2b professionals'})-[:PREFERS_STYLE]->(s2:ContentStyle)
MATCH (ui:UserIntent {name: 'purchase'})-[:REQUIRES_STYLE]->(s3:ContentStyle)
RETURN DISTINCT s1.name as platform_style, 
                s2.name as audience_style, 
                s3.name as intent_style
LIMIT 10
```

### Find Best Creative Types for Instagram
```cypher
MATCH (p:Platform {name: 'instagram'})-[r:SUPPORTS]->(ct:CreativeType)
RETURN ct.name, r.score
ORDER BY r.score DESC
```

## Product Category Queries

### Find Best Platforms for Tech Products
```cypher
MATCH (pc:ProductCategory {name: 'tech'})-[r:SUITABLE_FOR]->(p:Platform)
RETURN p.name, r.suitability_score
ORDER BY r.suitability_score DESC
```

### Get Complete Strategy for Tech Products on LinkedIn
```cypher
MATCH (pc:ProductCategory {name: 'tech'})-[:SUITABLE_FOR]->(p:Platform {name: 'linkedin'})
MATCH (p)-[:PREFERS_STYLE]->(cs:ContentStyle)
MATCH (p)-[:SUPPORTS]->(ct:CreativeType)
MATCH (pc)-[:WORKS_BEST_WITH]->(ct2:CreativeType)
RETURN p.name as platform,
       collect(DISTINCT cs.name)[0..5] as recommended_styles,
       collect(DISTINCT ct.name)[0..5] as platform_creative_types,
       collect(DISTINCT ct2.name)[0..5] as category_creative_types
```

## Example Queries

### Get Examples for Instagram
```cypher
MATCH (e:Example)-[:DEMONSTRATES]->(p:Platform {name: 'instagram'})
RETURN e.text, e.performance_score, e.engagement_rate
ORDER BY e.performance_score DESC
LIMIT 10
```

### Get Examples Using Fun Style
```cypher
MATCH (e:Example)-[:USES_STYLE]->(cs:ContentStyle {name: 'fun'})
RETURN e.text, e.platform
LIMIT 10
```

### Get Examples Targeting Gen-Z with Purchase Intent
```cypher
MATCH (e:Example)-[:TARGETS]->(a:Audience {name: 'gen-z'})
MATCH (e)-[:FOR_INTENT]->(ui:UserIntent {name: 'purchase'})
RETURN e.text, e.platform, e.performance_score
ORDER BY e.performance_score DESC
LIMIT 10
```

### Find Best Performing Examples by Platform
```cypher
MATCH (e:Example)-[:DEMONSTRATES]->(p:Platform)
RETURN p.name, 
       avg(e.performance_score) as avg_performance,
       avg(e.engagement_rate) as avg_engagement,
       count(e) as example_count
ORDER BY avg_performance DESC
```

## Complex Multi-Hop Queries

### Complete Strategy Query: Platform + Audience + Intent + Category
```cypher
MATCH (pc:ProductCategory {name: 'fashion'})-[:SUITABLE_FOR]->(p:Platform)
MATCH (p)-[:TARGETS]->(a:Audience {name: 'gen-z'})
MATCH (p)-[:PREFERS_STYLE]->(cs:ContentStyle)
MATCH (a)-[:PREFERS_STYLE]->(cs2:ContentStyle)
MATCH (ui:UserIntent {name: 'purchase'})-[:REQUIRES_STYLE]->(cs3:ContentStyle)
RETURN DISTINCT p.name as platform,
       collect(DISTINCT cs.name)[0..3] as platform_styles,
       collect(DISTINCT cs2.name)[0..3] as audience_styles,
       collect(DISTINCT cs3.name)[0..3] as intent_styles
LIMIT 5
```

### Find Similar Platforms Based on Shared Audiences
```cypher
MATCH (p1:Platform {name: 'instagram'})-[r1:TARGETS]->(a:Audience)
MATCH (p2:Platform)-[r2:TARGETS]->(a)
WHERE p1 <> p2
WITH p2, count(a) as shared_audiences, avg((r1.weight + r2.weight) / 2) as avg_weight
RETURN p2.name, shared_audiences, avg_weight
ORDER BY shared_audiences DESC, avg_weight DESC
LIMIT 5
```

### Get Examples That Match Platform + Style + Audience
```cypher
MATCH (e:Example)-[:DEMONSTRATES]->(p:Platform {name: 'instagram'})
MATCH (e)-[:USES_STYLE]->(cs:ContentStyle {name: 'visual'})
MATCH (e)-[:TARGETS]->(a:Audience {name: 'gen-z'})
RETURN e.text, e.performance_score
ORDER BY e.performance_score DESC
LIMIT 5
```

## Validation Queries

### Check Relationship Counts
```cypher
MATCH ()-[r]->()
RETURN type(r) as relationship_type, count(r) as count
ORDER BY count DESC
```

### Find Nodes Without Relationships
```cypher
MATCH (n)
WHERE NOT (n)--()
RETURN labels(n)[0] as node_type, n.name as name
LIMIT 20
```

### Verify Example Relationships
```cypher
MATCH (e:Example)
OPTIONAL MATCH (e)-[:DEMONSTRATES]->(p:Platform)
OPTIONAL MATCH (e)-[:USES_STYLE]->(cs:ContentStyle)
OPTIONAL MATCH (e)-[:TARGETS]->(a:Audience)
OPTIONAL MATCH (e)-[:FOR_INTENT]->(ui:UserIntent)
RETURN e.id,
       count(p) as platform_count,
       count(cs) as style_count,
       count(a) as audience_count,
       count(ui) as intent_count
ORDER BY platform_count DESC, style_count DESC
LIMIT 10
```

## Performance Queries

### Find Top Performing Examples
```cypher
MATCH (e:Example)
RETURN e.platform, 
       e.text,
       e.performance_score,
       e.engagement_rate
ORDER BY e.performance_score DESC
LIMIT 20
```

### Average Performance by Platform
```cypher
MATCH (e:Example)-[:DEMONSTRATES]->(p:Platform)
RETURN p.name,
       count(e) as example_count,
       avg(e.performance_score) as avg_performance,
       avg(e.engagement_rate) as avg_engagement
ORDER BY avg_performance DESC
```

## Tips

1. **Use LIMIT** to avoid overwhelming results
2. **Use RETURN DISTINCT** to avoid duplicate results in multi-hop queries
3. **Use OPTIONAL MATCH** when relationships might not exist
4. **Use collect()** to aggregate multiple related nodes
5. **Use ORDER BY** to sort results meaningfully

