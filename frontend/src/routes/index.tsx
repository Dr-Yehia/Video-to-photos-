import { createFileRoute } from "@tanstack/react-router";
import {
  ArrowRight, Battery, Boxes, Briefcase, CheckCircle2, ChevronRight, Clock, Cpu,
  FileText, FlaskConical, GraduationCap, Image as ImageIcon, Images, Layers, Lock,
  Package, PlayCircle, Presentation, RefreshCw, ScanLine, Search, Shield, ShieldCheck,
  Sparkles, Star, Trash2, Upload, Users, Video, Wand2, Youtube,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Navbar } from "@/components/framenote/Navbar";
import { HeroVisual } from "@/components/framenote/HeroVisual";
import { ConverterCard } from "@/components/framenote/ConverterCard";
import { Section } from "@/components/framenote/Section";
import { FAQAccordion } from "@/components/framenote/FAQAccordion";
import { Pricing } from "@/components/framenote/Pricing";
import { ComparisonTable } from "@/components/framenote/ComparisonTable";
import { DashboardPreview } from "@/components/framenote/DashboardPreview";
import { ResultsPreview } from "@/components/framenote/ResultsPreview";
import { Logo } from "@/components/framenote/Logo";

export const Route = createFileRoute("/")({
  component: Landing,
  head: () => ({
    scripts: [
      {
        type: "application/ld+json",
        children: JSON.stringify({
          "@context": "https://schema.org",
          "@type": "SoftwareApplication",
          name: "FrameNote AI",
          applicationCategory: "EducationApplication",
          operatingSystem: "Web",
          description:
            "Convert YouTube links and uploaded videos into clean visual notes, smart screenshots, PDFs, and image packs.",
          offers: { "@type": "Offer", price: "0", priceCurrency: "USD" },
        }),
      },
    ],
  }),
});

function Landing() {
  return (
    <div id="top" className="bg-background text-foreground">
      <Navbar />
      <Hero />
      <ConverterSection />
      <Problem />
      <Solution />
      <HowItWorks />
      <BeforeAfter />
      <UseCases />
      <Features />
      <OutputFormats />
      <DashboardSection />
      <ResultsSection />
      <Trust />
      <PricingSection />
      <Comparison />
      <Testimonials />
      <FAQSection />
      <SEOContent />
      <FinalCTA />
      <Footer />
    </div>
  );
}

/* -------------------------- HERO -------------------------- */

function Hero() {
  return (
    <section className="relative overflow-hidden bg-soft-hero">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 pt-14 sm:pt-20 pb-16 lg:pb-24">
        <div className="grid lg:grid-cols-2 gap-10 lg:gap-16 items-center">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-border bg-white px-3 py-1 text-xs font-semibold text-brand shadow-card">
              <Sparkles className="h-3.5 w-3.5" />
              Smart Completed-Frame Capture
            </div>
            <h1 className="mt-5 text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-ink leading-[1.05]">
              Convert Videos into{" "}
              <span className="text-gradient-brand">Clean Visual Notes</span>{" "}
              — Automatically
            </h1>
            <p className="mt-5 text-lg text-ink-muted max-w-xl leading-relaxed">
              FrameNote AI turns YouTube links and uploaded videos into smart screenshots,
              PDF notes, and organized image packs. It captures the completed explanation —
              not random frames.
            </p>

            <div className="mt-6 flex flex-col sm:flex-row gap-3">
              <Button className="h-12 rounded-full bg-gradient-brand text-white shadow-elevated hover:opacity-95 px-6 text-sm font-semibold">
                Start Free <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
              <Button variant="outline" className="h-12 rounded-full border-border px-6 text-sm font-semibold">
                <PlayCircle className="mr-2 h-4 w-4" /> See Smart Capture Demo
              </Button>
            </div>

            <p className="mt-4 text-xs text-ink-subtle">
              No manual screenshots. No duplicate frames. No messy PDFs.
            </p>

            {/* Small hero input */}
            <div className="mt-7 rounded-2xl border border-border bg-white shadow-card p-2 flex flex-col sm:flex-row gap-2">
              <div className="flex items-center gap-2 flex-1 px-3">
                <Youtube className="h-4 w-4 text-red-500 shrink-0" />
                <Input
                  placeholder="Paste a YouTube link…"
                  className="border-0 shadow-none focus-visible:ring-0 h-10 px-0 text-sm"
                />
              </div>
              <Button className="h-10 rounded-xl bg-gradient-brand text-white px-5 text-sm font-semibold">
                Convert
              </Button>
            </div>
            <p className="mt-2 text-[11px] text-ink-subtle pl-1">Try a short preview for free.</p>

            <div className="mt-8 flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-ink-muted">
              {[
                [Youtube, "YouTube links"],
                [Upload, "Video uploads"],
                [ScanLine, "Smart frame detection"],
                [Trash2, "Duplicate removal"],
                [FileText, "PDF export"],
              ].map(([Icon, label], i) => {
                const I = Icon as typeof Youtube;
                return (
                  <span key={i} className="inline-flex items-center gap-1.5 rounded-full bg-white/70 border border-border px-2.5 py-1">
                    <I className="h-3.5 w-3.5 text-brand" />
                    {label as string}
                  </span>
                );
              })}
            </div>
          </div>

          <div className="relative">
            <HeroVisual />
          </div>
        </div>
      </div>
    </section>
  );
}

