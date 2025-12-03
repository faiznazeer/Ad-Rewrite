# Ad Rewriter Agent

An intelligent ad rewriting system that adapts marketing copy for different social media platforms using LangChain, LangGraph, and a Neo4j knowledge graph.

## Overview

The Ad Rewriter Agent takes input text and rewrites it for multiple platforms (Instagram, LinkedIn, Twitter, etc.) in parallel, leveraging:
- **Neo4j Knowledge Graph**: Platform strategies, audience preferences, content styles, and relationships
- **LangChain**: Modular chains for text processing, LLM interaction, and example retrieval
- **LangGraph**: Parallel orchestration of platform-specific rewriting tasks
- **Vector Search**: Example-based retrieval using Chroma and HuggingFace embeddings
- **Graph RAG**: Combines structured graph knowledge with semantic vector search for context-aware rewrites

## Architecture

```
┌─────────────┐
│  FastAPI    │
│   /run-agent│
└──────┬──────┘
       │
┌──────▼──────────────────┐
│ LangGraph Orchestrator  │
│  (Parallel Execution)   │
└──────┬──────────────────┘
       │
   ┌───┴───┬─────────┬─────────┐
   │       │         │         │
┌──▼──┐ ┌─▼───┐   ┌──▼──┐   ┌──▼──┐
│Insta│ │FB   │   │Twit │   │ ... │
│Chain│ │Chain│   │Chain│   │     │
└──┬──┘ └─┬───┘   └──┬──┘   └──┬──┘
   │      │          │         │
   └──────┴──────────┴─────────┘
         │
    ┌────▼────┐
    │ Neo4j KG│
    │ Chroma  │
    │   LLM   │
    └─────────┘
```

### Components

- **`app/main.py`**: FastAPI endpoint accepting rewrite requests
- **`agent/langgraph_orchestration.py`**: LangGraph-based parallel execution
- **`agent/platform_agent.py`**: Per-platform LangChain chains (KG query, example retrieval, LLM rewriting)
- **`agent/kg_service.py`**: Neo4j knowledge graph queries with caching

## Setup

### Prerequisites

- Python 3.12+
- Neo4j (Docker recommended)
- OpenAI API key (or compatible LLM)

### Installation

1. **Clone and install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up Neo4j:**
   ```bash
   docker run -d --name neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:latest
   ```

3. **Configure environment variables** (`.env`):
   ```env
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=password
   OPENAI_API_KEY=your_key_here
   LLM_MODEL_NAME=gpt-5-mini
   EMBED_MODEL_NAME=all-MiniLM-L6-v2
   ```

4. **Populate Neo4j knowledge graph:**
   ```bash
   python scripts/populate_kg.py          # Base nodes
   python scripts/populate_relationships.py  # Relationships
   python scripts/populate_examples.py     # Example ad copy
   python scripts/test_kg_queries.py      # Verify setup
   ```

5. **Ingest examples into vector store:**
   ```bash
   python -m agent.platform_agent --ingest
   ```

6. **Start the API:**
   ```bash
   uvicorn app.main:app --reload
   ```

## API Usage

### Endpoint: `POST /run-agent`

**Request:**
```json
{
  "text": "Our new SaaS platform helps teams collaborate",
  "target_platforms": ["linkedin", "twitter"],
  "audience": "b2b professionals",
  "user_intent": "purchase",
  "product_category": "tech",
  "tone_map": {"linkedin": "professional"},
  "include_strategy_insights": true
}
```

**Response:**
```json
{
  "meta": {
    "latency_ms": 1234,
    "total_platforms": 2,
    "context": {
      "audience": "b2b professionals",
      "user_intent": "purchase",
      "product_category": "tech"
    }
  },
  "results": [
    {
      "platform": "linkedin",
      "rewritten_text": "...",
      "explanation": "...",
      "examples_used": [...],
      "strategy_data": {
        "preferred_styles": [...],
        "recommended_creative_types": [...],
        "target_audiences": [...]
      }
    }
  ],
  "strategy_insights": {
    "linkedin": {
      "recommended_styles": ["professional", "educational"],
      "recommended_creative_types": ["text-only", "video"],
      "target_audiences": ["b2b professionals", "millennials"],
      "audience_preferred_styles": [...],
      "intent_required_styles": [...],
      "category_suitability_score": 0.85
    }
  }
}
```

### Request Fields

- **`text`** (required): Input ad copy to rewrite
- **`target_platforms`** (required): List of platforms (e.g., `["instagram", "linkedin"]`)
- **`audience`** (optional): Target audience (`"gen-z"`, `"b2b professionals"`, etc.)
- **`user_intent`** (optional): Funnel stage (`"awareness"`, `"consideration"`, `"purchase"`, `"engagement"`)
- **`product_category`** (optional): Category (`"tech"`, `"fashion"`, `"food"`, `"b2b"`, `"services"`)
- **`tone_map`** (optional): Per-platform tone/style overrides (e.g., `{"linkedin": "professional"}`)
- **`include_strategy_insights`** (default: `true`): Include KG-based strategy recommendations in response

## Knowledge Graph Schema

The Neo4j knowledge graph models:

