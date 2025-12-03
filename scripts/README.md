# Neo4j Knowledge Graph Setup

This directory contains scripts to set up and populate the Neo4j knowledge graph for the ad-rewriter application.

## Prerequisites

1. **Install Neo4j**
   - **Option 1 (Docker - Recommended)**: 
     ```bash
     docker run -d \
       --name neo4j \
       -p 7474:7474 -p 7687:7687 \
       -e NEO4J_AUTH=neo4j/password \
       neo4j:latest
     ```
   - **Option 2 (Local Installation)**: Download from [neo4j.com](https://neo4j.com/download/)

2. **Set Environment Variables**
   Create a `.env` file in the project root:
   ```env
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=password
   ```

3. **Install Python Dependencies**
   ```bash
   pip install neo4j
   ```

## Setup Steps

### 1. Verify Connection
```bash
python -c "from agent.kg_service import verify_connection; print('Connected!' if verify_connection() else 'Failed')"
```

### 2. Populate Base Nodes
This creates all node types (Platforms, Audiences, Intents, etc.):
```bash
python scripts/populate_kg.py
```

### 3. Populate Relationships
This creates all relationships between nodes with realistic weights and scores:
```bash
python scripts/populate_relationships.py
```

This script creates:
- **Platform → Audience** (TARGETS): Which audiences each platform targets
- **Platform → CreativeType** (SUPPORTS): Which creative formats each platform supports
- **Platform → ContentStyle** (PREFERS_STYLE): Preferred content styles per platform
- **Platform → Platform** (SHARES_AUDIENCE_WITH): Audience overlap between platforms
- **Audience → ContentStyle** (PREFERS_STYLE): Style preferences by audience
- **UserIntent → ContentStyle** (REQUIRES_STYLE): Style requirements by intent
- **UserIntent → CreativeType** (WORKS_WITH): Creative type compatibility by intent
- **ProductCategory → Platform** (SUITABLE_FOR): Platform suitability by category
- **ProductCategory → CreativeType** (WORKS_BEST_WITH): Best creative types by category
- **CreativeType → Platform** (WORKS_BEST_ON): Best platforms for each creative type

### 4. Populate Examples
This loads examples from `examples.json` and creates Example nodes in Neo4j:
```bash
python scripts/populate_examples.py
```

This script:
- **Loads examples** from `data/examples.json`
- **Creates Example nodes** with metadata (performance_score, engagement_rate)
- **Links examples** to Platform, ContentStyle, Audience, and UserIntent nodes
- **Infers relationships** based on platform characteristics and text analysis

Each example is linked via:
- `(Example)-[:DEMONSTRATES]->(Platform)`
- `(Example)-[:USES_STYLE]->(ContentStyle)`
- `(Example)-[:TARGETS]->(Audience)` (inferred)
- `(Example)-[:FOR_INTENT]->(UserIntent)` (inferred)

### 5. Test Knowledge Graph
Run comprehensive test queries to verify everything is set up correctly:
```bash
python scripts/test_kg_queries.py
```

This test script verifies:
- ✅ Neo4j connection
- ✅ Node counts (all node types created)
- ✅ Platform relationships (audiences, creative types, styles)
- ✅ Audience preferences
- ✅ Intent requirements
- ✅ Category-platform suitability
- ✅ Example nodes and relationships
- ✅ Cross-platform insights
- ✅ Complex multi-hop queries
- ✅ kg_service.py function calls

**Run this before refactoring the main code to ensure the KG is working correctly!**

## Schema Overview

The knowledge graph models:

- **Platforms**: Instagram, LinkedIn, TikTok, etc.
- **Audiences**: Gen-Z, Millennials, B2B Professionals, etc.
- **User Intents**: Awareness, Consideration, Purchase, etc.
- **Creative Types**: Video, Image, Carousel, etc.
- **Content Styles**: Professional, Energetic, Visual, etc.
- **Product Categories**: Tech, Fashion, Food, etc.
- **Examples**: Ad copy examples with metadata

## Accessing Neo4j Browser

Once Neo4j is running, access the browser at:
- **URL**: http://localhost:7474
- **Username**: neo4j
- **Password**: password (or your configured password)

## Useful Cypher Queries

```cypher
// View all platforms
MATCH (p:Platform) RETURN p

// Find platforms targeting Gen-Z
MATCH (p:Platform)-[:TARGETS]->(a:Audience {name: 'gen-z'})
RETURN p.name

// Get recommended styles for LinkedIn
MATCH (p:Platform {name: 'linkedin'})-[:PREFERS_STYLE]->(s:ContentStyle)
RETURN s.name
```


