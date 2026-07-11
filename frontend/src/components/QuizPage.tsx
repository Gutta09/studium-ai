import { useEffect, useState } from "react";
import { generateQuiz, submitQuiz } from "../api/studium";
import type { Quiz, QuizResult } from "../api/studium";

interface Props {
  syllabusId: string;
  topic: string;
  onBack: () => void;
}

const LETTERS = ["A", "B", "C", "D"] as const;

export default function QuizPage({ syllabusId, topic, onBack }: Props) {
  const [quiz, setQuiz] = useState<Quiz | null>(null);
  const [answers, setAnswers] = useState<string[]>([]);
  const [result, setResult] = useState<QuizResult | null>(null);
  const [loadingQuiz, setLoadingQuiz] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Generate quiz as soon as the component mounts
  useEffect(() => {
    generateQuiz(syllabusId, topic)
      .then((q) => {
        setQuiz(q);
        setAnswers(new Array(q.questions.length).fill(""));
      })
      .catch((err) => {
        const msg =
          err?.response?.data?.detail ?? "Failed to generate quiz.";
        setError(msg);
      })
      .finally(() => setLoadingQuiz(false));
  }, [syllabusId, topic]);

  function selectAnswer(questionIdx: number, letter: string) {
    setAnswers((prev) => {
      const next = [...prev];
      next[questionIdx] = letter;
      return next;
    });
  }

  async function handleSubmit() {
    if (!quiz) return;
    const unanswered = answers.filter((a) => a === "").length;
    if (unanswered > 0) {
      setError(`Please answer all questions (${unanswered} remaining).`);
      return;
    }
    setError(null);
    setSubmitting(true);
    try {
      const r = await submitQuiz(quiz.quiz_id, answers);
      setResult(r);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Submission failed.";
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  }

  // ── Loading state ─────────────────────────────────────────────────────────
  if (loadingQuiz) {
    return (
      <div className="max-w-2xl mx-auto text-center py-24">
        <p className="text-violet-600 text-lg font-medium animate-pulse">
          Writing your quiz…
        </p>
        <p className="text-slate-400 text-sm mt-2">Topic: {topic}</p>
      </div>
    );
  }

  if (error && !quiz) {
    return (
      <div className="max-w-2xl mx-auto text-center py-16">
        <p className="text-red-500 mb-4">{error}</p>
        <button onClick={onBack} className="text-violet-600 hover:underline text-sm">
          ← Back to study plan
        </button>
      </div>
    );
  }

  // ── Results screen ────────────────────────────────────────────────────────
  if (result) {
    const passed = result.percentage >= 70;
    return (
      <div className="max-w-2xl mx-auto flex flex-col gap-6">
        {/* Score banner */}
        <div
          className={`rounded-2xl p-6 text-center ${
            passed
              ? "bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800"
              : "bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800"
          }`}
        >
          <p className="text-5xl font-bold mb-1">
            {result.score}/{result.total}
          </p>
          <p
            className={`text-lg font-medium ${
              passed ? "text-emerald-700 dark:text-emerald-300" : "text-amber-700 dark:text-amber-300"
            }`}
          >
            {result.percentage}% — {passed ? "Great job! 🎉" : "Keep studying! 📚"}
          </p>
          <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">{topic}</p>
        </div>

        {/* Breakdown */}
        <div className="flex flex-col gap-4">
          {result.breakdown.map((item, i) => (
            <div
              key={i}
              className={`bg-white dark:bg-slate-800 rounded-xl border p-5 ${
                item.is_correct ? "border-emerald-200 dark:border-emerald-800" : "border-red-200 dark:border-red-800"
              }`}
            >
              <div className="flex items-start gap-3 mb-3">
                <span
                  className={`shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white ${
                    item.is_correct ? "bg-emerald-500" : "bg-red-400"
                  }`}
                >
                  {item.is_correct ? "✓" : "✗"}
                </span>
                <p className="font-medium text-slate-800 dark:text-slate-100 text-sm">
                  {item.question}
                </p>
              </div>

              <div className="ml-9 flex flex-col gap-1 text-sm">
                {!item.is_correct && (
                  <p className="text-red-500">
                    Your answer: {item.selected_letter}. {item.selected_text}
                  </p>
                )}
                <p className="text-emerald-600 dark:text-emerald-400">
                  Correct: {item.correct_letter}. {item.correct_text}
                </p>
                <p className="text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">
                  {item.explanation}
                </p>
              </div>
            </div>
          ))}
        </div>

        <div className="flex gap-3 pb-8">
          <button
            onClick={onBack}
            className="flex-1 py-3 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:bg-slate-900/50 dark:hover:bg-slate-700/40 text-sm font-medium transition-colors"
          >
            ← Back to plan
          </button>
          <button
            onClick={() => {
              setResult(null);
              setAnswers(new Array(quiz!.questions.length).fill(""));
            }}
            className="flex-1 py-3 rounded-xl bg-violet-600 text-white text-sm font-medium hover:bg-violet-700 transition-colors"
          >
            Retake quiz
          </button>
        </div>
      </div>
    );
  }

  // ── Questions screen ──────────────────────────────────────────────────────
  const answeredCount = answers.filter((a) => a !== "").length;

  return (
    <div className="max-w-2xl mx-auto flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <button
            onClick={onBack}
            className="text-slate-400 hover:text-slate-600 dark:text-slate-300 text-sm mb-1"
          >
            ← Back
          </button>
          <h2 className="text-xl font-semibold text-slate-800 dark:text-slate-100">{topic}</h2>
          <p className="text-slate-400 text-sm">
            {quiz!.questions.length} questions · {answeredCount} answered
          </p>
        </div>
        {/* Progress bar */}
        <div className="w-24">
          <div className="h-2 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-violet-500 rounded-full transition-all"
              style={{
                width: `${(answeredCount / quiz!.questions.length) * 100}%`,
              }}
            />
          </div>
        </div>
      </div>

      {/* Questions */}
      {quiz!.questions.map((q, qi) => (
        <div
          key={qi}
          className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-6 shadow-sm"
        >
          <p className="font-medium text-slate-800 dark:text-slate-100 mb-4">
            <span className="text-violet-500 mr-2">{qi + 1}.</span>
            {q.question}
          </p>
          <div className="flex flex-col gap-2">
            {q.options.map((option, oi) => {
              const letter = LETTERS[oi];
              const selected = answers[qi] === letter;
              return (
                <button
                  key={oi}
                  onClick={() => selectAnswer(qi, letter)}
                  className={`text-left px-4 py-3 rounded-xl border text-sm transition-all ${
                    selected
                      ? "border-violet-400 bg-violet-50 dark:bg-violet-950/50 text-violet-700 dark:text-violet-300 font-medium"
                      : "border-slate-200 dark:border-slate-700 hover:border-violet-200 hover:bg-violet-50/50 dark:hover:bg-violet-950/30 text-slate-700 dark:text-slate-200"
                  }`}
                >
                  <span className="font-semibold mr-2">{letter}.</span>
                  {option}
                </button>
              );
            })}
          </div>
        </div>
      ))}

      {/* Error */}
      {error && (
        <p className="text-red-500 text-sm bg-red-50 dark:bg-red-950/40 px-4 py-2 rounded-lg">
          {error}
        </p>
      )}

      {/* Submit */}
      <button
        onClick={handleSubmit}
        disabled={submitting}
        className="bg-violet-600 text-white rounded-xl py-3 font-medium hover:bg-violet-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors mb-8"
      >
        {submitting ? "Scoring…" : `Submit Answers (${answeredCount}/${quiz!.questions.length})`}
      </button>
    </div>
  );
}
