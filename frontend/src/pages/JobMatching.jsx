import { useState } from "react";
import Layout from "../components/Layout";
import Panel from "../components/Panel";
import ProgressBar from "../components/ProgressBar";
import * as api from "../lib/api";

export default function JobMatching() {
  const [description, setDescription] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    if (!description.trim()) return;
    setLoading(true);
    setError("");
    try {
      const data = await api.matchJob(description);
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Layout>
      <h1 className="font-display text-3xl mb-1">Job matching</h1>
      <p className="text-muted text-sm mb-8">
        Paste a job description to see how your profile stacks up against it.
      </p>

      <form onSubmit={handleSubmit} className="mb-8">
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Paste a job description here"
          rows={8}
          className="w-full bg-surface border border-line rounded-sm px-4 py-3 text-sm text-paper focus:border-amber outline-none resize-none mb-3"
        />
        <button
          type="submit"
          disabled={loading}
          className="bg-amber text-ink px-6 py-2.5 rounded-sm text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
        >
          {loading ? "Matching…" : "Check match"}
        </button>
        {loading && <p className="text-sm text-muted mt-3">Loading the local career models. The first match can take up to a minute; later matches are faster.</p>}
        {error && <p className="text-sm text-coral mt-3">{error}</p>}
      </form>

      {result && (
        <div className="space-y-6">
          <Panel accent="amber">
            <p className="text-sm text-muted mb-2">Job match</p>
            <p className="font-mono text-6xl text-amber mb-3">{result.match_percent}%</p>
            <ProgressBar value={result.match_percent} accent="amber" showValue={false} />
          </Panel>

          <div className="grid md:grid-cols-2 gap-6">
            <Panel title="Matched skills" accent="teal">
              <ul className="space-y-2">
                {result.matched_skills?.map((s, index) => (
                  <li key={`${s}-${index}`} className="text-sm text-paper flex items-center gap-2">
                    <span className="text-teal font-mono">✓</span>
                    {s}
                  </li>
                ))}
              </ul>
            </Panel>
            <Panel title="Missing" accent="coral">
              <ul className="space-y-2">
                {result.missing_skills?.map((s, index) => (
                  <li key={`${s}-${index}`} className="text-sm text-muted flex items-center gap-2">
                    <span className="text-coral font-mono">✗</span>
                    {s}
                  </li>
                ))}
              </ul>
            </Panel>
          </div>

          <Panel title="Recommendation" accent="amber">
            <p className="text-sm text-paper leading-relaxed">{result.recommendation}</p>
          </Panel>
        </div>
      )}
    </Layout>
  );
}
