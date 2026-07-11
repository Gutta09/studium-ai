import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.syllabus import router as syllabus_router
from routes.quiz import router as quiz_router
from routes.results import router as results_router
from routes.questions import router as questions_router

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(title="STUDIUM AI")

# React dev server by default; override for deployed frontends
_origins = os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "STUDIUM AI"}


app.include_router(syllabus_router, prefix="/api")
app.include_router(quiz_router, prefix="/api")
app.include_router(results_router, prefix="/api")
app.include_router(questions_router, prefix="/api")
