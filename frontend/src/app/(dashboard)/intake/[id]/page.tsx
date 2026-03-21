"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Bot,
  Check,
  ChevronDown,
  ChevronUp,
  FileText,
  Loader2,
  Mail,
  Pencil,
  Shield,
  X,
} from "lucide-react";
import { toast } from "sonner";
import {
  useIntake,
  useUpdateIntake,
  useApproveIntake,
  useRejectIntake,
  useProcessIntake,
} from "@/hooks/use-intake";
import type { IntakeUpdateData } from "@/hooks/use-intake";
import { formatCurrency, formatDateShort } from "@/lib/utils";
import { QueryError } from "@/components/query-error";
import { useBreadcrumbs } from "@/components/layout/breadcrumb-context";

// ── Status config ────────────────────────────────────────────────────────────

const STATUS_CONFIG: Record<string, { label: string; badge: string }> = {
  detected: {
    label: "Gedetecteerd",
    badge: "bg-slate-50 text-slate-600 ring-slate-500/20",
  },
  processing: {
    label: "Verwerken...",
    badge: "bg-blue-50 text-blue-700 ring-blue-600/20",
  },
  pending_review: {
    label: "Te beoordelen",
    badge: "bg-amber-50 text-amber-700 ring-amber-600/20",
  },
  approved: {
    label: "Goedgekeurd",
    badge: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  },
  rejected: {
    label: "Afgewezen",
    badge: "bg-red-50 text-red-700 ring-red-600/20",
  },
  failed: {
    label: "Fout",
    badge: "bg-red-50 text-red-800 ring-red-700/20",
  },
};

// ── Confidence helpers ───────────────────────────────────────────────────────

function confidenceColor(c: number): string {
  if (c >= 0.85) return "bg-emerald-500";
  if (c >= 0.6) return "bg-amber-500";
  return "bg-red-500";
}

function confidenceLabel(c: number): string {
  if (c >= 0.85) return "Hoog";
  if (c >= 0.6) return "Gemiddeld";
  return "Laag";
}

function confidenceTextColor(c: number): string {
  if (c >= 0.85) return "text-emerald-700";
  if (c >= 0.6) return "text-amber-700";
  return "text-red-700";
}

// ── Editable field component ─────────────────────────────────────────────────

function EditableField({
  label,
  value,
  fieldKey,
  editable,
  type = "text",
  onSave,
  isSaving,
}: {
  label: string;
  value: string | null;
  fieldKey: string;
  editable: boolean;
  type?: "text" | "date" | "number";
  onSave: (key: string, val: string) => void;
  isSaving: boolean;
}) {
  const [editing, setEditing] = useState(false);
  const [editValue, setEditValue] = useState(value ?? "");

  const startEdit = () => {
    if (!editable) return;
    setEditValue(value ?? "");
    setEditing(true);
  };

  const cancelEdit = () => {
    setEditing(false);
    setEditValue(value ?? "");
  };

  const saveEdit = () => {
    if (editValue !== (value ?? "")) {
      onSave(fieldKey, editValue);
    }
    setEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") saveEdit();
    if (e.key === "Escape") cancelEdit();
  };

  if (editing) {
    return (
      <div>
        <label className="text-xs font-medium text-muted-foreground">
          {label}
        </label>
        <div className="flex items-center gap-1.5 mt-0.5">
          <input
            type={type}
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            onBlur={saveEdit}
            onKeyDown={handleKeyDown}
            autoFocus
            className="flex-1 rounded-md border border-primary/30 bg-background px-2.5 py-1.5 text-sm ring-1 ring-primary/20 focus:outline-none focus:ring-2 focus:ring-primary/40"
          />
          {isSaving && <Loader2 className="h-3.5 w-3.5 animate-spin text-muted-foreground" />}
        </div>
      </div>
    );
  }

  return (
    <div>
      <label className="text-xs font-medium text-muted-foreground">
        {label}
      </label>
      <div
        className={`flex items-center gap-1.5 mt-0.5 group/field ${
          editable ? "cursor-pointer" : ""
        }`}
        onClick={startEdit}
      >
        <span className="text-sm text-foreground">
          {value || (
            <span className="text-muted-foreground italic">Niet ingevuld</span>
          )}
        </span>
        {editable && (
          <Pencil className="h-3 w-3 text-muted-foreground opacity-0 group-hover/field:opacity-100 transition-opacity" />
        )}
      </div>
    </div>
  );
}

