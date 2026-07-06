"use client";

import { useMemo, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Sparkles,
  RefreshCw,
  TrendingUp,
  BookOpen,
  Info,
  Check,
  X,
  ClipboardCheck,
  ChevronRight,
  ChevronDown,
  AlertTriangle,
  Trash2,
  CheckSquare,
  Square,
} from "lucide-react";
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
  // Bron-context (S174): waar kwam dit antwoord vandaan?
  case_number: string | null;
  debtor: string | null;
  source_subject: string | null;
  source_date: string | null;
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

// Verweer-type (13 types, S174) — bepaalt waarop de AI dit voorbeeld matcht. Gespiegeld
// aan backend `app/ai_agent/defense_types.py` (DEFENSE_TYPE_LABELS) — houd beide gelijk.
const DEFENSE_TYPE_LABELS: Record<string, string> = {
  afwikkeling_intrekking: "Afwikkeling / intrekking opdracht (art. 9.3 / 20.4)",
  verlenging_opzegging: "Stilzwijgende verlenging / opzegging",
  betwisting_ongemotiveerd: "Ongemotiveerde betwisting",
  reeds_betaald_verrekening: "Reeds betaald / verrekening",
  consumentenbescherming_b2b: "Consumentenberoep (zakelijk → afgewezen)",
  betalingsregeling_schikking: "Betalingsregeling / schikking",
  derde_partij: "Advocaat / verzekeraar / derde partij",
  klacht_dienstverlening: "Klacht over dienstverlening",
  ncnp_gerechtelijke_fase: "No cure no pay (gerechtelijke fase)",
  vertegenwoordiging: "Onbevoegde vertegenwoordiging",
  opschorting_tegenvordering: "Opschorting / tegenvordering",
  av_toepasselijkheid: "Toepasselijkheid voorwaarden",
  kosten_rente_hoogte: "Hoogte kosten / rente",
  overig: "Overig / nieuw type",
};

// Oude keys (van vóór S174) → nieuwe groep, zodat bestaande kandidaten niet als 'overig'
// wegvallen tot het relabel-script is gedraaid. Gespiegeld aan backend LEGACY_TYPE_ALIASES.
const LEGACY_TYPE_ALIASES: Record<string, string> = {
  annuleringskosten_9_3: "afwikkeling_intrekking",
  afrekening_voorwaarden_20_4: "afwikkeling_intrekking",
  ncnp_verweer_gerechtelijk: "ncnp_gerechtelijke_fase",
  verlengd_abonnement: "verlenging_opzegging",
  english_renewal_9_3: "afwikkeling_intrekking",
};
// Keuzelijst bij goedkeuren: alleen de 13 actuele types + overig (geen oude aliassen).
const DEFENSE_TYPE_KEYS = [
  "afwikkeling_intrekking",
  "verlenging_opzegging",
  "betwisting_ongemotiveerd",
  "reeds_betaald_verrekening",
  "consumentenbescherming_b2b",
  "betalingsregeling_schikking",
  "derde_partij",
  "klacht_dienstverlening",
  "ncnp_gerechtelijke_fase",
  "vertegenwoordiging",
  "opschorting_tegenvordering",
  "av_toepasselijkheid",
  "kosten_rente_hoogte",
  "overig",
];

function catLabel(key: string): string {
  return CATEGORY_LABELS[key] ?? key;
}

// Normaliseer het verweer-type naar een actuele groep-key (oude alias → nieuwe groep;
// null/onbekend → 'overig'). Resultaat zit altijd in DEFENSE_TYPE_KEYS.
function typeKey(c: Candidate): string {
  const t = c.defense_type;
  if (!t) return "overig";
  if (DEFENSE_TYPE_LABELS[t]) return t;
  return LEGACY_TYPE_ALIASES[t] ?? "overig";
}

