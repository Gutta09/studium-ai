import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"


def generate_quiz(topic: str, num_questions: int = 5) -> list[dict]:
    response = client.chat.completions.create(
        model=MODEL,
        temperature=0.3,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a teacher creating multiple-choice quiz questions. Return JSON. "
                    'Return exactly: {"questions": [{"question": "...", "options": ["A text", "B text", "C text", "D text"], "correct_answer": "A", "explanation": "..."}, ...]}'
                    " correct_answer must be exactly A, B, C, or D."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Create exactly {num_questions} multiple-choice questions about: '{topic}'.\n"
                    "Each question must have 4 options and one correct answer (A, B, C, or D)."
                ),
            },
        ],
    )

    data = json.loads(response.choices[0].message.content)
    return data["questions"]
