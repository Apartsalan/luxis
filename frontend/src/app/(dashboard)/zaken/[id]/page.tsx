"use client";

import { useState, useEffect, useRef } from "react";
import { useConfirm, usePrompt } from "@/components/confirm-dialog";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  Bot,
  Briefcase,
  Check,
  ChevronDown,
  ChevronUp,
  Clock,
  CreditCard,
  Euro,
  File,
  Loader2,
  Mail,
  Workflow,
  X,
  Zap,
} from "lucide-react";
import { toast } from "sonner";
import { useCase, useUpdateCaseStatus, useDeleteCase } from "@/hooks/use-cases";
import {
  getTemplatesForStatus,
  type EmailLogEntry,
} from "@/hooks/use-documents";
import {
  EmailComposeDialog,
  type EmailComposeData,
  type EmailRecipient,
} from "@/components/email-compose-dialog";
import { useModules } from "@/hooks/use-modules";
import { useTimer, useAutoTimerPreference, getTimerSeconds, AUTO_SAVE_MIN_SECONDS } from "@/hooks/use-timer";
import { useBreadcrumbs } from "@/components/layout/breadcrumb-context";
import { useSendViaProvider, type SyncedEmailDetail } from "@/hooks/use-email-sync";
import { buildReplyPrefill, buildForwardPrefill, type ReplyPrefill } from "@/lib/email-reply";
import { useGenerateDraftForCase } from "@/hooks/use-incasso";
import { formatCurrency } from "@/lib/utils";
import { api } from "@/lib/api";
import { STATUS_LABELS } from "./types";

// ── Tab components ───────────────────────────────────────────────────────────
import DossierHeader from "./components/DossierHeader";
import DetailsTab from "./components/DetailsTab";
import TijdregistratieTab from "./components/TijdregistratieTab";
import UrenTab from "./components/UrenTab";
import { VorderingenFinancieelTab, BetalingenDerdengeldenTab, ProvisieSettingsSection } from "./components/incasso";
import { FacturenTab, DocumentenTab } from "./components/DocumentenTab";
import CorrespondentieTab from "./components/CorrespondentieTab";
import ActiviteitenTab from "./components/ActiviteitenTab";
import { StaphistorieTab } from "./components/StaphistorieTab";
import CaseConflictBanner from "./components/CaseConflictBanner";
import BasenetWarningBanner from "./components/BasenetWarningBanner";
import AgendaBlok from "./components/AgendaBlok";
import NoteDialog, { type NoteMode } from "./components/NoteDialog";
import DossierSidebar from "./components/DossierSidebar";
import { ErrorBoundary } from "@/components/error-boundary";
import { CaseActionFeed } from "@/components/case-action-feed/CaseActionFeed";

function TabErrorFallback({ tabName }: { tabName: string }) {
  return (
    <div className="flex items-center justify-center rounded-xl border border-dashed border-destructive/30 bg-destructive/5 py-12">
      <div className="text-center">
        <p className="text-sm font-medium text-destructive">
          Er ging iets mis in het tabblad &quot;{tabName}&quot;
        </p>
        <p className="mt-1 text-xs text-muted-foreground">
          De overige tabbladen werken nog normaal.
        </p>
      </div>
    </div>
  );
}

