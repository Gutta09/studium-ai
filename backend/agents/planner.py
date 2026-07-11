"""
Planner agent: extracts topics from syllabus text and builds a study plan.

Division of labour (deliberate): the LLM decides *pedagogy* — topic order,
how many sessions a topic deserves, what to study each session. Plain code
does the *calendar math* — assigning business-day dates. LLMs are unreliable
at date arithmetic, so dates are never delegated to the model.
"""

from datetime import date, timedelta

from llm import chat_json, LLMError

MAX_SYLLABUS_CHARS = 24_000  # ~6k tokens of syllabus text is plenty for topic extraction


def extract_topics(syllabus_text: str) -> list[str]:
    trimmed = syllabus_text[:MAX_SYLLABUS_CHARS]

    data = chat_json(
        system=(
            "You are an academic assistant. "
            "Extract topics from a syllabus and return them as JSON. "
            'Return exactly: {"topics": ["Topic 1", "Topic 2", ...]}'
        ),
        user=f"Extract all study topics from this syllabus in order.\n\nSyllabus:\n{trimmed}",
    )

    topics = data.get("topics")
    if not isinstance(topics, list):
        raise LLMError("Topic extraction returned an unexpected shape")

    # De-duplicate while preserving order; drop empty/non-string entries
    seen = set()
    clean = []
    for t in topics:
        if isinstance(t, str) and t.strip() and t.strip().lower() not in seen:
            seen.add(t.strip().lower())
            clean.append(t.strip())
    return clean


def business_days_from(start: date, count: int) -> list[date]:
    """The next `count` business days (Mon-Fri) starting from `start` inclusive."""
    days = []
    d = start
    while len(days) < count:
        if d.weekday() < 5:
            days.append(d)
        d += timedelta(days=1)
    return days


def assign_dates(sessions: list[dict], total_days: int, start: date | None = None) -> list[dict]:
    """
    Deterministically place sessions on business days.

    If there are fewer sessions than study days, sessions are spread evenly
    across the window; if more, they are truncated to one per day.
    """
    if not sessions:
        return []

    start = start or (date.today() + timedelta(days=1))
    window = business_days_from(start, total_days)

    if len(sessions) > len(window):
        sessions = sessions[: len(window)]

    n = len(sessions)
    dated = []
    for i, session in enumerate(sessions):
        # Even spread: session i sits at fraction i/(n-1) of the window
        slot = round(i * (len(window) - 1) / (n - 1)) if n > 1 else 0
        dated.append({
            "topic": session["topic"],
            "date": window[slot].isoformat(),
            "status": "pending",
            "description": session.get("description", ""),
        })
    return dated


def generate_study_plan(topics: list[str], total_days: int = 30) -> list[dict]:
    data = chat_json(
        system=(
            "You are an academic planner. Break topics into ordered study sessions and return JSON. "
            'Return exactly: {"sessions": [{"topic": "...", "description": "..."}, ...]}'
        ),
        user=(
            f"Plan study sessions for these {len(topics)} topics, in a sensible learning order:\n"
            f"{topics}\n\n"
            f"Constraints:\n"
            f"- The student has {total_days} study days in total\n"
            f"- Produce at most {total_days} sessions\n"
            f"- Complex topics may get two sessions; simple ones share or get one\n"
            f"- Each description says concretely what to study in that session\n"
            f"- Do NOT include dates — scheduling is handled separately"
        ),
    )

    raw_sessions = data.get("sessions")
    if not isinstance(raw_sessions, list):
        raise LLMError("Planner returned an unexpected shape")

    sessions = [
        s for s in raw_sessions
        if isinstance(s, dict) and isinstance(s.get("topic"), str) and s["topic"].strip()
    ]
    if not sessions:
        raise LLMError("Planner returned no usable sessions")

    return assign_dates(sessions, total_days)
