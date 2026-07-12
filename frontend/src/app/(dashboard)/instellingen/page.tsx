"use client";

import { useState } from "react";
import {
  User,
  Users,
  Building2,
  GitBranch,
  Mail,
  Puzzle,
  FileText,
  Cloud,
  Package,
  Sparkles,
} from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import { ProfielTab } from "./profiel-tab";
import { KantoorTab } from "./kantoor-tab";
import { ModulesTab } from "./modules-tab";
import { TeamTab } from "./team-tab";
import { WorkflowTab } from "./workflow-tab";
import { EmailTab } from "./email-tab";
import { SjablonenTab } from "./sjablonen-tab";
import { ExactTab } from "./exact-tab";
import { ProductenTab } from "./producten-tab";
import { AILerenTab } from "./ai-leren-tab";

const TABS = [
  { id: "profiel", label: "Profiel", icon: User },
  { id: "kantoor", label: "Kantoor", icon: Building2 },
  { id: "modules", label: "Modules", icon: Puzzle },
  { id: "team", label: "Team", icon: Users },
  { id: "workflow", label: "Workflow", icon: GitBranch },
  { id: "ai-leren", label: "Slim leren", icon: Sparkles },
  { id: "email", label: "E-mail", icon: Mail },
  { id: "sjablonen", label: "Sjablonen", icon: FileText },
  { id: "producten", label: "Producten", icon: Package },
  { id: "exact", label: "Exact Online", icon: Cloud },
];

export default function InstellingenPage() {
  const { user } = useAuth();
  // ponytail: query-param direct lezen bij mount — vermijdt useSearchParams + Suspense-eis.
  const [activeTab, setActiveTab] = useState(() => {
    if (typeof window === "undefined") return "profiel";
    const tab = new URLSearchParams(window.location.search).get("tab");
    return tab && TABS.some((t) => t.id === tab) ? tab : "profiel";
  });

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Instellingen</h1>
        <p className="text-sm text-muted-foreground">
          Beheer je profiel en kantoorinstellingen
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[220px,1fr]">
        {/* Sidebar navigation */}
        <nav className="space-y-0.5">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              }`}
            >
              <tab.icon className="h-4 w-4" />
              {tab.label}
            </button>
          ))}
        </nav>

        {/* Content — min-w-0: grid-cel mag krimpen, anders duwt nowrap-tekst (bijv. de
            Slim-leren-voorbeeldregels) de 1fr-kolom open tot ver buiten het scherm */}
        <div className="min-w-0 space-y-6">
          {activeTab === "profiel" && <ProfielTab user={user} />}
          {activeTab === "kantoor" && <KantoorTab />}
          {activeTab === "modules" && <ModulesTab />}
          {activeTab === "team" && <TeamTab />}
          {activeTab === "workflow" && <WorkflowTab />}
          {activeTab === "ai-leren" && <AILerenTab />}
          {activeTab === "email" && <EmailTab />}
          {activeTab === "sjablonen" && <SjablonenTab />}
          {activeTab === "producten" && <ProductenTab />}
          {activeTab === "exact" && <ExactTab />}
        </div>
      </div>
    </div>
  );
}
