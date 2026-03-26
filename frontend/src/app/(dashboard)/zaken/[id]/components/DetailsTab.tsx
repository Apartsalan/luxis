"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import {
  Building2,
  ChevronDown,
  Clock,
  Euro,
  FileText,
  Gavel,
  Loader2,
  MessageSquare,
  Pencil,
  Save,
  Search,
  Send,
  User,
} from "lucide-react";
import { toast } from "sonner";
import { useUpdateCase, useAddCaseActivity, useAddCaseParty, useRemoveCaseParty } from "@/hooks/use-cases";
import type { CaseDetail } from "@/hooks/use-cases";
import { useRelations } from "@/hooks/use-relations";
import { useModules } from "@/hooks/use-modules";
import { formatDate, formatRelativeTime } from "@/lib/utils";
import { ACTIVITY_ICONS, ACTIVITY_COLORS, stripHtml } from "../types";
import { RichNoteEditor, isNoteEmpty } from "@/components/rich-note-editor";

const DUTCH_COURTS = [
  "Rechtbank Amsterdam",
  "Rechtbank Den Haag",
  "Rechtbank Gelderland",
  "Rechtbank Limburg",
  "Rechtbank Midden-Nederland",
  "Rechtbank Noord-Holland",
  "Rechtbank Noord-Nederland",
  "Rechtbank Oost-Brabant",
  "Rechtbank Overijssel",
  "Rechtbank Rotterdam",
  "Rechtbank Zeeland-West-Brabant",
  "Gerechtshof Amsterdam",
  "Gerechtshof Arnhem-Leeuwarden",
  "Gerechtshof Den Haag",
  "Gerechtshof 's-Hertogenbosch",
  "Hoge Raad der Nederlanden",
];

const PROCEDURE_TYPES = [
  "Dagvaarding",
  "Verzoekschrift",
  "Kort geding",
  "Kantonzaak",
  "Handelszaak",
  "Hoger beroep",
  "Cassatie",
  "Incidenteel appel",
  "Verzet",
];

const COLLECTION_STRATEGIES = [
  { value: "standaard", label: "Standaard (volledig traject)", description: "Herinnering → aanmaning → 14-dagenbrief → sommatie → dagvaarding" },
  { value: "minnelijk", label: "Minnelijk", description: "Buitengerechtelijk traject, geen dagvaarding" },
  { value: "gerechtelijk", label: "Gerechtelijk", description: "Direct naar dagvaarding" },
];

const INTEREST_TYPES = [
  { value: "statutory", label: "Wettelijke rente (art. 6:119 BW)" },
  { value: "commercial", label: "Handelsrente (art. 6:119a BW)" },
  { value: "government", label: "Overheidsrente (art. 6:119b BW)" },
  { value: "contractual", label: "Contractuele rente" },
];

const PROCEDURE_PHASES = [
  "Aangebracht",
  "Dagvaarding uitgebracht",
  "Conclusie van antwoord",
  "Conclusie van repliek",
  "Conclusie van dupliek",
  "Comparitie van partijen",
  "Pleidooi",
  "Vonnis bepaald",
  "Vonnis gewezen",
  "Hoger beroep ingesteld",
  "Executie",
  "Afgerond",
];

