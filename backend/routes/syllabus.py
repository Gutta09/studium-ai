import io
from datetime import datetime, timezone

import pdfplumber
from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from agents.planner import extract_topics, generate_study_plan
from llm import LLMError
from db import syllabi, plans

router = APIRouter()

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB is far beyond any real syllabus


@router.post("/upload-syllabus")
def upload_syllabus(
    file: UploadFile = File(...),
    days: int = Form(30, ge=1, le=365),  # student-chosen study duration
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
        "sessions": sessions,
        "version": 1,
        "created_at": datetime.now(timezone.utc),
    })

    return {"syllabus_id": syllabus_id, "topics": topics, "sessions": sessions}
