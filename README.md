# Ad Rewriter Agent

An intelligent ad rewriting system that adapts marketing copy for different social media platforms using LangChain, LangGraph, and a Neo4j knowledge graph.

## Overview

The Ad Rewriter Agent takes input text and rewrites it for multiple platforms (Instagram, LinkedIn, Twitter, etc.) in parallel, leveraging:
- **Neo4j Knowledge Graph**: Platform constraints, audience preferences, content styles, and relationships
- **LangChain**: Modular chains for text processing, LLM interaction, and validation
- **LangGraph**: Parallel orchestration of platform-specific rewriting tasks
- **Vector Search**: Example-based retrieval using Chroma and HuggingFace embeddings

## Architecture

```
┌─────────────┐
│  FastAPI    │
│   /run-agent│
└──────┬──────┘
       │
┌──────▼──────────────────┐
│ LangGraph Orchestrator │
│  (Parallel Execution)   │
└──────┬──────────────────┘
       │
   ┌───┴───┬─────────┬─────────┐
   │       │         │         │
┌──▼──┐ ┌─▼──┐   ┌──▼──┐   ┌──▼──┐
│Insta│ │Link│   │Twit │   │ ... │
│Chain│ │Chain│   │Chain│   │     │
└──┬──┘ └─┬──┘   └──┬──┘   └──┬──┘
   │      │         │         │
   └──────┴─────────┴─────────┘
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
- **`agent/platform_agent.py`**: Per-platform LangChain chains (sanitization, retrieval, LLM rewriting, validation)
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
   python scripts/populate_kg.py          # Base nodes and constraints
   python scripts/populate_relationships.py  # Relationships
   python scripts/populate_examples.py     # Example ad copy
   python scripts/test_kg_queries.py      # Verify setup
   ```

5. **Start the API:**
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
  "include_strategy_insights": true,
  "suggest_alternative_platforms": true
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
  "validation_summary": {"total": 2, "ok": 2, "failed": 0},
  "results": [
    {
      "platform": "linkedin",
      "rewritten_text": "...",
      "explanation": "...",
      "validation": {"ok": true, "issues": []},
      "strategy_data": {...}
    }
  ],
  "strategy_insights": {
    "linkedin": {
      "recommended_styles": ["professional", "educational"],
      "recommended_creative_types": ["text-only", "video"],
      "target_audiences": ["b2b professionals", "millennials"]
    }
  }
}
```

### Request Fields

- **`text`** (required): Input ad copy to rewrite
- **`target_platforms`** (required): List of platforms (e.g., `["instagram", "linkedin"]`)
- **`audience`** (optional): Target audience (`"gen-z"`, `"b2b professionals"`, etc.)
- **`user_intent`** (optional): Funnel stage (`"awareness"`, `"purchase"`, etc.)
- **`product_category`** (optional): Category (`"tech"`, `"fashion"`, etc.)
- **`tone_map`** (optional): Per-platform tone overrides
- **`length_prefs`** (optional): Per-platform max length overrides
- **`include_strategy_insights`** (default: `true`): Include KG recommendations
- **`suggest_alternative_platforms`** (default: `true`): Suggest similar platforms

## Knowledge Graph Schema

The Neo4j knowledge graph models:

- **Platforms**: Instagram, LinkedIn, TikTok, etc. with constraints (max length, emoji policy, CTA requirements)
- **Audiences**: Gen-Z, Millennials, B2B Professionals, etc.
- **User Intents**: Awareness, Consideration, Purchase, Engagement
- **Content Styles**: Professional, Energetic, Visual, Casual, etc.
- **Creative Types**: Video, Image, Carousel, Text-only, etc.
- **Product Categories**: Tech, Fashion, Food, B2B, etc.
- **Examples**: Ad copy examples linked to platforms, styles, audiences, and intents

### Key Relationships

- `Platform -[:HAS_CONSTRAINT]-> Constraint`
- `Platform -[:PREFERS_STYLE]-> ContentStyle`
- `Platform -[:TARGETS]-> Audience`
- `Platform -[:SUPPORTS]-> CreativeType`
- `Audience -[:PREFERS_STYLE]-> ContentStyle`
- `UserIntent -[:REQUIRES_STYLE]-> ContentStyle`
- `ProductCategory -[:SUITABLE_FOR]-> Platform`

## How It Works

1. **Request Processing**: FastAPI receives rewrite request with platform targets and optional context
2. **Parallel Orchestration**: LangGraph creates parallel nodes for each platform
3. **Platform Chain Execution** (per platform):
   - Sanitize input text and extract entities
   - Query Neo4j KG for constraints, styles, and strategy
   - Retrieve similar examples from Chroma vector store
   - Invoke LLM with platform context, constraints, examples, and strategy
   - Validate output against platform constraints and repair if needed
4. **Response Assembly**: Combine results with strategy insights and validation summaries

## Performance Optimizations

- **Batched Neo4j Queries**: Single query replaces 8-11 separate queries per platform
- **LRU Caching**: Platform data cached (128 entries) for faster subsequent requests
- **Connection Pooling**: Neo4j driver configured with connection pooling
- **Parallel Execution**: LangGraph runs platform chains concurrently
- **Strategy Data Reuse**: Strategy insights reused from rewrite results (no re-querying)

Expected latency: **10-20 seconds** (or **5-15 seconds** with cache) for 2 platforms.

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
│   ├── populate_examples.py    # Load examples
│   └── test_kg_queries.py      # Verify KG setup
├── data/
│   └── examples.json           # Example ad copy
├── eval/
│   └── evaluate.py             # Evaluation harness
└── tests/
    └── test_platform_agent.py  # Unit tests
```

### Running Tests

```bash
pytest tests/
```

### Evaluation

```bash
python eval/evaluate.py  # Generates eval_results.csv
```

See `scripts/README.md` for detailed Neo4j setup instructions.
