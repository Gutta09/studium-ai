import io
import pdfplumber
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from agents.planner import extract_topics, generate_study_plan
from db import syllabi, plans

router = APIRouter()


@router.post("/upload-syllabus")
def upload_syllabus(
    file: UploadFile = File(...),
    days: int = Form(30),  # student-chosen study duration
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

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

    topics = extract_topics(raw_text)

    if not topics:
        raise HTTPException(status_code=422, detail="No topics could be extracted.")

    syllabus_doc = {"filename": file.filename, "raw_text": raw_text, "topics": topics}
    insert_result = syllabi.insert_one(syllabus_doc)
    syllabus_id = str(insert_result.inserted_id)

    sessions = generate_study_plan(topics, total_days=days)

    plans.insert_one({"syllabus_id": syllabus_id, "sessions": sessions, "version": 1})

    return {"syllabus_id": syllabus_id, "topics": topics, "sessions": sessions}
