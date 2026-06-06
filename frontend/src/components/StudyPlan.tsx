import type { Session, UploadResult } from "../api/studium";
import ProgressPanel from "./ProgressPanel";

interface Props {
  result: UploadResult;
  onReset: () => void;
  onQuiz: (topic: string) => void;
  onSessionsUpdated: (sessions: Session[]) => void;
}

const MONTHS = [
  "Jan","Feb","Mar","Apr","May","Jun",
  "Jul","Aug","Sep","Oct","Nov","Dec",
];

function formatDate(iso: string) {
  const d = new Date(iso + "T00:00:00");
  return `${d.getDate()} ${MONTHS[d.getMonth()]}`;
}

const PILL_COLORS = [
  "bg-violet-100 text-violet-700",
  "bg-sky-100 text-sky-700",
  "bg-emerald-100 text-emerald-700",
  "bg-amber-100 text-amber-700",
  "bg-rose-100 text-rose-700",
  "bg-indigo-100 text-indigo-700",
];

export default function StudyPlan({
  result,
  onReset,
  onQuiz,
  onSessionsUpdated,
}: Props) {
  const { syllabus_id, topics, sessions } = result;

  return (
    <div className="max-w-3xl mx-auto flex flex-col gap-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold text-slate-800">Your Study Plan</h2>
          <p className="text-slate-500 text-sm mt-1">
            {topics.length} topics · {sessions.length} study sessions
          </p>
        </div>
        <button onClick={onReset} className="text-sm text-violet-600 hover:underline">
          Upload another →
        </button>
      </div>

      {/* Topics */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
        <h3 className="font-semibold text-slate-700 mb-4">Extracted Topics</h3>
        <div className="flex flex-wrap gap-2">
          {topics.map((topic, i) => (
            <span
              key={i}
              className={`text-sm px-3 py-1 rounded-full font-medium ${PILL_COLORS[i % PILL_COLORS.length]}`}
            >
              {topic}
            </span>
          ))}
        </div>
      </div>

      {/* Progress Tracker — Phase 3 + 4 */}
      <ProgressPanel
        syllabusId={syllabus_id}
        onSessionsUpdated={onSessionsUpdated}
      />

      {/* Schedule */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <h3 className="font-semibold text-slate-700 px-6 py-4 border-b border-slate-100">
          Day-wise Schedule
        </h3>
        <div className="divide-y divide-slate-100">
          {sessions.map((session, i) => (
            <div
              key={i}
              className={`flex gap-4 items-center px-6 py-4 transition-colors ${
                session.is_review
                  ? "bg-amber-50 hover:bg-amber-100/60"
                  : "hover:bg-slate-50"
              }`}
            >
              {/* Date badge */}
              <span className="shrink-0 w-14 text-center bg-slate-100 text-slate-600 text-xs font-semibold rounded-lg py-1">
                {formatDate(session.date)}
              </span>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <p className="font-medium text-slate-800 text-sm">
                  {session.topic}
                  {session.is_review && (
                    <span className="ml-2 text-xs bg-amber-200 text-amber-700 px-1.5 py-0.5 rounded font-medium">
                      Review
                    </span>
                  )}
                </p>
                <p className="text-slate-500 text-xs mt-0.5 leading-relaxed">
                  {session.description}
                </p>
              </div>

              {/* Status + quiz button */}
              <div className="shrink-0 flex items-center gap-2">
                <span className="text-xs px-2 py-0.5 rounded-full bg-amber-50 text-amber-600 font-medium">
                  {session.status}
                </span>
                <button
                  onClick={() => onQuiz(session.topic)}
                  className="text-xs px-3 py-1 rounded-full bg-violet-600 text-white font-medium hover:bg-violet-700 transition-colors"
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
