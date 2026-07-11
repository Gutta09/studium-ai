"""Examiner agent: exam-style questions with model answers, grouped by marks."""

from llm import chat_json

MARK_SECTIONS = ("2_mark", "5_mark", "10_mark")


def _clean_section(items) -> list[dict]:
    if not isinstance(items, list):
        return []
    return [
        {"question": q["question"].strip(), "answer": str(q.get("answer", "")).strip()}
        for q in items
        if isinstance(q, dict) and isinstance(q.get("question"), str) and q["question"].strip()
    ]


def generate_important_questions(topic: str) -> dict:
    """
    Exam-style important questions for a topic, categorised by marks.
    Returns: { "2_mark": [...], "5_mark": [...], "10_mark": [...] }
    Each item: { "question": "...", "answer": "..." }
    """
    data = chat_json(
        system=(
            "You are an experienced university professor and exam setter. "
            "Generate important exam questions with model answers for the given topic, "
            "grouped by mark allocation. Return JSON exactly as: "
            '{"2_mark": [{"question": "...", "answer": "..."}, ...], '
            '"5_mark": [{"question": "...", "answer": "..."}, ...], '
            '"10_mark": [{"question": "...", "answer": "..."}, ...]}'
        ),
        user=(
            f"Generate important university exam questions for the topic: '{topic}'\n\n"
            "Requirements:\n"
            "- 2-mark questions (4 questions): short-answer, define/state/list type\n"
            "- 5-mark questions (3 questions): explain/describe/compare type, ~150 word answers\n"
            "- 10-mark questions (2 questions): long essay/analyse/evaluate type, ~300 word answers\n"
            "Questions should reflect what commonly appears in university exams."
        ),
        temperature=0.2,
    )

    return {section: _clean_section(data.get(section)) for section in MARK_SECTIONS}
