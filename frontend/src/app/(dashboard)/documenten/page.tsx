"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  FileText,
  File,
  Search,
  ArrowRight,
  Info,
  Download,
} from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import {
  useDocxTemplates,
  getTemplateLabel,
  getTemplateDescription,
} from "@/hooks/use-documents";
import { useCases } from "@/hooks/use-cases";
import type { CaseSummary } from "@/hooks/use-cases";
import type { DocxTemplateInfo } from "@/hooks/use-documents";

export default function DocumentenPage() {
  // A7 (S198): de HTML-Sjablonen-tab las een lege, DEPRECATED tabel en toonde
  // ontwikkelaarstaal — verwijderd. Alleen de Word-sjablonen blijven. Sjabloon-
  // beheer zelf hoort in Instellingen; deze pagina is puur de generatie-lijst.
  const { data: docxTemplates, isLoading: docxLoading } = useDocxTemplates();

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Sjablonen</h1>
        <p className="text-sm text-muted-foreground">
          De documentsjablonen die beschikbaar zijn voor dossiergeneratie
        </p>
      </div>

      {/* Info banner */}
      <div className="flex items-start gap-3 rounded-xl border border-primary/20 bg-primary/5 p-4">
        <Info className="mt-0.5 h-4 w-4 text-primary shrink-0" />
        <p className="text-sm text-foreground">
          Documenten worden gegenereerd vanuit een dossier. Ga naar een{" "}
          <Link href="/zaken" className="font-medium text-primary hover:underline">
            dossier
          </Link>{" "}
          en open het tabblad &quot;Documenten&quot; om een document te genereren
          op basis van deze sjablonen.
        </p>
      </div>

      <DocxTemplatesView templates={docxTemplates} isLoading={docxLoading} />
    </div>
  );
}

// ── Case Picker Dialog ──────────────────────────────────────────────────────

function CasePickerDialog({
  open,
  onClose,
  templateType,
}: {
  open: boolean;
  onClose: () => void;
  templateType: string;
}) {
  const router = useRouter();
  const [search, setSearch] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const { data: casesData } = useCases({
    search,
    per_page: 8,
    case_type: "incasso",
  });

  useEffect(() => {
    if (open) {
      setSearch("");
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [open]);

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) onClose(); }}>
      <DialogContent className="max-w-md p-0 gap-0">
        <DialogHeader className="p-4 border-b border-border space-y-0 text-left">
          <DialogTitle className="text-sm font-semibold text-foreground pr-8">
            Kies een dossier voor &quot;{getTemplateLabel(templateType)}&quot;
          </DialogTitle>
          <div className="mt-3 flex items-center gap-2 rounded-lg border border-border bg-background px-3 py-2">
            <Search className="h-4 w-4 text-muted-foreground shrink-0" />
            <input
              ref={inputRef}
              type="text"
              placeholder="Zoek op dossiernummer of naam..."
              aria-label="Zoek op dossiernummer of naam"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground"
            />
          </div>
        </DialogHeader>
        <div className="max-h-64 overflow-y-auto p-2">
          {casesData?.items?.length ? (
            casesData.items.map((c: CaseSummary) => (
              <button
                key={c.id}
                onClick={() => {
                  router.push(`/zaken/${c.id}?tab=documenten`);
                  onClose();
                }}
                className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left hover:bg-muted transition-colors"
              >
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-foreground truncate">
                    {c.case_number}
                  </p>
                  <p className="text-xs text-muted-foreground truncate">
                    {c.client?.name}{c.opposing_party?.name ? ` vs. ${c.opposing_party.name}` : ""}
                  </p>
                </div>
                <ArrowRight className="h-4 w-4 text-muted-foreground shrink-0" />
              </button>
            ))
          ) : (
            <p className="px-3 py-6 text-center text-sm text-muted-foreground">
              {search ? "Geen dossiers gevonden" : "Typ om te zoeken..."}
            </p>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

// ── Docx Templates View ─────────────────────────────────────────────────────

function DocxTemplatesView({
  templates,
  isLoading,
}: {
  templates: DocxTemplateInfo[] | undefined;
  isLoading: boolean;
}) {
  const [pickerTemplate, setPickerTemplate] = useState<string | null>(null);
  if (isLoading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="rounded-xl border border-border bg-card p-5 space-y-3">
            <div className="flex items-start justify-between">
              <div className="h-10 w-10 rounded-lg skeleton" />
              <div className="h-5 w-20 rounded-full skeleton" />
            </div>
            <div className="h-4 w-32 rounded skeleton" />
            <div className="h-3 w-full rounded skeleton" />
            <div className="h-3 w-24 rounded skeleton" />
          </div>
        ))}
      </div>
    );
  }

  if (!templates?.length) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border bg-card/50 py-20">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-muted">
          <File className="h-8 w-8 text-muted-foreground" />
        </div>
        <p className="mt-5 text-base font-medium text-foreground">
          Geen Word-templates beschikbaar
        </p>
        <p className="mt-1 text-sm text-muted-foreground">
          Neem contact op met de beheerder om templates toe te voegen.
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {templates.map((template) => (
          <div
            key={template.template_type}
            className="group rounded-xl border border-border bg-card p-5 hover:shadow-md hover:border-primary/20 transition-all"
          >
            <div className="flex items-start justify-between">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                <FileText className="h-5 w-5 text-primary" />
              </div>
              <span
                className={`rounded-full px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider ${
                  template.available
                    ? "bg-emerald-100 text-emerald-700"
                    : "bg-muted text-muted-foreground"
                }`}
              >
                {template.available ? "Beschikbaar" : "Niet beschikbaar"}
              </span>
            </div>
            <h3 className="mt-3 text-sm font-semibold text-foreground">
              {getTemplateLabel(template.template_type)}
            </h3>
            <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
              {getTemplateDescription(template.template_type)}
            </p>
            <div className="mt-3 flex items-center justify-between">
              <p className="text-[11px] text-muted-foreground">
                {template.filename}
              </p>
              {template.available && (
                <button
                  onClick={() => setPickerTemplate(template.template_type)}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-primary/10 px-2.5 py-1.5 text-xs font-medium text-primary hover:bg-primary/20 transition-colors"
                >
                  <Download className="h-3 w-3" />
                  Genereer
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      <CasePickerDialog
        open={pickerTemplate !== null}
        onClose={() => setPickerTemplate(null)}
        templateType={pickerTemplate ?? ""}
      />
    </>
  );
}
