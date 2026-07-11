"""Quizzer agent: multiple-choice questions for a topic, validated before use."""

from llm import chat_json, LLMError

VALID_LETTERS = {"A", "B", "C", "D"}


def _valid_question(q: dict) -> bool:
    return (
        isinstance(q, dict)
        and isinstance(q.get("question"), str) and q["question"].strip()
        and isinstance(q.get("options"), list) and len(q["options"]) == 4
        and all(isinstance(o, str) for o in q["options"])
        and q.get("correct_answer") in VALID_LETTERS
    )


def generate_quiz(topic: str, num_questions: int = 5) -> list[dict]:
    data = chat_json(
        system=(
            "You are a teacher creating multiple-choice quiz questions. Return JSON. "
            'Return exactly: {"questions": [{"question": "...", "options": ["A text", "B text", "C text", "D text"], "correct_answer": "A", "explanation": "..."}, ...]}'
            " correct_answer must be exactly A, B, C, or D."
        ),
        user=(
            f"Create exactly {num_questions} multiple-choice questions about: '{topic}'.\n"
            "Each question must have 4 options and one correct answer (A, B, C, or D)."
        ),
        temperature=0.3,
    )

    raw = data.get("questions")
    if not isinstance(raw, list):
        raise LLMError("Quizzer returned an unexpected shape")

    # Keep only well-formed questions; default missing explanations
    questions = []
    for q in raw:
        if _valid_question(q):
            q.setdefault("explanation", "")
            questions.append(q)
    return questions