/* -------------------- CONVERTER PREVIEW -------------------- */
function ConverterSection() {
  return (
    <Section
      id="converter"
      eyebrow="Live Converter"
      title="Turn any video into notes in one click"
      subtitle="Paste a link or upload a file. Choose quality. Let Smart Capture do the rest."
    >
      <div className="mx-auto max-w-3xl">
        <ConverterCard />
      </div>
    </Section>
  );
}

/* -------------------------- PROBLEM ------------------------- */
function Problem() {
  const items = [
    { icon: RefreshCw, title: "Random frames", desc: "Most tools capture frames at fixed intervals, even when the board is half-written." },
    { icon: Images, title: "Too many duplicates", desc: "A single lecture can create hundreds of repeated images." },
    { icon: Clock, title: "Missed final explanations", desc: "The most valuable moment is often when the instructor finishes writing." },
    { icon: Boxes, title: "Messy study files", desc: "Scattered screenshots are hard to review, share, and print." },
  ];
  return (
    <Section
      eyebrow="The Problem"
      title="Manual screenshots waste hours"
      subtitle="Video is not designed for note-taking. Old tools try to fix it with brute force. They fail."
      className="bg-soft/60"
    >
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {items.map((i) => (
          <div key={i.title} className="rounded-2xl bg-white border border-border shadow-card p-6">
            <div className="h-10 w-10 rounded-xl bg-destructive/10 flex items-center justify-center mb-4">
              <i.icon className="h-5 w-5 text-destructive" />
            </div>
            <div className="text-base font-semibold text-ink">{i.title}</div>
            <p className="mt-1.5 text-sm text-ink-muted leading-relaxed">{i.desc}</p>
          </div>
        ))}
      </div>

      {/* messy -> clean visual */}
      <div className="mt-12 grid md:grid-cols-2 gap-6 items-center">
        <div className="rounded-3xl border border-border bg-white p-6">
          <div className="text-xs font-semibold text-destructive uppercase mb-3">Before</div>
          <div className="grid grid-cols-4 gap-1.5">
            {Array.from({ length: 16 }).map((_, i) => (
              <div key={i} className="aspect-video rounded bg-slate-100 border border-slate-200" />
            ))}
          </div>
          <div className="mt-3 text-xs text-ink-subtle">142 messy, duplicate screenshots</div>
        </div>
        <div className="rounded-3xl border border-brand/30 bg-white p-6 shadow-glow">
          <div className="text-xs font-semibold text-success uppercase mb-3">After</div>
          <div className="rounded-xl bg-gradient-to-br from-blue-50 to-violet-50 p-6 flex items-center gap-4">
            <FileText className="h-10 w-10 text-brand" />
            <div>
              <div className="text-sm font-semibold text-ink">clean-notes.pdf</div>
              <div className="text-xs text-ink-subtle">24 pages · organized · study-ready</div>
            </div>
          </div>
          <div className="mt-3 text-xs text-ink-subtle">One clean PDF, ready to study.</div>
        </div>
      </div>
    </Section>
  );
}

