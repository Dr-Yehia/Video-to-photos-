export function Logo({ className = "" }: { className?: string }) {
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div className="relative h-8 w-8 rounded-xl bg-gradient-brand shadow-elevated flex items-center justify-center">
        <svg viewBox="0 0 24 24" className="h-4 w-4 text-white" fill="none" stroke="currentColor" strokeWidth="2.2">
          <rect x="3" y="5" width="18" height="14" rx="3" />
          <path d="m10 10 5 3-5 3z" fill="currentColor" stroke="none" />
        </svg>
        <span className="absolute -right-1 -top-1 h-3 w-3 rounded-full bg-white flex items-center justify-center shadow-card">
          <span className="h-1.5 w-1.5 rounded-full bg-success" />
        </span>
      </div>
      <span className="text-[17px] font-bold tracking-tight text-ink">
        FrameNote <span className="text-gradient-brand">AI</span>
      </span>
    </div>
  );
}
