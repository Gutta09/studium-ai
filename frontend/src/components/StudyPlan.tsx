import { useState } from "react";
import { Link } from "react-router-dom";
import { updateSessionStatus, type Session, type UploadResult } from "../api/studium";
import ProgressPanel from "./ProgressPanel";

interface Props {
  result: UploadResult;
  onSessionsUpdated: (sessions: Session[]) => void;
}

const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];

function formatDate(iso: string) {
  const d = new Date(iso + "T00:00:00");
  return `${d.getDate()} ${MONTHS[d.getMonth()]} ${d.getFullYear()}`;
}

const TOPIC_COLORS = [
  "bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300",
  "bg-sky-100 dark:bg-sky-900/50 text-sky-700 dark:text-sky-300",
  "bg-emerald-100 dark:bg-emerald-900/50 text-emerald-700 dark:text-emerald-300",
  "bg-amber-100 dark:bg-amber-900/50 text-amber-700 dark:text-amber-300",
  "bg-rose-100 dark:bg-rose-900/50 text-rose-700 dark:text-rose-300",
  "bg-violet-100 dark:bg-violet-900/50 text-violet-700 dark:text-violet-300",
];

export default function StudyPlan({ result, onSessionsUpdated }: Props) {
  const { syllabus_id, topics, sessions } = result;
  const [togglingIndex, setTogglingIndex] = useState<number | null>(null);

  const startDate = sessions.length ? formatDate(sessions[0].date) : "—";
  const endDate = sessions.length ? formatDate(sessions[sessions.length - 1].date) : "—";
  const doneCount = sessions.filter((s) => s.status === "done").length;
  const donePct = sessions.length ? Math.round((doneCount / sessions.length) * 100) : 0;

  async function toggleDone(index: number) {
    const next = sessions[index].status === "done" ? "pending" : "done";
    setTogglingIndex(index);
    try {
      const updated = await updateSessionStatus(syllabus_id, index, next);
      onSessionsUpdated(updated);
    } catch {
      // leave state as-is; a failed toggle is recoverable by clicking again
    } finally {
      setTogglingIndex(null);
    }
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">

      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Study Plan</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">Your personalised learning schedule</p>
        </div>
        <Link
          to="/"
          className="flex items-center gap-1.5 text-sm text-slate-500 dark:text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-2 hover:border-indigo-300 transition-colors"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
          </svg>
          Upload new syllabus
        </Link>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: "Total Topics", value: String(topics.length), color: "text-indigo-600" },
          { label: "Completed", value: `${doneCount}/${sessions.length} · ${donePct}%`, color: "text-sky-600" },
          { label: "Start Date", value: startDate, color: "text-emerald-600" },
          { label: "End Date", value: endDate, color: "text-amber-600" },
        ].map(({ label, value, color }) => (
          <div key={label} className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 px-5 py-4">
            <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">{label}</p>
            <p className={`text-xl font-bold ${color}`}>{value}</p>
          </div>
        ))}
      </div>

      {/* Topics */}
      <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-6">
        <h2 className="text-sm font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-4">
          Extracted Topics
        </h2>
        <div className="flex flex-wrap gap-2">
          {topics.map((topic, i) => (
            <span
              key={i}
              className={`text-sm px-3 py-1 rounded-full font-medium ${TOPIC_COLORS[i % TOPIC_COLORS.length]}`}
            >
              {topic}
            </span>
          ))}
        </div>
      </div>

      {/* Progress tracker */}
      <ProgressPanel syllabusId={syllabus_id} onSessionsUpdated={onSessionsUpdated} />

      {/* Schedule table */}
      <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-700/60 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
            Day-wise Schedule
          </h2>
          <span className="text-xs text-slate-400">{sessions.length} sessions</span>
        </div>

        {/* Table header */}
        <div className="grid grid-cols-[40px_80px_1fr_1fr_140px] gap-4 px-6 py-2 bg-slate-50 dark:bg-slate-900/50 border-b border-slate-100 dark:border-slate-700/60 text-xs font-semibold text-slate-400 uppercase tracking-wider">
          <span>Done</span>
          <span>Date</span>
          <span>Topic</span>
          <span>What to Study</span>
          <span className="text-right">Actions</span>
        </div>

        <div className="divide-y divide-slate-100 dark:divide-slate-700/60">
          {sessions.map((session, i) => {
            const done = session.status === "done";
            return (
              <div
                key={i}
                className={`grid grid-cols-[40px_80px_1fr_1fr_140px] gap-4 items-center px-6 py-3.5 transition-colors ${
                  session.is_review
                    ? "bg-amber-50/60 dark:bg-amber-900/20"
                    : "hover:bg-slate-50/80 dark:hover:bg-slate-700/40"
                } ${done ? "opacity-60" : ""}`}
              >
                {/* Done checkbox */}
                <input
                  type="checkbox"
                  checked={done}
                  disabled={togglingIndex === i}
                  onChange={() => toggleDone(i)}
                  aria-label={`Mark "${session.topic}" on ${formatDate(session.date)} as done`}
                  className="w-4 h-4 accent-indigo-600 cursor-pointer disabled:cursor-wait"
                />

                {/* Date */}
                <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">
                  {formatDate(session.date)}
                </span>

                {/* Topic */}
                <div>
                  <p className={`text-sm font-medium text-slate-800 dark:text-slate-100 ${done ? "line-through" : ""}`}>
                    {session.topic}
                  </p>
                  {session.is_review && (
                    <span className="text-xs bg-amber-100 dark:bg-amber-900/50 text-amber-700 dark:text-amber-300 px-1.5 py-0.5 rounded font-medium">
                      Review
                    </span>
                  )}
                </div>

                {/* Description */}
                <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                  {session.description}
                </p>

                {/* Actions */}
                <div className="flex items-center gap-1.5 justify-end">
                  <Link
                    to={`/plan/${syllabus_id}/questions/${encodeURIComponent(session.topic)}`}
                    className="text-xs px-2.5 py-1 rounded-lg border border-amber-200 dark:border-amber-800 text-amber-700 dark:text-amber-300 hover:bg-amber-50 dark:hover:bg-amber-900/30 font-medium transition-colors"
                  >
                    Imp. Qs
                  </Link>
                  <Link
                    to={`/plan/${syllabus_id}/quiz/${encodeURIComponent(session.topic)}`}
                    className="text-xs px-2.5 py-1 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 font-medium transition-colors"
                  >
                    Quiz
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
