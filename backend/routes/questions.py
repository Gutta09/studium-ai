from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from agents.examiner import generate_important_questions

router = APIRouter()


class QuestionsRequest(BaseModel):
    topic: str


@router.post("/important-questions")
def important_questions(body: QuestionsRequest):
    if not body.topic.strip():
        raise HTTPException(status_code=400, detail="Topic cannot be empty.")

    data = generate_important_questions(body.topic)

    return {
        "topic": body.topic,
        "2_mark": data.get("2_mark", []),
        "5_mark": data.get("5_mark", []),
        "10_mark": data.get("10_mark", []),
    }