// ── PII-hulp: mogelijke overgebleven namen opsporen ──────────────────────
// Woorden met een hoofdletter MIDDEN in een zin (voorafgegaan door een kleine letter,
// komma of haakje) zijn zelden een zinsbegin en vaak een eigennaam of bedrijfsnaam die
// het anonimiseer-voorstel liet staan. Puur een waarschuwing — Lisanne beslist.
const NAME_STOPWORDS = new Set([
  "Cliënte", "Cliënt", "Client", "Uw", "Ik", "Hierbij", "Vordering", "Sommatie",
  "Laatste", "Factuurnummer", "Datum", "Bedrag", "Thans", "BW", "IBAN", "EUR",
  "No", "Cure", "Pay", "Engels", "Betreft", "Geachte", "Artikel", "Indien",
]);
const MID_SENTENCE_CAP = /(?<=[a-zà-ÿ,)]\s)([A-ZÀ-Ÿ][a-zà-ÿ]{2,})/g;
const EMAIL_RE = /[\w.+-]+@[\w.-]+\.\w{2,}/g;

// Mogelijke overgebleven persoonsgegevens: namen/bedrijven (hoofdletter mid-zin) én
// e-mailadressen (die het anonimiseer-voorstel ook liet staan — echte prod-lek S169).
function suspectNames(text: string): string[] {
  const out = new Set<string>();
  for (const m of text.matchAll(EMAIL_RE)) out.add(m[0]);
  for (const m of text.matchAll(MID_SENTENCE_CAP)) {
    const w = m[1];
    if (!NAME_STOPWORDS.has(w)) out.add(w);
  }
  return [...out].slice(0, 8);
}

