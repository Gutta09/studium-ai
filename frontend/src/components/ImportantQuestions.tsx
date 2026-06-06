import { useEffect, useState } from "react";
import { fetchImportantQuestions } from "../api/studium";
import type { ImportantQuestionsResult } from "../api/studium";

interface Props {
  topic: string;
  onBack: () => void;
}

const SECTIONS: { key: keyof Omit<ImportantQuestionsResult, "topic">; label: string; marks: string; color: string }[] = [
  { key: "2_mark",  label: "Short Answer",  marks: "2 marks",  color: "emerald" },
  { key: "5_mark",  label: "Medium Answer", marks: "5 marks",  color: "sky"     },
  { key: "10_mark", label: "Long Essay",    marks: "10 marks", color: "violet"  },
];

const COLOR_MAP: Record<string, string> = {
  emerald: "bg-emerald-50 border-emerald-200 text-emerald-700",
  sky:     "bg-sky-50 border-sky-200 text-sky-700",
  violet:  "bg-violet-50 border-violet-200 text-violet-700",
};

const BADGE_MAP: Record<string, string> = {
  emerald: "bg-emerald-100 text-emerald-700",
  sky:     "bg-sky-100 text-sky-700",
  violet:  "bg-violet-100 text-violet-700",
};

export default function ImportantQuestions({ topic, onBack }: Props) {
  const [data, setData] = useState<ImportantQuestionsResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  useEffect(() => {
    fetchImportantQuestions(topic)
      .then(setData)
      .catch(() => setError("Failed to generate questions. Please try again."))
      .finally(() => setLoading(false));
  }, [topic]);

  function toggleAnswer(key: string) {
    setExpanded((prev) => ({ ...prev, [key]: !prev[key] }));
  }

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto text-center py-24 space-y-3">
        <div className="w-10 h-10 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-slate-600 font-medium">Generating important questions…</p>
        <p className="text-slate-400 text-sm">Topic: {topic}</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="max-w-3xl mx-auto text-center py-20">
        <p className="text-red-500 mb-4">{error}</p>
        <button onClick={onBack} className="text-indigo-600 hover:underline text-sm">← Back to study plan</button>
      </div>
    );
  }

  const totalQuestions = data["2_mark"].length + data["5_mark"].length + data["10_mark"].length;

  return (
    <div className="max-w-3xl mx-auto space-y-6">

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <button onClick={onBack} className="text-slate-400 hover:text-indigo-600 text-sm mb-2 flex items-center gap-1">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Study Plan
          </button>
          <h1 className="text-2xl font-bold text-slate-900">Important Questions</h1>
          <p className="text-slate-500 text-sm mt-1">
            <span className="font-medium text-slate-700">{topic}</span>
            &nbsp;·&nbsp;{totalQuestions} questions across 3 mark categories
          </p>
        </div>
      </div>

      {/* Tip banner */}
      <div className="bg-indigo-50 border border-indigo-100 rounded-xl px-5 py-3 flex items-start gap-3">
        <svg className="w-5 h-5 text-indigo-500 mt-0.5 shrink-0" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
        </svg>
        <p className="text-sm text-indigo-700">
          Click <span className="font-semibold">Show Answer</span> after attempting each question on your own for best results.
        </p>
      </div>

      {/* Sections */}
      {SECTIONS.map(({ key, label, marks, color }) => {
        const questions = data[key];
        if (!questions.length) return null;
        return (
          <div key={key} className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
            {/* Section header */}
            <div className={`flex items-center justify-between px-6 py-4 border-b ${COLOR_MAP[color]}`}>
              <div className="flex items-center gap-3">
                <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${BADGE_MAP[color]}`}>
                  {marks}
                </span>
                <h2 className="font-semibold text-slate-800">{label} Questions</h2>
              </div>
              <span className="text-xs text-slate-400">{questions.length} questions</span>
            </div>

            {/* Questions */}
            <div className="divide-y divide-slate-100">
              {questions.map((q, i) => {
                const id = `${key}-${i}`;
                return (
                  <div key={i} className="px-6 py-5">
                    {/* Question */}
                    <div className="flex items-start gap-3 mb-3">
                      <span className="shrink-0 w-6 h-6 bg-slate-100 text-slate-500 text-xs font-bold rounded-full flex items-center justify-center mt-0.5">
                        {i + 1}
                      </span>
                      <p className="text-slate-800 font-medium text-sm leading-relaxed">{q.question}</p>
                    </div>

                    {/* Toggle answer */}
                    <div className="ml-9">
                      <button
                        onClick={() => toggleAnswer(id)}
                        className="text-xs font-medium text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
                      >
                        {expanded[id] ? (
                          <>
                            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                            </svg>
                            Hide Answer
                          </>
                        ) : (
                          <>
                            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                            </svg>
                            Show Answer
                          </>
                        )}
                      </button>

                      {expanded[id] && (
                        <div className="mt-3 bg-slate-50 border border-slate-200 rounded-xl px-4 py-3">
                          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Model Answer</p>
                          <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">{q.answer}</p>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}
