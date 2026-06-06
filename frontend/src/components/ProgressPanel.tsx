import { useState } from "react";
import { getResults, replan } from "../api/studium";
import type { ResultsSummary, Session } from "../api/studium";

interface Props {
  syllabusId: string;
  onSessionsUpdated: (sessions: Session[]) => void;
}

export default function ProgressPanel({ syllabusId, onSessionsUpdated }: Props) {
  const [summary, setSummary] = useState<ResultsSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [replanning, setReplanning] = useState(false);
  const [replanned, setReplanned] = useState<string[] | null>(null); // topics addressed
  const [error, setError] = useState<string | null>(null);

  async function fetchProgress() {
    setLoading(true);
    setError(null);
    try {
      const data = await getResults(syllabusId);
      setSummary(data);
    } catch {
      setError("Could not fetch results. Have you taken any quizzes yet?");
    } finally {
      setLoading(false);
    }
  }

  async function handleReplan() {
    setReplanning(true);
    setError(null);
    try {
      const result = await replan(syllabusId);
      onSessionsUpdated(result.full_sessions);
      setReplanned(result.weak_topics_addressed);
      // Refresh the summary to show updated (now non-weak?) state
      const refreshed = await getResults(syllabusId);
      setSummary(refreshed);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Re-planning failed.";
      setError(msg);
    } finally {
      setReplanning(false);
    }
  }

  // ── Initial state: button to load ────────────────────────────────────────
  if (!summary && !loading) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-slate-700">Progress Tracker</h3>
            <p className="text-slate-400 text-sm mt-0.5">
              See how you're doing across topics
            </p>
          </div>
          <button
            onClick={fetchProgress}
            className="bg-slate-800 text-white text-sm px-4 py-2 rounded-xl hover:bg-slate-700 transition-colors"
          >
            Check Progress
          </button>
        </div>
        {error && (
          <p className="text-slate-400 text-sm mt-3">{error}</p>
        )}
      </div>
    );
  }

  if (loading) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm text-center">
        <p className="text-slate-400 text-sm animate-pulse">Loading your quiz results…</p>
      </div>
    );
  }

  if (!summary || summary.total_quizzes_taken === 0) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
        <p className="text-slate-500 text-sm">
          No quiz results yet. Take some quizzes and come back here to see your progress.
        </p>
      </div>
    );
  }

  const hasWeak = summary.weak_topics.length > 0;

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
        <div>
          <h3 className="font-semibold text-slate-700">Progress Tracker</h3>
          <p className="text-slate-400 text-sm mt-0.5">
            {summary.total_quizzes_taken} quiz{summary.total_quizzes_taken !== 1 ? "zes" : ""} taken
          </p>
        </div>
        <button
          onClick={fetchProgress}
          className="text-xs text-slate-400 hover:text-violet-600"
        >
          Refresh
        </button>
      </div>

      {/* Per-topic results */}
      <div className="divide-y divide-slate-50">
        {summary.topic_results.map((tr) => (
          <div key={tr.topic} className="flex items-center gap-4 px-6 py-3">
            {/* Score badge */}
            <span
              className={`shrink-0 w-12 text-center text-xs font-bold py-1 rounded-lg ${
                tr.is_weak
                  ? "bg-red-100 text-red-600"
                  : "bg-emerald-100 text-emerald-600"
              }`}
            >
              {tr.avg_percentage}%
            </span>

            {/* Topic name */}
            <span className="flex-1 text-sm text-slate-700">{tr.topic}</span>

            {/* Attempts + weak flag */}
            <div className="flex items-center gap-2 shrink-0">
              <span className="text-xs text-slate-400">
                {tr.attempts} attempt{tr.attempts !== 1 ? "s" : ""}
              </span>
              {tr.is_weak && (
                <span className="text-xs bg-red-50 text-red-500 px-2 py-0.5 rounded-full font-medium">
                  Weak
                </span>
              )}
            </div>

            {/* Score bar */}
            <div className="w-20 h-1.5 bg-slate-100 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full ${
                  tr.is_weak ? "bg-red-400" : "bg-emerald-400"
                }`}
                style={{ width: `${tr.avg_percentage}%` }}
              />
            </div>
          </div>
        ))}
      </div>

      {/* Weak topics + re-plan CTA */}
      {(hasWeak || replanned) && (
        <div
          className={`mx-4 mb-4 mt-2 rounded-xl p-4 ${
            replanned
              ? "bg-emerald-50 border border-emerald-200"
              : "bg-amber-50 border border-amber-200"
          }`}
        >
          {replanned ? (
            <div>
              <p className="text-emerald-700 font-medium text-sm">
                Extra sessions added for: {replanned.join(", ")}
              </p>
              <p className="text-emerald-600 text-xs mt-1">
                Scroll down to see your updated schedule.
              </p>
            </div>
          ) : (
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-amber-700 font-medium text-sm">
                  {summary.weak_topics.length} weak topic
                  {summary.weak_topics.length !== 1 ? "s" : ""} detected
                </p>
                <p className="text-amber-600 text-xs mt-0.5">
                  {summary.weak_topics.map((w) => w.topic).join(", ")}
                </p>
              </div>
              <button
                onClick={handleReplan}
                disabled={replanning}
                className="shrink-0 bg-amber-500 text-white text-sm px-4 py-2 rounded-xl hover:bg-amber-600 disabled:opacity-50 transition-colors"
              >
                {replanning ? "Replanning…" : "Adaptive Re-plan"}
              </button>
            </div>
          )}
        </div>
      )}

      {!hasWeak && !replanned && (
        <div className="px-6 pb-5 pt-2">
          <p className="text-emerald-600 text-sm font-medium">
            No weak topics — great work!
          </p>
        </div>
      )}

      {error && (
        <p className="px-6 pb-4 text-red-500 text-sm">{error}</p>
      )}
    </div>
  );
}
