import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Layout from "../components/Layout";
import Panel from "../components/Panel";
import ProgressBar from "../components/ProgressBar";
import * as api from "../lib/api";
import { useAuth } from "../context/AuthContext";

export default function Roadmap() {
  const { user } = useAuth();
  const [weeks, setWeeks] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!user) return;
    if (!user.target_role) {
      setError("Set a target role in your profile to build your roadmap.");
      return;
    }
    api.getRoadmap().then((data) => setWeeks(data.weeks)).catch((err) => setError(err.message));
  }, [user]);

  return (
    <Layout>
      <h1 className="font-display text-3xl mb-1">Your roadmap</h1>
      <p className="text-muted text-sm mb-8">
        A week-by-week plan for closing the gaps between where you are and your target role.
      </p>

      <Panel accent="amber">
        <div className="space-y-6">
          {error && <p className="text-sm text-coral">{error} <Link to="/profile" className="underline">Open profile</Link></p>}
          {weeks.map((w) => (
            <div key={w.label}>
              <ProgressBar label={`${w.label} · ${w.topic}`} value={w.progress} accent="amber" />
            </div>
          ))}
          {weeks.length === 0 && <p className="text-sm text-muted">Building your roadmap…</p>}
        </div>
      </Panel>
    </Layout>
  );
}