- **Platforms**: Instagram, LinkedIn, TikTok, Twitter, Facebook, etc.
- **Audiences**: Gen-Z, Millennials, B2B Professionals, Parents, etc.
- **User Intents**: Awareness, Consideration, Purchase, Engagement
- **Content Styles**: Professional, Energetic, Visual, Casual, Educational, etc.
- **Creative Types**: Video, Image, Carousel, Text-only, Story, etc.
- **Product Categories**: Tech, Fashion, Food, B2B, Services, etc.
- **Examples**: Ad copy examples linked to platforms, styles, audiences, and intents

### Key Relationships

- `Platform -[:PREFERS_STYLE {score}]-> ContentStyle`
- `Platform -[:TARGETS {weight}]-> Audience`
- `Platform -[:SUPPORTS {score}]-> CreativeType`
- `Audience -[:PREFERS_STYLE {preference_score}]-> ContentStyle`
- `UserIntent -[:REQUIRES_STYLE {strength}]-> ContentStyle`
- `ProductCategory -[:SUITABLE_FOR {suitability_score}]-> Platform`
- `Example -[:FOR_PLATFORM]-> Platform`
- `Example -[:HAS_STYLE]-> ContentStyle`
- `Example -[:TARGETS_AUDIENCE]-> Audience`
- `Example -[:FOR_INTENT]-> UserIntent`

## How It Works

1. **Request Processing**: FastAPI receives rewrite request with platform targets and optional context (audience, intent, category)
2. **Parallel Orchestration**: LangGraph creates parallel nodes for each platform
3. **Platform Chain Execution** (per platform):
   - Query Neo4j KG for platform strategies (styles, creative types, audience preferences)
   - Retrieve similar examples from Chroma vector store using semantic search
   - Invoke LLM with platform context, examples, and strategy recommendations
   - Return rewritten text with explanation and strategy data
4. **Response Assembly**: Combine results with strategy insights and metadata

## Graph RAG Approach

The system implements **Graph RAG** by combining:

1. **Structured Graph Knowledge**: Neo4j stores explicit relationships (e.g., `Platform → TARGETS → Audience → PREFERS_STYLE → ContentStyle`) with weighted edges, enabling multi-hop reasoning and precise strategy recommendations.

2. **Semantic Vector Search**: Chroma vector store retrieves similar ad examples using embeddings, capturing semantic similarity that complements structured knowledge.

3. **Hybrid Retrieval**: The LLM receives both structured strategy data (from Neo4j) and similar examples (from Chroma), enabling context-aware rewrites that respect platform conventions while learning from successful patterns.

This approach improves precision over pure vector search by leveraging explicit domain relationships, while maintaining recall through semantic example matching.

## Performance Optimizations

- **Batched Neo4j Queries**: Single query replaces 8-11 separate queries per platform
- **Connection Pooling**: Neo4j driver configured with connection pooling (50 max connections)
- **Parallel Execution**: LangGraph runs platform chains concurrently
- **Thread-Safe Initialization**: Double-check locking for embeddings and vector store singletons


## Evaluation

Evaluate the agent using examples as ground truth:

```bash
python eval/evaluate.py  # Generates eval_results.json with metrics
```

**Metrics calculated:**
- **ROUGE-L**: Longest common subsequence overlap (precision, recall, F-measure)
- **BLEU**: N-gram precision score with smoothing
- **Semantic Similarity**: Cosine similarity using embeddings (same model as agent)
- **Length Ratio**: Output length relative to ground truth

The evaluation script:
1. Loads examples from `examples.json` as ground truth
2. Creates test cases by pairing generic inputs with example outputs
3. Runs the agent on each test case
4. Calculates metrics comparing predictions to ground truth
5. Generates per-platform breakdowns and aggregate statistics

## Development

### Project Structure

```
ad-rewriter/
├── agent/
│   ├── kg_service.py           # Neo4j queries and caching
│   ├── platform_agent.py       # Platform-specific chains
│   └── langgraph_orchestration.py  # Parallel orchestration
├── app/
│   └── main.py                 # FastAPI endpoints
├── scripts/
│   ├── populate_kg.py          # Initialize KG nodes
│   ├── populate_relationships.py  # Create relationships
│   ├── populate_examples.py    # Load examples from examples.json
│   ├── test_kg_queries.py      # Verify KG setup
│   ├── README.md               # Detailed Neo4j setup guide
│   └── QUERY_EXAMPLES.md       # Example Cypher queries
├── data/
│   ├── examples.json           # Example ad copy (ground truth)
│   └── kg_schema.cypher        # Neo4j schema definition
├── eval/
│   └── evaluate.py             # Evaluation harness with metrics
└── requirements.txt
```

### Running Tests

```bash
# Test Neo4j setup
python scripts/test_kg_queries.py

# Run evaluation
python eval/evaluate.py
```

## Future Enhancements

Potential improvements for learning and adaptation:

1. **LangGraph Memory Nodes**: Use checkpointing to store rewrite history and user preferences
2. **Feedback Loop**: Add `/feedback` endpoint to collect user ratings and learn from successful rewrites
3. **Adaptive Prompts**: Dynamically adjust prompts based on user-specific successful patterns
4. **Performance-Based Weighting**: Weight example retrieval by success rates stored in Neo4j
5. **A/B Testing**: Track strategy performance metrics to enable data-driven improvements

See `scripts/README.md` for detailed Neo4j setup instructions and query examples.
