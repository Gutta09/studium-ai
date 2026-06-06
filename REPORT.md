# STUDIUM AI — Project Report
### Autonomous Learning Agent | Major Project

---

## 1. Project Overview

**STUDIUM AI** is an autonomous learning agent that turns a college syllabus PDF into a complete, adaptive study system. The student uploads a PDF, and the AI agent independently:

1. Extracts a structured list of topics
2. Generates a day-wise, deadline-aware study plan
3. Creates per-topic multiple-choice quizzes
4. Generates important exam questions categorised by marks (2 / 5 / 10)
5. Detects weak topics from quiz scores
6. Adaptively re-plans by adding extra revision sessions for weak topics

The core idea is the **agentic loop**: the agent plans → acts → observes feedback → self-corrects. This mirrors how an intelligent tutor would behave.

---

## 2. System Architecture

```
Student (Browser)
      │
      │  HTTP (JSON + multipart/form-data)
      ▼
┌─────────────────────────────────────┐
│           FastAPI Backend           │
│  /api/upload-syllabus               │
│  /api/quiz/generate                 │
│  /api/quiz/submit                   │
│  /api/important-questions           │
│  /api/results/{syllabus_id}         │
│  /api/replan                        │
└──────┬──────────────┬───────────────┘
       │              │
       ▼              ▼
  Groq API       MongoDB Atlas /
  (LLM calls)    Local MongoDB
```

### Agentic Loop Diagram

```
Upload PDF
    │
    ▼
[Agent 1] extract_topics()
    │   → pdfplumber extracts raw text
    │   → Groq (llama-3.3-70b) reads text, returns JSON topic list
    ▼
[Agent 2] generate_study_plan()
    │   → Groq schedules topics across N days (skips weekends)
    │   → Sessions stored in MongoDB
    ▼
Student Studies + Takes Quizzes
    │
    ▼
[Agent 3] generate_quiz()
    │   → Groq generates 5 MCQs per topic
    │   → Correct answers stored server-side (not sent to browser)
    ▼
Student Submits Answers → Score calculated server-side
    │
    ▼
[Phase 3] Aggregate Results
    │   → Per-topic average scores computed from MongoDB
    │   → Topics with avg score < 70% flagged as "weak"
    ▼
[Agent 4] generate_replan()  ← The self-correction step
    │   → Groq generates focused review sessions for weak topics
    │   → Appended to existing plan (version bumped)
    ▼
Updated Schedule Shown to Student
    │
    └── Loop repeats ↑
```

---

## 3. Technology Stack

### 3.1 Backend

| Technology | Version | Purpose | Why Chosen |
|---|---|---|---|
| **Python** | 3.9+ | Backend language | Dominant in AI/ML tooling; excellent library support |
| **FastAPI** | 0.128 | REST API framework | Async-capable, auto-generates docs, Pydantic validation built-in |
| **pdfplumber** | 0.11 | PDF text extraction | Better than PyPDF for layout-aware extraction; handles tables/columns |
| **Groq SDK** | 1.0 | LLM API client | llama-3.3-70b-versatile on Groq is free-tier, fast (700+ tokens/sec), and capable |
| **pymongo** | 4.17 | MongoDB driver | Simple sync driver; sufficient for a single-server demo project |
| **python-dotenv** | 1.2 | Env variable loading | Industry-standard pattern for keeping secrets out of source code |
| **Uvicorn** | 0.39 | ASGI server | Production-grade async server for FastAPI; `--reload` for development |

### 3.2 AI / LLM

| Technology | Purpose | Why Chosen |
|---|---|---|
| **Groq API** | All LLM inference | Free tier (no credit card required); llama-3.3-70b returns 700+ tokens/sec |
| **llama-3.3-70b-versatile** | Topic extraction, study planning, quiz generation, re-planning, exam questions | Best open-weight model for structured JSON output on Groq free tier |
| **JSON mode** (`response_format: json_object`) | Structured outputs | Guarantees parseable JSON from the LLM; avoids brittle regex parsing |

### 3.3 Frontend

| Technology | Version | Purpose | Why Chosen |
|---|---|---|---|
| **React** | 19 | UI framework | Component model maps cleanly to the app's views (upload → plan → quiz) |
| **Vite** | 8 | Build tool & dev server | Near-instant HMR; much faster than Create React App |
| **TypeScript** | 5 | Type safety | Catches API contract mismatches at compile time; essential for a multi-file project |
| **Tailwind CSS** | v4 | Styling | Utility-first; avoids writing separate CSS files; v4 Vite plugin is zero-config |
| **Axios** | 1.x | HTTP client | Cleaner API than fetch; automatic JSON parsing; easy error object access |

### 3.4 Database

| Technology | Purpose | Why Chosen |
|---|---|---|
| **MongoDB** | Document store for syllabi, plans, quizzes, results | Schema-free design fits the variable structure of AI-generated plans; JSON-native |