// ── Page ─────────────────────────────────────────────────────────────────────

export default function IntakeDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const [showReasoning, setShowReasoning] = useState(false);
  const [rejectMode, setRejectMode] = useState(false);
  const [rejectNote, setRejectNote] = useState("");

  const { data: intake, isLoading, isError, error, refetch } = useIntake(id);
  const updateMutation = useUpdateIntake();
  const approveMutation = useApproveIntake();
  const rejectMutation = useRejectIntake();
  const processMutation = useProcessIntake();

  const isMutating =
    updateMutation.isPending ||
    approveMutation.isPending ||
    rejectMutation.isPending ||
    processMutation.isPending;

  // Breadcrumbs
  useBreadcrumbs(
    intake
      ? [{ segment: id, label: intake.email_subject || "Intake" }]
      : [],
  );

  const isPending = intake?.status === "pending_review";
  const isDetected = intake?.status === "detected";
  const statusCfg =
    STATUS_CONFIG[intake?.status ?? ""] ?? STATUS_CONFIG.detected;

  // ── Handlers ─────────────────────────────────────────────────────────────

  const handleFieldSave = (key: string, value: string) => {
    updateMutation.mutate(
      { id, data: { [key]: value } as IntakeUpdateData },
      {
        onSuccess: () => {
          toast.success("Gegevens bijgewerkt");
        },
      },
    );
  };

  const handleApprove = () => {
    approveMutation.mutate(
      { id },
      {
        onSuccess: (data) => {
          toast.success(
            `Intake goedgekeurd — dossier ${data.created_case_number} aangemaakt`,
          );
        },
      },
    );
  };

  const handleReject = () => {
    rejectMutation.mutate(
      { id, note: rejectNote || undefined },
      {
        onSuccess: () => {
          toast.success("Intake afgewezen");
          setRejectMode(false);
          setRejectNote("");
        },
      },
    );
  };

  const handleProcess = () => {
    processMutation.mutate(
      { id },
      {
        onSuccess: () => {
          toast.success("AI verwerking gestart");
        },
      },
    );
  };

  // ── Loading / error states ─────────────────────────────────────────────

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-6 w-40 rounded bg-muted animate-pulse" />
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          <div className="lg:col-span-3 space-y-4">
            <div className="h-64 rounded-lg bg-muted animate-pulse" />
            <div className="h-48 rounded-lg bg-muted animate-pulse" />
          </div>
          <div className="lg:col-span-2 space-y-4">
            <div className="h-40 rounded-lg bg-muted animate-pulse" />
            <div className="h-32 rounded-lg bg-muted animate-pulse" />
          </div>
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <QueryError
        message={error?.message ?? "Kon intake verzoek niet laden"}
        onRetry={refetch}
      />
    );
  }

  if (!intake) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <h2 className="text-lg font-medium">Intake niet gevonden</h2>
        <Link
          href="/intake"
          className="mt-2 text-sm text-primary hover:underline"
        >
          Terug naar overzicht
        </Link>
      </div>
    );
  }

  // ── Render ─────────────────────────────────────────────────────────────

  return (
    <div className="space-y-6">
      {/* Back link + header */}
      <div>
        <Link
          href="/intake"
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-2"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Terug naar AI Intake
        </Link>

        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-semibold text-foreground truncate max-w-lg">
              {intake.email_subject || "Intake verzoek"}
            </h1>
            <span
              className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${statusCfg.badge}`}
            >
              {statusCfg.label}
            </span>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-2">
            {isDetected && (
              <button
                onClick={handleProcess}
                disabled={isMutating}
                className="inline-flex items-center gap-1.5 rounded-md bg-blue-600 px-3.5 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                {processMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Bot className="h-4 w-4" />
                )}
                Verwerken
              </button>
            )}
            {isPending && !rejectMode && (
              <>
                <button
                  onClick={() => setRejectMode(true)}
                  disabled={isMutating}
                  className="inline-flex items-center gap-1.5 rounded-md border border-red-200 px-3.5 py-2 text-sm font-medium text-red-700 hover:bg-red-50 disabled:opacity-50 transition-colors"
                >
                  <X className="h-4 w-4" />
                  Afwijzen
                </button>
                <button
                  onClick={handleApprove}
                  disabled={isMutating}
                  className="inline-flex items-center gap-1.5 rounded-md bg-emerald-600 px-3.5 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50 transition-colors"
                >
                  {approveMutation.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Check className="h-4 w-4" />
                  )}
                  Goedkeuren
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Reject note inline */}
      {rejectMode && (
        <div className="rounded-lg border border-red-200 bg-red-50/50 p-4">
          <p className="text-sm font-medium text-red-800 mb-2">
            Reden voor afwijzing (optioneel)
          </p>
          <textarea
            value={rejectNote}
            onChange={(e) => setRejectNote(e.target.value)}
            placeholder="Bijv. geen echte intake, dubbel verzoek, etc."
            rows={2}
            className="w-full rounded-md border border-red-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-400/40"
          />
          <div className="flex items-center gap-2 mt-2">
            <button
              onClick={handleReject}
              disabled={isMutating}
              className="inline-flex items-center gap-1.5 rounded-md bg-red-600 px-3.5 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50 transition-colors"
            >
              {rejectMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <X className="h-4 w-4" />
              )}
              Bevestig afwijzing
            </button>
            <button
              onClick={() => {
                setRejectMode(false);
                setRejectNote("");
              }}
              className="rounded-md px-3.5 py-2 text-sm font-medium text-muted-foreground hover:bg-muted transition-colors"
            >
              Annuleren
            </button>
          </div>
        </div>
      )}

      {/* Error message banner */}
      {intake.status === "failed" && intake.error_message && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <p className="text-sm font-medium text-red-800">
            Fout bij verwerking
          </p>
          <p className="text-sm text-red-700 mt-1">{intake.error_message}</p>
        </div>
      )}

      {/* Approved success banner */}
      {intake.status === "approved" && intake.created_case_id && (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4">
          <p className="text-sm font-medium text-emerald-800">
            Dossier aangemaakt
          </p>
          <div className="flex flex-wrap items-center gap-4 mt-2">
            <Link
              href={`/zaken/${intake.created_case_id}`}
              className="inline-flex items-center gap-1.5 text-sm font-medium text-emerald-700 hover:text-emerald-900 underline underline-offset-2"
            >
              <FileText className="h-3.5 w-3.5" />
              Dossier {intake.created_case_number}
            </Link>
            {intake.created_contact_id && (
              <Link
                href={`/relaties/${intake.created_contact_id}`}
                className="inline-flex items-center gap-1.5 text-sm font-medium text-emerald-700 hover:text-emerald-900 underline underline-offset-2"
              >
                Relatie: {intake.created_contact_name}
              </Link>
            )}
          </div>
        </div>
      )}

      {/* Two-column content */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Left column — editable data */}
        <div className="lg:col-span-3 space-y-4">
          {/* Debiteur gegevens */}
          <div className="rounded-lg border bg-card p-5">
            <h2 className="text-sm font-semibold text-foreground mb-4">
              Debiteur gegevens
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <EditableField
                label="Naam"
                value={intake.debtor_name}
                fieldKey="debtor_name"
                editable={isPending}
                onSave={handleFieldSave}
                isSaving={updateMutation.isPending}
              />
              <EditableField
                label="E-mail"
                value={intake.debtor_email}
                fieldKey="debtor_email"
                editable={isPending}
                onSave={handleFieldSave}
                isSaving={updateMutation.isPending}
              />
              <EditableField
                label="KvK-nummer"
                value={intake.debtor_kvk}
                fieldKey="debtor_kvk"
                editable={isPending}
                onSave={handleFieldSave}
                isSaving={updateMutation.isPending}
              />
              <div>
                <label className="text-xs font-medium text-muted-foreground">
                  Type
                </label>
                {isPending ? (
                  <select
                    value={intake.debtor_type}
                    onChange={(e) =>
                      handleFieldSave("debtor_type", e.target.value)
                    }
                    className="mt-0.5 block w-full rounded-md border bg-background px-2.5 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/40"
                  >
                    <option value="company">Bedrijf</option>
                    <option value="person">Particulier</option>
                  </select>
                ) : (
                  <p className="text-sm text-foreground mt-0.5">
                    {intake.debtor_type === "company"
                      ? "Bedrijf"
                      : "Particulier"}
                  </p>
                )}
              </div>
              <EditableField
                label="Adres"
                value={intake.debtor_address}
                fieldKey="debtor_address"
                editable={isPending}
                onSave={handleFieldSave}
                isSaving={updateMutation.isPending}
              />
              <div className="grid grid-cols-2 gap-3">
                <EditableField
                  label="Postcode"
                  value={intake.debtor_postcode}
                  fieldKey="debtor_postcode"
                  editable={isPending}
                  onSave={handleFieldSave}
                  isSaving={updateMutation.isPending}
                />
                <EditableField
                  label="Plaats"
                  value={intake.debtor_city}
                  fieldKey="debtor_city"
                  editable={isPending}
                  onSave={handleFieldSave}
                  isSaving={updateMutation.isPending}
                />
              </div>
            </div>
          </div>

          {/* Factuurgegevens */}
          <div className="rounded-lg border bg-card p-5">
            <h2 className="text-sm font-semibold text-foreground mb-4">
              Factuurgegevens
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <EditableField
                label="Factuurnummer"
                value={intake.invoice_number}
                fieldKey="invoice_number"
                editable={isPending}
                onSave={handleFieldSave}
                isSaving={updateMutation.isPending}
              />
              <EditableField
                label="Factuurdatum"
                value={
                  intake.invoice_date
                    ? formatDateShort(intake.invoice_date)
                    : null
                }
                fieldKey="invoice_date"
                editable={isPending}
                type="date"
                onSave={handleFieldSave}
                isSaving={updateMutation.isPending}
              />
              <EditableField
                label="Vervaldatum"
                value={
                  intake.due_date ? formatDateShort(intake.due_date) : null
                }
                fieldKey="due_date"
                editable={isPending}
                type="date"
                onSave={handleFieldSave}
                isSaving={updateMutation.isPending}
              />
              <EditableField
                label="Hoofdsom"
                value={
                  intake.principal_amount
                    ? formatCurrency(intake.principal_amount)
                    : null
                }
                fieldKey="principal_amount"
                editable={isPending}
                type="number"
                onSave={handleFieldSave}
                isSaving={updateMutation.isPending}
              />
              <div className="sm:col-span-2">
                <EditableField
                  label="Omschrijving"
                  value={intake.description}
                  fieldKey="description"
                  editable={isPending}
                  onSave={handleFieldSave}
                  isSaving={updateMutation.isPending}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Right column — metadata */}
        <div className="lg:col-span-2 space-y-4">
          {/* AI Analyse */}
          <div className="rounded-lg border bg-card p-5">
            <h2 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-1.5">
              <Bot className="h-4 w-4 text-primary" />
              AI Analyse
            </h2>

            {/* Confidence */}
            {intake.ai_confidence != null && (
              <div className="mb-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-muted-foreground">
                    Zekerheid
                  </span>
                  <span
                    className={`text-sm font-semibold tabular-nums ${confidenceTextColor(intake.ai_confidence)}`}
                  >
                    {Math.round(intake.ai_confidence * 100)}% —{" "}
                    {confidenceLabel(intake.ai_confidence)}
                  </span>
                </div>
                <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${confidenceColor(intake.ai_confidence)}`}
                    style={{
                      width: `${Math.round(intake.ai_confidence * 100)}%`,
                    }}
                  />
                </div>
              </div>
            )}

            {/* Model */}
            {intake.ai_model && (
              <div className="flex items-center justify-between text-xs mb-2">
                <span className="text-muted-foreground">AI Model</span>
                <span className="text-foreground font-mono">
                  {intake.ai_model}
                </span>
              </div>
            )}

            {/* PDF badge */}
            {intake.has_pdf_data && (
              <div className="flex items-center gap-1.5 text-xs text-blue-700 bg-blue-50 rounded-md px-2.5 py-1.5 mb-3">
                <FileText className="h-3.5 w-3.5" />
                PDF bijlage geanalyseerd
              </div>
            )}

            {/* Reasoning */}
            {intake.ai_reasoning && (
              <div>
                <button
                  onClick={() => setShowReasoning(!showReasoning)}
                  className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
                >
                  {showReasoning ? (
                    <ChevronUp className="h-3.5 w-3.5" />
                  ) : (
                    <ChevronDown className="h-3.5 w-3.5" />
                  )}
                  AI onderbouwing
                </button>
                {showReasoning && (
                  <div className="mt-2 rounded-md bg-muted/50 p-3 text-xs text-muted-foreground leading-relaxed whitespace-pre-wrap">
                    {intake.ai_reasoning}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Bron e-mail */}
          <div className="rounded-lg border bg-card p-5">
            <h2 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-1.5">
              <Mail className="h-4 w-4 text-muted-foreground" />
              Bron e-mail
            </h2>
            <div className="space-y-2.5">
              <div>
                <span className="text-xs text-muted-foreground">Van</span>
                <p className="text-sm text-foreground">
                  {intake.email_from || "-"}
                </p>
              </div>
              <div>
                <span className="text-xs text-muted-foreground">Onderwerp</span>
                <p className="text-sm text-foreground">
                  {intake.email_subject || "-"}
                </p>
              </div>
              <div>
                <span className="text-xs text-muted-foreground">Datum</span>
                <p className="text-sm text-foreground">
                  {intake.email_date
                    ? formatDateShort(intake.email_date)
                    : "-"}
                </p>
              </div>
              {intake.client_name && (
                <div>
                  <span className="text-xs text-muted-foreground">Cliënt</span>
                  <p className="text-sm text-foreground">
                    {intake.client_name}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Review info (only when reviewed) */}
          {(intake.status === "approved" || intake.status === "rejected") &&
            intake.reviewed_by_name && (
              <div className="rounded-lg border bg-card p-5">
                <h2 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-1.5">
                  <Shield className="h-4 w-4 text-muted-foreground" />
                  Beoordeling
                </h2>
                <div className="space-y-2.5">
                  <div>
                    <span className="text-xs text-muted-foreground">
                      Beoordeeld door
                    </span>
                    <p className="text-sm text-foreground">
                      {intake.reviewed_by_name}
                    </p>
                  </div>
                  {intake.reviewed_at && (
                    <div>
                      <span className="text-xs text-muted-foreground">
                        Datum
                      </span>
                      <p className="text-sm text-foreground">
                        {formatDateShort(intake.reviewed_at)}
                      </p>
                    </div>
                  )}
                  {intake.review_note && (
                    <div>
                      <span className="text-xs text-muted-foreground">
                        Notitie
                      </span>
                      <p className="text-sm text-foreground">
                        {intake.review_note}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}
        </div>
      </div>
    </div>
  );
}
