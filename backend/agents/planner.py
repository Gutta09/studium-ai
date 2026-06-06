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
                "content": (
                    "Extract all study topics from this syllabus in order.\n\n"
                    f"Syllabus:\n{trimmed}"
                ),
            },
        ],
    )

    data = json.loads(response.choices[0].message.content)
    return data["topics"]


def generate_study_plan(topics: list[str]) -> list[dict]:
    start_date = (date.today() + timedelta(days=1)).isoformat()

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
                    f"Create a study plan starting from {start_date} for these topics:\n"
                    f"{json.dumps(topics)}\n\n"
                    "Rules:\n"
                    "- 1 day for simple topics, 2 days for complex ones\n"
                    "- Skip weekends (Sat/Sun)\n"
                    "- Each description should say what to study that day\n"
                    "- status is always 'pending'"
                ),
            },
        ],
    )

    data = json.loads(response.choices[0].message.content)
    return data["sessions"]
