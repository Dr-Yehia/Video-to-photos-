import { useState } from "react";
import { Check, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";

type Plan = {
  name: string;
  price: { m: number | string; y: number | string };
  suffix?: string;
  desc: string;
  features: string[];
  cta: string;
  popular?: boolean;
  outline?: boolean;
};

const PLANS: Plan[] = [
  {
    name: "Free", price: { m: 0, y: 0 }, desc: "Best for testing.",
    features: [
      "3 short conversions per month",
      "Up to 10 minutes per video",
      "720p preview quality",
      "PDF export with watermark",
      "Basic duplicate removal",
      "Manual frame review",
    ],
    cta: "Start Free", outline: true,
  },
  {
    name: "Starter", price: { m: 9, y: 6 }, desc: "Best for casual learners.",
    features: [
      "30 video-minutes per month",
      "Up to 30 minutes per video",
      "720p and 1080p support",
      "Watermark-free PDF",
      "ZIP export",
      "Dashboard history",
      "Email support",
    ],
    cta: "Choose Starter", outline: true,
  },
  {
    name: "Pro", price: { m: 19, y: 12 }, desc: "Best for serious students, researchers, and professionals.",
    features: [
      "300 video-minutes per month",
      "Up to 2 hours per video",
      "1080p and best available quality",
      "Advanced Smart Capture",
      "Advanced duplicate removal",
      "Batch conversion",
      "Timestamped gallery",
      "PDF customization",
      "Priority processing",
      "Early access to PPT export",
    ],
    cta: "Start Pro", popular: true,
  },
  {
    name: "Team", price: { m: 49, y: 32 }, desc: "Best for teams, tutors, and labs.",
    features: [
      "1,000 video-minutes per month",
      "5 team seats",
      "Shared workspace",
      "Team project history",
      "Batch conversion",
      "Shared PDF library",
      "Priority support",
    ],
    cta: "Start Team", outline: true,
  },
];

const PACKS = [
  { min: "100 extra video-minutes", price: 5 },
  { min: "500 extra video-minutes", price: 19 },
  { min: "2,000 extra video-minutes", price: 59 },
];

export function Pricing() {
  const [yearly, setYearly] = useState(true);
  return (
    <>
      <div className="mb-10 flex items-center justify-center gap-3">
        <span className={`text-sm font-medium ${!yearly ? "text-ink" : "text-ink-subtle"}`}>Monthly</span>
        <button
          onClick={() => setYearly(!yearly)}
          className={`relative h-7 w-14 rounded-full transition ${yearly ? "bg-gradient-brand" : "bg-slate-200"}`}
          aria-label="Toggle billing"
        >
          <span className={`absolute top-0.5 h-6 w-6 rounded-full bg-white shadow transition ${yearly ? "left-7" : "left-0.5"}`} />
        </button>
        <span className={`text-sm font-medium ${yearly ? "text-ink" : "text-ink-subtle"}`}>
          Yearly <span className="ml-1 rounded-full bg-success/10 px-2 py-0.5 text-[11px] font-semibold text-success">Save 35%</span>
        </span>
      </div>

      <div className="grid gap-5 lg:grid-cols-4">
        {PLANS.map((p) => (
          <div
            key={p.name}
            className={`relative rounded-3xl border p-6 flex flex-col ${
              p.popular
                ? "border-transparent bg-white shadow-elevated ring-2 ring-brand/60"
                : "border-border bg-white shadow-card"
            }`}
          >
            {p.popular && (
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 inline-flex items-center gap-1 rounded-full bg-gradient-brand px-3 py-1 text-[11px] font-semibold text-white shadow-elevated">
                <Sparkles className="h-3 w-3" /> Most Popular
              </div>
            )}
            <div className="text-sm font-semibold text-brand">{p.name}</div>
            <div className="mt-3 flex items-baseline gap-1">
              <span className="text-4xl font-bold tracking-tight text-ink">
                ${yearly ? p.price.y : p.price.m}
              </span>
              <span className="text-sm text-ink-subtle">/month</span>
            </div>
            <p className="mt-2 text-sm text-ink-muted min-h-[40px]">{p.desc}</p>
            <Button className={`mt-5 rounded-full h-11 font-semibold ${
              p.popular ? "bg-gradient-brand text-white shadow-elevated" :
              p.outline ? "bg-white border border-border text-ink hover:bg-soft" : "bg-ink text-white"
            }`}>
              {p.cta}
            </Button>
            <ul className="mt-6 space-y-2.5 text-sm">
              {p.features.map((f) => (
                <li key={f} className="flex gap-2.5 text-ink-muted">
                  <Check className="h-4 w-4 shrink-0 text-brand mt-0.5" />
                  <span>{f}</span>
                </li>
              ))}
            </ul>
          </div>
        ))}

        <div className="relative rounded-3xl border border-dashed border-border bg-soft p-6 flex flex-col lg:col-span-4">
          <div className="flex flex-wrap items-start justify-between gap-6">
            <div>
              <div className="text-sm font-semibold text-brand">Enterprise</div>
              <div className="mt-2 text-2xl font-bold text-ink">Custom pricing</div>
              <p className="mt-1 text-sm text-ink-muted">Best for universities and organizations.</p>
              <ul className="mt-4 grid sm:grid-cols-2 gap-2 text-sm text-ink-muted">
                {["Custom limits", "API access", "SSO options", "Dedicated support", "Custom deployment discussion"].map((f) => (
                  <li key={f} className="flex gap-2"><Check className="h-4 w-4 text-brand mt-0.5" />{f}</li>
                ))}
              </ul>
            </div>
            <Button className="rounded-full bg-ink text-white h-11 px-6 self-center">Contact Sales</Button>
          </div>
        </div>
      </div>

      <div className="mt-6 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-xs text-ink-subtle">
        <span>Cancel anytime</span><span>·</span>
        <span>No hidden fees</span><span>·</span>
        <span>Instant access</span>
      </div>

      <div className="mt-14">
        <div className="text-center mb-6">
          <h3 className="text-xl font-bold text-ink">Need more? Grab a credit pack</h3>
          <p className="mt-1 text-sm text-ink-muted">Top up any plan without changing your subscription.</p>
        </div>
        <div className="grid sm:grid-cols-3 gap-4">
          {PACKS.map((p) => (
            <div key={p.min} className="rounded-2xl border border-border bg-white p-5 shadow-card flex items-center justify-between">
              <div>
                <div className="text-sm font-semibold text-ink">{p.min}</div>
                <div className="text-xs text-ink-subtle">One-time credit pack</div>
              </div>
              <div className="text-lg font-bold text-brand">${p.price}</div>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}
