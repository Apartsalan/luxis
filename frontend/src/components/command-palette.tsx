"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  Search,
  Briefcase,
  Users,
  FileText,
  Settings,
  LayoutDashboard,
  Scale,
  ArrowRight,
  Loader2,
  X,
} from "lucide-react";
import { api } from "@/lib/api";

interface SearchResult {
  id: string;
  type: "case" | "contact" | "document";
  title: string;
  subtitle: string;
  href: string;
}

const QUICK_ACTIONS = [
  { label: "Nieuw dossier", href: "/zaken/nieuw", icon: Briefcase },
  { label: "Nieuwe relatie", href: "/relaties/nieuw", icon: Users },
  { label: "Dashboard", href: "/", icon: LayoutDashboard },
  { label: "Dossiers", href: "/zaken", icon: Briefcase },
  { label: "Relaties", href: "/relaties", icon: Users },
  { label: "Uren", href: "/uren", icon: Scale },
  { label: "Facturen", href: "/facturen", icon: Scale },
  { label: "Documenten", href: "/documenten", icon: FileText },
  { label: "Instellingen", href: "/instellingen", icon: Settings },
];

const TYPE_ICONS = {
  case: Briefcase,
  contact: Users,
  document: FileText,
};

const TYPE_LABELS = {
  case: "Dossier",
  contact: "Relatie",
  document: "Document",
};

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();
  const debounceRef = useRef<NodeJS.Timeout | null>(null);

  // Ctrl+K to open
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        setOpen((prev) => !prev);
      }
      if (e.key === "Escape") {
        setOpen(false);
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Focus input when opened
  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 50);
      setQuery("");
      setResults([]);
      setSelectedIndex(0);
    }
  }, [open]);

  // Search on query change
  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      setSelectedIndex(0);
      return;
    }

    if (debounceRef.current) clearTimeout(debounceRef.current);

    debounceRef.current = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await api(`/api/search?q=${encodeURIComponent(query.trim())}&limit=10`);
        if (res.ok) {
          const data = await res.json();
          setResults(data.results ?? []);
        }
      } catch {
        // Silently fail — search is non-critical
      } finally {
        setLoading(false);
        setSelectedIndex(0);
      }
    }, 250);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query]);

  // Filter quick actions by query
  const filteredActions = query.trim()
    ? QUICK_ACTIONS.filter((a) =>
        a.label.toLowerCase().includes(query.toLowerCase())
      )
    : QUICK_ACTIONS;

  const allItems = [
    ...results.map((r) => ({ ...r, isResult: true as const })),
    ...filteredActions.map((a) => ({
      id: a.href,
      label: a.label,
      href: a.href,
      icon: a.icon,
      isResult: false as const,
    })),
  ];

  const handleSelect = useCallback(
    (href: string) => {
      setOpen(false);
      router.push(href);
    },
    [router]
  );

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((i) => Math.min(i + 1, allItems.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter" && allItems[selectedIndex]) {
      e.preventDefault();
      const item = allItems[selectedIndex];
      handleSelect(item.isResult ? item.href : item.href);
    }
  };

  if (!open) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm"
        onClick={() => setOpen(false)}
      />

      {/* Dialog */}
      <div className="fixed inset-x-0 top-[20%] z-50 mx-auto w-full max-w-lg px-4">
        <div className="rounded-xl border border-border bg-white shadow-2xl overflow-hidden">
          {/* Search input */}
          <div className="flex items-center gap-3 border-b border-border px-4 py-3">
            <Search className="h-5 w-5 text-muted-foreground shrink-0" />
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Zoek dossiers, relaties, documenten..."
              className="flex-1 bg-transparent text-sm text-foreground placeholder:text-muted-foreground outline-none"
            />
            {loading && <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />}
            <button
              onClick={() => setOpen(false)}
              className="rounded-md p-1 text-muted-foreground hover:text-foreground transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          {/* Results */}
          <div className="max-h-80 overflow-y-auto py-2">
            {/* Search results */}
            {results.length > 0 && (
              <div className="px-2">
                <p className="px-2 py-1.5 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                  Resultaten
                </p>
                {results.map((result, idx) => {
                  const Icon = TYPE_ICONS[result.type] || FileText;
                  const isSelected = idx === selectedIndex;
                  return (
                    <button
                      key={result.id}
                      onClick={() => handleSelect(result.href)}
                      onMouseEnter={() => setSelectedIndex(idx)}
                      className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left transition-colors ${
                        isSelected ? "bg-primary/10 text-primary" : "hover:bg-muted"
                      }`}
                    >
                      <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-md ${
                        isSelected ? "bg-primary/10" : "bg-muted"
                      }`}>
                        <Icon className="h-4 w-4" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium truncate">{result.title}</p>
                        <p className="text-xs text-muted-foreground truncate">{result.subtitle}</p>
                      </div>
                      <span className="text-[10px] font-medium text-muted-foreground/60 shrink-0">
                        {TYPE_LABELS[result.type]}
                      </span>
                    </button>
                  );
                })}
              </div>
            )}

            {/* Quick actions */}
            {filteredActions.length > 0 && (
              <div className="px-2 mt-1">
                <p className="px-2 py-1.5 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                  {query.trim() ? "Navigatie" : "Snelle acties"}
                </p>
                {filteredActions.map((action, idx) => {
                  const globalIdx = results.length + idx;
                  const isSelected = globalIdx === selectedIndex;
                  return (
                    <button
                      key={action.href}
                      onClick={() => handleSelect(action.href)}
                      onMouseEnter={() => setSelectedIndex(globalIdx)}
                      className={`flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left transition-colors ${
                        isSelected ? "bg-primary/10 text-primary" : "hover:bg-muted text-foreground"
                      }`}
                    >
                      <action.icon className="h-4 w-4 shrink-0" />
                      <span className="text-sm">{action.label}</span>
                      {isSelected && <ArrowRight className="h-3.5 w-3.5 ml-auto text-primary" />}
                    </button>
                  );
                })}
              </div>
            )}

            {/* Empty state */}
            {query.trim() && results.length === 0 && filteredActions.length === 0 && !loading && (
              <div className="py-8 text-center">
                <Search className="h-8 w-8 text-muted-foreground/30 mx-auto mb-2" />
                <p className="text-sm text-muted-foreground">
                  Geen resultaten voor "{query}"
                </p>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center gap-4 border-t border-border px-4 py-2 text-[10px] text-muted-foreground/60">
            <span className="flex items-center gap-1">
              <kbd className="rounded border border-border bg-muted px-1 py-0.5 font-mono">↑↓</kbd>
              Navigeren
            </span>
            <span className="flex items-center gap-1">
              <kbd className="rounded border border-border bg-muted px-1 py-0.5 font-mono">Enter</kbd>
              Openen
            </span>
            <span className="flex items-center gap-1">
              <kbd className="rounded border border-border bg-muted px-1 py-0.5 font-mono">Esc</kbd>
              Sluiten
            </span>
          </div>
        </div>
      </div>
    </>
  );
}
