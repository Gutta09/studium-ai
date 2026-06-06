import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"


def generate_replan(weak_topics: list[dict], start_date: str) -> list[dict]:
    weak_summary = "\n".join(
        f"  - {w['topic']} (scored {w['avg_percentage']}%)"
        for w in weak_topics
    )

    response = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an adaptive academic planner. Generate extra review sessions for weak topics and return JSON. "
                    'Return exactly: {"sessions": [{"topic": "...", "date": "YYYY-MM-DD", "status": "pending", "description": "...", "is_review": true}, ...]}'
                ),
            },
            {
                "role": "user",
                "content": (
                    f"The student struggled with these topics:\n{weak_summary}\n\n"
                    f"Add 2 extra review sessions per weak topic, starting from {start_date}.\n"
                    "Skip weekends. is_review must be true. Descriptions should be revision-focused."
                ),
            },
        ],
    )

    data = json.loads(response.choices[0].message.content)
    return data["sessions"]
