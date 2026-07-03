"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Sparkles, RefreshCw, TrendingUp, BookOpen, Info, Check, X, ClipboardCheck } from "lucide-react";
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
  candidates: number;
  total_examples: number;
  per_category: Record<string, number>;
  top_examples: { category: string; use_count: number; preview: string }[];
}

interface Candidate {
  id: string;
  category: string;
  defense_type: string | null;
  body: string;
  anonymized_body: string | null;
  created_at: string | null;
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

// Type verweer — bepaalt waarop de AI dit voorbeeld matcht.
const DEFENSE_TYPE_LABELS: Record<string, string> = {
  verlengd_abonnement: "Stilzwijgende verlenging abonnement",
  annuleringskosten_9_3: "Annuleringskosten (art. 9.3)",
  afrekening_voorwaarden_20_4: "Afrekening (art. 20.4)",
  ncnp_verweer_gerechtelijk: "No cure no pay",
  english_renewal_9_3: "Engels: verlenging / annulering",
  overig: "Overig / nieuw type",
};
const DEFENSE_TYPE_KEYS = Object.keys(DEFENSE_TYPE_LABELS);

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

  const { data: candidates } = useQuery<Candidate[]>({
    queryKey: ["learning-candidates"],
    queryFn: async () => {
      const res = await api("/api/ai-agent/learning/candidates");
      if (!res.ok) throw new Error("Kon kandidaten niet laden");
      return res.json();
    },
  });

  const backfill = useMutation({
    mutationFn: async () => {
      const res = await api("/api/ai-agent/learning/backfill", { method: "POST" });
      if (!res.ok) throw new Error("Zoeken naar kandidaten mislukt");
      return res.json() as Promise<{ added: number }>;
    },
    onSuccess: (r) => {
      toast.success(
        r.added > 0
          ? `${r.added} nieuw${r.added === 1 ? "e kandidaat" : "e kandidaten"} gevonden om te beoordelen`
          : "Geen nieuwe kandidaten — alles is al verwerkt"
      );
      queryClient.invalidateQueries({ queryKey: ["learning-candidates"] });
      queryClient.invalidateQueries({ queryKey: ["learning-stats"] });
    },
    onError: (e: unknown) => toast.error(e instanceof Error ? e.message : "Zoeken mislukt"),
  });

  const approve = useMutation({
    mutationFn: async (vars: { id: string; anonymized_body: string; defense_type: string }) => {
      const res = await api(`/api/ai-agent/learning/candidates/${vars.id}/approve`, {
        method: "POST",
        body: JSON.stringify({
          anonymized_body: vars.anonymized_body,
          defense_type: vars.defense_type,
        }),
      });
      if (!res.ok) throw new Error("Goedkeuren mislukt");
      return res.json();
    },
    onSuccess: () => {
      toast.success("Goedgekeurd — de AI gebruikt dit voortaan als voorbeeld");
      queryClient.invalidateQueries({ queryKey: ["learning-candidates"] });
      queryClient.invalidateQueries({ queryKey: ["learning-stats"] });
    },
    onError: (e: unknown) => toast.error(e instanceof Error ? e.message : "Goedkeuren mislukt"),
  });

  const reject = useMutation({
    mutationFn: async (id: string) => {
      const res = await api(`/api/ai-agent/learning/candidates/${id}/reject`, { method: "POST" });
      if (!res.ok) throw new Error("Afwijzen mislukt");
      return res.json();
    },
    onSuccess: () => {
      toast.success("Afgewezen — dit voorbeeld wordt niet gebruikt");
      queryClient.invalidateQueries({ queryKey: ["learning-candidates"] });
      queryClient.invalidateQueries({ queryKey: ["learning-stats"] });
    },
    onError: (e: unknown) => toast.error(e instanceof Error ? e.message : "Afwijzen mislukt"),
  });

  if (isLoading) {
    return <div className="h-40 rounded-xl skeleton" />;
  }

  const er = data?.edit_rate ?? { matched: 0, ongewijzigd: 0, licht: 0, fors: 0 };
  const total = er.matched || 0;
  const pct = (n: number) => (total > 0 ? Math.round((n / total) * 100) : 0);
  const perCat = Object.entries(data?.per_category ?? {}).sort((a, b) => b[1] - a[1]);
  const busy = approve.isPending || reject.isPending;

