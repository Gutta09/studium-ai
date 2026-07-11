import pytest

from agents import quizzer
from llm import LLMError

GOOD_Q = {
    "question": "Q?",
    "options": ["a", "b", "c", "d"],
    "correct_answer": "A",
    "explanation": "because",
}


def test_valid_questions_pass_through(monkeypatch):
    monkeypatch.setattr(quizzer, "chat_json", lambda **kw: {"questions": [GOOD_Q] * 3})
    assert len(quizzer.generate_quiz("topic", 3)) == 3


def test_malformed_questions_are_dropped(monkeypatch):
    bad = [
        {**GOOD_Q, "correct_answer": "E"},           # invalid letter
        {**GOOD_Q, "options": ["a", "b"]},           # too few options
        {**GOOD_Q, "question": "  "},                # empty question
        "not even a dict",
    ]
    monkeypatch.setattr(quizzer, "chat_json", lambda **kw: {"questions": [GOOD_Q] + bad})
    questions = quizzer.generate_quiz("topic")
    assert len(questions) == 1
    assert questions[0]["correct_answer"] == "A"


def test_missing_explanation_defaults_to_empty(monkeypatch):
    q = {k: v for k, v in GOOD_Q.items() if k != "explanation"}
    monkeypatch.setattr(quizzer, "chat_json", lambda **kw: {"questions": [q]})
    assert quizzer.generate_quiz("topic")[0]["explanation"] == ""


def test_bad_shape_raises(monkeypatch):
    monkeypatch.setattr(quizzer, "chat_json", lambda **kw: {"questions": "oops"})
    with pytest.raises(LLMError):
        quizzer.generate_quiz("topic")
