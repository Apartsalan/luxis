import { ConfidenceDot } from "./ConfidenceDot";
import type { LuxisModule } from "@/hooks/use-modules";

interface Step1Props {
  form: {
    case_type: string;
    debtor_type: string;
    description: string;
    reference: string;
    court_case_number: string;
    interest_type: string;
    contractual_rate: string;
    budget: string;
    date_opened: string;
    hourly_rate: string;
    payment_term_days: string;
    collection_strategy: string;
    debtor_notes: string;
  };
  updateField: (field: string, value: string) => void;
  isIncasso: boolean;
  inputClass: string;
  fieldConfidence: Record<string, number>;
  hasModule: (mod: LuxisModule) => boolean;
}

export function Step1Zaakgegevens({
  form,
  updateField,
  isIncasso,
  inputClass,
  fieldConfidence,
  hasModule,
}: Step1Props) {
  return (
    <>
      <div className="rounded-xl border border-border bg-card p-6 space-y-4">
        <h2 className="text-base font-semibold text-foreground">
          Dossiergegevens
        </h2>

        <div className="grid gap-4 sm:grid-cols-3">
          <div>
            <label className="block text-sm font-medium text-foreground">
              Dossiertype *
            </label>
            <select
              value={form.case_type}
              onChange={(e) => updateField("case_type", e.target.value)}
              className={inputClass}
            >
              <option value="incasso">Incasso</option>
              <option value="insolventie">Insolventie</option>
              <option value="advies">Advies</option>
              <option value="overig">Overig</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-foreground">
              Debiteurtype
              <ConfidenceDot field="debtor_type" confidence={fieldConfidence} />
            </label>
            <select
              value={form.debtor_type}
              onChange={(e) => updateField("debtor_type", e.target.value)}
              className={inputClass}
            >
              <option value="">Automatisch</option>
              <option value="b2b">B2B (bedrijf)</option>
              <option value="b2c">B2C (particulier)</option>
            </select>
            <p className="mt-1 text-[11px] text-muted-foreground">
              Wordt automatisch ingevuld bij selectie wederpartij
            </p>
          </div>
          <div>
            <label className="block text-sm font-medium text-foreground">
              Datum geopend *
            </label>
            <input
              type="date"
              required
              value={form.date_opened}
              onChange={(e) => updateField("date_opened", e.target.value)}
              className={inputClass}
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-foreground">
            Beschrijving
            <ConfidenceDot field="description" confidence={fieldConfidence} />
          </label>
          <textarea
            value={form.description}
            onChange={(e) => updateField("description", e.target.value)}
            rows={2}
            className={inputClass}
            placeholder="Korte omschrijving van het dossier..."
          />
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="block text-sm font-medium text-foreground">
              Referentie (klantreferentie)
            </label>
            <input
              type="text"
              value={form.reference}
              onChange={(e) => updateField("reference", e.target.value)}
              className={inputClass}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-foreground">
              Zaaknummer rechtbank
            </label>
            <input
              type="text"
              value={form.court_case_number}
              onChange={(e) =>
                updateField("court_case_number", e.target.value)
              }
              className={inputClass}
              placeholder="Bijv. C/13/123456 / HA ZA 24-789"
            />
          </div>
        </div>

        {/* G13: Budget field */}
        {hasModule("budget") && (
          <div className="sm:w-1/2">
            <label className="block text-sm font-medium text-foreground">
              Budget
            </label>
            <input
              type="number"
              step="0.01"
              min="0"
              value={form.budget}
              onChange={(e) => updateField("budget", e.target.value)}
              className={inputClass}
              placeholder="Bijv. 5000.00"
            />
            <p className="mt-1 text-[11px] text-muted-foreground">
              Optioneel budget in euro&apos;s voor dit dossier
            </p>
          </div>
        )}
      </div>

      {/* Interest settings — only for incasso */}
      {isIncasso && (
        <div className="rounded-xl border border-border bg-card p-6 space-y-4">
          <h2 className="text-base font-semibold text-foreground">
            Rente-instellingen
          </h2>

          <div>
            <label className="block text-sm font-medium text-foreground">
              Type rente
            </label>
            <select
              value={form.interest_type}
              onChange={(e) =>
                updateField("interest_type", e.target.value)
              }
              className={inputClass}
            >
              <option value="statutory">
                Wettelijke rente (art. 6:119 BW)
              </option>
              <option value="commercial">
                Handelsrente (art. 6:119a BW)
              </option>
              <option value="government">
                Overheidsrente (art. 6:119b BW)
              </option>
              <option value="contractual">Contractuele rente</option>
            </select>
          </div>

          {form.interest_type === "contractual" && (
            <div>
              <label className="block text-sm font-medium text-foreground">
                Contractueel rentepercentage (%) *
              </label>
              <input
                type="number"
                step="0.01"
                required={form.interest_type === "contractual"}
                value={form.contractual_rate}
                onChange={(e) =>
                  updateField("contractual_rate", e.target.value)
                }
                className={inputClass}
                placeholder="Bijv. 8.00"
              />
            </div>
          )}
        </div>
      )}

      {/* LF-19/22: Incasso-instellingen — only for incasso */}
      {isIncasso && (
        <div className="rounded-xl border border-border bg-card p-6 space-y-4">
          <h2 className="text-base font-semibold text-foreground">
            Incasso-instellingen
          </h2>
          <p className="text-xs text-muted-foreground -mt-2">
            Optionele instellingen voor dit incassodossier
          </p>

          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-foreground">
                Uurtarief
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={form.hourly_rate}
                onChange={(e) =>
                  updateField("hourly_rate", e.target.value)
                }
                className={inputClass}
                placeholder="Bijv. 250.00"
              />
              <p className="mt-1 text-[11px] text-muted-foreground">
                EUR per uur (overschrijft kantoorstandaard)
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground">
                Betalingstermijn
              </label>
              <input
                type="number"
                min="1"
                value={form.payment_term_days}
                onChange={(e) =>
                  updateField("payment_term_days", e.target.value)
                }
                className={inputClass}
                placeholder="Bijv. 14"
              />
              <p className="mt-1 text-[11px] text-muted-foreground">
                Dagen
              </p>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground">
              Incassostrategie
            </label>
            <select
              value={form.collection_strategy}
              onChange={(e) =>
                updateField("collection_strategy", e.target.value)
              }
              className={inputClass}
            >
              <option value="">Niet ingesteld</option>
              <option value="standaard">Standaard</option>
              <option value="minnelijk">Minnelijk</option>
              <option value="gerechtelijk">Gerechtelijk</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground">
              Debiteurnotities
            </label>
            <textarea
              value={form.debtor_notes}
              onChange={(e) =>
                updateField("debtor_notes", e.target.value)
              }
              rows={2}
              className={inputClass}
              placeholder="Bijv. debiteur heeft eerder betaald na 2e aanmaning..."
            />
          </div>
        </div>
      )}
    </>
  );
}
