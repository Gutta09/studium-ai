# STUDIUM AI — Autonomous Learning Agent

> Drop your syllabus. Get a smart study plan, quizzes, and exam questions — all in seconds.

An AI agent that turns a college syllabus PDF into a complete, adaptive study system.

## What it does

| Step | What happens |
|---|---|
| 1 | You upload a syllabus PDF and set your study deadline |
| 2 | AI extracts every topic from the document |
| 3 | AI builds a day-wise schedule fitting your deadline (weekends excluded) |
| 4 | Per-topic quizzes test your knowledge |
| 5 | Important exam questions (2 / 5 / 10 marks) with model answers |
| 6 | Weak topics (score < 70%) are detected automatically |
| 7 | AI re-plans — adds focused review sessions for weak topics |

## Tech Stack

- **Frontend** — React 19 + Vite + TypeScript + Tailwind CSS v4
- **Backend** — Python + FastAPI
- **AI** — Groq API (llama-3.3-70b-versatile) — free tier
- **Database** — MongoDB

## Run locally

### Backend
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# create .env with GROQ_API_KEY (free at console.groq.com) and MONGODB_URI
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**

## Features

- Dark mode toggle
- Study duration picker (7 / 14 / 30 / 60 / 90 days or custom)
- Adaptive re-planning — the core agentic loop
- Important Questions categorised by marks for exam prep
