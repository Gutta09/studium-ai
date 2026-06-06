import axios from "axios";

const API = "http://localhost:8000";

export interface Session {
  topic: string;
  date: string;
  status: "pending" | "done" | "skipped";
  description: string;
  is_review?: boolean; // true for sessions added by the adaptive re-planner
}

export interface UploadResult {
  syllabus_id: string;
  topics: string[];
  sessions: Session[];
}

// ── Quiz types ────────────────────────────────────────────────────────────────

export interface QuizQuestion {
  question: string;
  options: string[]; // [A text, B text, C text, D text]
}

export interface Quiz {
  quiz_id: string;
  topic: string;
  questions: QuizQuestion[];
}

export interface BreakdownItem {
  question: string;
  selected_letter: string;
  selected_text: string;
  correct_letter: string;
  correct_text: string;
  is_correct: boolean;
  explanation: string;
}

export interface QuizResult {
  score: number;
  total: number;
  percentage: number;
  breakdown: BreakdownItem[];
}

// ── API functions ─────────────────────────────────────────────────────────────

export async function uploadSyllabus(file: File): Promise<UploadResult> {
  const form = new FormData();
  form.append("file", file);

  const { data } = await axios.post<UploadResult>(
    `${API}/api/upload-syllabus`,
    form,
    { headers: { "Content-Type": "multipart/form-data" } }
  );

  return data;
}

export async function generateQuiz(
  syllabusId: string,
  topic: string
): Promise<Quiz> {
  const { data } = await axios.post<Quiz>(`${API}/api/quiz/generate`, {
    syllabus_id: syllabusId,
    topic,
  });
  return data;
}

export async function submitQuiz(
  quizId: string,
  answers: string[]
): Promise<QuizResult> {
  const { data } = await axios.post<QuizResult>(`${API}/api/quiz/submit`, {
    quiz_id: quizId,
    answers,
  });
  return data;
}

// ── Results + re-planning types ───────────────────────────────────────────────

export interface TopicResult {
  topic: string;
  attempts: number;
  avg_percentage: number;
  best_percentage: number;
  is_weak: boolean;
}

export interface ResultsSummary {
  syllabus_id: string;
  topic_results: TopicResult[];
  weak_topics: TopicResult[];
  total_quizzes_taken: number;
}

export interface ReplanResult {
  added_sessions: Session[];
  full_sessions: Session[];
  weak_topics_addressed: string[];
}

export async function getResults(syllabusId: string): Promise<ResultsSummary> {
  const { data } = await axios.get<ResultsSummary>(
    `${API}/api/results/${syllabusId}`
  );
  return data;
}

export async function replan(syllabusId: string): Promise<ReplanResult> {
  const { data } = await axios.post<ReplanResult>(`${API}/api/replan`, {
    syllabus_id: syllabusId,
  });
  return data;
}
