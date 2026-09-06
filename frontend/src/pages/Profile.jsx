import { useEffect, useState } from "react";
import Layout from "../components/Layout";
import Panel from "../components/Panel";
import * as api from "../lib/api";
import { useAuth } from "../context/AuthContext";

export default function Profile() {
  const { user, setUser } = useAuth();
  const [form, setForm] = useState({
    education: "",
    experience: "",
    target_role: "",
    career_goals: "",
  });
  const [skills, setSkills] = useState([]);
  const [newSkill, setNewSkill] = useState("");
  const [newLevel, setNewLevel] = useState("intermediate");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (user) {
      setForm({
        education: user.education || "",
        experience: user.experience || "",
        target_role: user.target_role || "",
        career_goals: user.career_goals || "",
      });
    }
    api.listSkills().then(setSkills).catch(() => {});
  }, [user]);

  async function handleSave(e) {
    e.preventDefault();
    const updated = await api.updateProfile(form);
    setUser(updated);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  async function handleAddSkill(e) {
    e.preventDefault();
    if (!newSkill.trim()) return;
    const skill = await api.addSkill({ skill: newSkill.trim(), level: newLevel });
    setSkills((s) => [...s, skill]);
    setNewSkill("");
  }

  async function handleRemoveSkill(id) {
    await api.deleteSkill(id);
    setSkills((s) => s.filter((sk) => sk.id !== id));
  }

  return (
    <Layout>
      <h1 className="font-display text-3xl mb-1">Profile</h1>
      <p className="text-muted text-sm mb-8">
        This is what your dashboard, job matches, and interview questions are built from.
      </p>

      <div className="space-y-6">
        <Panel title="Background" accent="amber">
          <form onSubmit={handleSave} className="space-y-4">
            <Field label="Target role">
              <input
                value={form.target_role}
                onChange={(e) => setForm({ ...form, target_role: e.target.value })}
                placeholder="e.g. Junior AI Engineer"
                className="input"
              />
            </Field>
            <Field label="Education">
              <textarea
                value={form.education}
                onChange={(e) => setForm({ ...form, education: e.target.value })}
                placeholder="Degree, university, graduation year"
                rows={2}
                className="input resize-none"
              />
            </Field>
            <Field label="Experience & projects">
              <textarea
                value={form.experience}
                onChange={(e) => setForm({ ...form, experience: e.target.value })}
                placeholder="Internships, projects, relevant work"
                rows={4}
                className="input resize-none"
              />
            </Field>
            <Field label="Career goals">
              <textarea
                value={form.career_goals}
                onChange={(e) => setForm({ ...form, career_goals: e.target.value })}
                placeholder="What you're aiming for over the next 1-2 years"
                rows={2}
                className="input resize-none"
              />
            </Field>

            <div className="flex items-center gap-3 pt-2">
              <button
                type="submit"
                className="bg-amber text-ink px-5 py-2 rounded-sm text-sm font-medium hover:opacity-90 transition-opacity"
              >
                Save changes
              </button>
              {saved && <span className="text-sm text-teal">Saved</span>}
            </div>
          </form>
        </Panel>

        <Panel title="Skills" accent="teal">
          <div className="flex flex-wrap gap-2 mb-4">
            {skills.map((s) => (
              <span
                key={s.id}
                className="inline-flex items-center gap-2 bg-surface2 border border-line px-3 py-1.5 rounded-sm text-sm"
              >
                {s.skill}
                <span className="text-muted text-xs font-mono">{s.level}</span>
                <button
                  onClick={() => handleRemoveSkill(s.id)}
                  className="text-muted hover:text-coral"
                  aria-label={`Remove ${s.skill}`}
                >
                  ×
                </button>
              </span>
            ))}
            {skills.length === 0 && (
              <p className="text-sm text-muted">No skills added yet.</p>
            )}
          </div>

          <form onSubmit={handleAddSkill} className="flex gap-2">
            <input
              value={newSkill}
              onChange={(e) => setNewSkill(e.target.value)}
              placeholder="Add a skill, e.g. Python"
              className="input flex-1"
            />
            <select
              value={newLevel}
              onChange={(e) => setNewLevel(e.target.value)}
              className="input w-36"
            >
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
            </select>
            <button
              type="submit"
              className="border border-line px-4 rounded-sm text-sm hover:border-teal hover:text-teal transition-colors"
            >
              Add
            </button>
          </form>
        </Panel>
      </div>

      <style>{`
        .input {
          width: 100%;
          background: #12141C;
          border: 1px solid #2E3241;
          border-radius: 4px;
          padding: 0.5rem 0.75rem;
          font-size: 0.875rem;
          color: #F1EEE4;
        }
        .input:focus { outline: none; border-color: #F0A84B; }
      `}</style>
    </Layout>
  );
}

function Field({ label, children }) {
  return (
    <div>
      <label className="block text-xs text-muted mb-1.5">{label}</label>
      {children}
    </div>
  );
}
