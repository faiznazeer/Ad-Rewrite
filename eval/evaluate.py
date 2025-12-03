"""Evaluation harness: run the agent on sample inputs and save metrics.

This script runs a small batch of inputs through the orchestration layer and
persists results to `eval_results.csv` inside the project root.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import List

from agent.langgraph_orchestration import run_parallel_rewrites

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
EXAMPLES = DATA / "examples.json"
OUT_CSV = ROOT / "eval_results.csv"


def load_examples(limit: int = 20) -> List[dict]:
	with open(EXAMPLES, "r", encoding="utf-8") as f:
		examples = json.load(f)
	return examples[:limit]


def evaluate_sample_examples():
	examples = load_examples(20)
	rows = []
	for ex in examples:
		text = ex["text"]
		platforms = [ex["platform"]]
		outputs = run_parallel_rewrites(text, platforms)
		# Normalize outputs: langgraph may return a list of chunks like [[], {...}]
		results = []
		if isinstance(outputs, dict):
			results = outputs.get("results") or []
		elif isinstance(outputs, list):
			# flatten nested lists and collect dict-like results
			for item in outputs:
				if isinstance(item, dict) and "rewritten_text" in item:
					results.append(item)
				elif isinstance(item, dict) and "results" in item:
					# item['results'] may be a dict or list
					r = item["results"]
					if isinstance(r, list):
						results.extend(r)
					else:
						results.append(r)
				elif isinstance(item, list):
					for sub in item:
						if isinstance(sub, dict):
							results.append(sub)

		for out in results:
			rows.append(
				{
					"id": ex.get("id"),
					"input": text,
					"platform": out.get("platform"),
					"rewritten": out.get("rewritten_text"),
					"explanation": out.get("explanation"),
				}
			)

	# write csv
	with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
		writer = csv.DictWriter(
			f, fieldnames=["id", "input", "platform", "rewritten", "explanation"]
		)
		writer.writeheader()
		for r in rows:
			writer.writerow(r)

	print(f"Wrote {len(rows)} rows to {OUT_CSV}")


if __name__ == "__main__":
	evaluate_sample_examples()

