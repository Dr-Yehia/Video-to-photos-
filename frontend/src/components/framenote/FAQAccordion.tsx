import { useState } from "react";
import { ChevronDown } from "lucide-react";

const FAQS = [
  { q: "What is FrameNote AI?", a: "A smart video-to-visual-notes tool that converts YouTube links and uploaded videos into clean screenshots, PDFs, and image packs." },
  { q: "How is it different from normal screenshot tools?", a: "Normal tools capture frames at fixed intervals. FrameNote AI detects completed visual moments and removes duplicates." },
  { q: "Can I convert YouTube videos to PDF?", a: "Yes. Paste a public YouTube link and generate a clean PDF from selected visual frames." },
  { q: "Can I upload my own videos?", a: "Yes. Supported formats include MP4, MOV, WEBM, and MKV." },
  { q: "Does it work for whiteboard or tablet lectures?", a: "Yes. It is designed for lectures where content appears gradually." },
  { q: "Can I remove unwanted frames?", a: "Yes. You can preview, select, remove, and reorder frames before export." },
  { q: "Does it support PowerPoint?", a: "PPT export is coming soon as a Pro feature." },
  { q: "Is there a free plan?", a: "Yes. You can try short conversions for free." },
  { q: "Is my content private?", a: "Videos are handled through secure processing flows and temporary files are automatically removed based on your plan." },
  { q: "Can I use copyrighted videos?", a: "You should only process content you own or have permission to use." },
];

export function FAQAccordion() {
  const [open, setOpen] = useState<number | null>(0);
  return (
    <div className="mx-auto max-w-3xl space-y-3">
      {FAQS.map((f, i) => {
        const isOpen = open === i;
        return (
          <div key={f.q} className={`rounded-2xl border transition-all ${isOpen ? "border-brand/30 bg-white shadow-elevated" : "border-border bg-white shadow-card"}`}>
            <button
              onClick={() => setOpen(isOpen ? null : i)}
              className="flex w-full items-center justify-between gap-4 px-5 py-4 text-left"
            >
              <span className="text-sm sm:text-base font-semibold text-ink">{f.q}</span>
              <ChevronDown className={`h-4 w-4 shrink-0 text-ink-subtle transition-transform ${isOpen ? "rotate-180 text-brand" : ""}`} />
            </button>
            {isOpen && (
              <div className="px-5 pb-5 text-sm text-ink-muted leading-relaxed">{f.a}</div>
            )}
          </div>
        );
      })}
    </div>
  );
}
