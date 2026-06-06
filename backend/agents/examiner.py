import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"


def generate_important_questions(topic: str) -> dict:
    """
    Generate exam-style important questions for a topic, categorised by marks.
    Returns: { "2_mark": [...], "5_mark": [...], "10_mark": [...] }
    Each item: { "question": "...", "answer": "..." }
    """
    response = client.chat.completions.create(
        model=MODEL,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an experienced university professor and exam setter. "
                    "Generate important exam questions with model answers for the given topic, "
                    "grouped by mark allocation. Return JSON exactly as: "
                    '{"2_mark": [{"question": "...", "answer": "..."}, ...], '
                    '"5_mark": [{"question": "...", "answer": "..."}, ...], '
                    '"10_mark": [{"question": "...", "answer": "..."}, ...]}'
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Generate important university exam questions for the topic: '{topic}'\n\n"
                    "Requirements:\n"
                    "- 2-mark questions (4 questions): short-answer, define/state/list type\n"
                    "- 5-mark questions (3 questions): explain/describe/compare type, ~150 word answers\n"
                    "- 10-mark questions (2 questions): long essay/analyse/evaluate type, ~300 word answers\n"
                    "Questions should reflect what commonly appears in university exams."
                ),
            },
        ],
    )

    return json.loads(response.choices[0].message.content)
