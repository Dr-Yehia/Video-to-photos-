import { BarChart3, Bell, Bookmark, CreditCard, FileText, FolderClock, Layers, Plus, Search, Settings, Sparkles, TrendingUp, Video } from "lucide-react";

const sidebar = [
  { icon: Plus, label: "New Conversion", active: true },
  { icon: FileText, label: "My Notes" },
  { icon: Layers, label: "Batch Jobs" },
  { icon: Bookmark, label: "Favorites" },
  { icon: CreditCard, label: "Billing" },
  { icon: Settings, label: "Settings" },
];

const stats = [
  { label: "Video minutes used", value: "184 / 300", accent: "brand", pct: 61 },
  { label: "PDFs generated", value: "42", accent: "violet", pct: 78 },
  { label: "Frames captured", value: "1,286", accent: "cyan", pct: 54 },
  { label: "Storage used", value: "3.2 GB", accent: "success", pct: 32 },
];

const rows = [
  { title: "Organic Chemistry — Lecture 14", src: "YouTube", dur: "48:12", frames: 34, type: "PDF", date: "Today", status: "Done" },
  { title: "React Server Components deep dive", src: "YouTube", dur: "1:12:04", frames: 61, type: "PDF + ZIP", date: "Today", status: "Done" },
  { title: "Cardiology webinar recording", src: "Upload", dur: "56:47", frames: 42, type: "PDF", date: "Yesterday", status: "Done" },
  { title: "Linear Algebra — matrix ops", src: "YouTube", dur: "34:20", frames: 27, type: "ZIP", date: "2d ago", status: "Processing" },
  { title: "UI design critique #12", src: "Upload", dur: "22:05", frames: 18, type: "PDF", date: "3d ago", status: "Done" },
];

export function DashboardPreview() {
  return (
    <div className="rounded-3xl border border-border bg-white shadow-elevated overflow-hidden">
      <div className="flex">
        {/* Sidebar */}
        <aside className="hidden md:flex w-56 shrink-0 flex-col border-r border-border bg-soft/60 p-4">
          <div className="flex items-center gap-2 mb-6">
            <div className="h-7 w-7 rounded-lg bg-gradient-brand" />
            <span className="text-sm font-bold text-ink">FrameNote</span>
          </div>
          <nav className="space-y-1">
            {sidebar.map((s) => (
              <div key={s.label} className={`flex items-center gap-2.5 px-3 py-2 rounded-xl text-sm ${
                s.active ? "bg-white shadow-card text-ink font-semibold" : "text-ink-muted hover:text-ink"
              }`}>
                <s.icon className={`h-4 w-4 ${s.active ? "text-brand" : ""}`} />
                {s.label}
              </div>
            ))}
          </nav>
          <div className="mt-auto rounded-2xl bg-gradient-brand p-4 text-white">
            <div className="text-xs font-semibold opacity-90">Upgrade to Team</div>
            <div className="text-[11px] opacity-80 mt-1">Batch jobs, 5 seats & shared library</div>
          </div>
        </aside>

        {/* Main */}
        <div className="flex-1 min-w-0">
          {/* Topbar */}
          <div className="flex items-center gap-3 border-b border-border px-4 sm:px-6 h-14">
            <div className="flex items-center gap-2 rounded-full bg-soft px-3 py-1.5 flex-1 max-w-md">
              <Search className="h-4 w-4 text-ink-subtle" />
              <span className="text-sm text-ink-subtle">Search your notes…</span>
            </div>
            <div className="hidden sm:flex items-center gap-1.5 rounded-full bg-accent px-3 py-1.5 text-xs font-semibold text-brand">
              <TrendingUp className="h-3.5 w-3.5" /> 184 / 300 min
            </div>
            <button className="rounded-full bg-gradient-brand text-white text-xs font-semibold px-3 py-1.5 shadow-card inline-flex items-center gap-1">
              <Sparkles className="h-3.5 w-3.5" /> Upgrade
            </button>
            <Bell className="h-4 w-4 text-ink-subtle" />
            <div className="h-8 w-8 rounded-full bg-gradient-to-br from-brand to-violet" />
          </div>

          {/* Content */}
          <div className="p-4 sm:p-6 space-y-6">
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              {stats.map((s) => (
                <div key={s.label} className="rounded-2xl border border-border bg-white p-4">
                  <div className="text-xs text-ink-subtle">{s.label}</div>
                  <div className="mt-1 text-xl font-bold text-ink">{s.value}</div>
                  <div className="mt-3 h-1.5 rounded-full bg-soft overflow-hidden">
                    <div className="h-full rounded-full bg-gradient-brand" style={{ width: `${s.pct}%` }} />
                  </div>
                </div>
              ))}
            </div>

            <div className="rounded-2xl border border-border overflow-hidden">
              <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-soft/50">
                <div className="flex items-center gap-2">
                  <FolderClock className="h-4 w-4 text-brand" />
                  <span className="text-sm font-semibold text-ink">Recent conversions</span>
                </div>
                <BarChart3 className="h-4 w-4 text-ink-subtle" />
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm min-w-[640px]">
                  <thead className="text-left text-xs text-ink-subtle uppercase tracking-wider bg-white">
                    <tr>
                      <th className="px-4 py-3 font-semibold">Video</th>
                      <th className="px-4 py-3 font-semibold">Source</th>
                      <th className="px-4 py-3 font-semibold">Duration</th>
                      <th className="px-4 py-3 font-semibold">Frames</th>
                      <th className="px-4 py-3 font-semibold">Export</th>
                      <th className="px-4 py-3 font-semibold">Date</th>
                      <th className="px-4 py-3 font-semibold">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((r) => (
                      <tr key={r.title} className="border-t border-border">
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <div className="h-8 w-12 rounded-md bg-gradient-to-br from-blue-100 to-violet-100 flex items-center justify-center">
                              <Video className="h-3.5 w-3.5 text-brand" />
                            </div>
                            <span className="font-medium text-ink truncate max-w-[220px]">{r.title}</span>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-ink-muted">{r.src}</td>
                        <td className="px-4 py-3 text-ink-muted">{r.dur}</td>
                        <td className="px-4 py-3 text-ink-muted">{r.frames}</td>
                        <td className="px-4 py-3 text-ink-muted">{r.type}</td>
                        <td className="px-4 py-3 text-ink-subtle">{r.date}</td>
                        <td className="px-4 py-3">
                          <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold ${
                            r.status === "Done" ? "bg-success/10 text-success" : "bg-accent text-brand"
                          }`}>
                            <span className="h-1.5 w-1.5 rounded-full bg-current" /> {r.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
