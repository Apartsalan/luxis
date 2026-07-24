"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Scale, Plus, Check, X, Pencil, Trash2, Info, AlertTriangle } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { DEFENSE_TYPE_LABELS, DEFENSE_TYPE_KEYS } from "./ai-leren-tab";

// ── Types ────────────────────────────────────────────────────────────────
interface KnowledgeRule {
  id: string;
  defense_type: string;
  applies_to: string;
  title: string;
  claim_description: string | null;
  rebuttal_body: string;
  legal_basis: string | null;
  status: string;
  is_active: boolean;
  reviewed_at: string | null;
  created_at: string | null;
}

type RuleForm = {
  defense_type: string;
  applies_to: string;
  title: string;
  claim_description: string;
  rebuttal_body: string;
  legal_basis: string;
};

const APPLIES_TO_LABELS: Record<string, string> = {
  alle: "Iedereen",
  zakelijk: "Alleen zakelijk (B2B)",
  consument: "Alleen consument (B2C)",
};

const STATUS_LABELS: Record<string, { label: string; cls: string }> = {
  goedgekeurd: {
    label: "Actief",
    cls: "bg-emerald-500/15 text-emerald-700 dark:text-emerald-300",
  },
  kandidaat: {
    label: "Concept",
    cls: "bg-amber-500/15 text-amber-700 dark:text-amber-300",
  },
  afgewezen: {
    label: "Uit",
    cls: "bg-muted text-muted-foreground",
  },
};

const EMPTY_FORM: RuleForm = {
  defense_type: "av_toepasselijkheid",
  applies_to: "zakelijk",
  title: "",
  claim_description: "",
  rebuttal_body: "",
  legal_basis: "",
};