/* -------------------------- SOLUTION ------------------------- */
function Solution() {
  const items = [
    { icon: ScanLine, title: "Captures completed frames", desc: "Waits until the board, slide, code, or diagram is visually complete.", tint: "bg-brand/10 text-brand" },
    { icon: Layers, title: "Removes duplicates", desc: "Keeps only the clearest version of each unique visual moment.", tint: "bg-violet/10 text-violet" },
    { icon: FileText, title: "Exports clean notes", desc: "Download organized PDF notes or ZIP image packs.", tint: "bg-cyan/10 text-cyan" },
  ];
  return (
    <Section
      eyebrow="The Solution"
      title="Smart Capture finds the moment that matters"
      subtitle="FrameNote AI analyzes visual changes, detects stable completed frames, removes near-duplicates, and exports clean study-ready notes."
    >
      <div className="grid md:grid-cols-3 gap-5">
        {items.map((i) => (
          <div key={i.title} className="rounded-3xl bg-white border border-border shadow-card p-7 hover:shadow-elevated transition">
            <div className={`h-12 w-12 rounded-2xl flex items-center justify-center mb-5 ${i.tint}`}>
              <i.icon className="h-6 w-6" />
            </div>
            <div className="text-lg font-semibold text-ink">{i.title}</div>
            <p className="mt-2 text-sm text-ink-muted leading-relaxed">{i.desc}</p>
          </div>
        ))}
      </div>
    </Section>
  );
}

/* -------------------------- HOW IT WORKS ------------------------- */
function HowItWorks() {
  const steps = [
    { icon: Youtube, title: "Paste or upload", desc: "Paste a YouTube link or upload your own video." },
    { icon: ScanLine, title: "Analyze visual changes", desc: "FrameNote AI scans the video and detects when the screen is changing." },
    { icon: Wand2, title: "Capture the completed moment", desc: "It saves the best frame when the explanation becomes stable and complete." },
    { icon: FileText, title: "Clean and export", desc: "Duplicates are removed and the selected frames are exported as PDF or ZIP." },
  ];
  return (
    <Section
      id="how"
      eyebrow="How It Works"
      title="How Smart Capture works"
      subtitle="Four steps, seconds of your time."
      className="bg-soft/60"
    >
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 relative">
        {steps.map((s, i) => (
          <div key={s.title} className="relative rounded-3xl bg-white border border-border shadow-card p-6">
            <div className="text-[11px] font-bold text-brand mb-3">STEP {i + 1}</div>
            <div className="h-11 w-11 rounded-xl bg-gradient-brand/10 flex items-center justify-center mb-4">
              <s.icon className="h-5 w-5 text-brand" />
            </div>
            <div className="text-base font-semibold text-ink">{s.title}</div>
            <p className="mt-1.5 text-sm text-ink-muted leading-relaxed">{s.desc}</p>
          </div>
        ))}
      </div>
      <div className="mt-8 mx-auto max-w-2xl text-center rounded-2xl border border-brand/20 bg-white px-6 py-4 shadow-card">
        <p className="text-sm text-ink-muted">
          <Sparkles className="inline h-4 w-4 text-brand mr-1 -mt-0.5" />
          Unlike fixed-interval screenshot tools, FrameNote AI is built for videos where information appears gradually.
        </p>
      </div>
    </Section>
  );
}

