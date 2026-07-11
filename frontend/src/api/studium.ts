import axios from "axios";

// Dev: Vite proxies /api to the FastAPI server (vite.config.ts).
// Prod: set VITE_API_URL to the deployed backend origin (including /api).
const API = import.meta.env.VITE_API_URL ?? "/api";

export const http = axios.create({ baseURL: API });

let _token: string | null = null;

export function setAuthToken(token: string | null) {
  _token = token;
}

http.interceptors.request.use((config) => {
  if (_token) config.headers.Authorization = `Bearer ${_token}`;
  return config;
});

// An expired/invalid token anywhere in the app sends the user back to sign-in
http.interceptors.response.use(undefined, (error) => {
  if (error?.response?.status === 401 && !error.config?.url?.startsWith("/auth")) {
    localStorage.removeItem("studium_token");
    localStorage.removeItem("studium_email");
    window.location.assign("/auth");
  }
  return Promise.reject(error);
});

// ── Auth ──────────────────────────────────────────────────────────────────────

export interface AuthResponse {
  token: string;
  email: string;
}

export async function register(email: string, password: string): Promise<AuthResponse> {
  const { data } = await http.post<AuthResponse>("/auth/register", { email, password });
  return data;
}

export async function login(email: string, password: string): Promise<AuthResponse> {
  const { data } = await http.post<AuthResponse>("/auth/login", { email, password });
  return data;
}

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

export async function uploadSyllabus(file: File, days: number): Promise<UploadResult> {
  const form = new FormData();
  form.append("file", file);
  form.append("days", String(days));

  const { data } = await http.post<UploadResult>(
    `/upload-syllabus`,
    form,
    { headers: { "Content-Type": "multipart/form-data" } }
  );

  return data;
}

export async function generateQuiz(
  syllabusId: string,
  topic: string
): Promise<Quiz> {
  const { data } = await http.post<Quiz>(`/quiz/generate`, {
    syllabus_id: syllabusId,
    topic,
  });
  return data;
}

export async function submitQuiz(
  quizId: string,
  answers: string[]
): Promise<QuizResult> {
  const { data } = await http.post<QuizResult>(`/quiz/submit`, {
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
  const { data } = await http.get<ResultsSummary>(`/results/${syllabusId}`);
  return data;
}

export async function replan(syllabusId: string): Promise<ReplanResult> {
  const { data } = await http.post<ReplanResult>(`/replan`, {
    syllabus_id: syllabusId,
  });
  return data;
}

// ── Important Questions types ─────────────────────────────────────────────────

export interface ExamQuestion {
  question: string;
  answer: string;
}

export interface ImportantQuestionsResult {
  topic: string;
  "2_mark": ExamQuestion[];
  "5_mark": ExamQuestion[];
  "10_mark": ExamQuestion[];
}

export async function fetchImportantQuestions(topic: string): Promise<ImportantQuestionsResult> {
  const { data } = await http.post<ImportantQuestionsResult>(
    `/important-questions`,
    { topic }
  );
  return data;
}

// ── Plans & dashboard ─────────────────────────────────────────────────────────

export interface SyllabusSummary {
  syllabus_id: string;
  filename: string;
  topics: number;
  sessions: number;
  done_sessions: number;
  created_at: string | null;
}

export async function listSyllabi(): Promise<SyllabusSummary[]> {
  const { data } = await http.get<SyllabusSummary[]>("/syllabi");
  return data;
}

export async function fetchPlan(syllabusId: string): Promise<UploadResult> {
  const { data } = await http.get<UploadResult>(`/plan/${syllabusId}`);
  return data;
}

export async function updateSessionStatus(
  syllabusId: string,
  index: number,
  status: "pending" | "done"
): Promise<Session[]> {
  const { data } = await http.patch<{ sessions: Session[] }>(
    `/plan/${syllabusId}/sessions/${index}`,
    { status }
  );
  return data.sessions;
}
