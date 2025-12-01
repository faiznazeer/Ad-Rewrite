"""FastAPI application exposing the ad-rewriter endpoints."""

from __future__ import annotations

import time
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from agent.langgraph_orchestration import run_parallel_rewrites


class RunAgentRequest(BaseModel):
	text: str = Field(..., description="Input text to rewrite")
	target_platforms: List[str] = Field(..., description="List of target platforms")
	tone_map: Optional[Dict[str, str]] = Field(None, description="Optional per-platform tone overrides")
	length_prefs: Optional[Dict[str, int]] = Field(None, description="Optional per-platform max length overrides")


app = FastAPI(title="Ad Rewriter Agent")


@app.get("/")
def health() -> Dict[str, str]:
	return {"status": "ok", "service": "ad-rewriter"}


@app.post("/run-agent")
def run_agent(req: RunAgentRequest):
	if not req.target_platforms:
		raise HTTPException(status_code=400, detail="target_platforms is required")
	start = time.monotonic()
	results = run_parallel_rewrites(
		text=req.text,
		target_platforms=req.target_platforms,
		tone_map=req.tone_map,
		length_map=req.length_prefs,
	)
	latency_ms = int((time.monotonic() - start) * 1000)

	# simple validation summary
	validation_summary = {"total": len(results), "ok": 0, "failed": 0}
	for r in results:
		v = r.get("validation")
		if v and v.get("ok"):
			validation_summary["ok"] += 1
		else:
			validation_summary["failed"] += 1

	return {
		"meta": {"latency_ms": latency_ms, "total_platforms": len(results)},
		"validation_summary": validation_summary,
		"results": results,
	}


@app.post("/run-agent/fallback")
def run_agent_fallback(req: RunAgentRequest):
	# For now, alias to the main endpoint — could implement single-prompt fallback mode.
	return run_agent(req)