export default function ZaakDetailPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const id = params.id as string;
  const { data: zaak, isLoading } = useCase(id);
  const updateStatus = useUpdateCaseStatus();
  const deleteCase = useDeleteCase();
  const { confirm, ConfirmDialog: ConfirmDialogEl } = useConfirm();
  const { prompt: promptDialog, PromptDialog: PromptDialogEl } = usePrompt();
  // Set breadcrumb label to case number
  useBreadcrumbs(zaak ? [{ segment: id, label: zaak.case_number }] : []);
  const { hasModule } = useModules();
  const { startTimer, stopTimer, discardTimer, timer } = useTimer();
  const [autoTimerEnabled] = useAutoTimerPreference();
  const tabFromUrl = searchParams.get("tab");
  const [activeTab, setActiveTab] = useState(tabFromUrl || "overzicht");
  // S216 blok 2: notitie/telefoonnotitie openen nu één venster (geen tab-gespring).
  const [noteDialogMode, setNoteDialogMode] = useState<NoteMode | null>(null);
  const autoStartedRef = useRef<string | null>(null);

  // T2: Workflow-suggestie banner state
  const [statusSuggestion, setStatusSuggestion] = useState<{ status: string; templates: string[] } | null>(null);

  // Auto-start timer when opening a case (if enabled)
  useEffect(() => {
    if (!autoTimerEnabled || !zaak) return;

    // Already auto-started for this case in this render cycle
    if (autoStartedRef.current === zaak.id) return;

    // Timer already running for THIS case — do nothing
    if (timer.running && timer.caseId === zaak.id) {
      autoStartedRef.current = zaak.id;
      return;
    }

    // Timer running for ANOTHER case — save/discard + start new
    if (timer.running && timer.caseId !== zaak.id) {
      const prevName = timer.caseName;
      const prevSeconds = getTimerSeconds(timer);
      if (prevSeconds >= AUTO_SAVE_MIN_SECONDS) {
        stopTimer().then(() => {
          const m = Math.max(1, Math.round(prevSeconds / 60));
          const h = Math.floor(m / 60);
          const min = m % 60;
          toast.info(
            `${h}:${String(min).padStart(2, "0")} opgeslagen voor ${prevName}`
          );
        });
      } else {
        discardTimer();
      }
    }

    // Start timer for current case
    const label = `${zaak.case_number}${zaak.client ? ` — ${zaak.client.name}` : ""}`;
    const timeout = timer.running && timer.caseId !== zaak.id ? 300 : 0;
    const t = setTimeout(() => {
      startTimer(zaak.id, label);
      toast.info(`Timer gestart voor ${zaak.case_number}`, { duration: 2000 });
    }, timeout);
    autoStartedRef.current = zaak.id;

    return () => clearTimeout(t);
  }, [zaak?.id, autoTimerEnabled]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleStatusChange = async (newStatus: string) => {
    const note = await promptDialog({ title: "Statuswijziging", description: "Notitie bij statuswijziging (optioneel):", placeholder: "Typ een notitie...", confirmText: "Wijzigen" });
    try {
      await updateStatus.mutateAsync({
        id,
        new_status: newStatus,
        note: note?.trim() || null,
      });
      toast.success(`Status gewijzigd naar ${STATUS_LABELS[newStatus]}`);

      // T2: Toon suggestie-banner als er aanbevolen templates zijn
      const nextTemplates = getTemplatesForStatus(newStatus, zaak?.debtor_type);
      if (nextTemplates.recommended.length > 0) {
        setStatusSuggestion({ status: newStatus, templates: nextTemplates.recommended });
        setTimeout(() => setStatusSuggestion(null), 30000);
      }
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Statuswijziging mislukt");
    }
  };

  const handleDelete = async () => {
    if (!await confirm({ title: "Dossier verwijderen", description: "Weet je zeker dat je dit dossier wilt verwijderen?", variant: "destructive", confirmText: "Verwijderen" })) return;
    try {
      await deleteCase.mutateAsync(id);
      toast.success("Dossier verwijderd");
      router.push("/zaken");
    } catch {
      toast.error("Kon het dossier niet verwijderen");
    }
  };

  // ── Freestanding email compose (F11) ────────────────────────────────────
  const [caseEmailOpen, setCaseEmailOpen] = useState(false);
  const [replyPrefill, setReplyPrefill] = useState<ReplyPrefill | null>(null);
  const [isSendingEmail, setIsSendingEmail] = useState(false);
  const sendViaProvider = useSendViaProvider(id);

  const handleReplyForward = (email: SyncedEmailDetail, mode: "reply" | "forward") => {
    setReplyPrefill(mode === "reply" ? buildReplyPrefill(email) : buildForwardPrefill(email));
    setCaseEmailOpen(true);
  };

  // ── AI-draft auto-open via ?draft=X query (sessie 133) ─────────────────
  const draftIdFromQuery = searchParams?.get("draft") ?? null;
  const [activeDraftId, setActiveDraftId] = useState<string | null>(null);
  const [draftSubject, setDraftSubject] = useState<string>("");
  const [draftBody, setDraftBody] = useState<string>("");
  const [draftBodyHtml, setDraftBodyHtml] = useState<string>("");

  useEffect(() => {
    if (!draftIdFromQuery) return;
    let cancelled = false;
    (async () => {
      try {
        let draftId = draftIdFromQuery;
        // "latest"-sentinel: open het nieuwste nog niet-verzonden concept van dit
        // dossier. Gebruikt door de CaseActionFeed "Openen"-knop — de
        // ai_draft_ready-notificatie draagt zelf geen concept-id, dus zoeken we
        // het hier op via de dossier-conceptenlijst (nieuwste eerst).
        if (draftIdFromQuery === "latest") {
          const listRes = await api(`/api/ai-agent/drafts/case/${id}`);
          if (!listRes.ok) throw new Error("Concept niet gevonden");
          const drafts = await listRes.json();
          const openable = (Array.isArray(drafts) ? drafts : []).find(
            (dr: { status?: string; sent_at?: string | null }) =>
              dr.status !== "sent" && !dr.sent_at
          );
          if (!openable) throw new Error("Geen openstaand concept voor dit dossier");
          draftId = openable.id;
        }
        const res = await api(`/api/ai-agent/drafts/${draftId}`);
        if (!res.ok) throw new Error("Concept niet gevonden");
        const d = await res.json();
        if (cancelled) return;
        setActiveDraftId(draftId);
        setDraftSubject(d.subject || "");
        setDraftBody(d.body || "");
        setDraftBodyHtml(d.body_html || "");
        setCaseEmailOpen(true);
      } catch (e) {
        toast.error(e instanceof Error ? e.message : "Kon AI-concept niet laden");
      }
    })();
    return () => { cancelled = true; };
  }, [draftIdFromQuery, id]);

  // BUG-73 fix (sessie 134): directe trigger ipv router.replace(?draft=X)
  // useSearchParams updatet niet altijd betrouwbaar na router.replace in Next.js 15,
  // dus we openen de dialog direct via state.
  const generateDraft = useGenerateDraftForCase();
  const openDraftDialog = async (draftId: string) => {
    try {
      const res = await api(`/api/ai-agent/drafts/${draftId}`);
      if (!res.ok) throw new Error("Concept niet gevonden");
      const d = await res.json();
      setActiveDraftId(draftId);
      setDraftSubject(d.subject || "");
      setDraftBody(d.body || "");
      setDraftBodyHtml(d.body_html || "");
      setCaseEmailOpen(true);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Concept niet gevonden";
      toast.error(msg);
    }
  };
  // Open het nieuwste nog niet-verzonden concept van dit dossier (gebruikt door
  // de "Concept openen"-knop op de dossier-taken-tab). Directe dialoog-opening
  // i.p.v. een ?draft=latest-navigatie → betrouwbaar binnen dezelfde pagina.
  const openLatestDraft = async () => {
    try {
      const listRes = await api(`/api/ai-agent/drafts/case/${id}`);
      if (!listRes.ok) throw new Error("Concept niet gevonden");
      const drafts = await listRes.json();
      const openable = (Array.isArray(drafts) ? drafts : []).find(
        (dr: { status?: string; sent_at?: string | null }) =>
          dr.status !== "sent" && !dr.sent_at
      );
      if (!openable) {
        toast.error("Geen openstaand concept voor dit dossier");
        return;
      }
      await openDraftDialog(openable.id);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Kon AI-concept niet laden");
    }
  };
  const handleGenerateDraft = async () => {
    try {
      const r = await generateDraft.mutateAsync(id);
      await openDraftDialog(r.draft_id);
      toast.success("Concept klaar — opent voor review");
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Fout bij genereren concept";
      toast.error(msg);
    }
  };

  const handleDraftSendComplete = async () => {
    if (!activeDraftId) return;
    try {
      const res = await api(`/api/incasso/cases/${id}/advance-after-send`, {
        method: "POST",
        body: JSON.stringify({ draft_id: activeDraftId }),
      });
      if (res.ok) {
        const r = await res.json();
        if (r.advanced) {
          toast.success(`Dossier naar volgende stap: ${r.to_step_name}`);
        }
      }
    } catch {
      // Silent — email was wel verzonden
    } finally {
      setActiveDraftId(null);
      setDraftSubject("");
      setDraftBody("");
      setDraftBodyHtml("");
      // Verwijder ?draft=X uit URL
      router.replace(`/zaken/${id}`);
    }
  };

  function buildDossierRecipients(z: typeof zaak): EmailRecipient[] {
    if (!z) return [];
    const recipients: EmailRecipient[] = [];
    if (z.client?.email) {
      recipients.push({ name: z.client.name, email: z.client.email, role: "client" });
    }
    if (z.opposing_party?.email) {
      recipients.push({ name: z.opposing_party.name, email: z.opposing_party.email, role: "opposing_party" });
    }
    if (z.parties) {
      for (const p of z.parties) {
        if (p.contact?.email && !recipients.some((r) => r.email === p.contact.email)) {
          recipients.push({ name: p.contact.name, email: p.contact.email, role: p.role });
        }
      }
    }
    return recipients;
  }

  const handleOpenInOutlook = async (data: EmailComposeData) => {
    const subject = data.custom_subject || `${zaak?.case_number || ""}`;
    const body = data.custom_body || "";

    const postEml = (complianceOverride: boolean) =>
      api(`/api/email/compose/cases/${id}`, {
        method: "POST",
        body: JSON.stringify({
          recipient_email: data.recipient_email,
          recipient_name: data.recipient_name,
          cc: data.cc,
          bcc: data.bcc,
          subject,
          body,
          body_html: data.body_html,
          case_file_ids: data.case_file_ids,
          inline_attachments: data.inline_attachments,
          template_type: data.template_type,
          compliance_override: complianceOverride,
        }),
      });

    try {
      let res = await postEml(false);

      // S224 — 14-dagenbrief-gate óók op de Outlook-route (.eml): zelfde
      // 'toch doorgaan'-bevestiging als bij direct versturen. Het systeem legt
      // bij doorzetten zelf een spoor op het dossier vast.
      if (res.status === 422) {
        const gateErr = await res.clone().json().catch(() => null);
        const gateDetail = gateErr?.detail;
        if (gateDetail && typeof gateDetail === "object" && gateDetail.code === "DAGENBRIEF_GATE") {
          const ok = await confirm({
            title: "Weet je het zeker?",
            description:
              "Voor deze consument is nog geen verstreken 14-dagenbrief geregistreerd. " +
              "Zonder die brief zijn de incassokosten bij een consument mogelijk niet " +
              "opeisbaar (art. 6:96 lid 6 BW). Heeft de consument de 14-dagenbrief al " +
              "ontvangen? Kies 'Toch openen' om de e-mail alsnog in Outlook te openen.",
            confirmText: "Toch openen",
            cancelText: "Annuleren",
            variant: "destructive",
          });
          if (!ok) return;
          res = await postEml(true);
        }
      }

      if (!res.ok) {
        const err = await res.json().catch(() => null);
        const detail = err?.detail;
        const msg = typeof detail === "string"
          ? detail
          : detail && typeof detail === "object" && typeof detail.message === "string"
            ? detail.message
            : "E-mail opstellen mislukt";
        throw new Error(msg);
      }

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `email-${zaak?.case_number || "concept"}.eml`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      toast.success("E-mail geopend in Outlook");
      setCaseEmailOpen(false);
      if (activeDraftId) await handleDraftSendComplete();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "E-mail opstellen mislukt");
    }
  };

  const postCompose = (data: EmailComposeData, complianceOverride: boolean) => {
    const subject = data.custom_subject || `${zaak?.case_number || ""}`;
    const body = data.custom_body || "";
    return api("/api/email/compose/send", {
      method: "POST",
      body: JSON.stringify({
        to: [data.recipient_email],
        subject,
        body_html: data.body_html || `<p>${body.replace(/\n/g, "<br>")}</p>`,
        cc: data.cc,
        bcc: data.bcc,
        case_id: data.case_id ?? id,
        case_file_ids: data.case_file_ids,
        inline_attachments: data.inline_attachments,
        reply_to_message_id: data.reply_to_message_id,
        references_root: data.references_root,
        forward_from_email_id: data.forward_from_email_id,
        // S212-review: sjabloontype mee zodat de backend het renteoverzicht
        // aanhangt bij 14-dagenbrief/eerste sommatie (zelfde als het .eml-pad).
        template_type: data.template_type,
        // AI-concept is al opgemaakt (huisstijl); niet opnieuw aankleden.
        // Alleen overslaan als er ook écht opgemaakte HTML is: mislukt de
        // huisstijl-wrap van een concept (body_html leeg), dan sturen we de
        // kale tekst en moet de achterkant hem wél aankleden.
        already_branded:
          data.already_branded || (!!activeDraftId && !!data.body_html),
        // S205: alleen true na de 'toch versturen'-bevestiging hieronder.
        compliance_override: complianceOverride,
      }),
    });
  };

  const handleDirectSend = async (data: EmailComposeData) => {
    setIsSendingEmail(true);
    try {
      let res = await postCompose(data, false);

      // S205 — 14-dagenbrief-blokkade: geen harde fout, maar een 'toch versturen'-
      // bevestiging. De backend stuurt code DAGENBRIEF_GATE (422). Simpel gehouden
      // (bewuste keuze Arsalan): één ja/nee, géén verplicht redenveld; het systeem
      // legt zelf een spoor op het dossier vast bij 'Toch versturen'.
      // ⚠️ Waarschuwingstekst = concept — juridisch nog langs Lisanne vóór livegang.
      if (res.status === 422) {
        const gateErr = await res.clone().json().catch(() => null);
        const gateDetail = gateErr?.detail;
        if (gateDetail && typeof gateDetail === "object" && gateDetail.code === "DAGENBRIEF_GATE") {
          const ok = await confirm({
            title: "Weet je het zeker?",
            description:
              "Voor deze consument is nog geen verstreken 14-dagenbrief geregistreerd. " +
              "Zonder die brief zijn de incassokosten bij een consument mogelijk niet " +
              "opeisbaar (art. 6:96 lid 6 BW). Heeft de consument de 14-dagenbrief al " +
              "ontvangen? Kies 'Toch versturen' om de sommatie alsnog te versturen.",
            confirmText: "Toch versturen",
            cancelText: "Annuleren",
            variant: "destructive",
          });
          if (!ok) return;
          res = await postCompose(data, true);
        }
      }

      if (!res.ok) {
        const err = await res.json().catch(() => null);
        const detail = err?.detail;
        const msg = typeof detail === "string"
          ? detail
          : detail && typeof detail === "object" && typeof detail.message === "string"
            ? detail.message
            : Array.isArray(detail)
              ? detail.map((d: { msg?: string }) => d.msg ?? JSON.stringify(d)).join(", ")
              : "E-mail verzenden mislukt";
        throw new Error(msg);
      }

      toast.success("E-mail verzonden");
      setCaseEmailOpen(false);
      if (activeDraftId) await handleDraftSendComplete();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "E-mail verzenden mislukt");
    } finally {
      setIsSendingEmail(false);
    }
  };

  // G5: Keyboard shortcuts (Linear-style)
  // Tab IDs for numeric shortcuts — order matches the tab bar
  const isIncasso = hasModule("incasso") && zaak?.case_type === "incasso";
  // S216: teruggebracht van 11/8 naar 7/6 tabbladen. Financieel bundelt
  // vorderingen+betalingen+regeling+derdengelden (alleen incasso); Tijdlijn is
  // het oude Activiteiten; Taken/Partijen zijn naar Overzicht verhuisd.
  const tabIds = [
    "overzicht",
    ...(isIncasso ? ["financieel"] : []),
    "facturen", "documenten", "correspondentie", "uren", "tijdlijn",
  ];

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't trigger when typing in inputs/textareas or when modifier keys are held
      const tag = (e.target as HTMLElement).tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || (e.target as HTMLElement).isContentEditable) return;
      if (e.ctrlKey || e.metaKey || e.altKey) return;

      switch (e.key.toLowerCase()) {
        case "t":
          e.preventDefault();
          if (timer.running && timer.caseId === id) {
            stopTimer();
            toast.info("Timer gestopt");
          } else if (zaak) {
            const label = `${zaak.case_number}${zaak.client ? ` — ${zaak.client.name}` : ""}`;
            startTimer(zaak.id, label);
            toast.info("Timer gestart");
          }
          break;
        case "n":
          e.preventDefault();
          setNoteDialogMode("note");
          break;
        case "d":
          e.preventDefault();
          setActiveTab("documenten");
          break;
        case "e":
          e.preventDefault();
          setCaseEmailOpen(true);
          break;
        case "f":
          e.preventDefault();
          setActiveTab("facturen");
          break;
        default:
          // 1-9: switch tabs
          if (e.key >= "1" && e.key <= "9") {
            const idx = parseInt(e.key) - 1;
            if (idx < tabIds.length) {
              e.preventDefault();
              setActiveTab(tabIds[idx]);
            }
          }
          break;
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [timer.running, timer.caseId, id, zaak, tabIds.length]); // eslint-disable-line react-hooks/exhaustive-deps

  if (isLoading) {
    return (
      <div className="space-y-6 animate-fade-in">
        <div className="h-8 w-48 rounded-md skeleton" />
        <div className="h-14 rounded-xl skeleton" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-24 rounded-xl skeleton" />
          ))}
        </div>
        <div className="h-10 rounded-lg skeleton" />
        <div className="h-64 rounded-xl skeleton" />
      </div>
    );
  }

  if (!zaak) {
    return (
      <div className="py-20 text-center">
        <Briefcase className="mx-auto h-12 w-12 text-muted-foreground/30" />
        <p className="mt-4 text-base font-medium text-foreground">
          Dossier niet gevonden
        </p>
        <Link
          href="/zaken"
          className="mt-2 inline-block text-sm text-primary hover:underline"
        >
          ← Terug naar dossiers
        </Link>
      </div>
    );
  }

  const tabs = [
    { id: "overzicht", label: "Overzicht", icon: Briefcase },
    ...(isIncasso ? [{ id: "financieel", label: "Financieel", icon: Euro }] : []),
    { id: "facturen", label: "Facturen", icon: CreditCard },
    { id: "documenten", label: "Documenten", icon: File },
    { id: "correspondentie", label: "Correspondentie", icon: Mail },
    { id: "uren", label: "Uren", icon: Clock },
    { id: "tijdlijn", label: "Tijdlijn", icon: Workflow },
  ];

  // S216: oude tab-ids (uit deep-links, notificaties, de actiefeed en externe
  // pagina's als /derdengelden en het dashboard) vertalen naar de nieuwe indeling
  // zodat geen enkele bestaande ?tab=-link stukgaat.
  const TAB_REDIRECTS: Record<string, string> = {
    taken: "overzicht",
    partijen: "overzicht",
    vorderingen: "financieel",
    betalingen: "financieel",
    staphistorie: "tijdlijn",
    activiteiten: "tijdlijn",
  };
  const mappedTab = TAB_REDIRECTS[activeTab] ?? activeTab;

  // CONN-6: een ?tab= deep-link kan een tab noemen die op dít dossier niet
  // bestaat (bv. ?tab=financieel op een niet-incasso dossier). Onbekende/
  // ontoegestane tab → val terug op overzicht, anders blijft het paneel leeg.
  const safeTab = tabs.some((t) => t.id === mappedTab) ? mappedTab : "overzicht";

  return (
    <div className="space-y-6 animate-fade-in">
      {ConfirmDialogEl}
      {PromptDialogEl}
      <DossierHeader
        zaak={zaak}
        isIncasso={isIncasso}
        activeTab={safeTab}
        setActiveTab={setActiveTab}
        handleStatusChange={handleStatusChange}
        handleDelete={handleDelete}
        updateStatusPending={updateStatus.isPending}
        statusSuggestion={statusSuggestion}
        setStatusSuggestion={setStatusSuggestion}
        timer={timer}
        startTimer={startTimer}
        setCaseEmailOpen={setCaseEmailOpen}
        onOpenNote={(mode) => setNoteDialogMode(mode)}
        onGenerateDraft={handleGenerateDraft}
        isGeneratingDraft={generateDraft.isPending}
      />

      {/* Sessie 134: legacy AI-suggestie + Followup banners verwijderd — pipeline
          /taken is nu enige bron van waarheid. Zie git history voor oude UI. */}

      {/* Main content + sidebar */}
      <div className="flex gap-6">
        <div className="min-w-0 flex-1">
          {/* Tabs — sticky under app header (UX-6: scroll indicators, UX-7: sticky) */}
          <div className="sticky top-14 z-30 bg-background -mx-4 sm:-mx-6 px-4 sm:px-6">
            <div className="relative">
              <div className="border-b border-border overflow-x-auto">
                <nav className="flex gap-0.5 min-w-max" role="tablist" aria-label="Dossier-tabbladen">
                  {tabs.map((tab) => (
                    <button
                      key={tab.id}
                      role="tab"
                      aria-selected={safeTab === tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`flex items-center gap-2 border-b-2 px-4 py-3 text-sm font-medium transition-colors whitespace-nowrap ${
                        safeTab === tab.id
                          ? "border-primary text-primary"
                          : "border-transparent text-muted-foreground hover:text-foreground hover:border-border"
                      }`}
                    >
                      <tab.icon className="h-4 w-4" />
                      {tab.label}
                    </button>
                  ))}
                </nav>
              </div>
            </div>
          </div>

          {/* Tab content — each tab wrapped in ErrorBoundary (UX-19) */}
          <div className="mt-6">
            {safeTab === "overzicht" && (
              <ErrorBoundary key="overzicht" fallback={<TabErrorFallback tabName="Overzicht" />}>
                <div className="space-y-6">
                  <BasenetWarningBanner zaak={zaak} />
                  <CaseConflictBanner zaak={zaak} />
                  <CaseActionFeed caseId={id} onNavigate={setActiveTab} />
                  <AgendaBlok caseId={id} />
                  {/* S216: Taken-tabblad verhuisd naar een blok op Overzicht —
                      volledige functionaliteit (toevoegen/afronden/overslaan +
                      "Concept openen"). De aparte /taken-pagina blijft bestaan. */}
                  <TijdregistratieTab caseId={id} onOpenDraft={openLatestDraft} />
                  <DetailsTab zaak={zaak} />
                </div>
              </ErrorBoundary>
            )}
            {isIncasso && safeTab === "financieel" && (
              <ErrorBoundary key="financieel" fallback={<TabErrorFallback tabName="Financieel" />}>
                {/* S216: Vorderingen + Betalingen + Regeling + Derdengelden gebundeld. */}
                <div className="space-y-8">
                  <VorderingenFinancieelTab caseId={id} />
                  <div className="border-t border-border" />
                  <BetalingenDerdengeldenTab caseId={id} />
                </div>
              </ErrorBoundary>
            )}
            {safeTab === "uren" && (
              <ErrorBoundary key="uren" fallback={<TabErrorFallback tabName="Uren" />}>
                <UrenTab caseId={id} />
              </ErrorBoundary>
            )}
            {safeTab === "facturen" && (
              <ErrorBoundary key="facturen" fallback={<TabErrorFallback tabName="Facturen" />}>
                <div className="space-y-8">
                  <FacturenTab caseId={id} clientId={zaak?.client?.id} />
                  {isIncasso && (
                    <>
                      <div className="border-t border-border" />
                      {/* S216: provisie-afspraak verhuisd van Vorderingen naar hier
                          (hoort bij cliëntfacturatie). */}
                      <ProvisieSettingsSection caseId={id} />
                    </>
                  )}
                </div>
              </ErrorBoundary>
            )}
            {safeTab === "documenten" && (
              <ErrorBoundary key="documenten" fallback={<TabErrorFallback tabName="Documenten" />}>
                <DocumentenTab caseId={id} caseNumber={zaak?.case_number} caseStatus={zaak?.status} debtorType={zaak?.debtor_type} opposingPartyName={zaak?.opposing_party?.name} clientName={zaak?.client?.name} />
              </ErrorBoundary>
            )}
            {safeTab === "correspondentie" && (
              <ErrorBoundary key="correspondentie" fallback={<TabErrorFallback tabName="Correspondentie" />}>
                <CorrespondentieTab caseId={id} onCompose={() => setCaseEmailOpen(true)} onReply={handleReplyForward} />
              </ErrorBoundary>
            )}
            {safeTab === "tijdlijn" && (
              <ErrorBoundary key="tijdlijn" fallback={<TabErrorFallback tabName="Tijdlijn" />}>
                <div className="space-y-6">
                  <ActiviteitenTab zaak={zaak} />
                  {isIncasso && (
                    <details className="rounded-xl border border-border bg-card">
                      <summary className="cursor-pointer px-5 py-4 text-sm font-semibold text-card-foreground select-none">
                        Stap-historie
                      </summary>
                      <div className="px-5 pb-5">
                        <StaphistorieTab caseId={id} />
                      </div>
                    </details>
                  )}
                </div>
              </ErrorBoundary>
            )}
          </div>
        </div>

        {/* G14: Properties sidebar */}
        <DossierSidebar zaak={zaak} isIncasso={isIncasso} />
      </div>

      {/* Freestanding email compose dialog (F11) */}
      <EmailComposeDialog
        open={caseEmailOpen}
        onOpenChange={(open) => {
          setCaseEmailOpen(open);
          if (!open) setReplyPrefill(null);
          if (!open && activeDraftId) {
            setActiveDraftId(null);
            setDraftSubject("");
            setDraftBody("");
            setDraftBodyHtml("");
            router.replace(`/zaken/${id}`);
          }
        }}
        onSend={handleOpenInOutlook}
        onSendDirect={handleDirectSend}
        isSending={isSendingEmail}
        title={
          replyPrefill
            ? replyPrefill.replyToMessageId ? "Beantwoorden" : "Doorsturen"
            : activeDraftId ? "AI-concept reviewen & versturen" : "E-mail opstellen"
        }
        defaultTo={replyPrefill?.to ?? ""}
        defaultToName={replyPrefill?.toName ?? ""}
        defaultSubject={
          replyPrefill
            ? replyPrefill.subject
            : activeDraftId
              ? draftSubject
              : zaak ? `${zaak.case_number}${zaak.client ? ` — ${zaak.client.name}` : ""}` : ""
        }
        defaultBody={!replyPrefill && activeDraftId ? draftBody : ""}
        defaultBodyHtml={replyPrefill ? replyPrefill.bodyHtml : activeDraftId ? draftBodyHtml : ""}
        replyToMessageId={replyPrefill?.replyToMessageId ?? null}
        referencesRoot={replyPrefill?.referencesRoot ?? null}
        forwardFromEmailId={replyPrefill?.forwardFromEmailId ?? null}
        recipients={zaak ? buildDossierRecipients(zaak) : []}
        caseId={id}
      />

      {/* S216 blok 2: notitie/telefoonnotitie-venster (kop-knoppen + sneltoets "n") */}
      <NoteDialog
        caseId={id}
        open={noteDialogMode !== null}
        mode={noteDialogMode ?? "note"}
        onOpenChange={(open) => { if (!open) setNoteDialogMode(null); }}
      />
    </div>
  );
}
