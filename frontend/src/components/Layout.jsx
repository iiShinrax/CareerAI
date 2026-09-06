import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/profile", label: "Profile" },
  { to: "/cv", label: "CV" },
  { to: "/jobs", label: "Job matching" },
  { to: "/roadmap", label: "Roadmap" },
  { to: "/chat", label: "Chat" },
  { to: "/interview", label: "Interview" },
];

export default function Layout({ children }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/");
  }

  return (
    <div className="min-h-screen flex">
      <aside className="w-56 shrink-0 border-r border-line flex flex-col">
        <div className="px-6 py-6 border-b border-line">
          <span className="font-display italic text-2xl text-paper">CareerAI</span>
        </div>

        <nav className="flex-1 py-4">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `block px-6 py-2.5 text-sm border-l-[3px] transition-colors ${
                  isActive
                    ? "border-amber text-paper bg-surface"
                    : "border-transparent text-muted hover:text-paper hover:border-line"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="px-6 py-5 border-t border-line">
          <div className="text-sm text-paper mb-1">{user?.name}</div>
          <div className="text-xs text-muted mb-3 truncate">{user?.email}</div>
          <button
            onClick={handleLogout}
            className="text-xs text-muted hover:text-coral transition-colors"
          >
            Log out
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto">
        <div className="max-w-4xl px-10 py-10">{children}</div>
      </main>
    </div>
  );
}