  return (
    <div className="space-y-6">
      {/* Header + uitleg */}
      <div>
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-violet-500" />
          <h2 className="text-lg font-semibold text-foreground">Slim leren</h2>
        </div>
        <p className="mt-1 text-sm text-muted-foreground">
          De AI stelt voor om jouw eigen sterke weerleggingen als vast standaardantwoord op
          te slaan. Jij beslist: controleer de geanonimiseerde tekst, keur goed of wijs af.
          Alleen goedgekeurde antwoorden gebruikt de AI later als voorbeeld — nooit iets
          zonder jouw akkoord.
        </p>
      </div>

      {/* Kandidaten om te beoordelen */}
      <div className="rounded-xl border border-border bg-card p-5">
        <div className="flex items-center justify-between gap-3 mb-3">
          <div className="flex items-center gap-2">
            <ClipboardCheck className="h-4 w-4 text-violet-600" />
            <h3 className="text-sm font-semibold text-foreground">
              Te beoordelen ({candidates?.length ?? 0})
            </h3>
          </div>
          <button
            type="button"
            onClick={() => backfill.mutate()}
            disabled={backfill.isPending}
            className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-card px-3 py-1.5 text-xs font-medium text-foreground hover:bg-muted transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${backfill.isPending ? "animate-spin" : ""}`} />
            Zoek nieuwe kandidaten
          </button>
        </div>

        {!candidates || candidates.length === 0 ? (
          <div className="flex items-start gap-2 rounded-lg bg-muted/50 p-3 text-sm text-muted-foreground">
            <Info className="h-4 w-4 mt-0.5 shrink-0" />
            <span>
              Geen kandidaten om te beoordelen. Zodra je maatwerk-weerleggingen verstuurt die
              nog niet in de standaardantwoorden zitten, verschijnen ze hier automatisch.
            </span>
          </div>
        ) : (
          <div className="space-y-4">
            {candidates.map((c) => (
              <CandidateCard
                key={c.id}
                candidate={c}
                busy={busy}
                onApprove={(vars) => approve.mutate(vars)}
                onReject={(id) => reject.mutate(id)}
              />
            ))}
          </div>
        )}
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

      {/* Goedgekeurde voorbeelden */}
      <div className="rounded-xl border border-border bg-card p-5">
        <div className="flex items-center gap-2 mb-3">
          <BookOpen className="h-4 w-4 text-blue-600" />
          <h3 className="text-sm font-semibold text-foreground">
            Goedgekeurde standaardantwoorden ({data?.total_examples ?? 0})
          </h3>
        </div>

        {perCat.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            Nog geen goedgekeurde voorbeelden. Beoordeel hierboven een kandidaat om de eerste
            toe te voegen.
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

// ── Kandidaat-kaart: controleer geanonimiseerde tekst → goedkeuren/afwijzen ──
function CandidateCard({
  candidate,
  busy,
  onApprove,
  onReject,
}: {
  candidate: Candidate;
  busy: boolean;
  onApprove: (vars: { id: string; anonymized_body: string; defense_type: string }) => void;
  onReject: (id: string) => void;
}) {
  const [text, setText] = useState(candidate.anonymized_body ?? candidate.body);
  const [type, setType] = useState(
    candidate.defense_type && DEFENSE_TYPE_KEYS.includes(candidate.defense_type)
      ? candidate.defense_type
      : "overig"
  );

  return (
    <div className="rounded-lg border border-border p-4 space-y-3">
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-medium text-primary">{catLabel(candidate.category)}</span>
        <select
          value={type}
          onChange={(e) => setType(e.target.value)}
          className="rounded-md border border-border bg-card px-2 py-1 text-xs text-foreground"
        >
          {DEFENSE_TYPE_KEYS.map((k) => (
            <option key={k} value={k}>
              {DEFENSE_TYPE_LABELS[k]}
            </option>
          ))}
        </select>
      </div>

      {/* Origineel ter referentie — kan nog namen/bedragen bevatten */}
      <details>
        <summary className="text-xs text-muted-foreground cursor-pointer select-none">
          Origineel tonen (met gegevens)
        </summary>
        <p className="mt-2 whitespace-pre-wrap rounded-md bg-muted/50 p-2 text-xs text-muted-foreground">
          {candidate.body}
        </p>
      </details>

      <div>
        <label className="text-xs font-medium text-foreground">
          Geanonimiseerde tekst — controleer dat er geen namen, bedragen of datums meer in staan:
        </label>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={6}
          className="mt-1.5 w-full rounded-md border border-border bg-card p-2.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
        />
      </div>

      <div className="flex items-center justify-end gap-2">
        <button
          type="button"
          onClick={() => onReject(candidate.id)}
          disabled={busy}
          className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-card px-3 py-1.5 text-xs font-medium text-muted-foreground hover:bg-muted transition-colors disabled:opacity-50"
        >
          <X className="h-3.5 w-3.5" />
          Afwijzen
        </button>
        <button
          type="button"
          onClick={() => onApprove({ id: candidate.id, anonymized_body: text, defense_type: type })}
          disabled={busy || text.trim().length < 20}
          className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50"
        >
          <Check className="h-3.5 w-3.5" />
          Goedkeuren
        </button>
      </div>
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
