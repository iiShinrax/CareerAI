import { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Auth() {
  const location = useLocation();
  const isSignup = location.pathname === "/signup";
  const navigate = useNavigate();
  const { login, signup } = useAuth();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      if (isSignup) {
        await signup(name, email, password);
      } else {
        await login(email, password);
      }
      navigate("/dashboard");
    } catch (err) {
      setError(err.message || "Something went wrong");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-6">
      <div className="w-full max-w-sm">
        <Link to="/" className="font-display italic text-2xl block text-center mb-10">
          CareerAI
        </Link>

        <div className="bg-surface border border-line p-8">
          <h1 className="text-lg text-paper mb-1">
            {isSignup ? "Create your account" : "Welcome back"}
          </h1>
          <p className="text-sm text-muted mb-6">
            {isSignup
              ? "Set up your profile to get a personalized readiness score."
              : "Log in to see your dashboard."}
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            {isSignup && (
              <div>
                <label className="block text-xs text-muted mb-1.5">Name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-ink border border-line rounded-sm px-3 py-2 text-sm text-paper focus:border-amber outline-none"
                />
              </div>
            )}
            <div>
              <label className="block text-xs text-muted mb-1.5">Email</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-ink border border-line rounded-sm px-3 py-2 text-sm text-paper focus:border-amber outline-none"
              />
            </div>
            <div>
              <label className="block text-xs text-muted mb-1.5">Password</label>
              <input
                type="password"
                required
                minLength={6}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-ink border border-line rounded-sm px-3 py-2 text-sm text-paper focus:border-amber outline-none"
              />
            </div>

            {error && <p className="text-sm text-coral">{error}</p>}

            <button
              type="submit"
              disabled={submitting}
              className="w-full bg-amber text-ink py-2.5 rounded-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
            >
              {submitting ? "Please wait…" : isSignup ? "Create account" : "Log in"}
            </button>
          </form>

          <p className="text-sm text-muted mt-6 text-center">
            {isSignup ? (
              <>
                Already have an account?{" "}
                <Link to="/login" className="text-paper hover:text-amber">
                  Log in
                </Link>
              </>
            ) : (
              <>
                New here?{" "}
                <Link to="/signup" className="text-paper hover:text-amber">
                  Create an account
                </Link>
              </>
            )}
          </p>
        </div>
      </div>
    </div>
  );
}
