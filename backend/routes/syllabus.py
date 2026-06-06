"""
syllabus.py — POST /api/upload-syllabus

Full pipeline in one request:
  1. Accept PDF file upload
  2. Extract text with pdfplumber
  3. Call Claude → topics
  4. Call Claude → study plan
  5. Store both in MongoDB
  6. Return everything to the frontend
"""

import io
import pdfplumber
from fastapi import APIRouter, UploadFile, File, HTTPException
from agents.planner import extract_topics, generate_study_plan
from db import syllabi, plans

router = APIRouter()


@router.post("/upload-syllabus")
def upload_syllabus(file: UploadFile = File(...)):
    # ── Step 1: validate file type ───────────────────────────────────────────
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    # ── Step 2: extract text from the PDF ───────────────────────────────────
    raw_bytes = file.file.read()
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

    # ── Step 3: Claude extracts topics ──────────────────────────────────────
    topics = extract_topics(raw_text)

    if not topics:
        raise HTTPException(
            status_code=422, detail="No topics could be extracted from the syllabus."
        )

    # ── Step 4: store the syllabus in MongoDB ───────────────────────────────
    syllabus_doc = {
        "filename": file.filename,
        "raw_text": raw_text,
        "topics": topics,
    }
    insert_result = syllabi.insert_one(syllabus_doc)
    syllabus_id = str(insert_result.inserted_id)

    # ── Step 5: Claude generates the study plan ─────────────────────────────
    sessions = generate_study_plan(topics)

    # ── Step 6: store the plan in MongoDB ───────────────────────────────────
    plan_doc = {
        "syllabus_id": syllabus_id,
        "sessions": sessions,
        "version": 1,
    }
    plans.insert_one(plan_doc)

    # ── Step 7: return everything to the frontend ───────────────────────────
    return {
        "syllabus_id": syllabus_id,
        "topics": topics,
        "sessions": sessions,
    }
