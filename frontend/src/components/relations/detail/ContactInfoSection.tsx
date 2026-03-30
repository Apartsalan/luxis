"use client";

import { Mail, Phone, MapPin, Clock, FileText, Euro } from "lucide-react";
import { formatDate } from "@/lib/utils";
import type { Contact } from "@/hooks/use-relations";

interface ContactInfoSectionProps {
  contact: Contact;
  editing: boolean;
  editForm: Record<string, string>;
  updateEdit: (field: string, value: string) => void;
  inputClass: string;
}

export function ContactInfoSection({
  contact,
  editing,
  editForm,
  updateEdit,
  inputClass,
}: ContactInfoSectionProps) {
  return (
    <div className="lg:col-span-3 space-y-6">
      <div className="rounded-xl border border-border bg-card p-6">
        <h2 className="mb-4 text-sm font-semibold text-card-foreground uppercase tracking-wider">
          Contactgegevens
        </h2>
        {editing ? (
          <div className="space-y-4">
            {contact.contact_type === "company" ? (
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                  Bedrijfsnaam
                </label>
                <input
                  type="text"
                  value={editForm.name}
                  onChange={(e) => updateEdit("name", e.target.value)}
                  className={inputClass}
                />
              </div>
            ) : (
              <div className="grid gap-4 grid-cols-2">
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                    Voornaam
                  </label>
                  <input
                    type="text"
                    value={editForm.first_name}
                    onChange={(e) =>
                      updateEdit("first_name", e.target.value)
                    }
                    className={inputClass}
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                    Achternaam
                  </label>
                  <input
                    type="text"
                    value={editForm.last_name}
                    onChange={(e) =>
                      updateEdit("last_name", e.target.value)
                    }
                    className={inputClass}
                  />
                </div>
              </div>
            )}
            {contact.contact_type === "person" && (
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                  Geboortedatum
                </label>
                <input
                  type="date"
                  value={editForm.date_of_birth}
                  onChange={(e) =>
                    updateEdit("date_of_birth", e.target.value)
                  }
                  className={inputClass}
                />
              </div>
            )}
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                  E-mail
                </label>
                <input
                  type="email"
                  value={editForm.email}
                  onChange={(e) => updateEdit("email", e.target.value)}
                  className={inputClass}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                  Telefoon
                </label>
                <input
                  type="tel"
                  value={editForm.phone}
                  onChange={(e) => updateEdit("phone", e.target.value)}
                  className={inputClass}
                />
              </div>
            </div>
            {contact.contact_type === "company" && (
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                    KvK-nummer
                  </label>
                  <input
                    type="text"
                    value={editForm.kvk_number}
                    onChange={(e) =>
                      updateEdit("kvk_number", e.target.value)
                    }
                    className={inputClass}
                    maxLength={8}
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                    BTW-nummer
                  </label>
                  <input
                    type="text"
                    value={editForm.btw_number}
                    onChange={(e) =>
                      updateEdit("btw_number", e.target.value)
                    }
                    className={inputClass}
                  />
                </div>
              </div>
            )}
            <div className="pt-2">
              <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                Bezoekadres
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                    Straat + huisnummer
                  </label>
                  <input
                    type="text"
                    value={editForm.visit_address}
                    onChange={(e) =>
                      updateEdit("visit_address", e.target.value)
                    }
                    className={inputClass}
                  />
                </div>
                <div className="grid gap-4 grid-cols-2">
                  <div>
                    <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                      Postcode
                    </label>
                    <input
                      type="text"
                      value={editForm.visit_postcode}
                      onChange={(e) =>
                        updateEdit("visit_postcode", e.target.value)
                      }
                      className={inputClass}
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                      Plaats
                    </label>
                    <input
                      type="text"
                      value={editForm.visit_city}
                      onChange={(e) =>
                        updateEdit("visit_city", e.target.value)
                      }
                      className={inputClass}
                    />
                  </div>
                </div>
              </div>
            </div>
            <div className="pt-2">
              <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                Postadres <span className="font-normal normal-case">(optioneel, indien afwijkend)</span>
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                    Postbus / straat
                  </label>
                  <input
                    type="text"
                    value={editForm.postal_address}
                    onChange={(e) =>
                      updateEdit("postal_address", e.target.value)
                    }
                    className={inputClass}
                    placeholder="bijv. Postbus 123"
                  />
                </div>
                <div className="grid gap-4 grid-cols-2">
                  <div>
                    <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                      Postcode
                    </label>
                    <input
                      type="text"
                      value={editForm.postal_postcode}
                      onChange={(e) =>
                        updateEdit("postal_postcode", e.target.value)
                      }
                      className={inputClass}
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                      Plaats
                    </label>
                    <input
                      type="text"
                      value={editForm.postal_city}
                      onChange={(e) =>
                        updateEdit("postal_city", e.target.value)
                      }
                      className={inputClass}
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {contact.email && (
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-muted">
                  <Mail className="h-4 w-4 text-muted-foreground" />
                </div>
                <a
                  href={`mailto:${contact.email}`}
                  className="text-sm text-primary hover:underline"
                >
                  {contact.email}
                </a>
              </div>
            )}
            {contact.phone && (
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-muted">
                  <Phone className="h-4 w-4 text-muted-foreground" />
                </div>
                <a
                  href={`tel:${contact.phone}`}
                  className="text-sm text-foreground hover:underline"
                >
                  {contact.phone}
                </a>
              </div>
            )}
            {contact.contact_type === "person" && contact.date_of_birth && (
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-muted">
                  <Clock className="h-4 w-4 text-muted-foreground" />
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Geboortedatum</p>
                  <p className="text-sm text-foreground">
                    {formatDate(contact.date_of_birth)}
                  </p>
                </div>
              </div>
            )}
            {contact.visit_address && (
              <div className="flex items-start gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-muted mt-0.5">
                  <MapPin className="h-4 w-4 text-muted-foreground" />
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">
                    {contact.postal_address ? "Bezoekadres" : "Adres"}
                  </p>
                  <p className="text-sm text-foreground">
                    {contact.visit_address}
                    <br />
                    {contact.visit_postcode} {contact.visit_city}
                  </p>
                </div>
              </div>
            )}
            {contact.postal_address && (
              <div className="flex items-start gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-muted mt-0.5">
                  <MapPin className="h-4 w-4 text-muted-foreground" />
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Postadres</p>
                  <p className="text-sm text-foreground">
                    {contact.postal_address}
                    <br />
                    {contact.postal_postcode} {contact.postal_city}
                  </p>
                </div>
              </div>
            )}
            {contact.kvk_number && (
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-muted">
                  <FileText className="h-4 w-4 text-muted-foreground" />
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">KvK</p>
                  <p className="text-sm font-mono text-foreground">
                    {contact.kvk_number}
                  </p>
                </div>
              </div>
            )}
            {contact.btw_number && (
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-muted">
                  <Euro className="h-4 w-4 text-muted-foreground" />
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">BTW</p>
                  <p className="text-sm font-mono text-foreground">
                    {contact.btw_number}
                  </p>
                </div>
              </div>
            )}
            {!contact.email &&
              !contact.phone &&
              !contact.visit_address &&
              !contact.kvk_number && (
                <p className="text-sm text-muted-foreground">
                  Geen contactgegevens ingevuld
                </p>
              )}
          </div>
        )}
      </div>

      {/* Billing Profile (F6) */}
      <div className="rounded-xl border border-border bg-card p-6">
        <h2 className="mb-3 text-sm font-semibold text-card-foreground uppercase tracking-wider">
          Facturatie
        </h2>
        {editing ? (
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">Standaard uurtarief (€)</label>
              <input
                type="number"
                step="0.01"
                value={editForm.default_hourly_rate}
                onChange={(e) => updateEdit("default_hourly_rate", e.target.value)}
                className={inputClass}
                placeholder="Bijv. 250.00"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">Betalingstermijn (dagen)</label>
              <input
                type="number"
                value={editForm.payment_term_days}
                onChange={(e) => updateEdit("payment_term_days", e.target.value)}
                className={inputClass}
                placeholder="Bijv. 14"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">Factuur e-mail</label>
              <input
                type="email"
                value={editForm.billing_email}
                onChange={(e) => updateEdit("billing_email", e.target.value)}
                className={inputClass}
                placeholder="facturen@bedrijf.nl"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">IBAN</label>
              <input
                type="text"
                value={editForm.iban}
                onChange={(e) => updateEdit("iban", e.target.value)}
                className={inputClass}
                placeholder="NL00 BANK 0000 0000 00"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">Standaard rentetype</label>
              <select
                value={editForm.default_interest_type || ""}
                onChange={(e) => updateEdit("default_interest_type", e.target.value)}
                className={inputClass}
              >
                <option value="">Geen standaard</option>
                <option value="statutory">Wettelijke rente (art. 6:119 BW)</option>
                <option value="commercial">Handelsrente (art. 6:119a BW)</option>
                <option value="government">Overheidsrente (art. 6:119b BW)</option>
                <option value="contractual">Contractuele rente</option>
              </select>
            </div>
            {editForm.default_interest_type === "contractual" && (
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">Contractueel rentepercentage (%)</label>
                <input
                  type="number"
                  step="0.01"
                  value={editForm.default_contractual_rate}
                  onChange={(e) => updateEdit("default_contractual_rate", e.target.value)}
                  className={inputClass}
                  placeholder="Bijv. 8.00"
                />
              </div>
            )}
          </div>
        ) : (contact.default_hourly_rate || contact.payment_term_days || contact.billing_email || contact.iban || contact.default_interest_type) ? (
          <dl className="grid gap-3 sm:grid-cols-2">
            {contact.default_hourly_rate && (
              <div>
                <dt className="text-xs text-muted-foreground">Uurtarief</dt>
                <dd className="text-sm font-medium text-foreground">€ {Number(contact.default_hourly_rate).toFixed(2)}</dd>
              </div>
            )}
            {contact.payment_term_days && (
              <div>
                <dt className="text-xs text-muted-foreground">Betalingstermijn</dt>
                <dd className="text-sm font-medium text-foreground">{contact.payment_term_days} dagen</dd>
              </div>
            )}
            {contact.billing_email && (
              <div>
                <dt className="text-xs text-muted-foreground">Factuur e-mail</dt>
                <dd className="text-sm text-foreground">{contact.billing_email}</dd>
              </div>
            )}
            {contact.iban && (
              <div>
                <dt className="text-xs text-muted-foreground">IBAN</dt>
                <dd className="text-sm font-mono text-foreground">{contact.iban}</dd>
              </div>
            )}
            {contact.default_interest_type && (
              <div>
                <dt className="text-xs text-muted-foreground">Standaard rente</dt>
                <dd className="text-sm font-medium text-foreground">
                  {{ statutory: "Wettelijke rente", commercial: "Handelsrente", government: "Overheidsrente", contractual: "Contractuele rente" }[contact.default_interest_type] ?? contact.default_interest_type}
                  {contact.default_interest_type === "contractual" && contact.default_contractual_rate != null && ` (${contact.default_contractual_rate}%)`}
                </dd>
              </div>
            )}
          </dl>
        ) : (
          <p className="text-sm text-muted-foreground">Geen facturatiegegevens ingesteld</p>
        )}
      </div>

      {/* Notes */}
      <div className="rounded-xl border border-border bg-card p-6">
        <h2 className="mb-3 text-sm font-semibold text-card-foreground uppercase tracking-wider">
          Notities
        </h2>
        {editing ? (
          <textarea
            value={editForm.notes}
            onChange={(e) => updateEdit("notes", e.target.value)}
            rows={4}
            className={`${inputClass} resize-none`}
            placeholder="Voeg notities toe..."
          />
        ) : contact.notes ? (
          <p className="text-sm text-foreground whitespace-pre-wrap leading-relaxed">
            {contact.notes}
          </p>
        ) : (
          <p className="text-sm text-muted-foreground">Geen notities</p>
        )}
      </div>
    </div>
  );
}
