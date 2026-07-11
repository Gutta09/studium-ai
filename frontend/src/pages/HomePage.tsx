import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { listSyllabi, type SyllabusSummary } from "../api/studium";
import SyllabusUpload from "../components/SyllabusUpload";

function ProgressRing({ done, total }: { done: number; total: number }) {
  const pct = total > 0 ? Math.round((done / total) * 100) : 0;
  return (
    <div className="text-right shrink-0">
      <p className="text-sm font-bold text-indigo-600 dark:text-indigo-400">{pct}%</p>
      <p className="text-xs text-slate-400">{done}/{total} done</p>
    </div>
  );
}

export default function HomePage() {
  const navigate = useNavigate();
  const [syllabi, setSyllabi] = useState<SyllabusSummary[] | null>(null);

  useEffect(() => {
    listSyllabi().then(setSyllabi).catch(() => setSyllabi([]));
  }, []);

  return (
    <div className="space-y-10">
      <div className="text-center space-y-4">
        <span className="inline-block bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300 text-xs font-semibold px-3 py-1 rounded-full uppercase tracking-wider">
          Adaptive Learning Agent
        </span>
        <h1 className="text-4xl font-extrabold text-slate-900 dark:text-white leading-tight">
          Turn your syllabus into<br />
          <span className="text-indigo-600">a complete study system.</span>
        </h1>
        <p className="text-slate-500 dark:text-slate-400 text-lg max-w-lg mx-auto">
          Drop your syllabus. Get a study plan, quizzes, and
          exam questions — and let the agent re-plan around your weak topics.
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

      <SyllabusUpload onResult={(r) => navigate(`/plan/${r.syllabus_id}`)} />

      {/* Previous syllabi */}
      {syllabi !== null && syllabi.length > 0 && (
        <div className="max-w-xl mx-auto">
          <h2 className="text-sm font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-3">
            Your study plans
          </h2>
          <div className="space-y-2">
            {syllabi.map((s) => (
              <Link
                key={s.syllabus_id}
                to={`/plan/${s.syllabus_id}`}
                className="flex items-center justify-between gap-4 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-5 py-3.5 hover:border-indigo-300 dark:hover:border-indigo-600 transition-colors group"
              >
                <div className="min-w-0">
                  <p className="text-sm font-medium text-slate-800 dark:text-slate-100 truncate group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                    {s.filename}
                  </p>
                  <p className="text-xs text-slate-400 mt-0.5">
                    {s.topics} topics · {s.sessions} sessions
                    {s.created_at ? ` · ${new Date(s.created_at).toLocaleDateString()}` : ""}
                  </p>
                </div>
                <ProgressRing done={s.done_sessions} total={s.sessions} />
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
