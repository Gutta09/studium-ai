from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from agents.examiner import generate_important_questions
from auth import current_user
from llm import LLMError

router = APIRouter()


class QuestionsRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=300)


@router.post("/important-questions")
def important_questions(body: QuestionsRequest, user: dict = Depends(current_user)):
    if not body.topic.strip():
        raise HTTPException(status_code=400, detail="Topic cannot be empty.")

    try:
        data = generate_important_questions(body.topic)
    except LLMError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return {
        "topic": body.topic,
        "2_mark": data.get("2_mark", []),
        "5_mark": data.get("5_mark", []),
        "10_mark": data.get("10_mark", []),
    }
