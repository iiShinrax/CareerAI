const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const inFlightRequests = new Map();

function authHeaders() {
  const token = localStorage.getItem("careerai_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request(path, { method = "GET", body, form = false } = {}) {
  const headers = { ...authHeaders() };
  let payload = body;
  if (body && !form) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }
  let res;
  try {
    res = await fetch(`${BASE_URL}${path}`, { method, headers, body: payload });
  } catch {
    throw new Error("CareerAI is unavailable. Check that the API is running and try again.");
  }
  if (!res.ok) {
    let detail = res.statusText;
    try { detail = (await res.json()).detail || detail; } catch { /* keep status text */ }
    const error = new Error(detail);
    error.status = res.status;
    throw error;
  }
  return res.status === 204 ? null : res.json();
}

function dedupeRequest(key, callback) {
  const existing = inFlightRequests.get(key);
  if (existing) return existing;
  const pending = callback().finally(() => inFlightRequests.delete(key));
  inFlightRequests.set(key, pending);
  return pending;
}

export async function signup({ name, email, password }) { return request("/api/auth/signup", { method: "POST", body: { name, email, password } }); }
export async function login({ email, password }) {
  const form = new URLSearchParams();
  form.set("username", email); form.set("password", password);
  const data = await request("/api/auth/login", { method: "POST", body: form, form: true });
  localStorage.setItem("careerai_token", data.access_token);
  return data;
}
export function logout() { localStorage.removeItem("careerai_token"); }
export async function getCurrentUser() { return request("/api/auth/me"); }
export async function getProfile() { return request("/api/profile/me"); }
export async function updateProfile(payload) { return request("/api/profile/me", { method: "PUT", body: payload }); }
export async function listSkills() { return request("/api/profile/skills"); }
export async function addSkill(payload) { return request("/api/profile/skills", { method: "POST", body: payload }); }
export async function deleteSkill(skillId) { return request(`/api/profile/skills/${skillId}`, { method: "DELETE" }); }

export async function uploadCV(file) {
  const form = new FormData(); form.append("file", file);
  return request("/api/cv/upload", { method: "POST", body: form, form: true });
}
export async function matchJob(jobDescription) { return request("/api/jobs/match", { method: "POST", body: { description: jobDescription } }); }
export function getRoadmap() { return dedupeRequest("roadmap", () => request("/api/roadmap/me")); }
export function analyzeCareer() { return dedupeRequest("career-analysis", () => request("/api/career/analyze", { method: "POST" })); }
export function startInterview() { return dedupeRequest("interview-start", () => request("/api/interview/start", { method: "POST" })); }
export async function sendChatMessage(message, sessionId) { return request("/api/chat/message", { method: "POST", body: { message, session_id: sessionId || null } }); }
export async function submitInterview(interviewId, answers) { return request(`/api/interview/${interviewId}/submit`, { method: "POST", body: { answers } }); }
export async function getEvaluation(interviewId) { return request(`/api/evaluation/${interviewId}`); }
