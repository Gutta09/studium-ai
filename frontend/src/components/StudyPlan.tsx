import type { Session, UploadResult } from "../api/studium";
import ProgressPanel from "./ProgressPanel";

interface Props {
  result: UploadResult;
  onReset: () => void;
  onQuiz: (topic: string) => void;
  onImportantQuestions: (topic: string) => void;
  onSessionsUpdated: (sessions: Session[]) => void;
}

const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];

function formatDate(iso: string) {
  const d = new Date(iso + "T00:00:00");
  return `${d.getDate()} ${MONTHS[d.getMonth()]} ${d.getFullYear()}`;
}

const TOPIC_COLORS = [
  "bg-indigo-100 text-indigo-700",
  "bg-sky-100 text-sky-700",
  "bg-emerald-100 text-emerald-700",
  "bg-amber-100 text-amber-700",
  "bg-rose-100 text-rose-700",
  "bg-violet-100 text-violet-700",
];

export default function StudyPlan({ result, onReset, onQuiz, onImportantQuestions, onSessionsUpdated }: Props) {
  const { syllabus_id, topics, sessions } = result;

  const startDate = sessions.length ? formatDate(sessions[0].date) : "—";
  const endDate = sessions.length ? formatDate(sessions[sessions.length - 1].date) : "—";

  return (
    <div className="max-w-5xl mx-auto space-y-6">

      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Study Plan</h1>
          <p className="text-sm text-slate-500 mt-0.5">Your personalised learning schedule</p>
        </div>
        <button
          onClick={onReset}
          className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-indigo-600 border border-slate-200 rounded-lg px-4 py-2 hover:border-indigo-300 transition-colors"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
          </svg>
          Upload new syllabus
        </button>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: "Total Topics", value: topics.length, color: "text-indigo-600" },
          { label: "Study Sessions", value: sessions.length, color: "text-sky-600" },
          { label: "Start Date", value: startDate, color: "text-emerald-600" },
          { label: "End Date", value: endDate, color: "text-amber-600" },
        ].map(({ label, value, color }) => (
          <div key={label} className="bg-white rounded-xl border border-slate-200 px-5 py-4">
            <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">{label}</p>
            <p className={`text-xl font-bold ${color}`}>{value}</p>
          </div>
        ))}
      </div>

      {/* Topics */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6">
        <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-4">
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
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wider">
            Day-wise Schedule
          </h2>
          <span className="text-xs text-slate-400">{sessions.length} sessions</span>
        </div>

        {/* Table header */}
        <div className="grid grid-cols-[80px_1fr_1fr_140px] gap-4 px-6 py-2 bg-slate-50 border-b border-slate-100 text-xs font-semibold text-slate-400 uppercase tracking-wider">
          <span>Date</span>
          <span>Topic</span>
          <span>What to Study</span>
          <span className="text-right">Actions</span>
        </div>

        <div className="divide-y divide-slate-100">
          {sessions.map((session, i) => (
            <div
              key={i}
              className={`grid grid-cols-[80px_1fr_1fr_140px] gap-4 items-center px-6 py-3.5 transition-colors ${
                session.is_review ? "bg-amber-50/60" : "hover:bg-slate-50/80"
              }`}
            >
              {/* Date */}
              <span className="text-xs font-semibold text-slate-500">
                {formatDate(session.date)}
              </span>

              {/* Topic */}
              <div>
                <p className="text-sm font-medium text-slate-800">
                  {session.topic}
                </p>
                {session.is_review && (
                  <span className="text-xs bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded font-medium">
                    Review
                  </span>
                )}
              </div>

              {/* Description */}
              <p className="text-xs text-slate-500 leading-relaxed">
                {session.description}
              </p>

              {/* Actions */}
              <div className="flex items-center gap-1.5 justify-end">
                <button
                  onClick={() => onImportantQuestions(session.topic)}
                  className="text-xs px-2.5 py-1 rounded-lg border border-amber-200 text-amber-700 hover:bg-amber-50 font-medium transition-colors"
                >
                  Imp. Qs
                </button>
                <button
                  onClick={() => onQuiz(session.topic)}
                  className="text-xs px-2.5 py-1 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 font-medium transition-colors"
                >
                  Quiz
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
