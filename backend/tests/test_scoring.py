from routes.quiz import score_quiz

QUESTIONS = [
    {
        "question": "What is 2+2?",
        "options": ["3", "4", "5", "6"],
        "correct_answer": "B",
        "explanation": "Basic arithmetic.",
    },
    {
        "question": "Capital of India?",
        "options": ["Mumbai", "Chennai", "New Delhi", "Kolkata"],
        "correct_answer": "C",
        "explanation": "",
    },
]


def test_perfect_score():
    result = score_quiz(QUESTIONS, ["B", "C"])
    assert result["score"] == 2
    assert result["percentage"] == 100
    assert all(item["is_correct"] for item in result["breakdown"])


def test_partial_score_and_breakdown_texts():
    result = score_quiz(QUESTIONS, ["A", "C"])
    assert result["score"] == 1
    assert result["percentage"] == 50
    first = result["breakdown"][0]
    assert first["selected_text"] == "3"
    assert first["correct_text"] == "4"
    assert not first["is_correct"]


def test_answers_are_case_and_whitespace_insensitive():
    result = score_quiz(QUESTIONS, [" b ", "c"])
    assert result["score"] == 2


def test_empty_quiz_scores_zero_percent():
    result = score_quiz([], [])
    assert result == {"score": 0, "total": 0, "percentage": 0, "breakdown": []}
