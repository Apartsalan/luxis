"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Sparkles, RefreshCw, TrendingUp, BookOpen, Info } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";

// ── Types ────────────────────────────────────────────────────────────────
interface LearningStats {
  edit_rate: {
    matched: number;
    ongewijzigd: number;
    licht: number;
    fors: number;
  };
  total_examples: number;
  per_category: Record<string, number>;
  top_examples: { category: string; use_count: number; preview: string }[];
}

// Nederlandse labels voor de classificatie-categorieën.
const CATEGORY_LABELS: Record<string, string> = {
  juridisch_verweer: "Juridisch verweer",
  betwisting: "Betwisting",
  belofte_tot_betaling: "Belofte tot betaling",
  betalingsregeling_verzoek: "Betalingsregeling",
  beweert_betaald: "Beweert betaald",
  onvermogen: "Onvermogen",
  ontvangstbevestiging: "Ontvangstbevestiging",
  niet_gerelateerd: "Niet gerelateerd",
};

function catLabel(key: string): string {
  return CATEGORY_LABELS[key] ?? key;
}

export function AILerenTab() {
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery<LearningStats>({
    queryKey: ["learning-stats"],
    queryFn: async () => {
      const res = await api("/api/ai-agent/learning/stats");
      if (!res.ok) throw new Error("Kon leer-statistieken niet laden");
      return res.json();
    },
  });

  const backfill = useMutation({
    mutationFn: async () => {
      const res = await api("/api/ai-agent/learning/backfill", { method: "POST" });
      if (!res.ok) throw new Error("Bijwerken mislukt");
      return res.json() as Promise<{ added: number }>;
    },
    onSuccess: (r) => {
      toast.success(
        r.added > 0
          ? `${r.added} nieuw${r.added === 1 ? "" : "e"} voorbeeld${r.added === 1 ? "" : "en"} geleerd`
          : "Geen nieuwe voorbeelden — alles is al verwerkt"
      );
      queryClient.invalidateQueries({ queryKey: ["learning-stats"] });
    },
    onError: (e: unknown) => toast.error(e instanceof Error ? e.message : "Bijwerken mislukt"),
  });

  if (isLoading) {
    return <div className="h-40 rounded-xl skeleton" />;
  }

  const er = data?.edit_rate ?? { matched: 0, ongewijzigd: 0, licht: 0, fors: 0 };
  const total = er.matched || 0;
  const pct = (n: number) => (total > 0 ? Math.round((n / total) * 100) : 0);
  const perCat = Object.entries(data?.per_category ?? {}).sort((a, b) => b[1] - a[1]);

  return (
    <div className="space-y-6">
      {/* Header + uitleg */}
      <div>
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-violet-500" />
          <h2 className="text-lg font-semibold text-foreground">Slim leren</h2>
        </div>
        <p className="mt-1 text-sm text-muted-foreground">
          De AI leert onzichtbaar van je eigen eerder verstuurde antwoorden: bij het
          opstellen van een concept gebruikt hij je meest passende eerdere antwoorden als
          voorbeeld. Hier zie je of dat goed gaat.
        </p>
      </div>

      {/* Kwaliteit: edit-rate */}
      <div className="rounded-xl border border-border bg-card p-5">
        <div className="flex items-center gap-2 mb-3">
          <TrendingUp className="h-4 w-4 text-emerald-600" />
          <h3 className="text-sm font-semibold text-foreground">
            Hoeveel pas je nog aan?
          </h3>
        </div>

        {total === 0 ? (
          <div className="flex items-start gap-2 rounded-lg bg-muted/50 p-3 text-sm text-muted-foreground">
            <Info className="h-4 w-4 mt-0.5 shrink-0" />
            <span>
              Nog te weinig verstuurde concepten om te meten. Deze meter vult zich
              vanzelf naarmate je AI-concepten beoordeelt en verstuurt — bijna ongewijzigd
              versturen betekent dat het goed werkt.
            </span>
          </div>
        ) : (
          <>
            <p className="text-sm text-muted-foreground mb-3">
              Van de laatste <span className="font-semibold text-foreground">{total}</span>{" "}
              verstuurde concepten:
            </p>
            {/* Gestapelde balk */}
            <div className="flex h-3 w-full overflow-hidden rounded-full bg-muted">
              <div className="bg-emerald-500" style={{ width: `${pct(er.ongewijzigd)}%` }} />
              <div className="bg-amber-400" style={{ width: `${pct(er.licht)}%` }} />
              <div className="bg-red-400" style={{ width: `${pct(er.fors)}%` }} />
            </div>
            <div className="mt-3 grid grid-cols-3 gap-2 text-center">
              <Legend color="bg-emerald-500" label="(Bijna) ongewijzigd" value={er.ongewijzigd} pct={pct(er.ongewijzigd)} />
              <Legend color="bg-amber-400" label="Licht aangepast" value={er.licht} pct={pct(er.licht)} />
              <Legend color="bg-red-400" label="Fors herschreven" value={er.fors} pct={pct(er.fors)} />
            </div>
            <p className="mt-3 text-xs text-muted-foreground">
              Hoe meer groen, hoe beter de concepten al aansluiten op hoe jij het schrijft.
            </p>
          </>
        )}
      </div>

      {/* Geleerde voorbeelden */}
      <div className="rounded-xl border border-border bg-card p-5">
        <div className="flex items-center justify-between gap-3 mb-3">
          <div className="flex items-center gap-2">
            <BookOpen className="h-4 w-4 text-blue-600" />
            <h3 className="text-sm font-semibold text-foreground">
              Geleerde voorbeelden ({data?.total_examples ?? 0})
            </h3>
          </div>
          <button
            type="button"
            onClick={() => backfill.mutate()}
            disabled={backfill.isPending}
            className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-card px-3 py-1.5 text-xs font-medium text-foreground hover:bg-muted transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${backfill.isPending ? "animate-spin" : ""}`} />
            Nu bijwerken
          </button>
        </div>

        {perCat.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            Nog geen voorbeelden geleerd. Klik op &quot;Nu bijwerken&quot; om te leren van je
            reeds verstuurde antwoorden, of verstuur een paar antwoorden — het vult zich
            daarna vanzelf.
          </p>
        ) : (
          <div className="space-y-1.5">
            {perCat.map(([cat, count]) => (
              <div key={cat} className="flex items-center justify-between text-sm">
                <span className="text-foreground">{catLabel(cat)}</span>
                <span className="font-medium tabular-nums text-muted-foreground">{count}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Meest gebruikt */}
      {data?.top_examples && data.top_examples.length > 0 && (
        <div className="rounded-xl border border-border bg-card p-5">
          <h3 className="text-sm font-semibold text-foreground mb-3">
            Van welke antwoorden leert de AI het meest?
          </h3>
          <div className="space-y-3">
            {data.top_examples.map((ex, i) => (
              <div key={i} className="rounded-lg border border-border p-3">
                <div className="flex items-center justify-between gap-2 mb-1">
                  <span className="text-xs font-medium text-primary">{catLabel(ex.category)}</span>
                  <span className="text-[11px] text-muted-foreground">
                    {ex.use_count}× gebruikt
                  </span>
                </div>
                <p className="text-xs text-muted-foreground line-clamp-2">{ex.preview}…</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function Legend({
  color,
  label,
  value,
  pct,
}: {
  color: string;
  label: string;
  value: number;
  pct: number;
}) {
  return (
    <div>
      <div className="flex items-center justify-center gap-1.5">
        <span className={`h-2 w-2 rounded-full ${color}`} />
        <span className="text-sm font-semibold text-foreground tabular-nums">{pct}%</span>
      </div>
      <p className="text-[11px] text-muted-foreground">{label}</p>
      <p className="text-[11px] text-muted-foreground tabular-nums">({value})</p>
    </div>
  );
}
