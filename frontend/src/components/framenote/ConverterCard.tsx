import { useState } from "react";
import { Check, FileDown, Loader2, Sparkles, Upload, Youtube } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const STEPS = [
  "Reading video",
  "Detecting completed frames",
  "Removing duplicates",
  "Building PDF",
  "Ready to download",
];

export function ConverterCard() {
  const [smart, setSmart] = useState(true);
  const [dedupe, setDedupe] = useState(true);
  const [pdf, setPdf] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [step, setStep] = useState(-1);

  const run = () => {
    setProcessing(true);
    setStep(0);
    let i = 0;
    const t = setInterval(() => {
      i += 1;
      if (i >= STEPS.length) {
        clearInterval(t);
        setTimeout(() => {
          setProcessing(false);
          setStep(-1);
        }, 2200);
      }
      setStep(i);
    }, 900);
  };

  return (
    <div className="rounded-3xl border border-border bg-white shadow-elevated p-4 sm:p-6">
      <Tabs defaultValue="url" className="w-full">
        <TabsList className="bg-soft rounded-full p-1 h-auto">
          <TabsTrigger value="url" className="rounded-full data-[state=active]:bg-white data-[state=active]:shadow-card px-4 py-2 text-sm">
            <Youtube className="h-4 w-4 mr-1.5" /> YouTube URL
          </TabsTrigger>
          <TabsTrigger value="upload" className="rounded-full data-[state=active]:bg-white data-[state=active]:shadow-card px-4 py-2 text-sm">
            <Upload className="h-4 w-4 mr-1.5" /> Upload Video
          </TabsTrigger>
        </TabsList>

        <TabsContent value="url" className="mt-5 space-y-4">
          <div className="flex flex-col sm:flex-row gap-2">
            <Input placeholder="https://youtube.com/watch?v=..." className="h-12 rounded-xl border-border bg-soft" />
            <Select defaultValue="best">
              <SelectTrigger className="h-12 rounded-xl sm:w-40 border-border bg-soft"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="auto">Auto</SelectItem>
                <SelectItem value="720">720p</SelectItem>
                <SelectItem value="1080">1080p</SelectItem>
                <SelectItem value="best">Best Available</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="grid sm:grid-cols-3 gap-2">
            <ToggleRow label="Smart completed-frame capture" v={smart} on={setSmart} />
            <ToggleRow label="Remove duplicates" v={dedupe} on={setDedupe} />
            <ToggleRow label="Create PDF" v={pdf} on={setPdf} />
          </div>

          <Button onClick={run} disabled={processing} className="w-full h-12 rounded-xl bg-gradient-brand text-white shadow-elevated hover:opacity-95 text-sm font-semibold">
            {processing ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Generating…</> : <><Sparkles className="mr-2 h-4 w-4" /> Generate Smart Notes</>}
          </Button>
        </TabsContent>

        <TabsContent value="upload" className="mt-5 space-y-4">
          <label className="block rounded-2xl border-2 border-dashed border-border bg-soft p-8 text-center cursor-pointer hover:border-brand/50 transition">
            <div className="mx-auto h-12 w-12 rounded-2xl bg-gradient-brand/10 flex items-center justify-center mb-3">
              <Upload className="h-5 w-5 text-brand" />
            </div>
            <div className="text-sm font-semibold text-ink">Drop your video here, or click to upload</div>
            <div className="mt-1 text-xs text-ink-subtle">MP4, MOV, WEBM, MKV · up to 2 hours on Pro</div>
            <input type="file" className="hidden" accept="video/*" />
          </label>
          <Button onClick={run} disabled={processing} className="w-full h-12 rounded-xl bg-gradient-brand text-white shadow-elevated hover:opacity-95 text-sm font-semibold">
            <Upload className="mr-2 h-4 w-4" /> Upload & Analyze
          </Button>
        </TabsContent>
      </Tabs>

      {step >= 0 && (
        <div className="mt-6 rounded-2xl border border-border bg-soft p-4">
          <div className="text-xs font-semibold text-ink-muted mb-3">Processing…</div>
          <ol className="space-y-2">
            {STEPS.map((s, i) => {
              const done = i < step;
              const active = i === step;
              return (
                <li key={s} className="flex items-center gap-3 text-sm">
                  <span className={`flex h-6 w-6 items-center justify-center rounded-full text-[11px] font-semibold ${
                    done ? "bg-success text-white" : active ? "bg-gradient-brand text-white animate-pulse-ring" : "bg-white border border-border text-ink-subtle"
                  }`}>
                    {done ? <Check className="h-3.5 w-3.5" /> : active ? <Loader2 className="h-3 w-3 animate-spin" /> : i + 1}
                  </span>
                  <span className={done ? "text-ink-muted line-through" : active ? "text-ink font-semibold" : "text-ink-subtle"}>{s}</span>
                  {i === STEPS.length - 1 && done && (
                    <span className="ml-auto inline-flex items-center gap-1 text-xs text-success font-semibold"><FileDown className="h-3.5 w-3.5" /> Download</span>
                  )}
                </li>
              );
            })}
          </ol>
        </div>
      )}
    </div>
  );
}

function ToggleRow({ label, v, on }: { label: string; v: boolean; on: (b: boolean) => void }) {
  return (
    <label className="flex items-center justify-between gap-3 rounded-xl border border-border bg-white px-3 py-2.5">
      <span className="text-xs sm:text-[13px] font-medium text-ink-muted leading-tight">{label}</span>
      <Switch checked={v} onCheckedChange={on} />
    </label>
  );
}
