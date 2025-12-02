# Migration from JSON to Neo4j Knowledge Graph

## Summary

The ad-rewriter application has been migrated from using a JSON configuration file (`kg.json`) to a Neo4j knowledge graph for storing and querying platform constraints, relationships, and domain knowledge.

## What Changed

### Removed
- `data/kg.json` - No longer used (can be archived for reference)
- `KG_PATH` constant
- `_load_kg()` function
- `_kg_cache` global variable

### Added
- Neo4j knowledge graph with rich domain knowledge
- `agent/kg_service.py` - Service layer for Neo4j queries
- Population scripts in `scripts/` directory
- Graph relationships between platforms, audiences, intents, styles, etc.

### Updated
- `agent/platform_agent.py`:
  - Now uses `get_platform_constraints()` from `kg_service` instead of loading JSON
  - Uses `get_platform_preferred_styles()` for style recommendations
  - `validate_text()` now accepts `constraints` parameter (instead of `kg_rules`)
  - `create_platform_chain()` queries Neo4j for platform data
  - Prompt template updated to use `constraints` instead of `kg_rules`

- `tests/test_platform_agent.py`:
  - Updated to use `constraints` parameter

## Benefits

1. **Rich Relationships**: Can query cross-platform insights, audience preferences, intent requirements
2. **Dynamic Updates**: Constraints can be updated in Neo4j without code changes
3. **Scalability**: Easy to add new platforms, audiences, styles, etc.
4. **Queryability**: Complex multi-hop queries for recommendations
5. **Extensibility**: Can add more domain knowledge (product categories, creative types, etc.)

## Migration Steps (if setting up fresh)

1. Install Neo4j (Docker recommended)
2. Set environment variables in `.env`:
   ```
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=password
   ```
3. Run population scripts in order:
   ```bash
   python scripts/populate_kg.py          # Base nodes
   python scripts/populate_relationships.py  # Relationships
   python scripts/populate_examples.py     # Examples
   ```
4. Test the setup:
   ```bash
   python scripts/test_kg_queries.py
   ```

## Backward Compatibility

- The API interface remains the same (`rewrite_for_platform()` function signature unchanged)
- Response format is identical
- No changes needed to calling code

## Notes

- `kg.json` can be kept as a backup/reference but is no longer loaded by the application
- All platform constraints are now stored in Neo4j as `Constraint` nodes linked via `HAS_CONSTRAINT` relationships
- Preferred styles are stored as `PREFERS_STYLE` relationships from Platform to ContentStyle nodes

