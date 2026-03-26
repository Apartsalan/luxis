"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import {
  Building2,
  User,
  Plus,
  Trash2,
  Search,
  Link2,
  Loader2,
} from "lucide-react";
import { toast } from "sonner";
import { useConfirm } from "@/components/confirm-dialog";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  type LinkedContactInfo,
  useSearchRelations,
  useCreateContactLink,
  useDeleteContactLink,
} from "@/hooks/use-relations";

const ROLE_OPTIONS = [
  "Directeur",
  "Contactpersoon",
  "Aandeelhouder",
  "Bestuurder",
  "Gemachtigde",
  "Werknemer",
];

interface ContactLinksProps {
  contactId: string;
  contactType: "company" | "person";
  links: LinkedContactInfo[];
}

export function ContactLinks({
  contactId,
  contactType,
  links,
}: ContactLinksProps) {
  const { confirm, ConfirmDialog: ConfirmDialogEl } = useConfirm();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedName, setSelectedName] = useState("");
  const [role, setRole] = useState("");
  const [showResults, setShowResults] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const searchRef = useRef<HTMLDivElement>(null);

  const isPerson = contactType === "person";
  const searchType = isPerson ? "company" : "person";
  const title = isPerson ? "Gekoppelde bedrijven" : "Contactpersonen";
  const addLabel = isPerson
    ? "Bedrijf koppelen"
    : "Contactpersoon koppelen";
  const emptyLabel = isPerson
    ? "Nog geen gekoppelde bedrijven"
    : "Nog geen contactpersonen";
  const emptyDescription = isPerson
    ? "Koppel een bedrijf om de zakelijke relatie vast te leggen."
    : "Koppel een contactpersoon om de relatie vast te leggen.";

  const { data: searchResults, isLoading: searching } = useSearchRelations(
    search,
    searchType
  );
  const createLink = useCreateContactLink();
  const deleteLink = useDeleteContactLink();

  // Close search results when clicking outside
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setShowResults(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSelect = (id: string, name: string) => {
    setSelectedId(id);
    setSelectedName(name);
    setSearch("");
    setShowResults(false);
  };

  const handleAdd = async () => {
    if (!selectedId) return;

    const data = isPerson
      ? { person_id: contactId, company_id: selectedId, role_at_company: role?.trim() || null }
      : { person_id: selectedId, company_id: contactId, role_at_company: role?.trim() || null };

    try {
      await createLink.mutateAsync(data);
      toast.success("Koppeling toegevoegd");
      setDialogOpen(false);
      resetForm();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Kon koppeling niet toevoegen");
    }
  };

  const handleDelete = async (linkId: string) => {
    if (!await confirm({ title: "Koppeling verwijderen", description: "Weet je zeker dat je deze koppeling wilt verwijderen?", variant: "destructive", confirmText: "Verwijderen" })) return;
    setDeletingId(linkId);
    try {
      await deleteLink.mutateAsync(linkId);
      toast.success("Koppeling verwijderd");
    } catch {
      toast.error("Kon koppeling niet verwijderen");
    } finally {
      setDeletingId(null);
    }
  };

  const resetForm = () => {
    setSearch("");
    setSelectedId(null);
    setSelectedName("");
    setRole("");
    setShowResults(false);
  };

  // Filter out already-linked contacts from search results
  const linkedIds = new Set(links.map((l) => l.contact.id));
  const filteredResults =
    searchResults?.items.filter(
      (c) => !linkedIds.has(c.id) && c.id !== contactId
    ) ?? [];

  const inputClass =
    "w-full rounded-lg border border-input bg-background px-3 py-2.5 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors";

  return (
    <>
      {ConfirmDialogEl}
      <div className="rounded-xl border border-border bg-card">
        <div className="flex items-center justify-between px-5 py-4 border-b border-border">
          <div className="flex items-center gap-2">
            <Link2 className="h-4 w-4 text-muted-foreground" />
            <h2 className="text-sm font-semibold text-card-foreground">
              {title}
              {links.length > 0 && (
                <span className="ml-1.5 inline-flex h-5 w-5 items-center justify-center rounded-full bg-primary/10 text-xs font-bold text-primary">
                  {links.length}
                </span>
              )}
            </h2>
          </div>
          <button
            type="button"
            onClick={() => {
              resetForm();
              setDialogOpen(true);
            }}
            className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
          >
            <Plus className="h-3.5 w-3.5" />
            {addLabel}
          </button>
        </div>

        {links.length > 0 ? (
          <div className="divide-y divide-border">
            {links.map((link) => (
              <div
                key={link.link_id}
                className="flex items-center justify-between px-5 py-3.5 hover:bg-muted/40 transition-colors group"
              >
                <Link
                  href={`/relaties/${link.contact.id}`}
                  className="flex items-center gap-3 min-w-0 flex-1"
                >
                  <div
                    className={`flex h-8 w-8 items-center justify-center rounded-full shrink-0 ${
                      link.contact.contact_type === "company"
                        ? "bg-blue-50 text-blue-600"
                        : "bg-violet-50 text-violet-600"
                    }`}
                  >
                    {link.contact.contact_type === "company" ? (
                      <Building2 className="h-3.5 w-3.5" />
                    ) : (
                      <User className="h-3.5 w-3.5" />
                    )}
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-foreground truncate hover:text-primary transition-colors">
                      {link.contact.name}
                    </p>
                    {link.role_at_company && (
                      <p className="text-xs text-muted-foreground">
                        {link.role_at_company}
                      </p>
                    )}
                  </div>
                </Link>
                <button
                  type="button"
                  onClick={() => handleDelete(link.link_id)}
                  disabled={deletingId === link.link_id}
                  className="rounded-lg p-1.5 text-muted-foreground opacity-0 group-hover:opacity-100 hover:text-destructive hover:bg-destructive/10 transition-all disabled:opacity-50"
                  title="Koppeling verwijderen"
                >
                  {deletingId === link.link_id ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <Trash2 className="h-3.5 w-3.5" />
                  )}
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div className="px-5 py-8 text-center">
            <Link2 className="mx-auto h-8 w-8 text-muted-foreground/30 mb-2" />
            <p className="text-sm text-muted-foreground">{emptyLabel}</p>
            <button
              type="button"
              onClick={() => {
                resetForm();
                setDialogOpen(true);
              }}
              className="mt-1 inline-block text-sm text-primary hover:underline"
            >
              {addLabel}
            </button>
          </div>
        )}
      </div>

      {/* Add Link Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{addLabel}</DialogTitle>
            <DialogDescription>
              Zoek een {isPerson ? "bedrijf" : "persoon"} om te koppelen.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 pt-2">
            {/* Search or selected */}
            {selectedId ? (
              <div className="flex items-center justify-between rounded-lg border border-primary/30 bg-primary/5 px-3 py-2.5">
                <div className="flex items-center gap-2">
                  <div
                    className={`flex h-7 w-7 items-center justify-center rounded-full ${
                      searchType === "company"
                        ? "bg-blue-50 text-blue-600"
                        : "bg-violet-50 text-violet-600"
                    }`}
                  >
                    {searchType === "company" ? (
                      <Building2 className="h-3.5 w-3.5" />
                    ) : (
                      <User className="h-3.5 w-3.5" />
                    )}
                  </div>
                  <span className="text-sm font-medium text-foreground">
                    {selectedName}
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setSelectedId(null);
                    setSelectedName("");
                  }}
                  className="text-xs text-muted-foreground hover:text-foreground"
                >
                  Wijzigen
                </button>
              </div>
            ) : (
              <div ref={searchRef} className="relative">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <input
                    type="text"
                    value={search}
                    onChange={(e) => {
                      setSearch(e.target.value);
                      setShowResults(true);
                    }}
                    onFocus={() => search.length >= 2 && setShowResults(true)}
                    placeholder={`Zoek ${isPerson ? "bedrijf" : "persoon"} op naam...`}
                    className={`${inputClass} pl-9`}
                    autoFocus
                  />
                  {searching && (
                    <Loader2 className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground animate-spin" />
                  )}
                </div>

                {showResults && search.length >= 2 && (
                  <div className="absolute z-10 mt-1 w-full rounded-lg border border-border bg-card shadow-lg max-h-48 overflow-auto">
                    {filteredResults.length > 0 ? (
                      filteredResults.map((c) => (
                        <button
                          key={c.id}
                          type="button"
                          onClick={() => handleSelect(c.id, c.name)}
                          className="flex w-full items-center gap-2.5 px-3 py-2.5 text-left hover:bg-muted/60 transition-colors"
                        >
                          <div
                            className={`flex h-7 w-7 items-center justify-center rounded-full shrink-0 ${
                              c.contact_type === "company"
                                ? "bg-blue-50 text-blue-600"
                                : "bg-violet-50 text-violet-600"
                            }`}
                          >
                            {c.contact_type === "company" ? (
                              <Building2 className="h-3.5 w-3.5" />
                            ) : (
                              <User className="h-3.5 w-3.5" />
                            )}
                          </div>
                          <div className="min-w-0">
                            <p className="text-sm font-medium text-foreground truncate">
                              {c.name}
                            </p>
                            {c.email && (
                              <p className="text-xs text-muted-foreground truncate">
                                {c.email}
                              </p>
                            )}
                          </div>
                        </button>
                      ))
                    ) : !searching ? (
                      <p className="px-3 py-3 text-sm text-muted-foreground text-center">
                        Geen resultaten gevonden
                      </p>
                    ) : null}
                  </div>
                )}
              </div>
            )}

            {/* Role */}
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                Rol (optioneel)
              </label>
              <div className="flex gap-2">
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className={inputClass}
                >
                  <option value="">Geen rol</option>
                  {ROLE_OPTIONS.map((r) => (
                    <option key={r} value={r}>
                      {r}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Actions */}
            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setDialogOpen(false)}
                className="rounded-lg border border-border px-4 py-2.5 text-sm hover:bg-muted transition-colors"
              >
                Annuleren
              </button>
              <button
                type="button"
                onClick={handleAdd}
                disabled={!selectedId || createLink.isPending}
                className="rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
              >
                {createLink.isPending ? "Toevoegen..." : "Toevoegen"}
              </button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
