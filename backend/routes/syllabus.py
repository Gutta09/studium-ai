import io
from datetime import datetime, timezone

import pdfplumber
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Literal

from agents.planner import extract_topics, generate_study_plan
from auth import current_user
from llm import LLMError
from db import syllabi, plans

router = APIRouter()

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB is far beyond any real syllabus


def owned_syllabus_or_404(syllabus_id: str, user_id: str) -> dict:
    """Resolve a syllabus the current user owns, or raise 400/404."""
    try:
        doc = syllabi.find_one({"_id": ObjectId(syllabus_id)})
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid syllabus ID.")
    if not doc or doc.get("user_id") != user_id:
        # 404 for both missing and foreign syllabi — don't leak existence
        raise HTTPException(status_code=404, detail="Syllabus not found.")
    return doc


@router.post("/upload-syllabus")
def upload_syllabus(
    file: UploadFile = File(...),
    days: int = Form(30, ge=1, le=365),  # student-chosen study duration
    user: dict = Depends(current_user),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    raw_bytes = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(raw_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="PDF is larger than 10 MB.")

    raw_text = ""
    try:
        with pdfplumber.open(io.BytesIO(raw_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    raw_text += page_text + "\n"
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not parse PDF: {e}")

    if not raw_text.strip():
        raise HTTPException(
            status_code=422,
            detail="PDF appears to have no extractable text (it may be a scanned image).",
        )

    try:
        topics = extract_topics(raw_text)
    except LLMError as e:
        raise HTTPException(status_code=502, detail=str(e))

    if not topics:
        raise HTTPException(status_code=422, detail="No topics could be extracted.")

    syllabus_doc = {
        "user_id": user["user_id"],
        "filename": file.filename,
        "raw_text": raw_text,
        "topics": topics,
        "created_at": datetime.now(timezone.utc),
    }
    insert_result = syllabi.insert_one(syllabus_doc)
    syllabus_id = str(insert_result.inserted_id)

    try:
        sessions = generate_study_plan(topics, total_days=days)
    except LLMError as e:
        raise HTTPException(status_code=502, detail=str(e))

    plans.insert_one({
        "syllabus_id": syllabus_id,
        "user_id": user["user_id"],
        "sessions": sessions,
        "version": 1,
        "created_at": datetime.now(timezone.utc),
    })

    return {"syllabus_id": syllabus_id, "topics": topics, "sessions": sessions}


@router.get("/syllabi")
def list_syllabi(user: dict = Depends(current_user)):
    """The current user's syllabi, newest first — powers the home dashboard."""
    out = []
    for doc in syllabi.find({"user_id": user["user_id"]}).sort("created_at", -1):
        syllabus_id = str(doc["_id"])
        plan = plans.find_one({"syllabus_id": syllabus_id})
        sessions = plan.get("sessions", []) if plan else []
        out.append({
            "syllabus_id": syllabus_id,
            "filename": doc.get("filename", "syllabus.pdf"),
            "topics": len(doc.get("topics", [])),
            "sessions": len(sessions),
            "done_sessions": sum(1 for s in sessions if s.get("status") == "done"),
            "created_at": doc["created_at"].isoformat() if doc.get("created_at") else None,
        })
    return out


@router.get("/plan/{syllabus_id}")
def get_plan(syllabus_id: str, user: dict = Depends(current_user)):
    """Full plan for a syllabus — lets the frontend restore state on refresh/deep link."""
    doc = owned_syllabus_or_404(syllabus_id, user["user_id"])
    plan = plans.find_one({"syllabus_id": syllabus_id})
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found for this syllabus.")
    return {
        "syllabus_id": syllabus_id,
        "topics": doc.get("topics", []),
        "sessions": plan.get("sessions", []),
    }


class SessionStatusUpdate(BaseModel):
    status: Literal["pending", "done"]


@router.patch("/plan/{syllabus_id}/sessions/{index}")
def update_session_status(
    syllabus_id: str,
    index: int,
    body: SessionStatusUpdate,
    user: dict = Depends(current_user),
):
    """Mark a study session done (or back to pending)."""
    owned_syllabus_or_404(syllabus_id, user["user_id"])
    plan = plans.find_one({"syllabus_id": syllabus_id})
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found for this syllabus.")
    sessions = plan.get("sessions", [])
    if not 0 <= index < len(sessions):
        raise HTTPException(status_code=404, detail="Session index out of range.")

    plans.update_one(
        {"_id": plan["_id"]},
        {"$set": {f"sessions.{index}.status": body.status}},
    )
    sessions[index]["status"] = body.status
    return {"sessions": sessions}
