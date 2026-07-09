import { Check, X, Minus } from "lucide-react";

const ROWS: [string, boolean | "partial", boolean | "partial", boolean | "partial"][] = [
  ["Captures completed explanations", true, false, false],
  ["Removes duplicate frames", true, false, false],
  ["Works with whiteboard and tablet lectures", true, "partial", false],
  ["Creates clean PDFs", true, "partial", "partial"],
  ["Allows manual frame review", true, false, false],
  ["Supports visual learning content", true, "partial", false],
  ["Designed for lectures, tutorials, webinars, and screen recordings", true, false, false],
];

function Cell({ v }: { v: boolean | "partial" }) {
  if (v === true) return <Check className="h-5 w-5 text-success mx-auto" />;
  if (v === "partial") return <Minus className="h-5 w-5 text-ink-subtle mx-auto" />;
  return <X className="h-5 w-5 text-ink-subtle/60 mx-auto" />;
}

export function ComparisonTable() {
  return (
    <div className="rounded-3xl border border-border bg-white shadow-card overflow-hidden">
      <div className="grid grid-cols-4 bg-soft text-sm font-semibold text-ink border-b border-border">
        <div className="px-4 sm:px-6 py-4">Feature</div>
        <div className="px-4 py-4 text-center text-brand">FrameNote AI</div>
        <div className="px-4 py-4 text-center text-ink-muted">Random screenshot tools</div>
        <div className="px-4 py-4 text-center text-ink-muted">Text-only note tools</div>
      </div>
      {ROWS.map(([label, a, b, c], i) => (
        <div key={label as string} className={`grid grid-cols-4 items-center text-sm ${i % 2 ? "bg-white" : "bg-soft/40"}`}>
          <div className="px-4 sm:px-6 py-4 text-ink-muted">{label as string}</div>
          <div className="px-4 py-4 border-l border-border/60 bg-brand/5"><Cell v={a as boolean | "partial"} /></div>
          <div className="px-4 py-4 border-l border-border/60"><Cell v={b as boolean | "partial"} /></div>
          <div className="px-4 py-4 border-l border-border/60"><Cell v={c as boolean | "partial"} /></div>
        </div>
      ))}
    </div>
  );
}
