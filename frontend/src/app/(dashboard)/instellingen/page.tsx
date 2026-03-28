"use client";

import { useState } from "react";
import {
  User,
  Users,
  Building2,
  Palette,
  Bell,
  GitBranch,
  Mail,
  Puzzle,
  FileText,
  Cloud,
} from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import { ProfielTab } from "./profiel-tab";
import { KantoorTab } from "./kantoor-tab";
import { ModulesTab } from "./modules-tab";
import { TeamTab } from "./team-tab";
import { WorkflowTab } from "./workflow-tab";
import { EmailTab } from "./email-tab";
import { MeldingenTab } from "./meldingen-tab";
import { SjablonenTab } from "./sjablonen-tab";
import { WeergaveTab } from "./weergave-tab";
import { ExactTab } from "./exact-tab";

const TABS = [
  { id: "profiel", label: "Profiel", icon: User },
  { id: "kantoor", label: "Kantoor", icon: Building2 },
  { id: "modules", label: "Modules", icon: Puzzle },
  { id: "team", label: "Team", icon: Users },
  { id: "workflow", label: "Workflow", icon: GitBranch },
  { id: "email", label: "E-mail", icon: Mail },
  { id: "meldingen", label: "Meldingen", icon: Bell },
  { id: "sjablonen", label: "Sjablonen", icon: FileText },
  { id: "exact", label: "Exact Online", icon: Cloud },
  { id: "weergave", label: "Weergave", icon: Palette },
];

export default function InstellingenPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState("profiel");

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

        {/* Content */}
        <div className="space-y-6">
          {activeTab === "profiel" && <ProfielTab user={user} />}
          {activeTab === "kantoor" && <KantoorTab />}
          {activeTab === "modules" && <ModulesTab />}
          {activeTab === "team" && <TeamTab />}
          {activeTab === "workflow" && <WorkflowTab />}
          {activeTab === "email" && <EmailTab />}
          {activeTab === "meldingen" && <MeldingenTab />}
          {activeTab === "sjablonen" && <SjablonenTab />}
          {activeTab === "exact" && <ExactTab />}
          {activeTab === "weergave" && <WeergaveTab />}
        </div>
      </div>
    </div>
  );
}
