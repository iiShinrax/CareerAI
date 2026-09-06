import { useState } from "react";
import Layout from "../components/Layout";
import Panel from "../components/Panel";
import ProgressBar from "../components/ProgressBar";
import * as api from "../lib/api";

export default function CVUpload() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [dragOver, setDragOver] = useState(false);

  async function analyze(selected) {
    setFile(selected);
    setLoading(true);
    try {
      const data = await api.uploadCV(selected);
      setResult(data);
    } finally {
      setLoading(false);
    }
  }

  function handleDrop(e) {
    e.preventDefault();
    setDragOver(false);
    const dropped = e.dataTransfer.files?.[0];
    if (dropped) analyze(dropped);
  }

  return (
    <Layout>
      <h1 className="font-display text-3xl mb-1">CV</h1>
      <p className="text-muted text-sm mb-8">
        Upload your CV as a PDF to get a score and specific improvements.
      </p>

      {!result && (
        <label
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          className={`block border-2 border-dashed rounded-sm px-8 py-16 text-center cursor-pointer transition-colors ${
            dragOver ? "border-amber bg-surface" : "border-line"
          }`}
        >
          <input
            type="file"
            accept=".pdf"
            className="hidden"
            onChange={(e) => e.target.files?.[0] && analyze(e.target.files[0])}
          />
          {loading ? (
            <p className="text-muted">Analyzing {file?.name}…</p>
          ) : (
            <>
              <p className="text-paper mb-1">Drop your CV here, or click to browse</p>
              <p className="text-sm text-muted">PDF only</p>
            </>
          )}
        </label>
      )}

      {result && (
        <div className="space-y-6">
          <Panel accent="amber">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted mb-1">{result.filename}</p>
                <p className="font-mono text-5xl text-amber">{result.score}%</p>
                <p className="text-sm text-muted mt-1">CV score</p>
              </div>
              <button
                onClick={() => {
                  setResult(null);
                  setFile(null);
                }}
                className="text-sm text-muted hover:text-paper border border-line px-4 py-2 rounded-sm"
              >
                Upload a different file
              </button>
            </div>
            <div className="mt-4">
              <ProgressBar value={result.score} accent="amber" showValue={false} />
            </div>
          </Panel>

          <Panel title="Skills detected" accent="teal">
            <div className="flex flex-wrap gap-2">
              {result.extracted_skills?.map((s, index) => (
                <span key={`${s}-${index}`} className="bg-surface2 border border-line px-3 py-1 rounded-sm text-sm">
                  {s}
                </span>
              ))}
            </div>
          </Panel>

          <Panel title="Weaknesses" accent="coral">
            <ul className="space-y-2">
              {result.weaknesses?.map((w, index) => (
                <li key={`${w}-${index}`} className="text-sm text-muted flex gap-2">
                  <span className="text-coral">·</span>
                  {w}
                </li>
              ))}
            </ul>
          </Panel>

          <Panel title="Recommendations" accent="amber">
            <ul className="space-y-2">
              {result.recommendations?.map((r, index) => (
                <li key={`${r}-${index}`} className="text-sm text-paper flex gap-2">
                  <span className="text-amber">·</span>
                  {r}
                </li>
              ))}
            </ul>
          </Panel>
        </div>
      )}
    </Layout>
  );
}
