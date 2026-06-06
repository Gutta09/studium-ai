import os
import json
from datetime import date, timedelta
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"


def extract_topics(syllabus_text: str) -> list[str]:
    trimmed = syllabus_text[:8000]

    response = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an academic assistant. "
                    "Extract topics from a syllabus and return them as JSON. "
                    'Return exactly: {"topics": ["Topic 1", "Topic 2", ...]}'
                ),
            },
            {
                "role": "user",
                "content": f"Extract all study topics from this syllabus in order.\n\nSyllabus:\n{trimmed}",
            },
        ],
    )

    data = json.loads(response.choices[0].message.content)
    return data["topics"]


def _business_end_date(start: date, n_days: int) -> date:
    """Return the date that is n_days business days (Mon–Fri) from start."""
    d = start
    added = 0
    while added < n_days:
        d += timedelta(days=1)
        if d.weekday() < 5:
            added += 1
    return d


def generate_study_plan(topics: list[str], total_days: int = 30) -> list[dict]:
    start = date.today() + timedelta(days=1)
    end = _business_end_date(start, total_days)

    response = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an academic planner. Create a day-wise study schedule and return it as JSON. "
                    'Return exactly: {"sessions": [{"topic": "...", "date": "YYYY-MM-DD", "status": "pending", "description": "..."}, ...]}'
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Create a study plan for these {len(topics)} topics:\n"
                    f"{json.dumps(topics)}\n\n"
                    f"Constraints:\n"
                    f"- Start date: {start.isoformat()}\n"
                    f"- Must finish by: {end.isoformat()} ({total_days} study days)\n"
                    f"- Skip weekends (Sat/Sun)\n"
                    f"- Distribute all topics within this window — complex topics get more days\n"
                    f"- Each session description should say what to study that day\n"
                    f"- status is always 'pending'"
                ),
            },
        ],
    )

    data = json.loads(response.choices[0].message.content)
    return data["sessions"]
