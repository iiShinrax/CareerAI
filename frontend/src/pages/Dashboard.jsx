import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Layout from "../components/Layout";
import Panel from "../components/Panel";
import ProgressBar from "../components/ProgressBar";
import BigNumber from "../components/BigNumber";
import { useAuth } from "../context/AuthContext";
import * as api from "../lib/api";

export default function Dashboard() {
  const { user } = useAuth();
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => {
    if (!user) return;
    if (!user.target_role) {
      setError("Set a target role in your profile to see your career analysis.");
      return;
    }
    api.analyzeCareer().then(setAnalysis).catch((err) => setError(err.message));
  }, [user]);
  return <Layout>
    <h1 className="font-display text-3xl mb-1">Welcome back{user?.name ? `, ${user.name.split(" ")[0]}` : ""}.</h1>
    <p className="text-muted text-sm mb-8">Target role: <span className="text-paper">{user?.target_role || "Not set yet"}</span></p>
    {error && <p className="text-sm text-coral mb-6">{error} <Link to="/profile" className="underline">Open profile</Link></p>}
    {analysis && <>
      <div className="grid md:grid-cols-3 gap-6 mb-8">
        <Panel accent="amber"><BigNumber value={analysis.readiness_percent} label="Career readiness" accent="amber" /></Panel>
        <Panel title="Matched skills" accent="teal"><p className="font-mono text-2xl text-teal">{analysis.matched_skills.length}</p><p className="text-xs text-muted mt-1">aligned with this role</p></Panel>
        <Panel title="Skill gaps" accent="coral"><p className="font-mono text-2xl text-coral">{analysis.missing_skills.length}</p><p className="text-xs text-muted mt-1">to develop next</p></Panel>
      </div>
      <Panel title="Readiness" accent="amber" className="mb-8"><ProgressBar value={analysis.readiness_percent} accent="amber" /></Panel>
    </>}
    <div className="flex gap-4"><Link to="/jobs" className="bg-amber text-ink px-6 py-3 rounded-sm text-sm font-medium hover:opacity-90 transition-opacity">Analyze a job</Link><Link to="/interview" className="border border-line px-6 py-3 rounded-sm text-sm hover:border-teal hover:text-teal transition-colors">Practice interview</Link></div>
  </Layout>;
}
