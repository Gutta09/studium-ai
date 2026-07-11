"""
Re-planner agent: focused review sessions for weak topics.

As with the planner, the LLM writes the *content* of the review sessions and
plain code assigns the business-day dates.
"""

from datetime import date

from llm import chat_json, LLMError
from agents.planner import business_days_from

SESSIONS_PER_WEAK_TOPIC = 2


def generate_replan(weak_topics: list[dict], start_date: str) -> list[dict]:
    weak_summary = "\n".join(
        f"  - {w['topic']} (scored {w['avg_percentage']}%)"
        for w in weak_topics
    )

    data = chat_json(
        system=(
            "You are an adaptive academic planner. Generate extra review sessions for weak topics and return JSON. "
            'Return exactly: {"sessions": [{"topic": "...", "description": "..."}, ...]}'
        ),
        user=(
            f"The student struggled with these topics:\n{weak_summary}\n\n"
            f"Create exactly {SESSIONS_PER_WEAK_TOPIC} review sessions per weak topic, "
            "in the order the topics are listed.\n"
            "Descriptions should be revision-focused: what to re-read, practise, and self-test.\n"
            "Do NOT include dates — scheduling is handled separately."
        ),
    )

    raw = data.get("sessions")
    if not isinstance(raw, list):
        raise LLMError("Re-planner returned an unexpected shape")

    sessions = [
        s for s in raw
        if isinstance(s, dict) and isinstance(s.get("topic"), str) and s["topic"].strip()
    ]
    if not sessions:
        raise LLMError("Re-planner returned no usable sessions")

    # One review session per business day, starting from start_date
    days = business_days_from(date.fromisoformat(start_date), len(sessions))
    return [
        {
            "topic": s["topic"],
            "date": d.isoformat(),
            "status": "pending",
            "description": s.get("description", ""),
            "is_review": True,
        }
        for s, d in zip(sessions, days)
    ]