export default function DetailsTab({ zaak, initialNoteText, onNoteTextConsumed }: { zaak: CaseDetail; initialNoteText?: string; onNoteTextConsumed?: () => void }) {
  const [noteText, setNoteText] = useState("");
  const addActivity = useAddCaseActivity();
  const updateCase = useUpdateCase();
  const addParty = useAddCaseParty();
  const removeParty = useRemoveCaseParty();
  const { hasModule } = useModules();

  // Advocaat wederpartij search state
  const [lawyerSearch, setLawyerSearch] = useState("");
  const { data: lawyerResults } = useRelations({
    search: lawyerSearch || undefined,
    per_page: 5,
  });
  const currentLawyer = zaak.parties?.find((p) => p.role === "advocaat_wederpartij");

  // Edit mode state
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState({
    description: zaak.description || "",
    reference: zaak.reference || "",
    court_case_number: zaak.court_case_number || "",
    court_name: zaak.court_name || "",
    judge_name: zaak.judge_name || "",
    chamber: zaak.chamber || "",
    procedure_type: zaak.procedure_type || "",
    procedure_phase: zaak.procedure_phase || "",
    budget: zaak.budget != null ? String(zaak.budget) : "",
    hourly_rate: zaak.hourly_rate != null ? String(zaak.hourly_rate) : "",
    payment_term_days: zaak.payment_term_days != null ? String(zaak.payment_term_days) : "",
    collection_strategy: zaak.collection_strategy || "",
    debtor_notes: zaak.debtor_notes || "",
    interest_type: zaak.interest_type || "statutory",
    contractual_rate: zaak.contractual_rate != null ? String(zaak.contractual_rate) : "",
    contractual_compound: zaak.contractual_compound ?? true,
  });

  // UX-16: Warn on unsaved changes (beforeunload)
  useEffect(() => {
    if (!isEditing) return;
    const handler = (e: BeforeUnloadEvent) => {
      e.preventDefault();
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [isEditing]);

  const isIncasso = zaak.case_type === "incasso";

  // Apply phone note text from parent
  useEffect(() => {
    if (initialNoteText) {
      setNoteText(initialNoteText);
      onNoteTextConsumed?.();
    }
  }, [initialNoteText]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleAddNote = async () => {
    if (isNoteEmpty(noteText)) return;
    try {
      await addActivity.mutateAsync({
        caseId: zaak.id,
        data: {
          activity_type: "note",
          title: "Notitie toegevoegd",
          description: noteText,
        },
      });
      setNoteText("");
      toast.success("Notitie toegevoegd");
    } catch {
      toast.error("Kon notitie niet toevoegen");
    }
  };

  const handleSaveDetails = async () => {
    try {
      await updateCase.mutateAsync({
        id: zaak.id,
        data: {
          description: editForm.description.trim() || null,
          reference: editForm.reference.trim() || null,
          court_case_number: editForm.court_case_number.trim() || null,
          court_name: editForm.court_name.trim() || null,
          judge_name: editForm.judge_name.trim() || null,
          chamber: editForm.chamber.trim() || null,
          procedure_type: editForm.procedure_type.trim() || null,
          procedure_phase: editForm.procedure_phase.trim() || null,
          ...(hasModule("budget") && { budget: editForm.budget || null }),
          ...(isIncasso && {
            hourly_rate: editForm.hourly_rate || null,
            payment_term_days: editForm.payment_term_days ? parseInt(editForm.payment_term_days, 10) : null,
            collection_strategy: editForm.collection_strategy || null,
            debtor_notes: editForm.debtor_notes.trim() || null,
            interest_type: editForm.interest_type || "statutory",
            contractual_rate: editForm.interest_type === "contractual" && editForm.contractual_rate
              ? editForm.contractual_rate
              : null,
            contractual_compound: editForm.interest_type === "contractual"
              ? editForm.contractual_compound
              : null,
          }),
        },
      });
      setIsEditing(false);
      toast.success("Dossiergegevens opgeslagen");
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Opslaan mislukt");
    }
  };

  const handleCancelEdit = () => {
    setEditForm({
      description: zaak.description || "",
      reference: zaak.reference || "",
      court_case_number: zaak.court_case_number || "",
      court_name: zaak.court_name || "",
      judge_name: zaak.judge_name || "",
      chamber: zaak.chamber || "",
      procedure_type: zaak.procedure_type || "",
      procedure_phase: zaak.procedure_phase || "",
      budget: zaak.budget != null ? String(zaak.budget) : "",
      hourly_rate: zaak.hourly_rate != null ? String(zaak.hourly_rate) : "",
      payment_term_days: zaak.payment_term_days != null ? String(zaak.payment_term_days) : "",
      collection_strategy: zaak.collection_strategy || "",
      debtor_notes: zaak.debtor_notes || "",
      interest_type: zaak.interest_type || "statutory",
      contractual_rate: zaak.contractual_rate != null ? String(zaak.contractual_rate) : "",
      contractual_compound: zaak.contractual_compound ?? true,
    });
    setIsEditing(false);
  };

  const editInputClass =
    "w-full rounded-lg border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors";

  return (
    <div className="grid gap-6 lg:grid-cols-5">
      {/* Left: Case details */}
      <div className="lg:col-span-3 space-y-6">
        <div className="rounded-xl border border-border bg-card p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-card-foreground uppercase tracking-wider">
              Dossiergegevens
            </h2>
            {!isEditing ? (
              <button
                onClick={() => setIsEditing(true)}
                className="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
              >
                <Pencil className="h-3.5 w-3.5" />
                Bewerken
              </button>
            ) : (
              <div className="flex items-center gap-2">
                <button
                  onClick={handleCancelEdit}
                  className="rounded-lg px-2.5 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                >
                  Annuleren
                </button>
                <button
                  onClick={handleSaveDetails}
                  disabled={updateCase.isPending}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
                >
                  <Save className="h-3.5 w-3.5" />
                  {updateCase.isPending ? "Opslaan..." : "Opslaan"}
                </button>
              </div>
            )}
          </div>

          {isEditing ? (
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="sm:col-span-2">
                <label className="block text-xs text-muted-foreground mb-1">
                  Beschrijving
                </label>
                <textarea
                  value={editForm.description}
                  onChange={(e) => setEditForm(f => ({ ...f, description: e.target.value }))}
                  rows={2}
                  className={editInputClass}
                  placeholder="Korte omschrijving van het dossier..."
                />
              </div>
              <div>
                <label className="block text-xs text-muted-foreground mb-1">
                  Kenmerk cliënt
                </label>
                <input
                  type="text"
                  value={editForm.reference}
                  onChange={(e) => setEditForm(f => ({ ...f, reference: e.target.value }))}
                  className={editInputClass}
                  placeholder="Bijv. INV-2024-001"
                />
              </div>
              <div>
                <label className="block text-xs text-muted-foreground mb-1">
                  Zaaknummer rechtbank
                </label>
                <input
                  type="text"
                  value={editForm.court_case_number}
                  onChange={(e) => setEditForm(f => ({ ...f, court_case_number: e.target.value }))}
                  className={editInputClass}
                  placeholder="Bijv. C/13/123456 / HA ZA 24-789"
                />
              </div>
              <div className="sm:col-span-2">
                <label className="block text-xs text-muted-foreground mb-1">
                  Advocaat wederpartij
                </label>
                {currentLawyer ? (
                  <div className="flex items-center gap-2">
                    <span className="rounded-lg bg-violet-50 px-3 py-1.5 text-sm text-violet-700 font-medium">
                      {currentLawyer.contact.name}
                    </span>
                    <button
                      type="button"
                      onClick={async () => {
                        try {
                          await removeParty.mutateAsync({ caseId: zaak.id, partyId: currentLawyer.id });
                          toast.success("Advocaat wederpartij verwijderd");
                        } catch {
                          toast.error("Kon advocaat niet verwijderen");
                        }
                      }}
                      className="text-xs text-destructive hover:underline"
                    >
                      Verwijderen
                    </button>
                  </div>
                ) : (
                  <div>
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
                      <input
                        type="text"
                        value={lawyerSearch}
                        onChange={(e) => setLawyerSearch(e.target.value)}
                        className="w-full rounded-lg border border-input bg-background pl-9 pr-4 py-2 text-sm placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors"
                        placeholder="Zoek advocaat wederpartij..."
                      />
                    </div>
                    {lawyerSearch && lawyerResults?.items && lawyerResults.items.length > 0 && (
                      <div className="mt-1 rounded-lg border border-border bg-card shadow-lg overflow-hidden max-h-40 overflow-y-auto">
                        {lawyerResults.items.map((contact) => (
                          <button
                            key={contact.id}
                            type="button"
                            onClick={async () => {
                              try {
                                await addParty.mutateAsync({
                                  caseId: zaak.id,
                                  data: { contact_id: contact.id, role: "advocaat_wederpartij" },
                                });
                                setLawyerSearch("");
                                toast.success(`${contact.name} toegevoegd als advocaat wederpartij`);
                              } catch (err: unknown) {
                                toast.error(err instanceof Error ? err.message : "Kon advocaat niet toevoegen");
                              }
                            }}
                            className="w-full px-3 py-2 text-left text-sm hover:bg-muted transition-colors"
                          >
                            {contact.name}
                            <span className="ml-2 text-xs text-muted-foreground">
                              {contact.contact_type === "company" ? "Bedrijf" : "Persoon"}
                            </span>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* G13: Budget field — only when budget module is enabled */}
              {hasModule("budget") && (
                <div>
                  <label className="block text-xs text-muted-foreground mb-1">
                    Budget
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={editForm.budget}
                    onChange={(e) => setEditForm(f => ({ ...f, budget: e.target.value }))}
                    className={editInputClass}
                    placeholder="Bijv. 5000.00"
                  />
                </div>
              )}
            </div>
          ) : (
          <dl className="grid gap-4 sm:grid-cols-2">
            <div>
              <dt className="text-xs text-muted-foreground mb-1">
                Beschrijving
              </dt>
              <dd className="text-sm text-foreground">
                {zaak.description || "-"}
              </dd>
            </div>
            <div>
              <dt className="text-xs font-medium text-foreground mb-1">
                Kenmerk cliënt
              </dt>
              <dd className="text-sm font-semibold text-primary font-mono">
                {zaak.reference || <span className="text-muted-foreground font-normal">-</span>}
              </dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground mb-1">
                Zaaknummer rechtbank
              </dt>
              <dd className="text-sm text-foreground font-mono">
                {zaak.court_case_number || "-"}
              </dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground mb-1">
                Advocaat wederpartij
              </dt>
              <dd className="text-sm text-foreground">
                {currentLawyer ? (
                  <Link
                    href={`/relaties/${currentLawyer.contact.id}`}
                    className="text-primary hover:underline"
                  >
                    {currentLawyer.contact.name}
                  </Link>
                ) : (
                  <span className="text-muted-foreground">-</span>
                )}
              </dd>
            </div>
            {zaak.assigned_to && (
              <div>
                <dt className="text-xs text-muted-foreground mb-1">
                  Toegewezen aan
                </dt>
                <dd className="text-sm text-foreground">
                  {zaak.assigned_to.full_name}
                </dd>
              </div>
            )}
            {zaak.date_closed && (
              <div>
                <dt className="text-xs text-muted-foreground mb-1">
                  Datum gesloten
                </dt>
                <dd className="text-sm text-foreground">
                  {formatDate(zaak.date_closed)}
                </dd>
              </div>
            )}
          </dl>
          )}
        </div>

        {/* Procesgegevens */}
        <div className="rounded-xl border border-border bg-card p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Gavel className="h-4 w-4 text-muted-foreground" />
              <h2 className="text-sm font-semibold text-card-foreground uppercase tracking-wider">
                Procesgegevens
              </h2>
            </div>
          </div>

          {isEditing ? (
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-xs text-muted-foreground mb-1">
                  Rechtbank
                </label>
                <div className="relative">
                  <select
                    value={editForm.court_name}
                    onChange={(e) => setEditForm(f => ({ ...f, court_name: e.target.value }))}
                    className={`${editInputClass} appearance-none pr-8`}
                  >
                    <option value="">Selecteer rechtbank...</option>
                    {DUTCH_COURTS.map(c => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                  <ChevronDown className="absolute right-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground pointer-events-none" />
                </div>
              </div>
              <div>
                <label className="block text-xs text-muted-foreground mb-1">
                  Rechter
                </label>
                <input
                  type="text"
                  value={editForm.judge_name}
                  onChange={(e) => setEditForm(f => ({ ...f, judge_name: e.target.value }))}
                  className={editInputClass}
                  placeholder="Naam behandelend rechter"
                />
              </div>
              <div>
                <label className="block text-xs text-muted-foreground mb-1">
                  Kamer
                </label>
                <input
                  type="text"
                  value={editForm.chamber}
                  onChange={(e) => setEditForm(f => ({ ...f, chamber: e.target.value }))}
                  className={editInputClass}
                  placeholder="Bijv. Handelskamer"
                />
              </div>
              <div>
                <label className="block text-xs text-muted-foreground mb-1">
                  Type procedure
                </label>
                <div className="relative">
                  <select
                    value={editForm.procedure_type}
                    onChange={(e) => setEditForm(f => ({ ...f, procedure_type: e.target.value }))}
                    className={`${editInputClass} appearance-none pr-8`}
                  >
                    <option value="">Selecteer type...</option>
                    {PROCEDURE_TYPES.map(t => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                  <ChevronDown className="absolute right-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground pointer-events-none" />
                </div>
              </div>
              <div>
                <label className="block text-xs text-muted-foreground mb-1">
                  Procesfase
                </label>
                <div className="relative">
                  <select
                    value={editForm.procedure_phase}
                    onChange={(e) => setEditForm(f => ({ ...f, procedure_phase: e.target.value }))}
                    className={`${editInputClass} appearance-none pr-8`}
                  >
                    <option value="">Selecteer fase...</option>
                    {PROCEDURE_PHASES.map(p => (
                      <option key={p} value={p}>{p}</option>
                    ))}
                  </select>
                  <ChevronDown className="absolute right-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground pointer-events-none" />
                </div>
              </div>
            </div>
          ) : (
            <dl className="grid gap-4 sm:grid-cols-2">
              <div>
                <dt className="text-xs text-muted-foreground mb-1">Rechtbank</dt>
                <dd className="text-sm text-foreground">{zaak.court_name || "-"}</dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground mb-1">Rechter</dt>
                <dd className="text-sm text-foreground">{zaak.judge_name || "-"}</dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground mb-1">Kamer</dt>
                <dd className="text-sm text-foreground">{zaak.chamber || "-"}</dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground mb-1">Type procedure</dt>
                <dd className="text-sm text-foreground">{zaak.procedure_type || "-"}</dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground mb-1">Procesfase</dt>
                <dd className="text-sm text-foreground">{zaak.procedure_phase || "-"}</dd>
              </div>
            </dl>
          )}
        </div>

        {/* Partijen inline */}
        <div className="rounded-xl border border-border bg-card p-6">
          <h2 className="mb-4 text-sm font-semibold text-card-foreground uppercase tracking-wider">
            Partijen
          </h2>
          <div className="grid gap-3 sm:grid-cols-2">
            {zaak.client && (
              <Link
                href={`/relaties/${zaak.client.id}`}
                className="flex items-center gap-3 rounded-lg border border-border p-3 hover:border-primary/30 hover:bg-muted/50 transition-all"
              >
                <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary/10">
                  <Building2 className="h-4 w-4 text-primary" />
                </div>
                <div>
                  <p className="text-sm font-medium text-foreground">
                    {zaak.client.name}
                  </p>
                  <p className="text-xs text-primary">Client</p>
                </div>
              </Link>
            )}
            {zaak.opposing_party && (
              <Link
                href={`/relaties/${zaak.opposing_party.id}`}
                className="flex items-center gap-3 rounded-lg border border-border p-3 hover:border-amber-300/50 hover:bg-muted/50 transition-all"
              >
                <div className="flex h-9 w-9 items-center justify-center rounded-full bg-amber-50">
                  <User className="h-4 w-4 text-amber-600" />
                </div>
                <div>
                  <p className="text-sm font-medium text-foreground">
                    {zaak.opposing_party.name}
                  </p>
                  <p className="text-xs text-amber-600">Wederpartij</p>
                </div>
              </Link>
            )}
          </div>
        </div>

        {/* Debiteurinstellingen — alleen bij incasso */}
        {isIncasso && (
          <div className="rounded-xl border border-border bg-card p-6">
            <div className="flex items-center gap-2 mb-4">
              <Euro className="h-4 w-4 text-muted-foreground" />
              <h2 className="text-sm font-semibold text-card-foreground uppercase tracking-wider">
                Debiteurinstellingen
              </h2>
            </div>

            {isEditing ? (
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="block text-xs text-muted-foreground mb-1">
                    Type rente
                  </label>
                  <div className="relative">
                    <select
                      value={editForm.interest_type}
                      onChange={(e) => setEditForm(f => ({ ...f, interest_type: e.target.value }))}
                      className={`${editInputClass} appearance-none pr-8`}
                    >
                      {INTEREST_TYPES.map(t => (
                        <option key={t.value} value={t.value}>{t.label}</option>
                      ))}
                    </select>
                    <ChevronDown className="absolute right-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground pointer-events-none" />
                  </div>
                </div>
                {editForm.interest_type === "contractual" && (
                  <>
                    <div>
                      <label className="block text-xs text-muted-foreground mb-1">
                        Contractueel rentepercentage (%)
                      </label>
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        max="100"
                        value={editForm.contractual_rate}
                        onChange={(e) => setEditForm(f => ({ ...f, contractual_rate: e.target.value }))}
                        className={editInputClass}
                        placeholder="Bijv. 8.00"
                      />
                    </div>
                    <div className="flex items-center gap-2 sm:col-span-2">
                      <input
                        type="checkbox"
                        id="contractual_compound"
                        checked={editForm.contractual_compound}
                        onChange={(e) => setEditForm(f => ({ ...f, contractual_compound: e.target.checked }))}
                        className="h-4 w-4 rounded border-input text-primary focus:ring-primary/20"
                      />
                      <label htmlFor="contractual_compound" className="text-sm text-foreground">
                        Samengestelde rente (rente op rente)
                      </label>
                    </div>
                  </>
                )}
                <div>
                  <label className="block text-xs text-muted-foreground mb-1">
                    Uurtarief (EUR/uur)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={editForm.hourly_rate}
                    onChange={(e) => setEditForm(f => ({ ...f, hourly_rate: e.target.value }))}
                    className={editInputClass}
                    placeholder="Bijv. 225.00"
                  />
                </div>
                <div>
                  <label className="block text-xs text-muted-foreground mb-1">
                    Betalingstermijn (dagen)
                  </label>
                  <input
                    type="number"
                    step="1"
                    min="1"
                    value={editForm.payment_term_days}
                    onChange={(e) => setEditForm(f => ({ ...f, payment_term_days: e.target.value }))}
                    className={editInputClass}
                    placeholder="Bijv. 14"
                  />
                </div>
                <div>
                  <label className="block text-xs text-muted-foreground mb-1">
                    Incassostrategie
                  </label>
                  <div className="relative">
                    <select
                      value={editForm.collection_strategy}
                      onChange={(e) => setEditForm(f => ({ ...f, collection_strategy: e.target.value }))}
                      className={`${editInputClass} appearance-none pr-8`}
                    >
                      <option value="">Selecteer strategie...</option>
                      {COLLECTION_STRATEGIES.map(s => (
                        <option key={s.value} value={s.value}>{s.label}</option>
                      ))}
                    </select>
                    <ChevronDown className="absolute right-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground pointer-events-none" />
                  </div>
                  {editForm.collection_strategy && (
                    <p className="mt-1 text-[11px] text-muted-foreground">
                      {COLLECTION_STRATEGIES.find(s => s.value === editForm.collection_strategy)?.description}
                    </p>
                  )}
                </div>
                <div className="sm:col-span-2">
                  <label className="block text-xs text-muted-foreground mb-1">
                    Debiteurnotities
                  </label>
                  <textarea
                    value={editForm.debtor_notes}
                    onChange={(e) => setEditForm(f => ({ ...f, debtor_notes: e.target.value }))}
                    rows={3}
                    className={editInputClass}
                    placeholder="Notities over de debiteur..."
                  />
                </div>
              </div>
            ) : (
              <dl className="grid gap-4 sm:grid-cols-2">
                <div>
                  <dt className="text-xs text-muted-foreground mb-1">Type rente</dt>
                  <dd className="text-sm text-foreground">
                    {INTEREST_TYPES.find(t => t.value === zaak.interest_type)?.label || "Wettelijke rente"}
                  </dd>
                </div>
                {zaak.interest_type === "contractual" && zaak.contractual_rate != null && (
                  <div>
                    <dt className="text-xs text-muted-foreground mb-1">Contractueel rentepercentage</dt>
                    <dd className="text-sm text-foreground">
                      {zaak.contractual_rate}%{zaak.contractual_compound ? " (samengesteld)" : " (enkelvoudig)"}
                    </dd>
                  </div>
                )}
                <div>
                  <dt className="text-xs text-muted-foreground mb-1">Uurtarief</dt>
                  <dd className="text-sm text-foreground">
                    {zaak.hourly_rate != null ? `€ ${Number(zaak.hourly_rate).toFixed(2)} / uur` : "-"}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-muted-foreground mb-1">Betalingstermijn</dt>
                  <dd className="text-sm text-foreground">
                    {zaak.payment_term_days != null ? `${zaak.payment_term_days} dagen` : "-"}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-muted-foreground mb-1">Incassostrategie</dt>
                  <dd className="text-sm text-foreground">
                    {COLLECTION_STRATEGIES.find(s => s.value === zaak.collection_strategy)?.label || "-"}
                  </dd>
                </div>
                <div className="sm:col-span-2">
                  <dt className="text-xs text-muted-foreground mb-1">Debiteurnotities</dt>
                  <dd className="text-sm text-foreground whitespace-pre-wrap">
                    {zaak.debtor_notes || "-"}
                  </dd>
                </div>
              </dl>
            )}
          </div>
        )}
      </div>

      {/* Right: Note + Recent Activity */}
      <div className="lg:col-span-2 space-y-6">
        {/* Quick note input — always visible */}
        <div className="rounded-xl border border-border bg-card p-4">
          <div className="flex items-center gap-2 mb-3">
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
            <h2 className="text-sm font-semibold text-card-foreground">
              Notitie
            </h2>
          </div>
          <RichNoteEditor
            content={noteText}
            onChange={setNoteText}
            placeholder="Schrijf een notitie..."
          />
          <div className="flex items-center justify-end mt-2">
            <button
              type="button"
              onClick={handleAddNote}
              disabled={isNoteEmpty(noteText) || addActivity.isPending}
              className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
            >
              {addActivity.isPending ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <Send className="h-3 w-3" />
              )}
              Opslaan
            </button>
          </div>
        </div>

        <div className="rounded-xl border border-border bg-card">
          <div className="flex items-center gap-2 px-5 py-4 border-b border-border">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <h2 className="text-sm font-semibold text-card-foreground">
              Recente activiteit
            </h2>
          </div>
          {zaak.recent_activities && zaak.recent_activities.length > 0 ? (
            <div className="relative">
              <div className="absolute left-[2.125rem] top-0 bottom-0 w-px bg-border" />
              {zaak.recent_activities.slice(0, 6).map((activity, idx: number) => {
                const Icon =
                  ACTIVITY_ICONS[activity.activity_type] ?? FileText;
                const colorClass =
                  ACTIVITY_COLORS[activity.activity_type] ?? "bg-muted text-muted-foreground";
                return (
                  <div
                    key={activity.id}
                    className="relative flex items-start gap-3 px-5 py-3.5"
                  >
                    <div
                      className={`relative z-10 mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full ${colorClass}`}
                    >
                      <Icon className="h-3.5 w-3.5" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-foreground">
                        {activity.title}
                      </p>
                      {activity.description && (
                        <p className="text-xs text-muted-foreground truncate">
                          {stripHtml(activity.description)}
                        </p>
                      )}
                      <p className="text-xs text-muted-foreground/70 mt-0.5">
                        {formatRelativeTime(activity.created_at)}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="px-5 py-8 text-center">
              <Clock className="h-8 w-8 text-muted-foreground/30 mx-auto mb-2" />
              <p className="text-sm text-muted-foreground">
                Nog geen activiteiten
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
