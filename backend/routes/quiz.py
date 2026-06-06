"""
quiz.py — Two endpoints for Phase 2.

POST /api/quiz/generate
  Generates 5 MCQ questions for a topic via Claude and stores them.
  Returns questions WITHOUT correct_answer (prevents cheating in the UI).

POST /api/quiz/submit
  Accepts the student's answers, scores them server-side,
  stores the result, and returns a full breakdown with explanations.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from bson import ObjectId
from bson.errors import InvalidId
from agents.quizzer import generate_quiz
from db import quizzes, results

router = APIRouter()


# ── Request/Response models ───────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    syllabus_id: str
    topic: str
    num_questions: int = 5


class SubmitRequest(BaseModel):
    quiz_id: str
    # One letter per question in order: e.g. ["A", "C", "B", "D", "A"]
    answers: list[str]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/quiz/generate")
def quiz_generate(body: GenerateRequest):
    """Generate a fresh quiz for a topic and return it without the answers."""

    # Ask Claude for questions (includes correct_answer + explanation in the DB doc)
    questions = generate_quiz(body.topic, body.num_questions)

    if not questions:
        raise HTTPException(status_code=422, detail="Claude returned no questions.")

    # Store the full quiz (with correct_answer) in MongoDB
    quiz_doc = {
        "syllabus_id": body.syllabus_id,
        "topic": body.topic,
        "questions": questions,  # stored with correct_answer
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

    # Fetch the quiz from MongoDB
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

    # Score each question
    score = 0
    breakdown = []

    for i, q in enumerate(stored_questions):
        student_answer = body.answers[i].upper()
        correct = q["correct_answer"]
        is_correct = student_answer == correct

        if is_correct:
            score += 1

        # Map letter to option text so the frontend can display what was chosen
        def letter_to_text(letter: str) -> str:
            idx = {"A": 0, "B": 1, "C": 2, "D": 3}.get(letter, 0)
            return q["options"][idx] if idx < len(q["options"]) else letter

        breakdown.append({
            "question": q["question"],
            "selected_letter": student_answer,
            "selected_text": letter_to_text(student_answer),
            "correct_letter": correct,
            "correct_text": letter_to_text(correct),
            "is_correct": is_correct,
            "explanation": q["explanation"],
        })

    # Store the result for Phase 3 (weak-topic detection)
    result_doc = {
        "quiz_id": body.quiz_id,
        "syllabus_id": quiz_doc["syllabus_id"],
        "topic": quiz_doc["topic"],
        "score": score,
        "total": num_q,
        "breakdown": breakdown,
    }
    results.insert_one(result_doc)

    return {
        "score": score,
        "total": num_q,
        "percentage": round(score / num_q * 100),
        "breakdown": breakdown,
    }