**Collections:**

| Collection | Stores |
|---|---|
| `syllabi` | filename, raw PDF text, extracted topics |
| `plans` | syllabus_id, sessions array, version number |
| `quizzes` | syllabus_id, topic, questions with correct answers |
| `results` | quiz_id, topic, score, total, per-question breakdown |

---

## 4. Key Design Decisions

### 4.1 Why Groq instead of OpenAI or Claude?
The project targets students without paid API subscriptions. Groq provides a **generous free tier** (30 req/min, 14,400 req/day) with no credit card. llama-3.3-70b-versatile is capable enough for all four agent tasks.

### 4.2 Why JSON mode instead of prompt engineering?
Early prototypes used prompt engineering ("return only JSON") — models still added preamble and markdown fences. `response_format: {"type": "json_object"}` enforces valid JSON at the API level, making downstream parsing reliable.

### 4.3 Why store quizzes in MongoDB with answers server-side?
If the correct answers were returned in the API response, a student could inspect network traffic and cheat. By storing them server-side and only returning them during the `submit` call, the scoring is tamper-proof.

### 4.4 Why use business days (Mon–Fri) for scheduling?
Students don't study on weekends in most academic calendars. Skipping weekends makes the generated plan more realistic and directly actionable.

### 4.5 Why pymongo (sync) instead of Motor (async)?
FastAPI runs sync route functions in a thread pool automatically. Motor adds complexity (async context managers, event loops) with no meaningful benefit at this scale. Keeping it sync keeps the code readable for a learning project.

---

## 5. API Endpoints Reference

| Method | Endpoint | Input | Output |
|---|---|---|---|
| POST | `/api/upload-syllabus` | PDF file + `days` (int) | topics[], sessions[] |
| POST | `/api/quiz/generate` | syllabus_id, topic | quiz_id, questions (no answers) |
| POST | `/api/quiz/submit` | quiz_id, answers[] | score, percentage, breakdown |
| POST | `/api/important-questions` | topic | 2_mark[], 5_mark[], 10_mark[] questions |
| GET | `/api/results/{syllabus_id}` | — | per-topic scores, weak_topics[] |
| POST | `/api/replan` | syllabus_id | added_sessions[], full_sessions[] |

---

## 6. Project Structure

```
studium/
├── backend/
│   ├── main.py                  # FastAPI app, CORS, router registration
│   ├── db.py                    # MongoDB connection + collection handles
│   ├── requirements.txt
│   ├── agents/
│   │   ├── planner.py           # Agent 1: topic extraction + study planning
│   │   ├── quizzer.py           # Agent 2: MCQ quiz generation
│   │   ├── replanner.py         # Agent 3: adaptive re-planning
│   │   └── examiner.py          # Agent 4: important exam questions
│   └── routes/
│       ├── syllabus.py          # POST /upload-syllabus
│       ├── quiz.py              # POST /quiz/generate + /quiz/submit
│       ├── results.py           # GET /results + POST /replan
│       └── questions.py         # POST /important-questions
└── frontend/
    └── src/
        ├── api/studium.ts       # All API calls + TypeScript types
        ├── App.tsx              # View router + dark mode state
        └── components/
            ├── SyllabusUpload.tsx    # Upload form with duration picker
            ├── StudyPlan.tsx         # Stats cards + schedule table
            ├── QuizPage.tsx          # MCQ quiz + results breakdown
            ├── ImportantQuestions.tsx # Exam questions by mark category
            └── ProgressPanel.tsx     # Score tracker + re-plan trigger
```

---

## 7. How to Run

### Prerequisites
- Python 3.9+, Node.js 18+, MongoDB running locally

### Backend
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Add GROQ_API_KEY to .env (free at console.groq.com)
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**

---

## 8. Demo Flow

1. **Upload** — Student uploads a syllabus PDF and selects study duration (e.g., 30 days)
2. **Plan Generated** — AI extracts topics and builds a day-wise schedule ending on the target date
3. **Important Questions** — Click "Imp. Qs" on any session to get 2/5/10-mark exam questions with model answers
4. **Take Quiz** — Click "Quiz" to get 5 MCQs on that topic; answer and submit
5. **Progress Tracker** — After a few quizzes, click "Check Progress" to see per-topic scores
6. **Adaptive Re-plan** — If weak topics are detected, click "Adaptive Re-plan" — the AI appends focused review sessions (highlighted in amber)

---

## 9. Future Scope

| Phase | Feature |
|---|---|
| 5 | Flashcard generation per topic |
| 6 | Pomodoro timer integrated into study sessions |
| 7 | Collaborative study groups with shared plans |
| 8 | Mobile app (React Native reusing the same backend) |
| 9 | Voice-based quiz mode |
| 10 | Integration with university LMS (Moodle, Canvas) |
