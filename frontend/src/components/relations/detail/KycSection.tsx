"use client";

import {
  Check,
  X,
  Pencil,
  Shield,
  ShieldCheck,
  ShieldAlert,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { formatDateShort } from "@/lib/utils";

export const KYC_STATUS_CONFIG: Record<
  string,
  { label: string; badge: string; icon: any }
> = {
  niet_gestart: {
    label: "Niet gestart",
    badge: "bg-red-50 text-red-700 ring-red-600/20",
    icon: ShieldAlert,
  },
  in_behandeling: {
    label: "In behandeling",
    badge: "bg-amber-50 text-amber-700 ring-amber-600/20",
    icon: Shield,
  },
  voltooid: {
    label: "Voltooid",
    badge: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
    icon: ShieldCheck,
  },
  verlopen: {
    label: "Verlopen",
    badge: "bg-red-50 text-red-700 ring-red-600/20",
    icon: ShieldAlert,
  },
};

const ID_TYPE_LABELS: Record<string, string> = {
  paspoort: "Paspoort",
  id_kaart: "ID-kaart",
  rijbewijs: "Rijbewijs",
  verblijfsdocument: "Verblijfsdocument",
  kvk_uittreksel: "KvK-uittreksel",
  anders: "Anders",
};

const RISK_LABELS: Record<string, { label: string; color: string }> = {
  laag: { label: "Laag", color: "bg-emerald-50 text-emerald-700" },
  midden: { label: "Midden", color: "bg-amber-50 text-amber-700" },
  hoog: { label: "Hoog", color: "bg-red-50 text-red-700" },
};

interface KycSectionProps {
  contactId: string;
  contactType: string;
  kycData: any;
  kycLoading: boolean;
  kycOpen: boolean;
  setKycOpen: (v: boolean) => void;
  kycEditing: boolean;
  setKycEditing: (v: boolean) => void;
  kycForm: Record<string, any>;
  updateKycField: (field: string, value: any) => void;
  startKycEditing: () => void;
  handleKycSave: () => Promise<void>;
  handleKycComplete: () => Promise<void>;
  saveKycIsPending: boolean;
  completeKycIsPending: boolean;
  inputClass: string;
}

export default function KycSection({
  contactId,
  contactType,
  kycData,
  kycLoading,
  kycOpen,
  setKycOpen,
  kycEditing,
  setKycEditing,
  kycForm,
  updateKycField,
  startKycEditing,
  handleKycSave,
  handleKycComplete,
  saveKycIsPending,
  completeKycIsPending,
  inputClass,
}: KycSectionProps) {
  const kycStatus = kycData?.status || "niet_gestart";
  const kycConfig =
    KYC_STATUS_CONFIG[kycStatus] || KYC_STATUS_CONFIG.niet_gestart;
  const KycIcon = kycConfig.icon;

  return (
    <div className="rounded-xl border border-border bg-card overflow-hidden">
      {/* Collapsible header */}
      <button
        type="button"
        onClick={() => setKycOpen(!kycOpen)}
        className="flex w-full items-center justify-between px-6 py-4 hover:bg-muted/30 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div
            className={`flex h-9 w-9 items-center justify-center rounded-lg ${
              kycStatus === "voltooid"
                ? "bg-emerald-50 text-emerald-600"
                : kycStatus === "in_behandeling"
                ? "bg-amber-50 text-amber-600"
                : "bg-red-50 text-red-600"
            }`}
          >
            <KycIcon className="h-5 w-5" />
          </div>
          <div className="text-left">
            <h2 className="text-sm font-semibold text-foreground">
              WWFT / Cliëntidentificatie
            </h2>
            <p className="text-xs text-muted-foreground">
              {kycStatus === "voltooid" && kycData?.verification_date
                ? `Geverifieerd op ${formatDateShort(kycData.verification_date)}`
                : kycStatus === "in_behandeling"
                ? "Verificatie in behandeling"
                : "Nog niet geverifieerd — verplicht per WWFT"}
              {kycData?.risk_level && (
                <span
                  className={`ml-2 inline-flex rounded-full px-1.5 py-0.5 text-[10px] font-medium ${
                    RISK_LABELS[kycData.risk_level]?.color || ""
                  }`}
                >
                  Risico: {RISK_LABELS[kycData.risk_level]?.label}
                </span>
              )}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {!kycEditing && kycStatus !== "voltooid" && (
            <span
              onClick={(e) => {
                e.stopPropagation();
                startKycEditing();
              }}
              className="text-xs text-primary hover:underline cursor-pointer"
            >
              {kycData ? "Bewerken" : "Starten"}
            </span>
          )}
          {kycOpen ? (
            <ChevronUp className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          )}
        </div>
      </button>

      {/* Collapsible content */}
      {kycOpen && (
        <div className="border-t border-border px-6 py-5 space-y-6">
          {kycEditing ? (
            /* ── KYC Edit Form ──────────────────────────────────── */
            <div className="space-y-6">
              {/* Risk Classification */}
              <div>
                <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                  Risicoclassificatie
                </h3>
                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                      Risiconiveau *
                    </label>
                    <select
                      value={kycForm.risk_level}
                      onChange={(e) =>
                        updateKycField("risk_level", e.target.value)
                      }
                      className={inputClass}
                    >
                      <option value="">Selecteer...</option>
                      <option value="laag">Laag</option>
                      <option value="midden">Midden</option>
                      <option value="hoog">Hoog</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                      Toelichting risico
                    </label>
                    <input
                      type="text"
                      value={kycForm.risk_notes}
                      onChange={(e) =>
                        updateKycField("risk_notes", e.target.value)
                      }
                      className={inputClass}
                      placeholder="Waarom dit risiconiveau?"
                    />
                  </div>
                </div>
              </div>

              {/* Identity Document */}
              <div>
                <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                  Identiteitsdocument
                </h3>
                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                      Type document *
                    </label>
                    <select
                      value={kycForm.id_type}
                      onChange={(e) =>
                        updateKycField("id_type", e.target.value)
                      }
                      className={inputClass}
                    >
                      <option value="">Selecteer...</option>
                      <option value="paspoort">Paspoort</option>
                      <option value="id_kaart">ID-kaart</option>
                      <option value="rijbewijs">Rijbewijs</option>
                      <option value="verblijfsdocument">
                        Verblijfsdocument
                      </option>
                      <option value="kvk_uittreksel">KvK-uittreksel</option>
                      <option value="anders">Anders</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                      Documentnummer *
                    </label>
                    <input
                      type="text"
                      value={kycForm.id_number}
                      onChange={(e) =>
                        updateKycField("id_number", e.target.value)
                      }
                      className={inputClass}
                      placeholder="Bijv. NW1234567"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                      Vervaldatum document
                    </label>
                    <input
                      type="date"
                      value={kycForm.id_expiry_date}
                      onChange={(e) =>
                        updateKycField("id_expiry_date", e.target.value)
                      }
                      className={inputClass}
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                      Datum verificatie *
                    </label>
                    <input
                      type="date"
                      value={kycForm.id_verified_at}
                      onChange={(e) =>
                        updateKycField("id_verified_at", e.target.value)
                      }
                      className={inputClass}
                    />
                  </div>
                </div>
              </div>

              {/* UBO — only for companies */}
              {contactType === "company" && (
                <div>
                  <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                    UBO (Ultimate Beneficial Owner)
                  </h3>
                  <div className="grid gap-4 sm:grid-cols-2">
                    <div>
                      <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                        Naam UBO *
                      </label>
                      <input
                        type="text"
                        value={kycForm.ubo_name}
                        onChange={(e) =>
                          updateKycField("ubo_name", e.target.value)
                        }
                        className={inputClass}
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                        Geboortedatum UBO
                      </label>
                      <input
                        type="date"
                        value={kycForm.ubo_dob}
                        onChange={(e) =>
                          updateKycField("ubo_dob", e.target.value)
                        }
                        className={inputClass}
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                        Nationaliteit
                      </label>
                      <input
                        type="text"
                        value={kycForm.ubo_nationality}
                        onChange={(e) =>
                          updateKycField("ubo_nationality", e.target.value)
                        }
                        className={inputClass}
                        placeholder="Bijv. Nederlands"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                        Belang (%)
                      </label>
                      <select
                        value={kycForm.ubo_percentage}
                        onChange={(e) =>
                          updateKycField("ubo_percentage", e.target.value)
                        }
                        className={inputClass}
                      >
                        <option value="">Selecteer...</option>
                        <option value="25-50%">25-50%</option>
                        <option value=">50%">Meer dan 50%</option>
                        <option value="100%">100%</option>
                      </select>
                    </div>
                  </div>
                </div>
              )}

              {/* PEP + Sanctions checks */}
              <div>
                <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                  Verplichte controles
                </h3>
                <div className="space-y-3">
                  {/* PEP */}
                  <div className="rounded-lg border border-border p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-foreground">
                        PEP-controle (Politically Exposed Person) *
                      </span>
                      <label className="relative inline-flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={kycForm.pep_checked}
                          onChange={(e) =>
                            updateKycField("pep_checked", e.target.checked)
                          }
                          className="sr-only peer"
                        />
                        <div className="w-9 h-5 bg-gray-200 peer-focus:ring-2 peer-focus:ring-primary/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:bg-primary after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all"></div>
                        <span className="text-xs text-muted-foreground">
                          Gecontroleerd
                        </span>
                      </label>
                    </div>
                    {kycForm.pep_checked && (
                      <div className="flex items-center gap-4">
                        <label className="flex items-center gap-2 text-sm">
                          <input
                            type="checkbox"
                            checked={kycForm.pep_is_pep}
                            onChange={(e) =>
                              updateKycField("pep_is_pep", e.target.checked)
                            }
                            className="rounded border-gray-300"
                          />
                          Is PEP
                        </label>
                        <input
                          type="text"
                          value={kycForm.pep_notes}
                          onChange={(e) =>
                            updateKycField("pep_notes", e.target.value)
                          }
                          className={`${inputClass} flex-1`}
                          placeholder="Toelichting..."
                        />
                      </div>
                    )}
                  </div>

                  {/* Sanctions */}
                  <div className="rounded-lg border border-border p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-foreground">
                        Sanctielijstcontrole *
                      </span>
                      <label className="relative inline-flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={kycForm.sanctions_checked}
                          onChange={(e) =>
                            updateKycField(
                              "sanctions_checked",
                              e.target.checked
                            )
                          }
                          className="sr-only peer"
                        />
                        <div className="w-9 h-5 bg-gray-200 peer-focus:ring-2 peer-focus:ring-primary/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:bg-primary after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all"></div>
                        <span className="text-xs text-muted-foreground">
                          Gecontroleerd
                        </span>
                      </label>
                    </div>
                    {kycForm.sanctions_checked && (
                      <div className="flex items-center gap-4">
                        <label className="flex items-center gap-2 text-sm">
                          <input
                            type="checkbox"
                            checked={kycForm.sanctions_hit}
                            onChange={(e) =>
                              updateKycField(
                                "sanctions_hit",
                                e.target.checked
                              )
                            }
                            className="rounded border-gray-300"
                          />
                          Hit gevonden
                        </label>
                        <input
                          type="text"
                          value={kycForm.sanctions_notes}
                          onChange={(e) =>
                            updateKycField(
                              "sanctions_notes",
                              e.target.value
                            )
                          }
                          className={`${inputClass} flex-1`}
                          placeholder="Toelichting..."
                        />
                      </div>
                    )}
                  </div>

                  {/* Source of Funds */}
                  <div className="rounded-lg border border-border p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-foreground">
                        Herkomst middelen
                      </span>
                      <label className="relative inline-flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={kycForm.source_of_funds_verified}
                          onChange={(e) =>
                            updateKycField(
                              "source_of_funds_verified",
                              e.target.checked
                            )
                          }
                          className="sr-only peer"
                        />
                        <div className="w-9 h-5 bg-gray-200 peer-focus:ring-2 peer-focus:ring-primary/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:bg-primary after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all"></div>
                        <span className="text-xs text-muted-foreground">
                          Geverifieerd
                        </span>
                      </label>
                    </div>
                    <input
                      type="text"
                      value={kycForm.source_of_funds}
                      onChange={(e) =>
                        updateKycField("source_of_funds", e.target.value)
                      }
                      className={inputClass}
                      placeholder="Bijv. bedrijfsomzet, salaris, etc."
                    />
                  </div>
                </div>
              </div>

              {/* Notes */}
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                  Opmerkingen
                </label>
                <textarea
                  value={kycForm.notes}
                  onChange={(e) => updateKycField("notes", e.target.value)}
                  rows={2}
                  className={`${inputClass} resize-none`}
                  placeholder="Eventuele opmerkingen bij de verificatie..."
                />
              </div>

              {/* Save / Cancel */}
              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={handleKycSave}
                  disabled={saveKycIsPending}
                  className="rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
                >
                  {saveKycIsPending ? "Opslaan..." : "Opslaan"}
                </button>
                <button
                  type="button"
                  onClick={() => setKycEditing(false)}
                  className="rounded-lg border border-border px-4 py-2.5 text-sm hover:bg-muted transition-colors"
                >
                  Annuleren
                </button>
              </div>
            </div>
          ) : kycData ? (
            /* ── KYC Read-Only View ─────────────────────────────── */
            <div className="space-y-5">
              {/* Summary grid */}
              <div className="grid gap-4 sm:grid-cols-3">
                {/* Risk level */}
                <div className="rounded-lg bg-muted/50 p-3">
                  <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">
                    Risiconiveau
                  </p>
                  {kycData.risk_level ? (
                    <span
                      className={`mt-1 inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                        RISK_LABELS[kycData.risk_level]?.color || ""
                      }`}
                    >
                      {RISK_LABELS[kycData.risk_level]?.label}
                    </span>
                  ) : (
                    <p className="mt-1 text-sm text-muted-foreground">—</p>
                  )}
                </div>

                {/* ID Document */}
                <div className="rounded-lg bg-muted/50 p-3">
                  <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">
                    ID-document
                  </p>
                  {kycData.id_type ? (
                    <p className="mt-1 text-sm text-foreground">
                      {ID_TYPE_LABELS[kycData.id_type] || kycData.id_type}
                      {kycData.id_number && (
                        <span className="ml-1 font-mono text-xs text-muted-foreground">
                          ({kycData.id_number})
                        </span>
                      )}
                    </p>
                  ) : (
                    <p className="mt-1 text-sm text-muted-foreground">—</p>
                  )}
                </div>

                {/* Next Review */}
                <div className="rounded-lg bg-muted/50 p-3">
                  <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">
                    Volgende review
                  </p>
                  {kycData.next_review_date ? (
                    <p className="mt-1 text-sm text-foreground">
                      {formatDateShort(kycData.next_review_date)}
                    </p>
                  ) : (
                    <p className="mt-1 text-sm text-muted-foreground">—</p>
                  )}
                </div>
              </div>

              {/* Checks */}
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="flex items-center gap-2">
                  {kycData.pep_checked ? (
                    <Check className="h-4 w-4 text-emerald-500" />
                  ) : (
                    <X className="h-4 w-4 text-red-400" />
                  )}
                  <span className="text-sm text-foreground">
                    PEP-controle
                    {kycData.pep_is_pep && (
                      <span className="ml-1 text-xs text-red-600 font-medium">
                        (PEP!)
                      </span>
                    )}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  {kycData.sanctions_checked ? (
                    <Check className="h-4 w-4 text-emerald-500" />
                  ) : (
                    <X className="h-4 w-4 text-red-400" />
                  )}
                  <span className="text-sm text-foreground">
                    Sanctielijst
                    {kycData.sanctions_hit && (
                      <span className="ml-1 text-xs text-red-600 font-medium">
                        (Hit!)
                      </span>
                    )}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  {kycData.source_of_funds_verified ? (
                    <Check className="h-4 w-4 text-emerald-500" />
                  ) : (
                    <X className="h-4 w-4 text-red-400" />
                  )}
                  <span className="text-sm text-foreground">
                    Herkomst middelen
                  </span>
                </div>
                {contactType === "company" && (
                  <div className="flex items-center gap-2">
                    {kycData.ubo_name ? (
                      <Check className="h-4 w-4 text-emerald-500" />
                    ) : (
                      <X className="h-4 w-4 text-red-400" />
                    )}
                    <span className="text-sm text-foreground">
                      UBO-registratie
                      {kycData.ubo_name && (
                        <span className="ml-1 text-xs text-muted-foreground">
                          ({kycData.ubo_name})
                        </span>
                      )}
                    </span>
                  </div>
                )}
              </div>

              {/* Verified by */}
              {kycData.verified_by && (
                <div className="text-xs text-muted-foreground">
                  Geverifieerd door {kycData.verified_by.full_name}
                  {kycData.verification_date &&
                    ` op ${formatDateShort(kycData.verification_date)}`}
                </div>
              )}

              {/* Notes */}
              {kycData.notes && (
                <div className="text-sm text-foreground whitespace-pre-wrap">
                  {kycData.notes}
                </div>
              )}

              {/* Action buttons */}
              <div className="flex gap-3 pt-1">
                {kycStatus !== "voltooid" && (
                  <button
                    type="button"
                    onClick={handleKycComplete}
                    disabled={completeKycIsPending}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50 transition-colors"
                  >
                    <ShieldCheck className="h-4 w-4" />
                    {completeKycIsPending
                      ? "Afronden..."
                      : "Verificatie afronden"}
                  </button>
                )}
                <button
                  type="button"
                  onClick={startKycEditing}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-border px-4 py-2 text-sm hover:bg-muted transition-colors"
                >
                  <Pencil className="h-4 w-4" />
                  Bewerken
                </button>
              </div>
            </div>
          ) : (
            /* ── No KYC yet ─────────────────────────────────────── */
            <div className="py-4 text-center">
              <ShieldAlert className="mx-auto h-10 w-10 text-red-300 mb-3" />
              <p className="text-sm font-medium text-foreground">
                Nog geen WWFT-verificatie gestart
              </p>
              <p className="mt-1 text-xs text-muted-foreground max-w-sm mx-auto">
                De WWFT verplicht advocatenkantoren om de identiteit van
                cliënten te verifiëren voordat juridische diensten worden
                verleend.
              </p>
              <button
                type="button"
                onClick={startKycEditing}
                className="mt-4 inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
              >
                <Shield className="h-4 w-4" />
                Verificatie starten
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
