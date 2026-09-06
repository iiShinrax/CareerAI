export default function ProgressBar({ label, value, accent = "amber", showValue = true }) {
  const accentColor = { amber: "#F0A84B", teal: "#5FD3C4", coral: "#E8646B" }[accent];

  return (
    <div>
      {label && (
        <div className="flex items-baseline justify-between mb-1.5">
          <span className="text-sm text-muted">{label}</span>
          {showValue && <span className="font-mono text-sm text-paper">{value}%</span>}
        </div>
      )}
      <div className="ledger-bar w-full">
        <div
          className="ledger-fill transition-all duration-700 ease-out"
          style={{ width: `${Math.min(100, Math.max(0, value))}%`, background: accentColor }}
        />
      </div>
    </div>
  );
}
