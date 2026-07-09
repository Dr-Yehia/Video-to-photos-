import { Check, FileText, Sparkles, X, Youtube } from "lucide-react";

/**
 * A CSS/SVG 3D-style hero composition:
 * floating video player + frame cards + PDF preview + AI scan glow.
 */
export function HeroVisual() {
  return (
    <div className="relative aspect-[5/5] sm:aspect-[6/5] lg:aspect-square w-full">
      {/* soft glow backdrop */}
      <div className="absolute inset-0 -z-10">
        <div className="absolute left-1/2 top-1/2 h-[80%] w-[80%] -translate-x-1/2 -translate-y-1/2 rounded-full bg-gradient-brand opacity-15 blur-3xl" />
      </div>

      {/* Video player card */}
      <div
        className="absolute left-1/2 top-1/2 w-[78%] -translate-x-[62%] -translate-y-[54%] rounded-3xl bg-white shadow-elevated border border-border p-3 animate-float"
        style={{ transform: "translate(-62%, -54%) perspective(1200px) rotateY(-8deg) rotateX(4deg)" }}
      >
        <div className="relative aspect-video rounded-2xl bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 overflow-hidden">
          {/* scan line */}
          <div className="absolute inset-x-0 h-16 bg-gradient-to-b from-transparent via-brand/40 to-transparent animate-scan" />
          {/* whiteboard mock */}
          <div className="absolute inset-6 rounded-xl bg-white/95 p-4">
            <div className="h-2 w-24 rounded-full bg-slate-900/80 mb-3" />
            <div className="space-y-1.5">
              <div className="h-1.5 w-32 rounded-full bg-slate-300" />
              <div className="h-1.5 w-40 rounded-full bg-slate-300" />
              <div className="h-1.5 w-28 rounded-full bg-brand/70" />
            </div>
            <div className="mt-3 flex items-end gap-1 h-8">
              {[3, 6, 4, 7, 5, 8, 6].map((h, i) => (
                <div key={i} className="w-1.5 rounded-t bg-gradient-brand" style={{ height: `${h * 4}px` }} />
              ))}
            </div>
          </div>
          {/* play chip */}
          <div className="absolute left-3 top-3 flex items-center gap-1.5 rounded-full bg-black/50 px-2 py-1 text-[10px] text-white backdrop-blur">
            <Youtube className="h-3 w-3 text-red-400" />
            YouTube URL
          </div>
        </div>
        {/* timeline */}
        <div className="mt-3 px-2">
          <div className="relative h-1.5 rounded-full bg-slate-100">
            <div className="absolute inset-y-0 left-0 w-2/5 rounded-full bg-gradient-brand" />
            {[15, 32, 55, 72].map((p) => (
              <div key={p} className="absolute -top-1 h-3.5 w-3.5 -translate-x-1/2 rounded-full bg-white border-2 border-brand shadow-card" style={{ left: `${p}%` }} />
            ))}
          </div>
          <div className="mt-2 flex items-center justify-between text-[10px] text-ink-subtle">
            <span>00:00</span>
            <span className="flex items-center gap-1 text-brand font-semibold">
              <Sparkles className="h-3 w-3" /> Smart Capture
            </span>
            <span>42:18</span>
          </div>
        </div>
      </div>

      {/* Best completed frame card */}
      <div className="absolute right-2 top-[6%] w-[46%] rounded-2xl bg-white shadow-glow border border-brand/30 p-2.5 animate-float-alt"
        style={{ transform: "perspective(900px) rotateY(6deg) rotateX(-3deg)" }}
      >
        <div className="relative aspect-video rounded-xl bg-gradient-to-br from-blue-50 to-violet-50 overflow-hidden">
          <div className="absolute inset-3 rounded-lg bg-white/90 p-2">
            <div className="h-1.5 w-16 rounded-full bg-ink mb-1.5" />
            <div className="space-y-1">
              <div className="h-1 w-full rounded bg-slate-200" />
              <div className="h-1 w-4/5 rounded bg-slate-200" />
              <div className="h-1 w-3/5 rounded bg-brand" />
            </div>
          </div>
          <span className="absolute right-2 top-2 inline-flex items-center gap-1 rounded-full bg-success/95 px-2 py-0.5 text-[9px] font-semibold text-white">
            <Check className="h-2.5 w-2.5" /> Best
          </span>
        </div>
        <div className="mt-2 px-1 pb-0.5 text-[10px] font-medium text-ink-muted">
          Best completed frame captured
        </div>
      </div>

      {/* Duplicate removed card */}
      <div className="absolute left-[4%] bottom-[18%] w-[38%] rounded-2xl bg-white shadow-card border border-border p-2 animate-float"
        style={{ transform: "perspective(900px) rotateY(-10deg) rotateX(3deg)" }}
      >
        <div className="relative aspect-video rounded-lg bg-slate-100 overflow-hidden">
          <div className="absolute inset-0 bg-white/60" />
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="inline-flex items-center gap-1 rounded-full bg-white/95 px-2 py-1 text-[10px] font-semibold text-destructive border border-destructive/20">
              <X className="h-3 w-3" /> Duplicate removed
            </span>
          </div>
        </div>
      </div>

      {/* PDF preview */}
      <div className="absolute right-[4%] bottom-[8%] w-[42%] rounded-2xl bg-white shadow-elevated border border-border p-3 animate-float-alt"
        style={{ transform: "perspective(900px) rotateY(10deg) rotateX(-2deg)" }}
      >
        <div className="flex items-center gap-2 mb-2">
          <div className="h-7 w-7 rounded-lg bg-gradient-to-br from-brand/10 to-violet/10 flex items-center justify-center">
            <FileText className="h-3.5 w-3.5 text-brand" />
          </div>
          <div>
            <div className="text-[10px] font-semibold text-ink">notes.pdf</div>
            <div className="text-[9px] text-ink-subtle">12 pages · 1.2 MB</div>
          </div>
        </div>
        <div className="aspect-[3/4] rounded-lg bg-soft p-2 space-y-1.5">
          <div className="h-1.5 w-3/4 rounded bg-ink" />
          <div className="h-1 w-full rounded bg-slate-200" />
          <div className="h-1 w-5/6 rounded bg-slate-200" />
          <div className="mt-1.5 aspect-video rounded bg-gradient-to-br from-blue-100 to-violet-100" />
          <div className="h-1 w-full rounded bg-slate-200" />
          <div className="h-1 w-2/3 rounded bg-slate-200" />
        </div>
        <div className="mt-2 inline-flex items-center gap-1 rounded-full bg-accent px-2 py-0.5 text-[9px] font-semibold text-brand">
          <Sparkles className="h-2.5 w-2.5" /> Smart PDF Notes
        </div>
      </div>

      {/* Floating micro-labels */}
      <div className="absolute left-[10%] top-[10%] rounded-full bg-white shadow-card border border-border px-2.5 py-1 text-[10px] font-medium text-ink-muted animate-float">
        No Duplicates
      </div>
      <div className="absolute right-[38%] top-[42%] rounded-full bg-white shadow-card border border-border px-2.5 py-1 text-[10px] font-medium text-ink-muted animate-float-alt">
        Clean PDF
      </div>
    </div>
  );
}