export function KnowledgeRulesSection() {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<RuleForm>(EMPTY_FORM);

  const { data: rules, isLoading } = useQuery<KnowledgeRule[]>({
    queryKey: ["knowledge-rules"],
    queryFn: async () => {
      const res = await api("/api/ai-agent/learning/rules");
      if (!res.ok) throw new Error("Kon kennisregels niet laden");
      return res.json();
    },
  });

  const invalidate = () =>
    queryClient.invalidateQueries({ queryKey: ["knowledge-rules"] });

  const resetForm = () => {
    setForm(EMPTY_FORM);
    setShowForm(false);
    setEditingId(null);
  };

  const save = useMutation({
    mutationFn: async (vars: { id: string | null; form: RuleForm }) => {
      const url = vars.id
        ? `/api/ai-agent/learning/rules/${vars.id}`
        : "/api/ai-agent/learning/rules";
      const res = await api(url, {
        method: vars.id ? "PUT" : "POST",
        body: JSON.stringify(vars.form),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Opslaan mislukt");
      }
      return res.json();
    },
    onSuccess: (_r, vars) => {
      invalidate();
      resetForm();
      toast.success(
        vars.id
          ? "Regel bijgewerkt"
          : "Regel opgeslagen als concept — keur hem goed om de AI hem te laten gebruiken"
      );
    },
    onError: (e: unknown) => toast.error(e instanceof Error ? e.message : "Opslaan mislukt"),
  });

  const approve = useMutation({
    mutationFn: async (id: string) => {
      const res = await api(`/api/ai-agent/learning/rules/${id}/approve`, { method: "POST" });
      if (!res.ok) throw new Error("Goedkeuren mislukt");
      return res.json();
    },
    onSuccess: () => {
      invalidate();
      toast.success("Goedgekeurd — de AI gebruikt deze regel voortaan");
    },
    onError: (e: unknown) => toast.error(e instanceof Error ? e.message : "Goedkeuren mislukt"),
  });

  const reject = useMutation({
    mutationFn: async (id: string) => {
      const res = await api(`/api/ai-agent/learning/rules/${id}/reject`, { method: "POST" });
      if (!res.ok) throw new Error("Uitzetten mislukt");
      return res.json();
    },
    onSuccess: () => {
      invalidate();
      toast.success("Uitgezet — de AI gebruikt deze regel niet meer");
    },
    onError: (e: unknown) => toast.error(e instanceof Error ? e.message : "Uitzetten mislukt"),
  });

  const remove = useMutation({
    mutationFn: async (id: string) => {
      const res = await api(`/api/ai-agent/learning/rules/${id}`, { method: "DELETE" });
      if (!res.ok) throw new Error("Verwijderen mislukt");
      return res.json();
    },
    onSuccess: () => {
      invalidate();
      toast.success("Regel verwijderd");
    },
    onError: (e: unknown) => toast.error(e instanceof Error ? e.message : "Verwijderen mislukt"),
  });

  const startEdit = (r: KnowledgeRule) => {
    setForm({
      defense_type: r.defense_type,
      applies_to: r.applies_to,
      title: r.title,
      claim_description: r.claim_description ?? "",
      rebuttal_body: r.rebuttal_body,
      legal_basis: r.legal_basis ?? "",
    });
    setEditingId(r.id);
    setShowForm(true);
  };

  const doDelete = (id: string) => {
    if (!window.confirm("Deze regel definitief verwijderen?")) return;
    remove.mutate(id);
  };

  const canSave = form.title.trim().length > 0 && form.rebuttal_body.trim().length >= 20;
  const pending = save.isPending || approve.isPending || reject.isPending || remove.isPending;

  return (
    <div className="rounded-xl border border-border bg-card p-5">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
        <div className="flex items-center gap-2">
          <Scale className="h-4 w-4 text-blue-600" />
          <h3 className="text-sm font-semibold text-foreground">
            Juridische kennisregels ({rules?.length ?? 0})
          </h3>
        </div>
        {!showForm && (
          <button
            type="button"
            onClick={() => {
              setForm(EMPTY_FORM);
              setEditingId(null);
              setShowForm(true);
            }}
            className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-card px-3 py-1.5 text-xs font-medium text-foreground hover:bg-muted transition-colors"
          >
            <Plus className="h-3.5 w-3.5" />
            Nieuwe regel
          </button>
        )}
      </div>

      <div className="mb-4 flex items-start gap-2 rounded-lg bg-blue-500/10 p-3 text-xs text-foreground">
        <Info className="h-4 w-4 mt-0.5 shrink-0 text-blue-600" />
        <span>
          Leg vast welke standaard-verweren onjuist zijn en waarom (met wetsartikel). Anders
          dan &ldquo;Slim leren&rdquo; hierboven — dat leert van je verstuurde mails — tik je
          hier zelf de kennis in. De AI gebruikt een regel alleen als de debiteur dat verweer
          voert én de voorwaarde (iedereen / zakelijk / consument) klopt. Een regel telt pas
          mee nadat je hem goedkeurt.
        </span>
      </div>

      {/* Formulier */}
      {showForm && (
        <div className="mb-4 space-y-3 rounded-lg border border-border bg-muted/20 p-4">
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className="text-xs font-medium text-foreground">Bij welk verweer?</label>
              <select
                value={form.defense_type}
                onChange={(e) => setForm({ ...form, defense_type: e.target.value })}
                className="mt-1 w-full rounded-md border border-border bg-card px-2 py-1.5 text-xs text-foreground"
              >
                {DEFENSE_TYPE_KEYS.filter((k) => k !== "overig").map((k) => (
                  <option key={k} value={k}>
                    {DEFENSE_TYPE_LABELS[k]}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs font-medium text-foreground">Geldt voor</label>
              <select
                value={form.applies_to}
                onChange={(e) => setForm({ ...form, applies_to: e.target.value })}
                className="mt-1 w-full rounded-md border border-border bg-card px-2 py-1.5 text-xs text-foreground"
              >
                {Object.entries(APPLIES_TO_LABELS).map(([k, v]) => (
                  <option key={k} value={k}>
                    {v}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {form.applies_to === "consument" && (
            <div className="flex items-start gap-2 rounded-md bg-amber-500/10 p-2 text-[11px] text-amber-700 dark:text-amber-300">
              <AlertTriangle className="h-3.5 w-3.5 mt-0.5 shrink-0" />
              <span>
                Let op: veel &ldquo;standaard&rdquo;-weerleggingen (zoals de onmogelijkheid om
                de voorwaarden te vernietigen) gelden juist NIET voor consumenten. Weet je
                zeker dat deze regel voor consumenten hoort?
              </span>
            </div>
          )}

          <div>
            <label className="text-xs font-medium text-foreground">Korte titel</label>
            <input
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              placeholder="bv. AV-vernietiging door zakelijke partij"
              className="mt-1 w-full rounded-md border border-border bg-card px-2.5 py-1.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
            />
          </div>

          <div>
            <label className="text-xs font-medium text-foreground">
              Welke stelling voert de debiteur? <span className="text-muted-foreground">(optioneel)</span>
            </label>
            <input
              value={form.claim_description}
              onChange={(e) => setForm({ ...form, claim_description: e.target.value })}
              placeholder="bv. 'Wij vernietigen de algemene voorwaarden'"
              className="mt-1 w-full rounded-md border border-border bg-card px-2.5 py-1.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
            />
          </div>

          <div>
            <label className="text-xs font-medium text-foreground">
              Standaard-weerlegging (wat de AI mag gebruiken)
            </label>
            <textarea
              value={form.rebuttal_body}
              onChange={(e) => setForm({ ...form, rebuttal_body: e.target.value })}
              rows={5}
              placeholder="Leg uit waarom de stelling onjuist is, met het wetsartikel."
              className="mt-1 w-full rounded-md border border-border bg-card p-2.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
            />
          </div>

          <div>
            <label className="text-xs font-medium text-foreground">
              Wetsartikel <span className="text-muted-foreground">(optioneel)</span>
            </label>
            <input
              value={form.legal_basis}
              onChange={(e) => setForm({ ...form, legal_basis: e.target.value })}
              placeholder="bv. art. 6:235 lid 1 BW"
              className="mt-1 w-full rounded-md border border-border bg-card px-2.5 py-1.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
            />
          </div>

          <div className="flex items-center justify-end gap-2">
            <button
              type="button"
              onClick={resetForm}
              className="rounded-lg border border-border bg-card px-3 py-1.5 text-xs font-medium text-muted-foreground hover:bg-muted transition-colors"
            >
              Annuleren
            </button>
            <button
              type="button"
              onClick={() => save.mutate({ id: editingId, form })}
              disabled={!canSave || pending}
              className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50"
            >
              <Check className="h-3.5 w-3.5" />
              {editingId ? "Wijzigingen opslaan" : "Opslaan als concept"}
            </button>
          </div>
        </div>
      )}

      {/* Lijst */}
      {isLoading ? (
        <div className="h-16 rounded-lg skeleton" />
      ) : !rules || rules.length === 0 ? (
        !showForm && (
          <p className="text-sm text-muted-foreground">
            Nog geen kennisregels. Voeg er een toe met &ldquo;Nieuwe regel&rdquo;.
          </p>
        )
      ) : (
        <div className="divide-y divide-border rounded-lg border border-border">
          {rules.map((r) => {
            const st = STATUS_LABELS[r.status] ?? STATUS_LABELS.afgewezen;
            return (
              <div key={r.id} className="p-3">
                <div className="flex flex-wrap items-center gap-2">
                  <span className={`shrink-0 rounded px-1.5 py-0.5 text-[10px] font-medium ${st.cls}`}>
                    {st.label}
                  </span>
                  <span className="text-sm font-medium text-foreground">{r.title}</span>
                  <span className="rounded bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground">
                    {DEFENSE_TYPE_LABELS[r.defense_type] ?? r.defense_type}
                  </span>
                  <span className="rounded bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground">
                    {APPLIES_TO_LABELS[r.applies_to] ?? r.applies_to}
                  </span>
                  <div className="ml-auto flex items-center gap-1">
                    {r.status !== "goedgekeurd" && (
                      <button
                        type="button"
                        onClick={() => approve.mutate(r.id)}
                        disabled={pending}
                        title="Goedkeuren"
                        className="rounded-md border border-green-300 bg-green-50 p-1 text-green-700 hover:bg-green-100 disabled:opacity-50 dark:border-green-900 dark:bg-green-950/40 dark:text-green-300"
                      >
                        <Check className="h-3.5 w-3.5" />
                      </button>
                    )}
                    {r.status === "goedgekeurd" && (
                      <button
                        type="button"
                        onClick={() => reject.mutate(r.id)}
                        disabled={pending}
                        title="Uitzetten"
                        className="rounded-md border border-border bg-card p-1 text-muted-foreground hover:bg-muted disabled:opacity-50"
                      >
                        <X className="h-3.5 w-3.5" />
                      </button>
                    )}
                    <button
                      type="button"
                      onClick={() => startEdit(r)}
                      disabled={pending}
                      title="Bewerken"
                      className="rounded-md border border-border bg-card p-1 text-muted-foreground hover:bg-muted disabled:opacity-50"
                    >
                      <Pencil className="h-3.5 w-3.5" />
                    </button>
                    <button
                      type="button"
                      onClick={() => doDelete(r.id)}
                      disabled={pending}
                      title="Verwijderen"
                      className="rounded-md border border-border bg-card p-1 text-muted-foreground hover:bg-red-50 hover:text-red-600 disabled:opacity-50 dark:hover:bg-red-950/40"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>
                {r.claim_description && (
                  <p className="mt-1.5 text-xs text-muted-foreground">
                    <span className="font-medium">Stelling:</span> {r.claim_description}
                  </p>
                )}
                <p className="mt-1 text-xs text-foreground/80 line-clamp-2">{r.rebuttal_body}</p>
                {r.legal_basis && (
                  <p className="mt-1 text-[11px] font-medium text-blue-600">{r.legal_basis}</p>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
