"use client";

import { useState } from "react";
import {
  Euro,
  FileText,
  Pencil,
  Plus,
  Save,
  Trash2,
  X,
} from "lucide-react";
import { toast } from "sonner";
import { useConfirm } from "@/components/confirm-dialog";
import {
  useClaims,
  useCreateClaim,
  useUpdateClaim,
  useDeleteClaim,
  useCaseInterest,
} from "@/hooks/use-collections";
import { useCaseFiles } from "@/hooks/use-case-files";
import { formatCurrency, formatDateShort } from "@/lib/utils";

export function VorderingenTab({ caseId }: { caseId: string }) {
  const { data: claims, isLoading } = useClaims(caseId);
  const { data: interest } = useCaseInterest(caseId);
  const { data: caseFiles } = useCaseFiles(caseId);
  const createClaim = useCreateClaim();
  const updateClaim = useUpdateClaim();
  const deleteClaim = useDeleteClaim();
  const { confirm, ConfirmDialog: ConfirmDialogEl } = useConfirm();
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState({
    description: "",
    principal_amount: "",
    default_date: "",
    invoice_number: "",
    invoice_date: "",
    invoice_file_id: "",
    rate_basis: "yearly",
  });
  const [form, setForm] = useState({
    description: "",
    principal_amount: "",
    default_date: "",
    invoice_number: "",
    invoice_date: "",
    rate_basis: "yearly",
  });

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createClaim.mutateAsync({
        caseId,
        data: {
          description: form.description,
          principal_amount: form.principal_amount,
          default_date: form.default_date,
          ...(form.invoice_number && { invoice_number: form.invoice_number }),
          ...(form.invoice_date && { invoice_date: form.invoice_date }),
          rate_basis: form.rate_basis,
        },
      });
      toast.success("Vordering toegevoegd");
      setShowForm(false);
      setForm({
        description: "",
        principal_amount: "",
        default_date: "",
        invoice_number: "",
        invoice_date: "",
        rate_basis: "yearly",
      });
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Er ging iets mis");
    }
  };

  const handleDelete = async (claimId: string) => {
    if (!await confirm({ title: "Vordering verwijderen", description: "Weet je zeker dat je deze vordering wilt verwijderen?", variant: "destructive", confirmText: "Verwijderen" })) return;
    try {
      await deleteClaim.mutateAsync({ caseId, claimId });
      toast.success("Vordering verwijderd");
    } catch {
      toast.error("Kon niet verwijderen");
    }
  };

  const startEdit = (claim: { id: string; description: string; principal_amount: number; default_date: string; invoice_number: string | null; invoice_date: string | null; invoice_file_id: string | null; rate_basis?: string }) => {
    setEditingId(claim.id);
    setEditForm({
      description: claim.description,
      principal_amount: String(claim.principal_amount),
      default_date: claim.default_date,
      invoice_number: claim.invoice_number || "",
      invoice_date: claim.invoice_date || "",
      invoice_file_id: claim.invoice_file_id || "",
      rate_basis: claim.rate_basis || "yearly",
    });
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingId) return;
    try {
      await updateClaim.mutateAsync({
        caseId,
        claimId: editingId,
        data: {
          description: editForm.description,
          principal_amount: editForm.principal_amount,
          default_date: editForm.default_date,
          ...(editForm.invoice_number ? { invoice_number: editForm.invoice_number } : { invoice_number: null }),
          ...(editForm.invoice_date ? { invoice_date: editForm.invoice_date } : { invoice_date: null }),
          ...(editForm.invoice_file_id ? { invoice_file_id: editForm.invoice_file_id } : { invoice_file_id: null }),
          rate_basis: editForm.rate_basis,
        },
      });
      toast.success("Vordering bijgewerkt");
      setEditingId(null);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Er ging iets mis");
    }
  };

  const inputClass =
    "mt-1.5 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors";

  return (
    <div className="space-y-4">
      {ConfirmDialogEl}
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold text-foreground">
          Vorderingen
        </h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          <Plus className="h-3.5 w-3.5" />
          Vordering toevoegen
        </button>
      </div>

      {showForm && (
        <form
          onSubmit={handleCreate}
          className="rounded-xl border border-primary/20 bg-primary/5 p-5 space-y-3"
        >
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className="block text-xs font-medium text-foreground">
                Beschrijving *
              </label>
              <input
                type="text"
                required
                value={form.description}
                onChange={(e) =>
                  setForm((f) => ({ ...f, description: e.target.value }))
                }
                className={inputClass}
                placeholder="Factuur nr. 2025-001"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-foreground">
                Hoofdsom *
              </label>
              <input
                type="number"
                step="0.01"
                required
                value={form.principal_amount}
                onChange={(e) =>
                  setForm((f) => ({ ...f, principal_amount: e.target.value }))
                }
                className={inputClass}
                placeholder="0.00"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-foreground">
                Verzuimdatum *
              </label>
              <input
                type="date"
                required
                value={form.default_date}
                onChange={(e) =>
                  setForm((f) => ({ ...f, default_date: e.target.value }))
                }
                className={inputClass}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-foreground">
                Factuurnummer
              </label>
              <input
                type="text"
                value={form.invoice_number}
                onChange={(e) =>
                  setForm((f) => ({ ...f, invoice_number: e.target.value }))
                }
                className={inputClass}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-foreground">
                Rentefrequentie
              </label>
              <select
                value={form.rate_basis}
                onChange={(e) =>
                  setForm((f) => ({ ...f, rate_basis: e.target.value }))
                }
                className={inputClass}
              >
                <option value="yearly">Per jaar</option>
                <option value="monthly">Per maand</option>
              </select>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={createClaim.isPending}
              className="rounded-lg bg-primary px-4 py-2 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              {createClaim.isPending ? "Opslaan..." : "Opslaan"}
            </button>
            <button
              type="button"
              onClick={() => setShowForm(false)}
              className="rounded-lg border border-border px-4 py-2 text-xs font-medium hover:bg-muted"
            >
              Annuleren
            </button>
          </div>
        </form>
      )}

      {isLoading ? (
        <div className="space-y-2">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-16 rounded-lg skeleton" />
          ))}
        </div>
      ) : claims && claims.length > 0 ? (
        <div className="rounded-xl border border-border bg-card overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border">
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Beschrijving
                </th>
                <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Hoofdsom
                </th>
                <th className="hidden sm:table-cell px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Verzuimdatum
                </th>
                <th className="hidden md:table-cell px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Rente
                </th>
                <th className="px-4 py-3 w-10" />
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {claims.map((claim) => {
                const claimInterest = interest?.claims.find(
                  (c) => c.claim_id === claim.id
                );
                const isEditing = editingId === claim.id;

                if (isEditing) {
                  return (
                    <tr key={claim.id} className="bg-muted/20">
                      <td className="px-4 py-2">
                        <input
                          type="text"
                          value={editForm.description}
                          onChange={(e) => setEditForm((f) => ({ ...f, description: e.target.value }))}
                          className={inputClass}
                          placeholder="Beschrijving"
                        />
                        <input
                          type="text"
                          value={editForm.invoice_number}
                          onChange={(e) => setEditForm((f) => ({ ...f, invoice_number: e.target.value }))}
                          className={`${inputClass} mt-1`}
                          placeholder="Factuurnummer (optioneel)"
                        />
                        {caseFiles && caseFiles.length > 0 && (
                          <select
                            value={editForm.invoice_file_id}
                            onChange={(e) => setEditForm((f) => ({ ...f, invoice_file_id: e.target.value }))}
                            className={`${inputClass} mt-1`}
                          >
                            <option value="">Gekoppeld bestand (optioneel)</option>
                            {caseFiles.map((file) => (
                              <option key={file.id} value={file.id}>
                                {file.original_filename}
                              </option>
                            ))}
                          </select>
                        )}
                        <select
                          value={editForm.rate_basis}
                          onChange={(e) => setEditForm((f) => ({ ...f, rate_basis: e.target.value }))}
                          className={`${inputClass} mt-1`}
                        >
                          <option value="yearly">Rente per jaar</option>
                          <option value="monthly">Rente per maand</option>
                        </select>
                      </td>
                      <td className="px-4 py-2">
                        <input
                          type="number"
                          step="0.01"
                          min="0.01"
                          value={editForm.principal_amount}
                          onChange={(e) => setEditForm((f) => ({ ...f, principal_amount: e.target.value }))}
                          className={`${inputClass} text-right`}
                        />
                      </td>
                      <td className="hidden sm:table-cell px-4 py-2">
                        <input
                          type="date"
                          value={editForm.default_date}
                          onChange={(e) => setEditForm((f) => ({ ...f, default_date: e.target.value }))}
                          className={inputClass}
                        />
                      </td>
                      <td className="hidden md:table-cell px-4 py-2" />
                      <td className="px-4 py-2">
                        <div className="flex items-center gap-1">
                          <button
                            onClick={handleUpdate}
                            disabled={updateClaim.isPending}
                            className="rounded p-1 text-primary hover:bg-primary/10 transition-colors"
                            title="Opslaan"
                          >
                            <Save className="h-3.5 w-3.5" />
                          </button>
                          <button
                            onClick={() => setEditingId(null)}
                            className="rounded p-1 text-muted-foreground hover:bg-muted transition-colors"
                            title="Annuleren"
                          >
                            <X className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                }

                return (
                  <tr
                    key={claim.id}
                    className="hover:bg-muted/30 transition-colors"
                  >
                    <td className="px-4 py-3">
                      <p className="text-sm font-medium text-foreground">
                        {claim.description}
                      </p>
                      {claim.invoice_number && (
                        <p className="text-xs text-muted-foreground">
                          Factuur: {claim.invoice_number}
                        </p>
                      )}
                      {claim.invoice_file_id && caseFiles && (() => {
                        const linkedFile = caseFiles.find((f) => f.id === claim.invoice_file_id);
                        return linkedFile ? (
                          <p className="text-xs text-muted-foreground flex items-center gap-1 mt-0.5">
                            <FileText className="h-3 w-3" />
                            {linkedFile.original_filename}
                          </p>
                        ) : null;
                      })()}
                    </td>
                    <td className="px-4 py-3 text-right text-sm font-semibold text-foreground tabular-nums">
                      {formatCurrency(claim.principal_amount)}
                    </td>
                    <td className="hidden sm:table-cell px-4 py-3 text-sm text-muted-foreground">
                      {formatDateShort(claim.default_date)}
                    </td>
                    <td className="hidden md:table-cell px-4 py-3 text-right text-sm text-accent font-medium tabular-nums">
                      {claimInterest
                        ? formatCurrency(claimInterest.total_interest)
                        : "-"}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => startEdit(claim)}
                          className="rounded p-1 text-muted-foreground hover:text-primary hover:bg-primary/10 transition-colors"
                          title="Bewerken"
                        >
                          <Pencil className="h-3.5 w-3.5" />
                        </button>
                        <button
                          onClick={() => handleDelete(claim.id)}
                          className="rounded p-1 text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors"
                          title="Verwijderen"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
            {interest && (
              <tfoot>
                <tr className="border-t-2 border-border bg-muted/20">
                  <td className="px-4 py-3 text-sm font-bold text-foreground">
                    Totaal
                  </td>
                  <td className="px-4 py-3 text-right text-sm font-bold text-foreground tabular-nums">
                    {formatCurrency(interest.total_principal)}
                  </td>
                  <td className="hidden sm:table-cell px-4 py-3" />
                  <td className="hidden md:table-cell px-4 py-3 text-right text-sm font-bold text-accent tabular-nums">
                    {formatCurrency(interest.total_interest)}
                  </td>
                  <td className="px-4 py-3" />
                </tr>
              </tfoot>
            )}
          </table>
        </div>
      ) : (
        <div className="rounded-xl border border-dashed border-border py-12 text-center">
          <Euro className="mx-auto h-10 w-10 text-muted-foreground/30" />
          <p className="mt-3 text-sm text-muted-foreground">
            Nog geen vorderingen
          </p>
          <button
            onClick={() => setShowForm(true)}
            className="mt-2 text-sm text-primary hover:underline"
          >
            Voeg de eerste vordering toe
          </button>
        </div>
      )}
    </div>
  );
}
