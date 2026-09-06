export default function BigNumber({ value, unit = "%", label, accent = "amber", size = "lg" }) {
  const accentColor = { amber: "#F0A84B", teal: "#5FD3C4", coral: "#E8646B" }[accent];
  const sizeClass = size === "lg" ? "text-7xl" : "text-4xl";

  return (
    <div>
      <div className={`font-mono ${sizeClass} leading-none`} style={{ color: accentColor }}>
        {value}
        <span className="text-2xl align-top ml-1">{unit}</span>
      </div>
      {label && <div className="text-sm text-muted mt-2">{label}</div>}
    </div>
  );
}
