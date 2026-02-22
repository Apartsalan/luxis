"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import {
  Building2,
  ChevronDown,
  Clock,
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
import { useRelations } from "@/hooks/use-relations";
import { formatDate, formatRelativeTime } from "@/lib/utils";
import { ACTIVITY_ICONS, ACTIVITY_COLORS } from "../types";

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

export default function DetailsTab({ zaak, initialNoteText, onNoteTextConsumed }: { zaak: any; initialNoteText?: string; onNoteTextConsumed?: () => void }) {
  const [noteText, setNoteText] = useState("");
  const addActivity = useAddCaseActivity();
  const updateCase = useUpdateCase();
  const addParty = useAddCaseParty();
  const removeParty = useRemoveCaseParty();

  // Advocaat wederpartij search state
  const [lawyerSearch, setLawyerSearch] = useState("");
  const { data: lawyerResults } = useRelations({
    search: lawyerSearch || undefined,
    per_page: 5,
  });
  const currentLawyer = zaak.parties?.find((p: any) => p.role === "advocaat_wederpartij");

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
  });

  // Apply phone note text from parent
  useEffect(() => {
    if (initialNoteText) {
      setNoteText(initialNoteText);
      onNoteTextConsumed?.();
    }
  }, [initialNoteText]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleAddNote = async () => {
    const text = noteText.trim();
    if (!text) return;
    try {
      await addActivity.mutateAsync({
        caseId: zaak.id,
        data: {
          activity_type: "note",
          title: "Notitie toegevoegd",
          description: text,
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
        },
      });
      setIsEditing(false);
      toast.success("Dossiergegevens opgeslagen");
    } catch (err: any) {
      toast.error(err.message || "Opslaan mislukt");
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
                  Referentie (klantreferentie)
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
                              } catch (err: any) {
                                toast.error(err.message || "Kon advocaat niet toevoegen");
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
              <dt className="text-xs text-muted-foreground mb-1">
                Referentie
              </dt>
              <dd className="text-sm text-foreground font-mono">
                {zaak.reference || "-"}
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
            {zaak.contractual_rate && (
              <div>
                <dt className="text-xs text-muted-foreground mb-1">
                  Contractueel rentepercentage
                </dt>
                <dd className="text-sm text-foreground">
                  {zaak.contractual_rate}%
                  {zaak.contractual_compound
                    ? " (samengesteld)"
                    : " (enkelvoudig)"}
                </dd>
              </div>
            )}
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
          <textarea
            value={noteText}
            onChange={(e) => setNoteText(e.target.value)}
            placeholder="Schrijf een notitie..."
            rows={3}
            className="w-full rounded-lg border border-input bg-background px-3 py-2.5 text-sm placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors resize-none"
          />
          <div className="flex items-center justify-between mt-2">
            <p className="text-[10px] text-muted-foreground">
              **vet**, *cursief*, - opsomming
            </p>
            <button
              type="button"
              onClick={handleAddNote}
              disabled={!noteText.trim() || addActivity.isPending}
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
              {zaak.recent_activities.slice(0, 6).map((activity: any, idx: number) => {
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
                          {activity.description}
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
