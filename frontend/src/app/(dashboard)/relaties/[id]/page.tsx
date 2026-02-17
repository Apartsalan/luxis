"use client";

import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Building2, User, Mail, Phone, MapPin, Edit, Trash2 } from "lucide-react";
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
      router.push("/relaties");
    } catch {
      alert("Kon de relatie niet verwijderen");
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-navy-200 border-t-navy-500" />
      </div>
    );
  }

  if (!contact) {
    return (
      <div className="py-20 text-center">
        <p className="text-muted-foreground">Relatie niet gevonden</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link
            href="/relaties"
            className="rounded-md p-2 hover:bg-muted transition-colors"
          >
            <ArrowLeft className="h-5 w-5 text-navy-500" />
          </Link>
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-navy-100">
              {contact.contact_type === "company" ? (
                <Building2 className="h-5 w-5 text-navy-500" />
              ) : (
                <User className="h-5 w-5 text-navy-500" />
              )}
            </div>
            <div>
              <h1 className="text-2xl font-bold text-navy-800">{contact.name}</h1>
              <p className="text-sm text-muted-foreground">
                {contact.contact_type === "company" ? "Bedrijf" : "Persoon"} &middot;
                Aangemaakt op {formatDate(contact.created_at)}
              </p>
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleDelete}
            className="inline-flex items-center gap-1 rounded-md border border-red-200 px-3 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"
          >
            <Trash2 className="h-4 w-4" />
            Verwijderen
          </button>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Contact info */}
        <div className="rounded-lg border border-border bg-white p-6">
          <h2 className="mb-4 text-lg font-semibold text-navy-800">
            Contactgegevens
          </h2>
          <div className="space-y-3">
            {contact.email && (
              <div className="flex items-center gap-3">
                <Mail className="h-4 w-4 text-muted-foreground" />
                <a
                  href={`mailto:${contact.email}`}
                  className="text-sm text-navy-600 hover:underline"
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
                  className="text-sm text-navy-600 hover:underline"
                >
                  {contact.phone}
                </a>
              </div>
            )}
            {contact.visit_address && (
              <div className="flex items-start gap-3">
                <MapPin className="h-4 w-4 text-muted-foreground mt-0.5" />
                <div className="text-sm text-navy-600">
                  {contact.visit_address}
                  <br />
                  {contact.visit_postcode} {contact.visit_city}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Business info */}
        <div className="rounded-lg border border-border bg-white p-6">
          <h2 className="mb-4 text-lg font-semibold text-navy-800">
            {contact.contact_type === "company" ? "Bedrijfsgegevens" : "Details"}
          </h2>
          <div className="space-y-3">
            {contact.kvk_number && (
              <div>
                <p className="text-xs text-muted-foreground">KvK-nummer</p>
                <p className="text-sm font-medium text-navy-700">{contact.kvk_number}</p>
              </div>
            )}
            {contact.btw_number && (
              <div>
                <p className="text-xs text-muted-foreground">BTW-nummer</p>
                <p className="text-sm font-medium text-navy-700">{contact.btw_number}</p>
              </div>
            )}
            {contact.first_name && (
              <div>
                <p className="text-xs text-muted-foreground">Naam</p>
                <p className="text-sm font-medium text-navy-700">
                  {contact.first_name} {contact.last_name}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Notes */}
      {contact.notes && (
        <div className="rounded-lg border border-border bg-white p-6">
          <h2 className="mb-3 text-lg font-semibold text-navy-800">Notities</h2>
          <p className="text-sm text-navy-600 whitespace-pre-wrap">{contact.notes}</p>
        </div>
      )}
    </div>
  );
}
