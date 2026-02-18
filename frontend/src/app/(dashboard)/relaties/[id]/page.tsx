"use client";

import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Building2,
  User,
  Mail,
  Phone,
  MapPin,
  Trash2,
} from "lucide-react";
import { toast } from "sonner";
import { useRelation, useDeleteRelation } from "@/hooks/use-relations";
import { formatDate } from "@/lib/utils";

export default function RelatieDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const { data: contact, isLoading } = useRelation(id);
  const deleteRelation = useDeleteRelation();

  const handleDelete = async () => {
    if (!confirm("Weet je zeker dat je deze relatie wilt verwijderen?")) return;
    try {
      await deleteRelation.mutateAsync(id);
      toast.success("Relatie verwijderd");
      router.push("/relaties");
    } catch {
      toast.error("Kon de relatie niet verwijderen");
    }
  };

  if (isLoading) {
    return (
      <div className="mx-auto max-w-3xl space-y-6 animate-fade-in">
        <div className="h-8 w-48 rounded-md skeleton" />
        <div className="grid gap-6 md:grid-cols-2">
          <div className="h-48 rounded-lg skeleton" />
          <div className="h-48 rounded-lg skeleton" />
        </div>
      </div>
    );
  }

  if (!contact) {
    return (
      <div className="py-20 text-center">
        <p className="text-muted-foreground">Relatie niet gevonden</p>
        <Link
          href="/relaties"
          className="mt-2 inline-block text-sm text-primary hover:underline"
        >
          Terug naar relaties
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link
            href="/relaties"
            className="rounded-lg p-2 hover:bg-muted transition-colors"
          >
            <ArrowLeft className="h-5 w-5 text-muted-foreground" />
          </Link>
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
              {contact.contact_type === "company" ? (
                <Building2 className="h-5 w-5 text-primary" />
              ) : (
                <User className="h-5 w-5 text-primary" />
              )}
            </div>
            <div>
              <h1 className="text-2xl font-bold text-foreground">
                {contact.name}
              </h1>
              <p className="text-sm text-muted-foreground">
                {contact.contact_type === "company" ? "Bedrijf" : "Persoon"}{" "}
                &middot; Aangemaakt op {formatDate(contact.created_at)}
              </p>
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleDelete}
            className="inline-flex items-center gap-1 rounded-lg border border-destructive/20 px-3 py-2 text-sm text-destructive hover:bg-destructive/10 transition-colors"
          >
            <Trash2 className="h-4 w-4" />
            Verwijderen
          </button>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Contact info */}
        <div className="rounded-xl border border-border bg-card p-6">
          <h2 className="mb-4 text-base font-semibold text-foreground">
            Contactgegevens
          </h2>
          <div className="space-y-3">
            {contact.email && (
              <div className="flex items-center gap-3">
                <Mail className="h-4 w-4 text-muted-foreground" />
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
                <Phone className="h-4 w-4 text-muted-foreground" />
                <a
                  href={`tel:${contact.phone}`}
                  className="text-sm text-foreground hover:underline"
                >
                  {contact.phone}
                </a>
              </div>
            )}
            {contact.visit_address && (
              <div className="flex items-start gap-3">
                <MapPin className="h-4 w-4 text-muted-foreground mt-0.5" />
                <div className="text-sm text-foreground">
                  {contact.visit_address}
                  <br />
                  {contact.visit_postcode} {contact.visit_city}
                </div>
              </div>
            )}
            {!contact.email && !contact.phone && !contact.visit_address && (
              <p className="text-sm text-muted-foreground">
                Geen contactgegevens
              </p>
            )}
          </div>
        </div>

        {/* Business info */}
        <div className="rounded-xl border border-border bg-card p-6">
          <h2 className="mb-4 text-base font-semibold text-foreground">
            {contact.contact_type === "company"
              ? "Bedrijfsgegevens"
              : "Details"}
          </h2>
          <div className="space-y-3">
            {contact.kvk_number && (
              <div>
                <p className="text-xs text-muted-foreground">KvK-nummer</p>
                <p className="text-sm font-medium text-foreground">
                  {contact.kvk_number}
                </p>
              </div>
            )}
            {contact.btw_number && (
              <div>
                <p className="text-xs text-muted-foreground">BTW-nummer</p>
                <p className="text-sm font-medium text-foreground">
                  {contact.btw_number}
                </p>
              </div>
            )}
            {contact.first_name && (
              <div>
                <p className="text-xs text-muted-foreground">Naam</p>
                <p className="text-sm font-medium text-foreground">
                  {contact.first_name} {contact.last_name}
                </p>
              </div>
            )}
            {!contact.kvk_number &&
              !contact.btw_number &&
              !contact.first_name && (
                <p className="text-sm text-muted-foreground">
                  Geen extra gegevens
                </p>
              )}
          </div>
        </div>
      </div>

      {/* Notes */}
      {contact.notes && (
        <div className="rounded-xl border border-border bg-card p-6">
          <h2 className="mb-3 text-base font-semibold text-foreground">
            Notities
          </h2>
          <p className="text-sm text-foreground whitespace-pre-wrap">
            {contact.notes}
          </p>
        </div>
      )}
    </div>
  );
}