/* -------------------------- BEFORE / AFTER ------------------------- */
function BeforeAfter() {
  const before = ["Pause video manually", "Take screenshots", "Rename files", "Delete duplicates", "Build PDF manually"];
  const after = ["Paste link", "Smart capture", "Duplicate removal", "Clean PDF", "Ready to study"];
  return (
    <Section eyebrow="Before vs After" title="From an evening of work to seconds">
      <div className="grid md:grid-cols-2 gap-5">
        <div className="rounded-3xl bg-white border border-border p-7">
          <div className="text-sm font-semibold text-destructive mb-4">Old way</div>
          <ul className="space-y-3">
            {before.map((b) => (
              <li key={b} className="flex items-center gap-3 text-sm text-ink-muted">
                <span className="h-6 w-6 rounded-full bg-destructive/10 text-destructive flex items-center justify-center text-xs">✕</span>
                {b}
              </li>
            ))}
          </ul>
        </div>
        <div className="rounded-3xl bg-white border border-brand/30 p-7 shadow-glow relative">
          <div className="absolute -top-3 left-7 rounded-full bg-gradient-brand px-3 py-1 text-[11px] font-semibold text-white">FrameNote AI</div>
          <div className="text-sm font-semibold text-brand mb-4 mt-1">The new way</div>
          <ul className="space-y-3">
            {after.map((b) => (
              <li key={b} className="flex items-center gap-3 text-sm text-ink">
                <CheckCircle2 className="h-5 w-5 text-success" />
                {b}
              </li>
            ))}
          </ul>
          <Button className="mt-6 rounded-full bg-gradient-brand text-white shadow-elevated">
            Try Smart Capture Free <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </div>
      </div>
    </Section>
  );
}

/* -------------------------- USE CASES ------------------------- */
function UseCases() {
  const cases = [
    { icon: GraduationCap, title: "University lectures", desc: "Turn recorded lectures into clean study PDFs." },
    { icon: Cpu, title: "Math & engineering tutorials", desc: "Capture full board solutions after the instructor finishes writing." },
    { icon: FlaskConical, title: "Medical lectures", desc: "Save diagrams, slides, and visual explanations." },
    { icon: Wand2, title: "Coding tutorials", desc: "Capture completed code screens without repeated half-written frames." },
    { icon: Presentation, title: "Webinars", desc: "Convert training sessions into shareable PDF notes." },
    { icon: PlayCircle, title: "Online courses", desc: "Use it with YouTube, course videos, and screen recordings." },
    { icon: Search, title: "Research videos", desc: "Extract visual evidence, diagrams, and important frames." },
    { icon: Users, title: "Teachers & creators", desc: "Turn your own lessons into downloadable study materials." },
  ];
  return (
    <Section id="use-cases" eyebrow="Use Cases" title="Built for every kind of visual learning" className="bg-soft/60">
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {cases.map((c) => (
          <div key={c.title} className="group rounded-2xl bg-white border border-border p-5 shadow-card hover:shadow-elevated hover:-translate-y-0.5 transition">
            <div className="h-10 w-10 rounded-xl bg-gradient-brand/10 flex items-center justify-center mb-4">
              <c.icon className="h-5 w-5 text-brand" />
            </div>
            <div className="text-sm font-semibold text-ink">{c.title}</div>
            <p className="mt-1 text-xs text-ink-muted leading-relaxed">{c.desc}</p>
          </div>
        ))}
      </div>
    </Section>
  );
}

