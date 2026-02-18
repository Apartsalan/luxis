"use client";

import { useState } from "react";
import {
  FileText,
  Download,
  Plus,
  Search,
  File,
  FileCheck,
  Clock,
} from "lucide-react";

// This page is a functional placeholder that will connect to the
// document generation backend once it's ready. For now it shows
// the templates available and a mock list of generated documents.

const TEMPLATES = [
  {
    id: "14-dagenbrief",
    name: "14-dagenbrief",
    description: "Aanmaning op grond van art. 6:96 BW met BIK-berekening",
    category: "incasso",
  },
  {
    id: "sommatie",
    name: "Sommatie",
    description: "Tweede aanmaning met renteberekening en termijn",
    category: "incasso",
  },
  {
    id: "renteberekening",
    name: "Renteberekening",
    description: "Gedetailleerd overzicht van rente per periode",
    category: "financieel",
  },
  {
    id: "betalingsoverzicht",
    name: "Betalingsoverzicht",
    description: "Samenvatting van alle betalingen en verdeling art. 6:44 BW",
    category: "financieel",
  },
];

const CATEGORY_LABELS: Record<string, string> = {
  incasso: "Incasso",
  financieel: "Financieel",
};

export default function DocumentenPage() {
  const [search, setSearch] = useState("");
  const [tab, setTab] = useState<"templates" | "gegenereerd">("templates");

  const filteredTemplates = TEMPLATES.filter(
    (t) =>
      t.name.toLowerCase().includes(search.toLowerCase()) ||
      t.description.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Documenten</h1>
          <p className="text-sm text-muted-foreground">
            Genereer documenten vanuit templates
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-border">
        <nav className="flex gap-1">
          <button
            onClick={() => setTab("templates")}
            className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-medium transition-colors ${
              tab === "templates"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <FileText className="h-4 w-4" />
            Templates
          </button>
          <button
            onClick={() => setTab("gegenereerd")}
            className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-medium transition-colors ${
              tab === "gegenereerd"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <FileCheck className="h-4 w-4" />
            Gegenereerd
          </button>
        </nav>
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full rounded-lg border border-input bg-background pl-10 pr-4 py-2.5 text-sm placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors"
          placeholder="Zoek documenten..."
        />
      </div>

      {tab === "templates" ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filteredTemplates.map((template) => (
            <div
              key={template.id}
              className="group rounded-xl border border-border bg-card p-5 hover:shadow-md hover:border-primary/20 transition-all"
            >
              <div className="flex items-start justify-between">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                  <File className="h-5 w-5 text-primary" />
                </div>
                <span className="rounded-full bg-muted px-2 py-0.5 text-[10px] font-medium text-muted-foreground uppercase tracking-wider">
                  {CATEGORY_LABELS[template.category] ?? template.category}
                </span>
              </div>
              <h3 className="mt-3 text-sm font-semibold text-foreground">
                {template.name}
              </h3>
              <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
                {template.description}
              </p>
              <button
                className="mt-4 inline-flex w-full items-center justify-center gap-1.5 rounded-lg border border-border px-3 py-2 text-xs font-medium text-foreground hover:bg-muted transition-colors group-hover:border-primary/30 group-hover:text-primary"
                onClick={() =>
                  alert(
                    "Document generatie wordt gekoppeld zodra de backend klaar is. Ga naar een zaak en genereer het document vanuit het zaak-detail."
                  )
                }
              >
                <Plus className="h-3.5 w-3.5" />
                Genereer document
              </button>
            </div>
          ))}
        </div>
      ) : (
        <div className="rounded-xl border border-dashed border-border py-16 text-center">
          <Clock className="mx-auto h-12 w-12 text-muted-foreground/30" />
          <h3 className="mt-4 text-base font-semibold text-foreground">
            Nog geen documenten gegenereerd
          </h3>
          <p className="mt-1 text-sm text-muted-foreground max-w-sm mx-auto">
            Gegenereerde documenten verschijnen hier. Ga naar een zaak om een
            document te genereren vanuit een template.
          </p>
        </div>
      )}
    </div>
  );
}
