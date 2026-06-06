"""
results.py — Phase 3 + Phase 4 endpoints.

GET  /api/results/{syllabus_id}
  Reads all quiz results for this syllabus, aggregates per-topic scores,
  and flags weak topics (average < 70%).

POST /api/replan
  Reads weak topics, calls Claude to generate extra review sessions,
  appends them to the existing plan in MongoDB, returns the full updated plan.
"""

from datetime import date, timedelta
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from collections import defaultdict
from agents.replanner import generate_replan
from db import results as results_col, plans, syllabi

router = APIRouter()

WEAK_THRESHOLD = 70  # below this % → topic is "weak"


# ── Helper ────────────────────────────────────────────────────────────────────

def _aggregate_results(syllabus_id: str) -> list[dict]:
    """Group all quiz results by topic and compute average scores."""
    topic_data: dict = defaultdict(lambda: {"scores": [], "totals": []})

    for doc in results_col.find({"syllabus_id": syllabus_id}):
        t = doc["topic"]
        topic_data[t]["scores"].append(doc["score"])
        topic_data[t]["totals"].append(doc["total"])

    aggregated = []
    for topic, data in topic_data.items():
        attempts = len(data["scores"])
        percentages = [
            round(s / t * 100)
            for s, t in zip(data["scores"], data["totals"])
        ]
        avg_pct = round(sum(percentages) / attempts)
        aggregated.append({
            "topic": topic,
            "attempts": attempts,
            "avg_percentage": avg_pct,
            "best_percentage": max(percentages),
            "is_weak": avg_pct < WEAK_THRESHOLD,
        })

    # Sort by avg_percentage so weakest topics appear first
    aggregated.sort(key=lambda x: x["avg_percentage"])
    return aggregated


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/results/{syllabus_id}")
def get_results(syllabus_id: str):
    """Return aggregated per-topic quiz results and a list of weak topics."""
    topic_results = _aggregate_results(syllabus_id)

    weak_topics = [t for t in topic_results if t["is_weak"]]

    return {
        "syllabus_id": syllabus_id,
        "topic_results": topic_results,
        "weak_topics": weak_topics,
        "total_quizzes_taken": sum(t["attempts"] for t in topic_results),
    }


class ReplanRequest(BaseModel):
    syllabus_id: str


@router.post("/replan")
def replan(body: ReplanRequest):
    """
    Detect weak topics → ask Claude for extra sessions → update the plan.
    Returns the full updated session list (original + new review sessions).
    """
    # 1. Find weak topics for this syllabus
    topic_results = _aggregate_results(body.syllabus_id)
    weak_topics = [t for t in topic_results if t["is_weak"]]

    if not weak_topics:
        raise HTTPException(
            status_code=400,
            detail="No weak topics detected — no re-planning needed!",
        )

    # 2. Find the current plan to get the last session date
    plan_doc = plans.find_one({"syllabus_id": body.syllabus_id})
    if not plan_doc:
        raise HTTPException(status_code=404, detail="Plan not found for this syllabus.")

    existing_sessions = plan_doc.get("sessions", [])

    # Start new sessions the day after the current plan ends (or tomorrow)
    if existing_sessions:
        last_date_str = max(s["date"] for s in existing_sessions)
        last_date = date.fromisoformat(last_date_str)
        start_date = (last_date + timedelta(days=1)).isoformat()
    else:
        start_date = (date.today() + timedelta(days=1)).isoformat()

    # 3. Ask Claude to generate focused review sessions
    new_sessions = generate_replan(weak_topics, start_date)

    if not new_sessions:
        raise HTTPException(status_code=422, detail="Re-planner returned no sessions.")

    # 4. Append the new sessions to the existing plan in MongoDB
    updated_sessions = existing_sessions + new_sessions
    plans.update_one(
        {"syllabus_id": body.syllabus_id},
        {
            "$set": {
                "sessions": updated_sessions,
                "version": plan_doc.get("version", 1) + 1,
            }
        },
    )

    return {
        "added_sessions": new_sessions,
        "full_sessions": updated_sessions,
        "weak_topics_addressed": [w["topic"] for w in weak_topics],
    }
