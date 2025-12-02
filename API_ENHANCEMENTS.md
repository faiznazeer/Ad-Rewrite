# API Enhancements with Neo4j Knowledge Graph

## Overview

The API has been enhanced to leverage the Neo4j knowledge graph for context-aware ad rewriting. The system now uses audience, intent, and product category information to provide more intelligent rewrites and strategy recommendations.

## Enhanced Request Model

### New Fields

```python
class RunAgentRequest(BaseModel):
    text: str
    target_platforms: List[str]
    
    # NEW: Knowledge graph context fields
    audience: Optional[str]  # e.g., 'gen-z', 'b2b professionals', 'millennials'
    user_intent: Optional[str]  # e.g., 'awareness', 'consideration', 'purchase', 'engagement'
    product_category: Optional[str]  # e.g., 'tech', 'fashion', 'food', 'b2b'
    
    # Existing optional fields
    tone_map: Optional[Dict[str, str]]
    length_prefs: Optional[Dict[str, int]]
    
    # NEW: Strategy options (default: True)
    include_strategy_insights: bool = True
    suggest_alternative_platforms: bool = True
```

## Enhanced Response

### New Response Fields

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
    "validation_summary": {...},
    "results": [...],
    
    // NEW: Strategy insights from knowledge graph
    "strategy_insights": {
        "linkedin": {
            "recommended_styles": ["professional", "educational", "neutral"],
            "recommended_creative_types": ["text-only", "video", "carousel"],
            "target_audiences": ["b2b professionals", "millennials"],
            "audience_preferred_styles": ["professional", "educational"],
            "intent_required_styles": ["professional", "concise"],
            "category_suitability_score": 0.9
        }
    },
    
    // NEW: Alternative platform suggestions
    "alternative_platforms": {
        "linkedin": [
            {"platform": "twitter", "overlap": 0.65}
        ]
    }
}
```

## How It Works

### 1. Intelligent Style Selection

**Before (JSON-based):**
- Used platform's default preferred styles only
- Example: LinkedIn → "professional"

**After (KG-powered):**
- Combines platform + audience + intent preferences
- Example: LinkedIn + B2B Professionals + Purchase → Prioritizes "professional" + "concise" + "educational"

### 2. Context-Aware Rewrites

The LLM now receives:
- **Platform constraints** (max length, emoji policy, CTA requirements)
- **Recommended styles** based on audience/intent
- **Creative type recommendations**
- **Category-platform suitability scores**

This enables the LLM to create more targeted, effective rewrites.

### 3. Strategy Recommendations

For each platform, the API returns:
- Recommended content styles (prioritized by context)
- Recommended creative types (video, image, carousel, etc.)
- Target audiences
- Audience-specific style preferences (if audience provided)
- Intent-specific style requirements (if intent provided)
- Category-platform suitability score (if category provided)

### 4. Cross-Platform Insights

If `suggest_alternative_platforms=true`:
- Returns platforms that share audiences with requested platforms
- Includes overlap percentages
- Helps users discover new platforms for their campaigns

## Example Usage

### Basic Request (No KG Context)
```json
POST /run-agent
{
    "text": "Our new SaaS platform helps teams collaborate",
    "target_platforms": ["linkedin"]
}
```

### Enhanced Request (With KG Context)
```json
POST /run-agent
{
    "text": "Our new SaaS platform helps teams collaborate better",
    "target_platforms": ["linkedin", "twitter"],
    "audience": "b2b professionals",
    "user_intent": "purchase",
    "product_category": "tech",
    "include_strategy_insights": true,
    "suggest_alternative_platforms": true
}
```

### Response Benefits

1. **Better Rewrites**: Ads optimized for B2B + Purchase intent
2. **Style Recommendations**: "Professional + Concise styles work best"
3. **Creative Recommendations**: "Text-only and Video formats perform well"
4. **Platform Suggestions**: "Consider Reddit for tech communities"
5. **Category Insights**: "Tech products have 90% suitability for LinkedIn"

## Implementation Details

### Platform Chain Enhancement

`create_platform_chain()` now:
1. Queries KG for platform constraints
2. Gets intelligent style recommendations using `get_recommended_styles(platform, audience, intent)`
3. Retrieves comprehensive strategy using `get_platform_strategy(platform, audience, intent, category)`
4. Includes strategy context in LLM prompt
5. Uses KG-derived styles for better rewrites

### Prompt Enhancement

The LLM prompt now includes:
- Platform constraints
- Recommended styles (from KG)
- Creative type recommendations
- Audience preferences (if provided)
- Intent requirements (if provided)
- Category insights (if provided)

This gives the LLM much richer context for creating effective rewrites.

## Benefits

1. **More Targeted Rewrites**: Context-aware based on audience, intent, category
2. **Better Style Selection**: Combines multiple KG relationships
3. **Strategic Insights**: Actionable recommendations for each platform
4. **Cross-Platform Discovery**: Find new platforms based on audience overlap
5. **Category Optimization**: Understand which platforms work best for your product type

## Migration Notes

- All new fields are **optional** - API still works without them
- Default behavior enhanced: `include_strategy_insights` and `suggest_alternative_platforms` default to `true`
- Existing code will work but won't get KG benefits without providing context fields

