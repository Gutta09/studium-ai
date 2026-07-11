"""
quiz.py — quiz generation and scoring.

POST /api/quiz/generate
  Generates MCQ questions for a topic via the LLM and stores them.
  Returns questions WITHOUT correct_answer (prevents cheating in the UI).

POST /api/quiz/submit
  Accepts the student's answers, scores them server-side,
  stores the result, and returns a full breakdown with explanations.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from bson import ObjectId
from bson.errors import InvalidId

from agents.quizzer import generate_quiz, VALID_LETTERS
from llm import LLMError
from db import quizzes, results, syllabi

router = APIRouter()


# ── Request/Response models ───────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    syllabus_id: str
    topic: str = Field(min_length=1, max_length=300)
    num_questions: int = Field(default=5, ge=1, le=20)


class SubmitRequest(BaseModel):
    quiz_id: str
    # One letter per question in order: e.g. ["A", "C", "B", "D", "A"]
    answers: list[str]


# ── Scoring (pure function — unit-tested in tests/test_scoring.py) ────────────

def score_quiz(stored_questions: list[dict], answers: list[str]) -> dict:
    def letter_to_text(q: dict, letter: str) -> str:
        idx = {"A": 0, "B": 1, "C": 2, "D": 3}.get(letter, -1)
        return q["options"][idx] if 0 <= idx < len(q["options"]) else letter

    score = 0
    breakdown = []
    for q, raw_answer in zip(stored_questions, answers):
        student_answer = raw_answer.strip().upper()
        correct = q["correct_answer"]
        is_correct = student_answer == correct
        if is_correct:
            score += 1
        breakdown.append({
            "question": q["question"],
            "selected_letter": student_answer,
            "selected_text": letter_to_text(q, student_answer),
            "correct_letter": correct,
            "correct_text": letter_to_text(q, correct),
            "is_correct": is_correct,
            "explanation": q.get("explanation", ""),
        })

    total = len(stored_questions)
    return {
        "score": score,
        "total": total,
        "percentage": round(score / total * 100) if total else 0,
        "breakdown": breakdown,
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/quiz/generate")
def quiz_generate(body: GenerateRequest):
    """Generate a fresh quiz for a topic and return it without the answers."""

    # The syllabus_id is client-supplied — verify it refers to a real syllabus
    try:
        syllabus = syllabi.find_one({"_id": ObjectId(body.syllabus_id)})
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid syllabus ID.")
    if not syllabus:
        raise HTTPException(status_code=404, detail="Syllabus not found.")

    try:
        questions = generate_quiz(body.topic, body.num_questions)
    except LLMError as e:
        raise HTTPException(status_code=502, detail=str(e))

    if not questions:
        raise HTTPException(status_code=422, detail="The LLM returned no valid questions.")

    # Store the full quiz (with correct_answer) in MongoDB
    quiz_doc = {
        "syllabus_id": body.syllabus_id,
        "topic": body.topic,
        "questions": questions,  # stored with correct_answer
        "created_at": datetime.now(timezone.utc),
    }
    insert_result = quizzes.insert_one(quiz_doc)
    quiz_id = str(insert_result.inserted_id)

    # Return questions WITHOUT correct_answer or explanation
    # — those are revealed only after the student submits
    safe_questions = [
        {"question": q["question"], "options": q["options"]}
        for q in questions
    ]

    return {
        "quiz_id": quiz_id,
        "topic": body.topic,
        "questions": safe_questions,
    }


@router.post("/quiz/submit")
def quiz_submit(body: SubmitRequest):
    """Score the student's answers and return a breakdown with explanations."""

    try:
        quiz_doc = quizzes.find_one({"_id": ObjectId(body.quiz_id)})
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid quiz ID.")

    if not quiz_doc:
        raise HTTPException(status_code=404, detail="Quiz not found.")

    stored_questions = quiz_doc["questions"]
    num_q = len(stored_questions)

    if len(body.answers) != num_q:
        raise HTTPException(
            status_code=400,
            detail=f"Expected {num_q} answers, got {len(body.answers)}.",
        )

    invalid = [a for a in body.answers if a.strip().upper() not in VALID_LETTERS]
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Answers must be A, B, C or D — got {invalid[:3]}.",
        )

    scored = score_quiz(stored_questions, body.answers)

    # Store the result for weak-topic detection
    results.insert_one({
        "quiz_id": body.quiz_id,
        "syllabus_id": quiz_doc["syllabus_id"],
        "topic": quiz_doc["topic"],
        "score": scored["score"],
        "total": scored["total"],
        "breakdown": scored["breakdown"],
        "created_at": datetime.now(timezone.utc),
    })

    return scored
