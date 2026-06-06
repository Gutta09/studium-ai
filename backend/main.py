from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.syllabus import router as syllabus_router
from routes.quiz import router as quiz_router
from routes.results import router as results_router
from routes.questions import router as questions_router

app = FastAPI(title="STUDIUM AI")

# Allow requests from the React dev server (port 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(syllabus_router, prefix="/api")
app.include_router(quiz_router, prefix="/api")
app.include_router(results_router, prefix="/api")
app.include_router(questions_router, prefix="/api")
