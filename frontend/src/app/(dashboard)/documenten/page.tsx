"use client";

import { useState } from "react";
import Link from "next/link";
import {
  FileText,
  File,
  FileCheck,
  Search,
  ArrowRight,
  Info,
} from "lucide-react";
import {
  useDocxTemplates,
  getTemplateLabel,
  getTemplateDescription,
} from "@/hooks/use-documents";
import { useDocumentTemplates } from "@/hooks/use-documents";

export default function DocumentenPage() {
  const [tab, setTab] = useState<"docx" | "html">("docx");
  const { data: docxTemplates, isLoading: docxLoading } = useDocxTemplates();
  const { data: htmlTemplates, isLoading: htmlLoading } =
    useDocumentTemplates();

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Sjablonen</h1>
        <p className="text-sm text-muted-foreground">
          Beheer de documentsjablonen die beschikbaar zijn voor dossiergeneratie
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

      {/* Tabs */}
      <div className="border-b border-border">
        <nav className="flex gap-1">
          <button
            onClick={() => setTab("docx")}
            className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-medium transition-colors ${
              tab === "docx"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <FileText className="h-4 w-4" />
            Word Templates
          </button>
          <button
            onClick={() => setTab("html")}
            className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-medium transition-colors ${
              tab === "html"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <FileCheck className="h-4 w-4" />
            HTML Sjablonen
          </button>
        </nav>
      </div>

      {tab === "docx" ? (
        <DocxTemplatesView templates={docxTemplates} isLoading={docxLoading} />
      ) : (
        <HtmlTemplatesView
          templates={htmlTemplates}
          isLoading={htmlLoading}
        />
      )}
    </div>
  );
}

// ── Docx Templates View ─────────────────────────────────────────────────────

function DocxTemplatesView({
  templates,
  isLoading,
}: {
  templates: any[] | undefined;
  isLoading: boolean;
}) {
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
          <File className="h-8 w-8 text-muted-foreground/50" />
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
          <p className="mt-2 text-[11px] text-muted-foreground/70">
            {template.filename}
          </p>
        </div>
      ))}
    </div>
  );
}

// ── HTML Templates View ─────────────────────────────────────────────────────

function HtmlTemplatesView({
  templates,
  isLoading,
}: {
  templates: any[] | undefined;
  isLoading: boolean;
}) {
  if (isLoading) {
    return (
      <div className="space-y-2">
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex items-center gap-3 rounded-lg border border-border bg-card p-4">
            <div className="h-9 w-9 rounded-lg skeleton" />
            <div className="flex-1 space-y-2">
              <div className="h-4 w-40 rounded skeleton" />
              <div className="h-3 w-24 rounded skeleton" />
            </div>
            <div className="h-5 w-16 rounded-full skeleton" />
          </div>
        ))}
      </div>
    );
  }

  if (!templates?.length) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border bg-card/50 py-20">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-muted">
          <FileCheck className="h-8 w-8 text-muted-foreground/50" />
        </div>
        <p className="mt-5 text-base font-medium text-foreground">
          Nog geen HTML-sjablonen aangemaakt
        </p>
        <p className="mt-1 text-sm text-muted-foreground max-w-sm mx-auto">
          HTML-sjablonen worden gebruikt voor het genereren van documenten
          binnen het systeem. Ze kunnen via de API worden aangemaakt.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {templates.map((template) => (
        <div
          key={template.id}
          className="flex items-center justify-between rounded-lg border border-border bg-card p-4 hover:border-primary/20 transition-colors"
        >
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-muted">
              <FileText className="h-4 w-4 text-muted-foreground" />
            </div>
            <div>
              <p className="text-sm font-medium text-foreground">
                {template.name}
              </p>
              <p className="text-xs text-muted-foreground">
                Type: {template.template_type}
              </p>
            </div>
          </div>
          <span
            className={`rounded-full px-2 py-0.5 text-xs font-medium ${
              template.is_active
                ? "bg-emerald-100 text-emerald-700"
                : "bg-muted text-muted-foreground"
            }`}
          >
            {template.is_active ? "Actief" : "Inactief"}
          </span>
        </div>
      ))}
    </div>
  );
}