/* -------------------------- FEATURES ------------------------- */
function Features() {
  const features = [
    { icon: Youtube, title: "YouTube to PDF converter" },
    { icon: Upload, title: "Video upload support" },
    { icon: ScanLine, title: "Smart completed-frame capture" },
    { icon: Trash2, title: "Duplicate frame removal" },
    { icon: Video, title: "720p, 1080p & best quality" },
    { icon: FileText, title: "PDF export" },
    { icon: Package, title: "ZIP image export" },
    { icon: Wand2, title: "Manual frame review" },
    { icon: Clock, title: "Timestamped frame gallery" },
    { icon: Layers, title: "Batch conversion (paid plans)" },
    { icon: Presentation, title: "PPT export coming soon" },
    { icon: Shield, title: "Secure processing" },
  ];
  return (
    <Section id="features" eyebrow="Features" title="Everything you need to turn video into notes">
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {features.map((f) => (
          <div key={f.title} className="group flex items-start gap-4 rounded-2xl border border-border bg-white p-5 shadow-card hover:shadow-elevated hover:border-brand/30 transition">
            <div className="h-10 w-10 shrink-0 rounded-xl bg-gradient-brand/10 flex items-center justify-center group-hover:bg-gradient-brand group-hover:text-white transition">
              <f.icon className="h-5 w-5 text-brand group-hover:text-white" />
            </div>
            <div>
              <div className="text-sm font-semibold text-ink">{f.title}</div>
              <div className="mt-0.5 text-xs text-ink-subtle">Fast, reliable, and study-ready.</div>
            </div>
          </div>
        ))}
      </div>
    </Section>
  );
}

/* -------------------------- OUTPUT FORMATS ------------------------- */
function OutputFormats() {
  const items = [
    { icon: FileText, title: "PDF Notes", desc: "Best for studying, printing, and sharing." },
    { icon: ImageIcon, title: "Image Pack", desc: "Download selected frames as organized images." },
    { icon: Clock, title: "Timestamped Gallery", desc: "Review frames with their video timestamps." },
    { icon: Presentation, title: "PPT Export", desc: "Coming soon for Pro users.", soon: true },
  ];
  return (
    <Section eyebrow="Outputs" title="Export your video as clean study material" className="bg-soft/60">
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {items.map((i) => (
          <div key={i.title} className="rounded-3xl bg-white border border-border shadow-card p-6 relative overflow-hidden">
            {i.soon && (
              <span className="absolute right-4 top-4 rounded-full bg-accent text-brand text-[10px] font-semibold px-2 py-0.5">SOON</span>
            )}
            <div className="h-12 w-12 rounded-2xl bg-gradient-brand/10 flex items-center justify-center mb-4">
              <i.icon className="h-6 w-6 text-brand" />
            </div>
            <div className="text-base font-semibold text-ink">{i.title}</div>
            <p className="mt-1 text-sm text-ink-muted">{i.desc}</p>
          </div>
        ))}
      </div>
    </Section>
  );
}

/* -------------------------- DASHBOARD ------------------------- */
function DashboardSection() {
  return (
    <Section eyebrow="Dashboard" title="Your notes, organized" subtitle="A calm control center for all your conversions.">
      <DashboardPreview />
    </Section>
  );
}

function ResultsSection() {
  return (
    <Section eyebrow="Results" title="Review, refine and export" subtitle="Preview every captured frame, tune your PDF, and download." className="bg-soft/60">
      <ResultsPreview />
    </Section>
  );
}

/* -------------------------- TRUST ------------------------- */
function Trust() {
  const items = [
    { icon: ShieldCheck, title: "Secure uploads", desc: "Videos are handled through secure processing flows." },
    { icon: Battery, title: "Auto-cleanup", desc: "Temporary files are automatically removed based on the plan." },
    { icon: Wand2, title: "User control", desc: "Users can review, remove, and reorder frames before export." },
    { icon: Lock, title: "Ethical use", desc: "Only process content you own or have permission to use." },
  ];
  return (
    <Section eyebrow="Privacy" title="Private by design">
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {items.map((i) => (
          <div key={i.title} className="rounded-2xl bg-white border border-border p-6 shadow-card">
            <div className="h-10 w-10 rounded-xl bg-success/10 flex items-center justify-center mb-4">
              <i.icon className="h-5 w-5 text-success" />
            </div>
            <div className="text-sm font-semibold text-ink">{i.title}</div>
            <p className="mt-1 text-xs text-ink-muted leading-relaxed">{i.desc}</p>
          </div>
        ))}
      </div>
      <p className="mt-8 text-center text-sm text-ink-subtle">
        Built for learning, productivity, and responsible content transformation.
      </p>
    </Section>
  );
}

