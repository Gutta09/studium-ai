import { useRef, useState } from "react";
import { uploadSyllabus } from "../api/studium";
import type { UploadResult } from "../api/studium";

interface Props {
  onResult: (result: UploadResult) => void;
}

export default function SyllabusUpload({ onResult }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0] ?? null;
    setSelectedFile(f);
    setError(null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedFile) return;

    setLoading(true);
    setError(null);

    try {
      const result = await uploadSyllabus(selectedFile);
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
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-8 max-w-lg mx-auto">
      <h2 className="text-2xl font-semibold text-slate-800 mb-1">
        Upload Your Syllabus
      </h2>
      <p className="text-slate-500 text-sm mb-6">
        The AI will extract topics and build a personalized study plan.
      </p>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        {/* Drop zone */}
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          className="border-2 border-dashed border-slate-300 rounded-xl p-8 text-center hover:border-violet-400 hover:bg-violet-50 transition-colors cursor-pointer"
        >
          {selectedFile ? (
            <span className="text-violet-600 font-medium">
              📄 {selectedFile.name}
            </span>
          ) : (
            <span className="text-slate-400">
              Click to select a PDF file
            </span>
          )}
        </button>

        <input
          ref={inputRef}
          type="file"
          accept=".pdf"
          onChange={handleFileChange}
          className="hidden"
        />

        {error && (
          <p className="text-red-500 text-sm bg-red-50 rounded-lg px-4 py-2">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={!selectedFile || loading}
          className="bg-violet-600 text-white rounded-xl py-3 px-6 font-medium hover:bg-violet-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? "Analyzing syllabus…" : "Generate Study Plan"}
        </button>

        {loading && (
          <p className="text-center text-slate-400 text-sm animate-pulse">
            Claude is extracting topics and building your schedule…
          </p>
        )}
      </form>
    </div>
  );
}
