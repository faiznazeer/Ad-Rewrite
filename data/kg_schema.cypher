// Neo4j Knowledge Graph Schema for Ad Rewriter Domain
// This file defines the node types, relationship types, and constraints

// ============================================================================
// CONSTRAINTS (Unique constraints and indexes)
// ============================================================================

// Platform nodes
CREATE CONSTRAINT platform_name IF NOT EXISTS FOR (p:Platform) REQUIRE p.name IS UNIQUE;
CREATE INDEX platform_name_index IF NOT EXISTS FOR (p:Platform) ON (p.name);

// Audience nodes
CREATE CONSTRAINT audience_name IF NOT EXISTS FOR (a:Audience) REQUIRE a.name IS UNIQUE;
CREATE INDEX audience_name_index IF NOT EXISTS FOR (a:Audience) ON (a.name);

// UserIntent nodes
CREATE CONSTRAINT intent_name IF NOT EXISTS FOR (ui:UserIntent) REQUIRE ui.name IS UNIQUE;
CREATE INDEX intent_name_index IF NOT EXISTS FOR (ui:UserIntent) ON (ui.name);

// CreativeType nodes
CREATE CONSTRAINT creativetype_name IF NOT EXISTS FOR (ct:CreativeType) REQUIRE ct.name IS UNIQUE;
CREATE INDEX creativetype_name_index IF NOT EXISTS FOR (ct:CreativeType) ON (ct.name);

// ContentStyle nodes
CREATE CONSTRAINT contentstyle_name IF NOT EXISTS FOR (cs:ContentStyle) REQUIRE cs.name IS UNIQUE;
CREATE INDEX contentstyle_name_index IF NOT EXISTS FOR (cs:ContentStyle) ON (cs.name);

// ProductCategory nodes
CREATE CONSTRAINT productcategory_name IF NOT EXISTS FOR (pc:ProductCategory) REQUIRE pc.name IS UNIQUE;
CREATE INDEX productcategory_name_index IF NOT EXISTS FOR (pc:ProductCategory) ON (pc.name);

// Example nodes
CREATE CONSTRAINT example_id IF NOT EXISTS FOR (e:Example) REQUIRE e.id IS UNIQUE;
CREATE INDEX example_id_index IF NOT EXISTS FOR (e:Example) ON (e.id);

// ============================================================================
// NODE PROPERTIES
// ============================================================================

// Platform: {name, description, type, created_at}
// Audience: {name, age_range, demographics, description}
// UserIntent: {name, funnel_stage, description}
// CreativeType: {name, format, description}
// ContentStyle: {name, tone, description}
// ProductCategory: {name, industry, description}
// Example: {id, text, platform, tone, performance_score, engagement_rate, created_at}

// ============================================================================
// RELATIONSHIP TYPES
// ============================================================================

// Platform relationships
// (Platform)-[:TARGETS {weight: float 0-1}]->(Audience)
// (Platform)-[:SUPPORTS {score: float 0-1}]->(CreativeType)
// (Platform)-[:PREFERS_STYLE {score: float 0-1}]->(ContentStyle)

// Audience relationships
// (Audience)-[:PREFERS_STYLE {preference_score: float 0-1}]->(ContentStyle)
// (Audience)-[:ENGAGES_WITH {engagement_rate: float}]->(CreativeType)

// UserIntent relationships
// (UserIntent)-[:REQUIRES_STYLE {strength: float 0-1}]->(ContentStyle)
// (UserIntent)-[:WORKS_WITH {compatibility: float 0-1}]->(CreativeType)

// ProductCategory relationships
// (ProductCategory)-[:SUITABLE_FOR {suitability_score: float 0-1}]->(Platform)
// (ProductCategory)-[:WORKS_BEST_WITH {effectiveness: float 0-1}]->(CreativeType)

// CreativeType relationships
// (CreativeType)-[:WORKS_BEST_ON {effectiveness: float 0-1}]->(Platform)

// ContentStyle relationships
// (ContentStyle)-[:EFFECTIVE_AT {timing_score: float 0-1}]->(TimeContext)

// Example relationships
// (Example)-[:DEMONSTRATES]->(Platform)
// (Example)-[:USES_STYLE]->(ContentStyle)
// (Example)-[:TARGETS]->(Audience)
// (Example)-[:FOR_INTENT]->(UserIntent)
// (Example)-[:FOR_CATEGORY]->(ProductCategory)

// ============================================================================
// EXAMPLE QUERIES
// ============================================================================

// Get recommended styles for LinkedIn targeting B2B professionals with purchase intent
// MATCH (p:Platform {name: 'linkedin'})-[:PREFERS_STYLE]->(s:ContentStyle)
// MATCH (a:Audience {name: 'b2b professionals'})-[:PREFERS_STYLE]->(s2:ContentStyle)
// MATCH (ui:UserIntent {name: 'purchase'})-[:REQUIRES_STYLE]->(s3:ContentStyle)
// RETURN DISTINCT s.name, s2.name, s3.name

// Get creative types that work best for tech products on LinkedIn
// MATCH (pc:ProductCategory {name: 'tech'})-[:SUITABLE_FOR]->(p:Platform {name: 'linkedin'})
// MATCH (p)-[:SUPPORTS]->(ct:CreativeType)
// RETURN ct.name, ct.score
// ORDER BY ct.score DESC


