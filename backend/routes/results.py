"""
results.py — progress aggregation and adaptive re-planning.

GET  /api/results/{syllabus_id}
  Reads all quiz results for this syllabus, aggregates per-topic scores,
  and flags weak topics (average < 70%).

POST /api/replan
  Reads weak topics, asks the LLM for extra review sessions, appends them
  to the existing plan in MongoDB, returns the full updated plan.
  Topics that already received review sessions are not re-planned again.
"""

from datetime import date, timedelta
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from agents.replanner import generate_replan
from auth import current_user
from routes.syllabus import owned_syllabus_or_404
from llm import LLMError
from db import results as results_col, plans

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
def get_results(syllabus_id: str, user: dict = Depends(current_user)):
    """Return aggregated per-topic quiz results and a list of weak topics."""
    owned_syllabus_or_404(syllabus_id, user["user_id"])
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
def replan(body: ReplanRequest, user: dict = Depends(current_user)):
    """
    Detect weak topics → ask the LLM for extra sessions → update the plan.
    Returns the full updated session list (original + new review sessions).
    """
    owned_syllabus_or_404(body.syllabus_id, user["user_id"])

    # 1. Find weak topics for this syllabus
    topic_results = _aggregate_results(body.syllabus_id)
    weak_topics = [t for t in topic_results if t["is_weak"]]

    if not weak_topics:
        raise HTTPException(
            status_code=400,
            detail="No weak topics detected — no re-planning needed!",
        )

    # 2. Find the current plan
    plan_doc = plans.find_one({"syllabus_id": body.syllabus_id})
    if not plan_doc:
        raise HTTPException(status_code=404, detail="Plan not found for this syllabus.")

    # Idempotency: don't add more review sessions for topics that already
    # got them in a previous replan
    already_reviewed = set(plan_doc.get("reviewed_topics", []))
    weak_topics = [t for t in weak_topics if t["topic"] not in already_reviewed]
    if not weak_topics:
        raise HTTPException(
            status_code=400,
            detail="All weak topics already have review sessions. Take the reviews, then re-test!",
        )

    existing_sessions = plan_doc.get("sessions", [])

    # Start new sessions the day after the current plan ends (or tomorrow)
    if existing_sessions:
        last_date = date.fromisoformat(max(s["date"] for s in existing_sessions))
        start_date = (last_date + timedelta(days=1)).isoformat()
    else:
        start_date = (date.today() + timedelta(days=1)).isoformat()

    # 3. Ask the LLM to generate focused review sessions
    try:
        new_sessions = generate_replan(weak_topics, start_date)
    except LLMError as e:
        raise HTTPException(status_code=502, detail=str(e))

    if not new_sessions:
        raise HTTPException(status_code=422, detail="Re-planner returned no sessions.")

    # 4. Append the new sessions to the existing plan in MongoDB
    updated_sessions = existing_sessions + new_sessions
    plans.update_one(
        {"syllabus_id": body.syllabus_id},
        {
            "$set": {
                "sessions": updated_sessions,
                "reviewed_topics": sorted(already_reviewed | {w["topic"] for w in weak_topics}),
            },
            "$inc": {"version": 1},
        },
    )

    return {
        "added_sessions": new_sessions,
        "full_sessions": updated_sessions,
        "weak_topics_addressed": [w["topic"] for w in weak_topics],
    }
