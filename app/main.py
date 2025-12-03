"""FastAPI endpoints for ad rewriting agent."""

from __future__ import annotations

import time
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from agent.langgraph_orchestration import run_parallel_rewrites


class RunAgentRequest(BaseModel):
	text: str = Field(..., description="Input text to rewrite")
	target_platforms: List[str] = Field(..., description="List of target platforms (e.g., ['instagram', 'linkedin'])")
	audience: Optional[str] = Field(None, description="Target audience segment (e.g., 'gen-z', 'millennials', 'b2b professionals', 'parents')")
	user_intent: Optional[str] = Field(None, description="User intent/funnel stage (e.g., 'awareness', 'consideration', 'purchase', 'engagement')")
	product_category: Optional[str] = Field(None, description="Product category (e.g., 'tech', 'fashion', 'food', 'b2b', 'services')")
	tone_map: Optional[Dict[str, str]] = Field(None, description="Optional per-platform tone/style overrides")
	include_strategy_insights: bool = Field(True, description="Include KG-based strategy recommendations in response")


app = FastAPI(title="Ad Rewriter Agent")

@app.get("/")
def health() -> Dict[str, str]:
	return {"status": "ok", "service": "ad-rewriter"}

@app.post("/run-agent")
def run_agent(req: RunAgentRequest):
	"""Ad rewriting endpoint with Neo4j KG integration and strategy insights."""
	if not req.target_platforms:
		raise HTTPException(status_code=400, detail="target_platforms is required")
	
	start = time.monotonic()
	
	results = run_parallel_rewrites(
		text=req.text,
		target_platforms=req.target_platforms,
		audience=req.audience,
		user_intent=req.user_intent,
		product_category=req.product_category,
		tone_map=req.tone_map,
	)
	
	latency_ms = int((time.monotonic() - start) * 1000)

	response = {
		"meta": {
			"latency_ms": latency_ms,
			"total_platforms": len(results),
			"context": {
				"audience": req.audience,
				"user_intent": req.user_intent,
				"product_category": req.product_category,
			},
		},
		"results": results,
	}
	
	# Add strategy insights if requested
	if req.include_strategy_insights:
		strategy_insights = {}
		
		results_by_platform = {r.get("platform"): r for r in results if r.get("platform")}
		
		for platform in req.target_platforms:
			result = results_by_platform.get(platform)
			strategy = result.get("strategy_data", {}) if result else {}
			if not strategy:
				continue
			
			strategy_insights[platform] = {
				"recommended_styles": strategy.get("preferred_styles", [])[:5],
				"recommended_creative_types": strategy.get("recommended_creative_types", [])[:5],
				"target_audiences": strategy.get("target_audiences", [])[:5],
			}
			
			if req.audience and "audience_preferred_styles" in strategy:
				strategy_insights[platform]["audience_preferred_styles"] = strategy["audience_preferred_styles"]
			if req.user_intent and "intent_required_styles" in strategy:
				strategy_insights[platform]["intent_required_styles"] = strategy["intent_required_styles"]
			if req.product_category and "category_suitability_score" in strategy:
				strategy_insights[platform]["category_suitability_score"] = strategy["category_suitability_score"]
		
		if strategy_insights:
			response["strategy_insights"] = strategy_insights

	return response
