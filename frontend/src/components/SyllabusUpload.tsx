import { useRef, useState } from "react";
import { uploadSyllabus } from "../api/studium";
import type { UploadResult } from "../api/studium";

interface Props {
  onResult: (result: UploadResult) => void;
}

const PRESETS = [7, 14, 30, 60, 90];

function computeEndDate(days: number): string {
  const d = new Date();
  let added = 0;
  while (added < days) {
    d.setDate(d.getDate() + 1);
    if (d.getDay() !== 0 && d.getDay() !== 6) added++;
  }
  return d.toLocaleDateString("en-US", {
    month: "long", day: "numeric", year: "numeric",
  });
}

export default function SyllabusUpload({ onResult }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [days, setDays] = useState(30);
  const [customDays, setCustomDays] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const activeDays = customDays !== "" ? parseInt(customDays) || 30 : days;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const result = await uploadSyllabus(file, activeDays);
      onResult(result);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Upload failed. Is the backend running?";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-xl mx-auto">
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">

        {/* Card header */}
        <div className="bg-indigo-50 dark:bg-indigo-950/40 border-b border-indigo-100 dark:border-indigo-900/50 px-8 py-5">
          <h2 className="text-lg font-semibold text-indigo-900 dark:text-indigo-200">Upload Syllabus</h2>
          <p className="text-sm text-indigo-600 dark:text-indigo-400 mt-0.5">
            AI will extract topics and build your personalised schedule
          </p>
        </div>

        <form onSubmit={handleSubmit} className="px-8 py-6 space-y-6">

          {/* File picker */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-200 mb-2">
              Syllabus Document <span className="text-red-400">*</span>
            </label>
            <button
              type="button"
              onClick={() => inputRef.current?.click()}
              className={`w-full border-2 border-dashed rounded-xl px-6 py-8 text-center transition-colors ${
                file
                  ? "border-indigo-300 bg-indigo-50"
                  : "border-slate-200 dark:border-slate-700 hover:border-indigo-300 hover:bg-slate-50"
              }`}
            >
              {file ? (
                <div className="flex items-center justify-center gap-3">
                  <svg className="w-5 h-5 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <span className="text-sm font-medium text-indigo-700 dark:text-indigo-300">{file.name}</span>
                  <span className="text-xs text-indigo-400">
                    ({(file.size / 1024).toFixed(0)} KB)
                  </span>
                </div>
              ) : (
                <div className="space-y-2">
                  <svg className="w-8 h-8 text-slate-300 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                  </svg>
                  <p className="text-sm text-slate-400">Click to upload PDF</p>
                </div>
              )}
            </button>
            <input
              ref={inputRef}
              type="file"
              accept=".pdf"
              className="hidden"
              onChange={(e) => { setFile(e.target.files?.[0] ?? null); setError(null); }}
            />
          </div>

          {/* Duration */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-200 mb-2">
              Study Duration
            </label>
            <div className="flex gap-2 flex-wrap mb-3">
              {PRESETS.map((p) => (
                <button
                  key={p}
                  type="button"
                  onClick={() => { setDays(p); setCustomDays(""); }}
                  className={`px-4 py-1.5 rounded-lg text-sm font-medium border transition-colors ${
                    activeDays === p
                      ? "bg-indigo-600 text-white border-indigo-600"
                      : "bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:border-indigo-300 hover:text-indigo-600"
                  }`}
                >
                  {p} days
                </button>
              ))}
              <input
                type="number"
                min={1}
                max={365}
                placeholder="Custom"
                value={customDays}
                onChange={(e) => setCustomDays(e.target.value)}
                className="w-24 px-3 py-1.5 rounded-lg text-sm border border-slate-200 dark:border-slate-700 focus:outline-none focus:border-indigo-400 text-slate-700 dark:text-slate-200 placeholder-slate-300"
              />
            </div>
            <p className="text-xs text-slate-400">
              Target completion:{" "}
              <span className="font-medium text-slate-600 dark:text-slate-300">{computeEndDate(activeDays)}</span>
              <span className="ml-1 text-slate-400">({activeDays} study days, weekends excluded)</span>
            </p>
          </div>

          {error && (
            <div className="flex items-start gap-2 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 rounded-lg px-4 py-3">
              <svg className="w-4 h-4 text-red-400 mt-0.5 shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={!file || loading}
            className="w-full bg-indigo-600 text-white rounded-xl py-3 text-sm font-semibold hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
                Analysing syllabus…
              </>
            ) : (
              "Generate Study Plan"
            )}
          </button>

          {loading && (
            <p className="text-center text-xs text-slate-400 animate-pulse">
              Extracting topics and building your {activeDays}-day schedule…
            </p>
          )}
        </form>
      </div>
    </div>
  );
}
