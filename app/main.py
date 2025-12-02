"""FastAPI application exposing the ad-rewriter endpoints with Neo4j knowledge graph integration."""

from __future__ import annotations

import time
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from agent.langgraph_orchestration import run_parallel_rewrites
from agent.kg_service import get_similar_platforms


class RunAgentRequest(BaseModel):
	text: str = Field(..., description="Input text to rewrite")
	target_platforms: List[str] = Field(..., description="List of target platforms (e.g., ['instagram', 'linkedin'])")
	
	# Knowledge graph context fields for enhanced rewrites
	audience: Optional[str] = Field(
		None, 
		description="Target audience segment (e.g., 'gen-z', 'millennials', 'b2b professionals', 'parents')"
	)
	user_intent: Optional[str] = Field(
		None,
		description="User intent/funnel stage (e.g., 'awareness', 'consideration', 'purchase', 'engagement')"
	)
	product_category: Optional[str] = Field(
		None,
		description="Product category (e.g., 'tech', 'fashion', 'food', 'b2b', 'services')"
	)
	
	# Optional overrides
	tone_map: Optional[Dict[str, str]] = Field(None, description="Optional per-platform tone/style overrides")
	length_prefs: Optional[Dict[str, int]] = Field(None, description="Optional per-platform max length overrides")
	
	# Strategy options
	include_strategy_insights: bool = Field(True, description="Include KG-based strategy recommendations in response")
	suggest_alternative_platforms: bool = Field(True, description="Suggest alternative platforms based on audience overlap")


app = FastAPI(title="Ad Rewriter Agent")


@app.get("/")
def health() -> Dict[str, str]:
	return {"status": "ok", "service": "ad-rewriter"}


@app.post("/run-agent")
def run_agent(req: RunAgentRequest):
	"""Enhanced ad rewriting endpoint with Neo4j knowledge graph integration.
	
	Uses audience, intent, and product category to provide context-aware rewrites
	with strategy recommendations and platform suggestions.
	"""
	if not req.target_platforms:
		raise HTTPException(status_code=400, detail="target_platforms is required")
	
	start = time.monotonic()
	
	# Run parallel rewrites with KG context
	results = run_parallel_rewrites(
		text=req.text,
		target_platforms=req.target_platforms,
		audience=req.audience,
		user_intent=req.user_intent,
		product_category=req.product_category,
		tone_map=req.tone_map,
		length_map=req.length_prefs,
	)
	
	latency_ms = int((time.monotonic() - start) * 1000)
	
	# Normalize results to a flat list of dicts
	normalized: list[dict] = []
	for r in results:
		if isinstance(r, dict):
			normalized.append(r)
		elif isinstance(r, list):
			for item in r:
				if isinstance(item, dict):
					normalized.append(item)
	results = normalized

	# Validation summary
	validation_summary = {"total": len(results), "ok": 0, "failed": 0}
	for r in results:
		v = r.get("validation")
		if v and v.get("ok"):
			validation_summary["ok"] += 1
		else:
			validation_summary["failed"] += 1

	# Build response with strategy insights
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
		"validation_summary": validation_summary,
		"results": results,
	}
	
	# Add strategy insights if requested
	if req.include_strategy_insights:
		strategy_insights = {}
		
		# Reuse strategy data from results instead of re-querying (performance optimization)
		# Build a map of platform -> result for easy lookup
		results_by_platform = {r.get("platform"): r for r in results if r.get("platform")}
		
		for platform in req.target_platforms:
			# Try to get strategy data from results first (already fetched during rewrite)
			result = results_by_platform.get(platform)
			strategy = result.get("strategy_data", {}) if result else {}
			
			# If strategy data not in results (shouldn't happen, but fallback), skip this platform
			if not strategy:
				continue
			
			strategy_insights[platform] = {
				"recommended_styles": strategy.get("preferred_styles", [])[:5],
				"recommended_creative_types": strategy.get("recommended_creative_types", [])[:5],
				"target_audiences": strategy.get("target_audiences", [])[:5],
			}
			
			# Add audience-specific styles if audience provided
			if req.audience and "audience_preferred_styles" in strategy:
				strategy_insights[platform]["audience_preferred_styles"] = strategy["audience_preferred_styles"]
			
			# Add intent-specific styles if intent provided
			if req.user_intent and "intent_required_styles" in strategy:
				strategy_insights[platform]["intent_required_styles"] = strategy["intent_required_styles"]
			
			# Add category suitability if category provided
			if req.product_category and "category_suitability_score" in strategy:
				strategy_insights[platform]["category_suitability_score"] = strategy["category_suitability_score"]
		
		if strategy_insights:
			response["strategy_insights"] = strategy_insights
		
		# Suggest alternative platforms if requested
		if req.suggest_alternative_platforms:
			alternative_platforms = {}
			for platform in req.target_platforms:
				similar = get_similar_platforms(platform, limit=3)
				if similar:
					alternative_platforms[platform] = similar
			if alternative_platforms:
				response["alternative_platforms"] = alternative_platforms

	return response


@app.post("/run-agent/fallback")
def run_agent_fallback(req: RunAgentRequest):
	# For now, alias to the main endpoint — could implement single-prompt fallback mode.
	return run_agent(req)