/* -------------------------- PRICING ------------------------- */
function PricingSection() {
  return (
    <Section
      id="pricing"
      eyebrow="Pricing"
      title="Start free. Upgrade when you need more power."
      subtitle="Try Smart Capture with a short video preview. Upgrade for longer videos, HD exports, batch conversion, and watermark-free PDFs."
      className="bg-soft/60"
    >
      <Pricing />
    </Section>
  );
}

/* -------------------------- COMPARISON ------------------------- */
function Comparison() {
  return (
    <Section eyebrow="Comparison" title="Why FrameNote AI is different">
      <ComparisonTable />
    </Section>
  );
}

/* -------------------------- TESTIMONIALS ------------------------- */
function Testimonials() {
  const t = [
    { q: "FrameNote AI saved me hours before exams. It captured the full board solution instead of dozens of messy screenshots.", n: "Sarah M.", r: "Engineering Student" },
    { q: "I use it to extract diagrams and key visuals from recorded seminars. The duplicate removal is a huge time saver.", n: "Daniel R.", r: "PhD Researcher" },
    { q: "I turned my recorded lessons into clean PDF handouts for students in minutes.", n: "Maya K.", r: "Online Tutor" },
    { q: "Perfect for webinars and technical training. I can review key visuals without rewatching the entire video.", n: "James L.", r: "Product Manager" },
  ];
  return (
    <Section eyebrow="Loved by learners" title="What people are saying" className="bg-soft/60">
      <div className="grid md:grid-cols-2 gap-4">
        {t.map((x) => (
          <div key={x.n} className="rounded-3xl bg-white border border-border p-6 shadow-card">
            <div className="flex text-brand mb-3">
              {Array.from({ length: 5 }).map((_, i) => <Star key={i} className="h-4 w-4 fill-current" />)}
            </div>
            <p className="text-base text-ink leading-relaxed">&ldquo;{x.q}&rdquo;</p>
            <div className="mt-4 flex items-center gap-3">
              <div className="h-9 w-9 rounded-full bg-gradient-to-br from-brand to-violet" />
              <div>
                <div className="text-sm font-semibold text-ink">{x.n}</div>
                <div className="text-xs text-ink-subtle">{x.r}</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </Section>
  );
}

/* -------------------------- FAQ ------------------------- */
function FAQSection() {
  return (
    <Section id="faq" eyebrow="FAQ" title="Questions, answered">
      <FAQAccordion />
    </Section>
  );
}

/* -------------------------- SEO CONTENT ------------------------- */
function SEOContent() {
  const links = [
    ["YouTube to PDF", "/youtube-to-pdf"],
    ["Video to PDF", "/video-to-pdf"],
    ["Extract slides from video", "/extract-slides-from-video"],
    ["Lecture video to notes", "/lecture-video-to-notes"],
    ["YouTube screenshot tool", "/youtube-screenshot-tool"],
    ["Video to images", "/video-to-images"],
    ["Video to PPT", "/video-to-ppt"],
    ["Whiteboard video notes", "/whiteboard-video-notes"],
  ];
  return (
    <Section className="bg-soft/60">
      <div className="mx-auto max-w-4xl">
        <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-ink text-center">
          The smarter YouTube to PDF converter for visual learners
        </h2>
        <p className="mt-5 text-base text-ink-muted leading-relaxed text-center">
          FrameNote AI is built for students, teachers, researchers, and professionals who need
          more than a basic video screenshot tool. Instead of capturing random frames every few
          seconds, it identifies meaningful visual moments, removes repeated screenshots, and
          turns lectures, tutorials, webinars, and screen recordings into clean PDF notes.
        </p>
        <div className="mt-8 flex flex-wrap justify-center gap-2">
          {links.map(([label, href]) => (
            <a key={href} href={href} className="inline-flex items-center gap-1 rounded-full bg-white border border-border px-3 py-1.5 text-xs text-ink-muted hover:text-brand hover:border-brand/40 transition">
              {label} <ChevronRight className="h-3 w-3" />
            </a>
          ))}
        </div>
      </div>
    </Section>
  );
}

/* -------------------------- FINAL CTA ------------------------- */
function FinalCTA() {
  return (
    <section className="py-24">
      <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
        <div className="relative overflow-hidden rounded-[2rem] bg-gradient-brand p-10 sm:p-16 text-center text-white shadow-elevated">
          <div className="absolute -top-24 -right-24 h-72 w-72 rounded-full bg-white/10 blur-3xl" />
          <div className="absolute -bottom-24 -left-24 h-72 w-72 rounded-full bg-white/10 blur-3xl" />
          <h2 className="relative text-3xl sm:text-5xl font-bold tracking-tight">
            Stop taking screenshots manually
          </h2>
          <p className="relative mt-4 text-base sm:text-lg text-white/85 max-w-2xl mx-auto">
            Paste a video link, let FrameNote AI find the completed frames, and download clean visual notes in minutes.
          </p>
          <div className="relative mt-8 flex flex-col sm:flex-row justify-center gap-3">
            <Button className="h-12 rounded-full bg-white text-brand hover:bg-white/90 px-6 font-semibold shadow-elevated">
              Start Free <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
            <Button variant="outline" className="h-12 rounded-full bg-transparent border-white/40 text-white hover:bg-white/10 px-6 font-semibold">
              View Pricing
            </Button>
          </div>
          <p className="relative mt-4 text-xs text-white/70">
            Try a short preview today. Upgrade when you need longer videos, HD exports, and batch conversion.
          </p>
        </div>
      </div>
    </section>
  );
}

/* -------------------------- FOOTER ------------------------- */
function Footer() {
  const cols = [
    { title: "Product", links: ["YouTube to PDF", "Video Upload", "Smart Capture", "PDF Export", "Pricing"] },
    { title: "Use Cases", links: ["Students", "Teachers", "Researchers", "Webinars", "Online Courses"] },
    { title: "Resources", links: ["Blog", "Help Center", "FAQ", "Contact", "Roadmap"] },
    { title: "Legal", links: ["Privacy Policy", "Terms of Service", "Content Rights", "Security"] },
  ];
  return (
    <footer className="border-t border-border bg-white">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-14">
        <div className="grid gap-10 lg:grid-cols-5">
          <div className="lg:col-span-1">
            <Logo />
            <p className="mt-4 text-sm text-ink-muted max-w-xs">
              Convert videos into clean visual notes — automatically.
            </p>
            <div className="mt-4 inline-flex items-center gap-1.5 rounded-full bg-accent px-2.5 py-1 text-[11px] font-semibold text-brand">
              <Briefcase className="h-3 w-3" /> For learning & work
            </div>
          </div>
          {cols.map((c) => (
            <div key={c.title}>
              <div className="text-xs font-semibold text-ink uppercase tracking-wider mb-4">{c.title}</div>
              <ul className="space-y-2.5">
                {c.links.map((l) => (
                  <li key={l}>
                    <a href="#" className="text-sm text-ink-muted hover:text-ink transition">{l}</a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div className="mt-12 pt-6 border-t border-border flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-ink-subtle">
          <div>© 2026 FrameNote AI. All rights reserved.</div>
          <div className="flex items-center gap-4">
            <a href="#" className="hover:text-ink">Privacy</a>
            <a href="#" className="hover:text-ink">Terms</a>
            <a href="#" className="hover:text-ink">Security</a>
          </div>
        </div>
      </div>
    </footer>
  );
}
