import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import Layout from "../components/Layout";
import Panel from "../components/Panel";
import ProgressBar from "../components/ProgressBar";
import BigNumber from "../components/BigNumber";
import * as api from "../lib/api";

export default function InterviewResults() {
  const { interviewId } = useParams();
  const [data, setData] = useState(null);

  useEffect(() => {
    api.getEvaluation(interviewId).then(setData);
  }, [interviewId]);

  if (!data) {
    return (
      <Layout>
        <p className="text-muted text-sm">Scoring your interview…</p>
      </Layout>
    );
  }

  return (
    <Layout>
      <h1 className="font-display text-3xl mb-1">Interview results</h1>
      <p className="text-muted text-sm mb-8">Here's how that session broke down.</p>

      <Panel accent="amber" className="mb-6 text-center">
        <BigNumber value={data.score} label="Overall score" accent="amber" />
      </Panel>

      <Panel title="Breakdown" accent="teal" className="mb-6">
        <div className="space-y-4">
          <ProgressBar label="Technical" value={data.technical_score} accent="teal" />
          <ProgressBar label="Communication" value={data.communication_score} accent="teal" />
          <ProgressBar label="Projects" value={data.projects_score} accent="teal" />
          <ProgressBar label="Problem solving" value={data.problem_solving_score} accent="teal" />
        </div>
      </Panel>

      <div className="grid md:grid-cols-2 gap-6 mb-8">
        <Panel title="Strengths" accent="teal">
          <ul className="space-y-2">
            {data.strengths?.map((s) => (
              <li key={s} className="text-sm text-paper flex gap-2">
                <span className="text-teal font-mono">✓</span>
                {s}
              </li>
            ))}
          </ul>
        </Panel>
        <Panel title="Improve" accent="coral">
          <ul className="space-y-2">
            {data.improvements?.map((s) => (
              <li key={s} className="text-sm text-muted flex gap-2">
                <span className="text-coral font-mono">⚠</span>
                {s}
              </li>
            ))}
          </ul>
        </Panel>
      </div>

      <Link
        to="/interview"
        className="inline-block bg-amber text-ink px-6 py-3 rounded-sm text-sm font-medium hover:opacity-90 transition-opacity"
      >
        Practice again
      </Link>
    </Layout>
  );
}
