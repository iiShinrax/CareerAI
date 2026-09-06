export default function Panel({ title, accent = "amber", children, className = "" }) {
  const accentColor = { amber: "#F0A84B", teal: "#5FD3C4", coral: "#E8646B" }[accent];

  return (
    <div className={`bg-surface border border-line ${className}`}>
      {title && (
        <div
          className="px-5 py-3 border-b border-line flex items-center gap-3"
          style={{ borderLeft: `3px solid ${accentColor}` }}
        >
          <h3 className="font-sans text-sm text-paper tracking-wide">{title}</h3>
        </div>
      )}
      <div className={title ? "p-5" : "p-5 border-l-[3px]"} style={!title ? { borderLeftColor: accentColor } : {}}>
        {children}
      </div>
    </div>
  );
}
