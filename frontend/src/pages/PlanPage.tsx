import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchPlan, type UploadResult, type Session } from "../api/studium";
import StudyPlan from "../components/StudyPlan";

export default function PlanPage() {
  const { syllabusId } = useParams<{ syllabusId: string }>();
  const [plan, setPlan] = useState<UploadResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!syllabusId) return;
    fetchPlan(syllabusId)
      .then(setPlan)
      .catch(() => setError("Couldn't load this study plan — it may not exist."));
  }, [syllabusId]);

  if (error) {
    return (
      <div className="text-center py-20 space-y-4">
        <p className="text-red-500">{error}</p>
        <Link to="/" className="text-indigo-600 dark:text-indigo-400 hover:underline text-sm">
          ← Back home
        </Link>
      </div>
    );
  }

  if (!plan) {
    return (
      <div className="text-center py-24">
        <div className="w-10 h-10 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        <p className="text-slate-400 text-sm">Loading your study plan…</p>
      </div>
    );
  }

  return (
    <StudyPlan
      result={plan}
      onSessionsUpdated={(sessions: Session[]) => setPlan({ ...plan, sessions })}
    />
  );
}
