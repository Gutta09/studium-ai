import { useState } from "react";
import type { UploadResult } from "./api/studium";
import SyllabusUpload from "./components/SyllabusUpload";
import StudyPlan from "./components/StudyPlan";
import QuizPage from "./components/QuizPage";

// The app has three views. This type describes which one we're in.
type View =
  | { mode: "upload" }
  | { mode: "plan"; result: UploadResult }
  | { mode: "quiz"; result: UploadResult; topic: string };

export default function App() {
  const [view, setView] = useState<View>({ mode: "upload" });

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Nav */}
      <header className="bg-white border-b border-slate-200 px-6 py-4">
        <div className="max-w-3xl mx-auto flex items-center gap-2">
          <button
            onClick={() => setView({ mode: "upload" })}
            className="text-xl font-bold text-violet-600"
          >
            STUDIUM
          </button>
          <span className="text-xs bg-violet-100 text-violet-600 px-2 py-0.5 rounded-full font-medium">
            AI
          </span>
          {/* Breadcrumb */}
          {view.mode !== "upload" && (
            <span className="ml-2 text-slate-300 text-sm">
              /
              <button
                onClick={() =>
                  view.mode === "quiz"
                    ? setView({ mode: "plan", result: view.result })
                    : setView({ mode: "upload" })
                }
                className="ml-2 text-slate-500 hover:text-violet-600"
              >
                {view.mode === "quiz" ? "Study Plan" : "Upload"}
              </button>
            </span>
          )}
          {view.mode === "quiz" && (
            <span className="text-slate-300 text-sm">
              / <span className="text-slate-500">Quiz</span>
            </span>
          )}
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-12">
        {view.mode === "upload" && (
          <>
            <div className="text-center mb-10">
              <h1 className="text-4xl font-bold text-slate-900 mb-3">
                Upload your syllabus.
                <br />
                <span className="text-violet-600">Get a study plan.</span>
              </h1>
              <p className="text-slate-500 text-lg max-w-md mx-auto">
                An AI agent reads your syllabus, extracts every topic, and
                builds a personalised day-by-day schedule automatically.
              </p>
            </div>
            <SyllabusUpload
              onResult={(result) => setView({ mode: "plan", result })}
            />
          </>
        )}

        {view.mode === "plan" && (
          <StudyPlan
            result={view.result}
            onReset={() => setView({ mode: "upload" })}
            onQuiz={(topic) =>
              setView({ mode: "quiz", result: view.result, topic })
            }
            onSessionsUpdated={(sessions) =>
              setView((prev) =>
                prev.mode === "plan"
                  ? { ...prev, result: { ...prev.result, sessions } }
                  : prev
              )
            }
          />
        )}

        {view.mode === "quiz" && (
          <QuizPage
            syllabusId={view.result.syllabus_id}
            topic={view.topic}
            onBack={() => setView({ mode: "plan", result: view.result })}
          />
        )}
      </main>
    </div>
  );
}
