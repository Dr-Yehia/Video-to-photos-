import { useEffect, useState } from "react";
import { Menu, X } from "lucide-react";
import { Logo } from "./Logo";
import { Button } from "@/components/ui/button";

const nav = [
  { label: "Product", href: "#features" },
  { label: "How It Works", href: "#how" },
  { label: "Use Cases", href: "#use-cases" },
  { label: "Pricing", href: "#pricing" },
  { label: "FAQ", href: "#faq" },
];

export function Navbar() {
  const [open, setOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const on = () => setScrolled(window.scrollY > 8);
    on();
    window.addEventListener("scroll", on);
    return () => window.removeEventListener("scroll", on);
  }, []);

  return (
    <header
      className={`sticky top-0 z-50 w-full backdrop-blur-xl transition-all ${
        scrolled ? "bg-white/80 border-b border-border" : "bg-white/60 border-b border-transparent"
      }`}
    >
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8 h-16">
        <a href="#top" className="shrink-0"><Logo /></a>
        <nav className="hidden lg:flex items-center gap-8">
          {nav.map((n) => (
            <a key={n.href} href={n.href} className="text-sm font-medium text-ink-muted hover:text-ink transition-colors">
              {n.label}
            </a>
          ))}
        </nav>
        <div className="hidden lg:flex items-center gap-2">
          <a href="#" className="text-sm font-medium text-ink-muted hover:text-ink px-3 py-2">Sign In</a>
          <Button variant="outline" className="rounded-full border-border">View Demo</Button>
          <Button className="rounded-full bg-gradient-brand text-white hover:opacity-95 shadow-elevated">Start Free</Button>
        </div>
        <button onClick={() => setOpen(!open)} className="lg:hidden p-2 rounded-lg hover:bg-soft" aria-label="Menu">
          {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>
      {open && (
        <div className="lg:hidden border-t border-border bg-white px-4 py-4 space-y-3">
          {nav.map((n) => (
            <a key={n.href} href={n.href} onClick={() => setOpen(false)} className="block text-sm font-medium text-ink-muted py-1">
              {n.label}
            </a>
          ))}
          <div className="flex flex-col gap-2 pt-2">
            <Button variant="outline" className="rounded-full">View Demo</Button>
            <Button className="rounded-full bg-gradient-brand text-white">Start Free</Button>
          </div>
        </div>
      )}
    </header>
  );
}