// Toon de opgeslagen tekst met plaatshouders groen en verdachte resten amber gemarkeerd.
function Highlighted({ text, suspects }: { text: string; suspects: string[] }) {
  const flagged = new Set(suspects);
  const tokens = text.split(/(\[[^\]]+\]|[\w.+-]+@[\w.-]+\.\w{2,}|\s+)/);
  return (
    <p className="whitespace-pre-wrap break-words rounded-md border border-border bg-muted/30 p-2.5 text-xs leading-relaxed text-foreground">
      {tokens.map((tok, i) => {
        if (/^\[[^\]]+\]$/.test(tok)) {
          return (
            <mark key={i} className="rounded bg-emerald-500/15 px-0.5 text-emerald-700 dark:text-emerald-300">
              {tok}
            </mark>
          );
        }
        if (flagged.has(tok) || flagged.has(tok.replace(/[^\wÀ-ÿ]/g, ""))) {
          return (
            <mark key={i} className="rounded bg-amber-500/20 px-0.5 text-amber-700 dark:text-amber-300">
              {tok}
            </mark>
          );
        }
        return <span key={i}>{tok}</span>;
      })}
    </p>
  );
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

  // Beoordeeld-teller voor deze sessie (voortgangsgevoel bij een lange wachtrij).
  const [reviewed, setReviewed] = useState(0);
  const [catFilter, setCatFilter] = useState<string>("alle");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  const dropFromCache = (ids: Set<string>) =>
    queryClient.setQueryData<Candidate[]>(["learning-candidates"], (old) =>
      (old ?? []).filter((c) => !ids.has(c.id))
    );

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
    onSuccess: (_r, vars) => {
      dropFromCache(new Set([vars.id]));
      setReviewed((n) => n + 1);
      queryClient.invalidateQueries({ queryKey: ["learning-stats"] });
      toast.success("Goedgekeurd — de AI gebruikt dit voortaan als voorbeeld");
    },
    onError: (e: unknown) => toast.error(e instanceof Error ? e.message : "Goedkeuren mislukt"),
  });

  const reject = useMutation({
    mutationFn: async (id: string) => {
      const res = await api(`/api/ai-agent/learning/candidates/${id}/reject`, { method: "POST" });
      if (!res.ok) throw new Error("Afwijzen mislukt");
      return res.json();
    },
    onSuccess: (_r, id) => {
      dropFromCache(new Set([id]));
      setReviewed((n) => n + 1);
      queryClient.invalidateQueries({ queryKey: ["learning-stats"] });
      toast.success("Afgewezen — dit voorbeeld wordt niet gebruikt");
    },
    onError: (e: unknown) => toast.error(e instanceof Error ? e.message : "Afwijzen mislukt"),
  });

  const rejectBulk = useMutation({
    mutationFn: async (ids: string[]) => {
      const res = await api("/api/ai-agent/learning/candidates/reject-bulk", {
        method: "POST",
        body: JSON.stringify({ ids }),
      });
      if (!res.ok) throw new Error("Bulk afwijzen mislukt");
      return res.json() as Promise<{ rejected: number }>;
    },
    onSuccess: (r, ids) => {
      dropFromCache(new Set(ids));
      setReviewed((n) => n + r.rejected);
      setSelected(new Set());
      queryClient.invalidateQueries({ queryKey: ["learning-stats"] });
      toast.success(`${r.rejected} afgewezen`);
    },
    onError: (e: unknown) => toast.error(e instanceof Error ? e.message : "Bulk afwijzen mislukt"),
  });

  const pending = approve.isPending || reject.isPending || rejectBulk.isPending;

  // Zichtbare kandidaten (na categoriefilter) en gegroepeerd per verweer-type.
  const visible = useMemo(
    () => (candidates ?? []).filter((c) => catFilter === "alle" || c.category === catFilter),
    [candidates, catFilter]
  );

  const groups = useMemo(() => {
    const byType = new Map<string, Candidate[]>();
    for (const c of visible) {
      const t = typeKey(c);
      let arr = byType.get(t);
      if (!arr) {
        arr = [];
        byType.set(t, arr);
      }
      arr.push(c);
    }
    // Binnen een groep op tekst-begin sorteren → bijna-identieke sjablonen komen naast elkaar.
    for (const arr of byType.values()) {
      arr.sort((a, b) =>
        (a.body || "").slice(0, 140).localeCompare((b.body || "").slice(0, 140))
      );
    }
    return DEFENSE_TYPE_KEYS.filter((t) => byType.has(t)).map(
      (t) => [t, byType.get(t)!] as const
    );
  }, [visible]);

  if (isLoading) {
    return <div className="h-40 rounded-xl skeleton" />;
  }

  const er = data?.edit_rate ?? { matched: 0, ongewijzigd: 0, licht: 0, fors: 0 };
  const total = er.matched || 0;
  const pct = (n: number) => (total > 0 ? Math.round((n / total) * 100) : 0);
  const perCat = Object.entries(data?.per_category ?? {}).sort((a, b) => b[1] - a[1]);

  const visibleIds = visible.map((c) => c.id);
  const allVisibleSelected =
    visibleIds.length > 0 && visibleIds.every((id) => selected.has(id));

  const toggleSel = (id: string) =>
    setSelected((prev) => {
      const n = new Set(prev);
      if (n.has(id)) n.delete(id);
      else n.add(id);
      return n;
    });
  const toggleExpand = (id: string) =>
    setExpanded((prev) => {
      const n = new Set(prev);
      if (n.has(id)) n.delete(id);
      else n.add(id);
      return n;
    });
  const toggleSelectAllVisible = () =>
    setSelected((prev) => {
      if (allVisibleSelected) {
        const n = new Set(prev);
        visibleIds.forEach((id) => n.delete(id));
        return n;
      }
      return new Set([...prev, ...visibleIds]);
    });
  const doBulkReject = () => {
    const ids = [...selected];
    if (ids.length === 0) return;
    if (
      !window.confirm(
        `${ids.length} kandidaat${ids.length === 1 ? "" : "en"} afwijzen? ` +
          "Ze voeden de AI dan niet — dit is een status-wijziging, geen definitieve verwijdering."
      )
    )
      return;
    rejectBulk.mutate(ids);
  };

  const catFilters: { id: string; label: string }[] = [
    { id: "alle", label: "Alle" },
    { id: "juridisch_verweer", label: "Juridisch verweer" },
    { id: "betwisting", label: "Betwisting" },
  ];

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
        <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
          <div className="flex items-center gap-2">
            <ClipboardCheck className="h-4 w-4 text-violet-600" />
            <h3 className="text-sm font-semibold text-foreground">
              Te beoordelen ({candidates?.length ?? 0})
            </h3>
            {reviewed > 0 && (
              <span className="text-xs text-muted-foreground">· {reviewed} beoordeeld deze sessie</span>
            )}
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
          <>
            {/* Werkwijze-tip: niet alles hoeft, keur per type je beste goed. */}
            <div className="mb-3 flex items-start gap-2 rounded-lg bg-violet-500/10 p-3 text-xs text-foreground">
              <Info className="h-4 w-4 mt-0.5 shrink-0 text-violet-600" />
              <span>
                Je hoeft niet alle {candidates.length} te beoordelen. De AI pakt per verweer-type
                maar een paar van je beste antwoorden. Keur per groep je sterkste weerlegging goed
                en wijs de rest — dubbelingen en ruis — gerust in bulk af.
              </span>
            </div>

            {/* Filter + bulk-balk */}
            <div className="mb-3 flex flex-wrap items-center gap-2">
              {catFilters.map((f) => (
                <button
                  key={f.id}
                  type="button"
                  onClick={() => setCatFilter(f.id)}
                  className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                    catFilter === f.id
                      ? "bg-primary text-primary-foreground"
                      : "border border-border bg-card text-muted-foreground hover:bg-muted"
                  }`}
                >
                  {f.label}
                </button>
              ))}
              <div className="ml-auto flex items-center gap-2">
                <button
                  type="button"
                  onClick={toggleSelectAllVisible}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-card px-2.5 py-1 text-xs font-medium text-muted-foreground hover:bg-muted transition-colors"
                >
                  {allVisibleSelected ? (
                    <CheckSquare className="h-3.5 w-3.5" />
                  ) : (
                    <Square className="h-3.5 w-3.5" />
                  )}
                  {allVisibleSelected ? "Selectie wissen" : "Selecteer zichtbare"}
                </button>
                {selected.size > 0 && (
                  <button
                    type="button"
                    onClick={doBulkReject}
                    disabled={pending}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-red-300 bg-red-50 px-3 py-1 text-xs font-medium text-red-700 hover:bg-red-100 transition-colors disabled:opacity-50 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                    Wijs {selected.size} af
                  </button>
                )}
              </div>
            </div>

            {/* Gegroepeerde, compacte lijst */}
            <div className="space-y-5">
              {groups.map(([type, items]) => (
                <div key={type}>
                  <div className="mb-1.5 flex items-center gap-2 px-0.5">
                    <span className="text-xs font-semibold text-foreground">
                      {DEFENSE_TYPE_LABELS[type]}
                    </span>
                    <span className="text-[11px] text-muted-foreground">({items.length})</span>
                  </div>
                  <div className="divide-y divide-border rounded-lg border border-border">
                    {items.map((c) => (
                      <CandidateRow
                        key={c.id}
                        candidate={c}
                        selected={selected.has(c.id)}
                        expanded={expanded.has(c.id)}
                        disabled={pending}
                        onToggleSelect={() => toggleSel(c.id)}
                        onToggleExpand={() => toggleExpand(c.id)}
                        onApprove={(vars) => approve.mutate(vars)}
                        onReject={(id) => reject.mutate(id)}
                      />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>

      {/* Kwaliteit: edit-rate */}
      <div className="rounded-xl border border-border bg-card p-5">
        <div className="flex items-center gap-2 mb-3">
          <TrendingUp className="h-4 w-4 text-emerald-600" />
          <h3 className="text-sm font-semibold text-foreground">Hoeveel pas je nog aan?</h3>
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

// ── Kandidaat-rij: compact ingeklapt, editor bij uitklappen ──────────────
function CandidateRow({
  candidate,
  selected,
  expanded,
  disabled,
  onToggleSelect,
  onToggleExpand,
  onApprove,
  onReject,
}: {
  candidate: Candidate;
  selected: boolean;
  expanded: boolean;
  disabled: boolean;
  onToggleSelect: () => void;
  onToggleExpand: () => void;
  onApprove: (vars: { id: string; anonymized_body: string; defense_type: string }) => void;
  onReject: (id: string) => void;
}) {
  const [text, setText] = useState(candidate.anonymized_body ?? candidate.body);
  const [type, setType] = useState(typeKey(candidate));

  const preview = (candidate.anonymized_body ?? candidate.body).replace(/\s+/g, " ").trim();
  const suspects = expanded ? suspectNames(text) : [];

  return (
    <div className="text-sm">
      {/* Compacte kop — altijd zichtbaar */}
      <div className="flex items-center gap-2 px-3 py-2">
        <input
          type="checkbox"
          checked={selected}
          onChange={onToggleSelect}
          onClick={(e) => e.stopPropagation()}
          className="h-3.5 w-3.5 shrink-0 cursor-pointer accent-primary"
          aria-label="Selecteer kandidaat"
        />
        <button
          type="button"
          onClick={onToggleExpand}
          className="flex min-w-0 flex-1 items-center gap-2 text-left"
        >
          {expanded ? (
            <ChevronDown className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
          ) : (
            <ChevronRight className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
          )}
          <span className="shrink-0 rounded bg-muted px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground">
            {catLabel(candidate.category)}
          </span>
          <span className="truncate text-xs text-foreground">{preview}</span>
          <span className="ml-auto shrink-0 text-[10px] tabular-nums text-muted-foreground">
            {preview.length} tekens
          </span>
        </button>
      </div>

      {/* Editor — alleen bij uitklappen (houdt de lijst kort) */}
      {expanded && (
        <div className="space-y-3 border-t border-border bg-muted/20 p-4">
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

          {/* Bron-context (S174): op welke mail/dossier was dit antwoord? */}
          {(candidate.case_number || candidate.source_subject) && (
            <div className="rounded-md border border-border bg-muted/30 px-2.5 py-2 text-[11px] leading-relaxed text-muted-foreground">
              <span className="font-medium text-foreground">Bron: </span>
              {candidate.case_number ? `dossier ${candidate.case_number}` : "onbekend dossier"}
              {candidate.debtor ? ` · ${candidate.debtor}` : ""}
              {candidate.source_subject && (
                <>
                  <br />
                  <span className="italic">&ldquo;{candidate.source_subject}&rdquo;</span>
                  {candidate.source_date
                    ? ` · ${new Date(candidate.source_date).toLocaleDateString("nl-NL")}`
                    : ""}
                </>
              )}
            </div>
          )}

          {/* Origineel ter referentie — kan nog namen/bedragen bevatten */}
          <details>
            <summary className="text-xs text-muted-foreground cursor-pointer select-none">
              Origineel tonen (met gegevens)
            </summary>
            <p className="mt-2 whitespace-pre-wrap break-words rounded-md bg-muted/50 p-2 text-xs text-muted-foreground">
              {candidate.body}
            </p>
          </details>

          {/* Gemarkeerd voorbeeld: plaatshouders groen, mogelijke namen amber */}
          <div>
            <label className="text-xs font-medium text-foreground">
              Voorbeeld zoals opgeslagen — plaatshouders staan groen, mogelijke resten amber:
            </label>
            <div className="mt-1.5">
              <Highlighted text={text} suspects={suspects} />
            </div>
            {suspects.length > 0 && (
              <div className="mt-2 flex flex-wrap items-center gap-1.5">
                <AlertTriangle className="h-3.5 w-3.5 text-amber-600" />
                <span className="text-[11px] text-amber-700 dark:text-amber-400">
                  Mogelijk nog een naam, bedrijf of e-mailadres:
                </span>
                {suspects.map((s) => (
                  <span
                    key={s}
                    className="rounded bg-amber-500/15 px-1.5 py-0.5 text-[11px] text-amber-700 dark:text-amber-300"
                  >
                    {s}
                  </span>
                ))}
              </div>
            )}
          </div>

          <div>
            <label className="text-xs font-medium text-foreground">
              Pas de geanonimiseerde tekst zo nodig aan:
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
              disabled={disabled}
              className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-card px-3 py-1.5 text-xs font-medium text-muted-foreground hover:bg-muted transition-colors disabled:opacity-50"
            >
              <X className="h-3.5 w-3.5" />
              Afwijzen
            </button>
            <button
              type="button"
              onClick={() => onApprove({ id: candidate.id, anonymized_body: text, defense_type: type })}
              disabled={disabled || text.trim().length < 20}
              className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50"
            >
              <Check className="h-3.5 w-3.5" />
              Goedkeuren
            </button>
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
