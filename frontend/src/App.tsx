import { useState, useEffect } from "react";
import type { UploadResult, Session } from "./api/studium";
import SyllabusUpload from "./components/SyllabusUpload";
import StudyPlan from "./components/StudyPlan";
import QuizPage from "./components/QuizPage";
import ImportantQuestions from "./components/ImportantQuestions";

type View =
  | { mode: "upload" }
  | { mode: "plan"; result: UploadResult }
  | { mode: "quiz"; result: UploadResult; topic: string }
  | { mode: "questions"; result: UploadResult; topic: string };

export default function App() {
  const [view, setView] = useState<View>({ mode: "upload" });
  const [dark, setDark] = useState(() => localStorage.getItem("theme") === "dark");

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    localStorage.setItem("theme", dark ? "dark" : "light");
  }, [dark]);

  function goToPlan(result: UploadResult) {
    setView({ mode: "plan", result });
  }

  function updateSessions(sessions: Session[]) {
    setView((prev) =>
      prev.mode === "plan"
        ? { ...prev, result: { ...prev.result, sessions } }
        : prev
    );
  }

  const getBackToPlan = () => {
    if ("result" in view) goToPlan((view as { result: UploadResult }).result);
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 transition-colors">

      {/* ── Navigation ───────────────────────────────────────────────────────── */}
      <header className="bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 shadow-sm sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-6 h-14 flex items-center justify-between">

          {/* Logo */}
          <button onClick={() => setView({ mode: "upload" })} className="flex items-center gap-2.5 group">
            <div className="w-7 h-7 bg-indigo-600 rounded-lg flex items-center justify-center group-hover:bg-indigo-700 transition-colors">
              <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10.394 2.08a1 1 0 00-.788 0l-7 3a1 1 0 000 1.84L5.25 8.051a.999.999 0 01.356-.257l4-1.714a1 1 0 11.788 1.838L7.667 9.088l1.94.831a1 1 0 00.787 0l7-3a1 1 0 000-1.838l-7-3zM3.31 9.397L5 10.12v4.102a8.969 8.969 0 00-1.05-.174 1 1 0 01-.89-.89 11.115 11.115 0 01.25-3.762zM9.3 16.573A9.026 9.026 0 007 14.935v-3.957l1.818.78a3 3 0 002.364 0l5.508-2.361a11.026 11.026 0 01.25 3.762 1 1 0 01-.89.89 8.968 8.968 0 00-5.35 2.524 1 1 0 01-1.4 0zM6 18a1 1 0 001-1v-2.065a8.935 8.935 0 00-2-.712V17a1 1 0 001 1z" />
              </svg>
            </div>
            <span className="font-bold text-slate-900 dark:text-white text-sm tracking-tight">STUDIUM AI</span>
          </button>

          {/* Breadcrumb */}
          {view.mode !== "upload" && (
            <nav className="flex items-center gap-1.5 text-sm">
              <button onClick={() => setView({ mode: "upload" })} className="text-slate-400 hover:text-indigo-500">Home</button>
              <span className="text-slate-300 dark:text-slate-600">/</span>
              {"result" in view && view.mode !== "plan" ? (
                <>
                  <button onClick={getBackToPlan} className="text-slate-400 hover:text-indigo-500">Study Plan</button>
                  <span className="text-slate-300 dark:text-slate-600">/</span>
                  <span className="text-slate-700 dark:text-slate-200 font-medium capitalize">{view.mode === "quiz" ? "Quiz" : "Important Questions"}</span>
                </>
              ) : (
                <span className="text-slate-700 dark:text-slate-200 font-medium">Study Plan</span>
              )}
            </nav>
          )}

          {/* Dark mode toggle */}
          <button
            onClick={() => setDark(!dark)}
            className="w-9 h-9 rounded-lg border border-slate-200 dark:border-slate-600 flex items-center justify-center hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
            title="Toggle dark mode"
          >
            {dark ? (
              <svg className="w-4 h-4 text-amber-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" clipRule="evenodd" />
              </svg>
            ) : (
              <svg className="w-4 h-4 text-slate-500" fill="currentColor" viewBox="0 0 20 20">
                <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" />
              </svg>
            )}
          </button>
        </div>
      </header>

      {/* ── Content ───────────────────────────────────────────────────────────── */}
      <main className="max-w-5xl mx-auto px-4 py-10">

        {view.mode === "upload" && (
          <div className="space-y-10">
            <div className="text-center space-y-4">
              <span className="inline-block bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300 text-xs font-semibold px-3 py-1 rounded-full uppercase tracking-wider">
                Autonomous Learning Agent
              </span>
              <h1 className="text-4xl font-extrabold text-slate-900 dark:text-white leading-tight">
                Turn your syllabus into<br />
                <span className="text-indigo-600">a complete study system.</span>
              </h1>
              <p className="text-slate-500 dark:text-slate-400 text-lg max-w-lg mx-auto">
                Drop your syllabus. Get a smart study plan, quizzes, and
                exam questions — all in seconds.
              </p>
            </div>

            <div className="flex flex-wrap justify-center gap-3 text-sm">
              {["Topic Extraction", "Study Plan", "Per-topic Quizzes", "Important Questions", "Adaptive Re-planning"].map((f) => (
                <span key={f} className="flex items-center gap-1.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-full px-4 py-1.5 text-slate-600 dark:text-slate-300 shadow-sm">
                  <span className="w-1.5 h-1.5 bg-indigo-500 rounded-full" />
                  {f}
                </span>
              ))}
            </div>

            <SyllabusUpload onResult={goToPlan} />
          </div>
        )}

        {view.mode === "plan" && (
          <StudyPlan
            result={view.result}
            onReset={() => setView({ mode: "upload" })}
            onQuiz={(topic) => setView({ mode: "quiz", result: view.result, topic })}
            onImportantQuestions={(topic) => setView({ mode: "questions", result: view.result, topic })}
            onSessionsUpdated={updateSessions}
          />
        )}

        {view.mode === "quiz" && (
          <QuizPage
            syllabusId={view.result.syllabus_id}
            topic={view.topic}
            onBack={getBackToPlan}
          />
        )}

        {view.mode === "questions" && (
          <ImportantQuestions
            topic={view.topic}
            onBack={getBackToPlan}
          />
        )}
      </main>
    </div>
  );
}
