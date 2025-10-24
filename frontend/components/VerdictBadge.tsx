interface VerdictBadgeProps {
  verdict: "pass" | "fail" | "needs_review" | string;
  confidence?: number;
  className?: string;
}

export default function VerdictBadge({ verdict, confidence, className = "" }: VerdictBadgeProps) {
  const getColors = () => {
    switch (verdict) {
      case "pass":
        return "bg-emerald-50 text-emerald-700 border-emerald-300";
      case "fail":
        return "bg-rose-50 text-rose-700 border-rose-300";
      case "needs_review":
        return "bg-amber-50 text-amber-700 border-amber-300";
      default:
        return "bg-slate-50 text-slate-700 border-slate-300";
    }
  };

  const getLabel = () => {
    switch (verdict) {
      case "pass":
        return "✓ PASS";
      case "fail":
        return "✗ FAIL";
      case "needs_review":
        return "⚠ NEEDS REVIEW";
      default:
        return verdict.toUpperCase();
    }
  };

  return (
    <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full border-2 font-semibold ${getColors()} ${className}`}>
      <span>{getLabel()}</span>
      {confidence !== undefined && (
        <span className="text-sm opacity-75">
          {(confidence * 100).toFixed(0)}%
        </span>
      )}
    </div>
  );
}
