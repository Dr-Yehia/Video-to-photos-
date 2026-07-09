import { Check, Clock, Download, FileText, Image as ImageIcon, Maximize2, Package, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";

const frames = [
  { t: "02:14", sel: true }, { t: "05:47", sel: true }, { t: "09:03", sel: false },
  { t: "12:31", sel: true }, { t: "18:22", sel: true }, { t: "24:10", sel: false },
  { t: "29:45", sel: true }, { t: "34:12", sel: true },
];

export function ResultsPreview() {
  return (
    <div className="rounded-3xl border border-border bg-white shadow-elevated overflow-hidden">
      {/* Top stats */}
      <div className="border-b border-border px-4 sm:px-6 py-4 bg-soft/50">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="text-xs text-ink-subtle">Results</div>
            <div className="text-base font-semibold text-ink truncate max-w-md">Organic Chemistry — Full Lecture 14</div>
          </div>
          <div className="flex flex-wrap items-center gap-2 text-[11px]">
            {[
              ["Source", "YouTube"], ["Duration", "48:12"], ["Quality", "1080p"],
              ["Captured", "34"], ["Duplicates removed", "127"], ["PDF pages", "34"],
            ].map(([k, v]) => (
              <span key={k} className="rounded-full bg-white border border-border px-2.5 py-1 text-ink-muted">
                <b className="text-ink font-semibold">{v}</b> · {k}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className="grid lg:grid-cols-[1fr_320px]">
        {/* Gallery */}
        <div className="p-4 sm:p-6 border-b lg:border-b-0 lg:border-r border-border">
          <div className="flex items-center justify-between mb-4">
            <div className="text-sm font-semibold text-ink">Captured frames</div>
            <div className="text-xs text-ink-subtle">Select · Reorder · Remove</div>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {frames.map((f, i) => (
              <div key={i} className={`group relative rounded-xl overflow-hidden border ${f.sel ? "border-brand shadow-glow" : "border-border"}`}>
                <div className="aspect-video bg-gradient-to-br from-blue-50 via-white to-violet-50 relative">
                  <div className="absolute inset-3 rounded-md bg-white/90 p-2 space-y-1">
                    <div className="h-1 w-2/3 rounded bg-ink" />
                    <div className="h-1 w-full rounded bg-slate-200" />
                    <div className="h-1 w-4/5 rounded bg-slate-200" />
                    <div className="h-1 w-1/2 rounded bg-brand" />
                  </div>
                  <span className="absolute left-1.5 top-1.5 inline-flex items-center gap-1 rounded-full bg-black/60 text-white text-[9px] px-1.5 py-0.5">
                    <Clock className="h-2.5 w-2.5" /> {f.t}
                  </span>
                  <span className={`absolute right-1.5 top-1.5 flex h-5 w-5 items-center justify-center rounded-md text-[10px] ${
                    f.sel ? "bg-gradient-brand text-white" : "bg-white border border-border text-ink-subtle"
                  }`}>
                    {f.sel && <Check className="h-3 w-3" />}
                  </span>
                  <div className="absolute inset-x-0 bottom-0 flex items-center justify-between px-1.5 py-1 bg-white/90 opacity-0 group-hover:opacity-100 transition">
                    <button className="p-1 rounded hover:bg-soft" title="Fullscreen"><Maximize2 className="h-3 w-3 text-ink-subtle" /></button>
                    <button className="p-1 rounded hover:bg-soft" title="Remove"><Trash2 className="h-3 w-3 text-destructive" /></button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Export sidebar */}
        <aside className="p-4 sm:p-6 space-y-4 bg-soft/40">
          <div>
            <div className="text-xs font-semibold text-ink-subtle uppercase tracking-wider mb-2">PDF layout</div>
            <div className="grid grid-cols-3 gap-2">
              {["One / page", "Compact", "Study notes"].map((l, i) => (
                <button key={l} className={`rounded-lg border px-2 py-2 text-[11px] font-medium ${
                  i === 2 ? "border-brand bg-white text-brand shadow-card" : "border-border bg-white text-ink-muted"
                }`}>{l}</button>
              ))}
            </div>
          </div>
          <label className="flex items-center justify-between rounded-lg bg-white border border-border px-3 py-2 text-sm text-ink-muted">
            Include timestamps <span className="h-4 w-7 rounded-full bg-gradient-brand relative"><span className="absolute right-0.5 top-0.5 h-3 w-3 rounded-full bg-white" /></span>
          </label>
          <label className="flex items-center justify-between rounded-lg bg-white border border-border px-3 py-2 text-sm text-ink-muted">
            Add cover page <span className="h-4 w-7 rounded-full bg-gradient-brand relative"><span className="absolute right-0.5 top-0.5 h-3 w-3 rounded-full bg-white" /></span>
          </label>
          <div>
            <div className="text-xs text-ink-subtle mb-1">Image quality</div>
            <div className="rounded-lg bg-white border border-border px-3 py-2 text-sm text-ink flex items-center justify-between">Best available <span className="text-ink-subtle text-xs">▾</span></div>
          </div>
          <div>
            <div className="text-xs text-ink-subtle mb-1">File name</div>
            <div className="rounded-lg bg-white border border-border px-3 py-2 text-sm text-ink">organic-chem-lecture-14</div>
          </div>
          <div className="space-y-2 pt-2">
            <Button className="w-full rounded-xl h-10 bg-gradient-brand text-white shadow-elevated">
              <Download className="h-4 w-4 mr-2" /> Download PDF
            </Button>
            <Button variant="outline" className="w-full rounded-xl h-10">
              <Package className="h-4 w-4 mr-2" /> Download ZIP
            </Button>
            <Button variant="outline" className="w-full rounded-xl h-10">
              <FileText className="h-4 w-4 mr-2" /> Save to Dashboard
            </Button>
            <button className="w-full text-xs text-ink-subtle hover:text-ink pt-1 inline-flex items-center justify-center gap-1">
              <ImageIcon className="h-3.5 w-3.5" /> Start New Conversion
            </button>
          </div>
        </aside>
      </div>
    </div>
  );
}
