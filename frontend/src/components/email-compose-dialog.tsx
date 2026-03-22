"use client";

import { useState } from "react";
import { Mail, Paperclip, Send, Loader2, X, Plus, User } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

// ── Types ────────────────────────────────────────────────────────────────────

export interface EmailComposeData {
  recipient_email: string;
  recipient_name?: string | null;
  cc?: string[] | null;
  custom_subject?: string | null;
  custom_body?: string | null;
}

/** A known recipient from the case (client, opposing party, etc.) */
export interface EmailRecipient {
  name: string;
  email: string;
  role: string;
}

// ── Dutch role labels ───────────────────────────────────────────────────────

const ROLE_LABELS: Record<string, string> = {
  client: "Client",
  opposing_party: "Wederpartij",
  advocaat_wederpartij: "Advocaat wederpartij",
  deurwaarder: "Deurwaarder",
  rechtbank: "Rechtbank",
  mediator: "Mediator",
  deskundige: "Deskundige",
  getuige: "Getuige",
  notaris: "Notaris",
  overig: "Overig",
};

function getRoleLabel(role: string): string {
  return ROLE_LABELS[role] ?? role;
}

export interface EmailComposeDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSend: (data: EmailComposeData) => void;
  isSending?: boolean;
  /** Pre-filled recipient email */
  defaultTo?: string;
  /** Pre-filled recipient name */
  defaultToName?: string;
  /** Pre-filled subject */
  defaultSubject?: string;
  /** Pre-filled body */
  defaultBody?: string;
  /** Attachment filename to display */
  attachmentName?: string;
  /** Dialog title override */
  title?: string;
  /** Known recipients from the case for quick-select chips */
  recipients?: EmailRecipient[];
}

// ── Component ────────────────────────────────────────────────────────────────

export function EmailComposeDialog({
  open,
  onOpenChange,
  onSend,
  isSending = false,
  defaultTo = "",
  defaultToName = "",
  defaultSubject = "",
  defaultBody = "",
  attachmentName,
  title = "E-mail versturen",
  recipients,
}: EmailComposeDialogProps) {
  const [to, setTo] = useState(defaultTo);
  const [toName, setToName] = useState(defaultToName);
  const [ccList, setCcList] = useState<string[]>([]);
  const [ccInput, setCcInput] = useState("");
  const [showCc, setShowCc] = useState(false);
  const [subject, setSubject] = useState(defaultSubject);
  const [body, setBody] = useState(defaultBody);
  const [selectedRecipientEmail, setSelectedRecipientEmail] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  // Reset form when dialog opens with new defaults
  const handleOpenChange = (nextOpen: boolean) => {
    if (nextOpen) {
      setTo(defaultTo);
      setToName(defaultToName);
      setCcList([]);
      setCcInput("");
      setShowCc(false);
      setSubject(defaultSubject);
      setBody(defaultBody);
      setSelectedRecipientEmail(null);
      setFieldErrors({});
    }
    onOpenChange(nextOpen);
  };

  const selectRecipient = (recipient: EmailRecipient) => {
    if (selectedRecipientEmail === recipient.email) {
      // Deselect
      setTo("");
      setToName("");
      setSelectedRecipientEmail(null);
    } else {
      setTo(recipient.email);
      setToName(recipient.name);
      setSelectedRecipientEmail(recipient.email);
    }
  };

  const addCc = () => {
    const email = ccInput.trim();
    if (email && !ccList.includes(email)) {
      setCcList([...ccList, email]);
      setCcInput("");
    }
  };

  const removeCc = (email: string) => {
    setCcList(ccList.filter((e) => e !== email));
  };

  const handleCcKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addCc();
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const errors: Record<string, string> = {};
    if (!to.trim()) {
      errors.to = "E-mailadres is verplicht";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(to.trim())) {
      errors.to = "Ongeldig e-mailadres";
    }
    if (!subject.trim()) {
      errors.subject = "Onderwerp is verplicht";
    }
    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      return;
    }

    onSend({
      recipient_email: to.trim(),
      recipient_name: toName.trim() || null,
      cc: ccList.length > 0 ? ccList : null,
      custom_subject: subject.trim() || null,
      custom_body: body.trim() || null,
    });
  };

  const validRecipients = recipients?.filter((r) => r.email) ?? [];

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-[560px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Mail className="h-5 w-5 text-primary" />
            {title}
          </DialogTitle>
          <DialogDescription>
            Vul de e-mail in en klik op versturen
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Recipient quick-select chips */}
          {validRecipients.length > 0 && (
            <div className="space-y-1.5">
              <Label className="text-xs text-muted-foreground">Snelkeuze ontvanger</Label>
              <div className="flex flex-wrap gap-1.5">
                {validRecipients.map((r) => (
                  <button
                    key={r.email}
                    type="button"
                    onClick={() => selectRecipient(r)}
                    className={cn(
                      "inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium transition-colors",
                      "border cursor-pointer",
                      selectedRecipientEmail === r.email
                        ? "bg-primary text-primary-foreground border-primary"
                        : "bg-background text-foreground border-border hover:bg-muted"
                    )}
                  >
                    <User className="h-3 w-3" />
                    <span>{r.name}</span>
                    <span className="text-[10px] opacity-70">
                      {getRoleLabel(r.role)}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Aan */}
          <div className="space-y-1.5">
            <Label htmlFor="email-to">Aan *</Label>
            <div className="flex gap-2">
              <Input
                id="email-to"
                type="email"
                placeholder="email@voorbeeld.nl"
                value={to}
                onChange={(e) => {
                  setTo(e.target.value);
                  if (fieldErrors.to) setFieldErrors((p) => { const n = { ...p }; delete n.to; return n; });
                  // Clear chip selection if user manually types
                  if (selectedRecipientEmail && e.target.value !== selectedRecipientEmail) {
                    setSelectedRecipientEmail(null);
                  }
                }}
                required
                className={cn("flex-1", fieldErrors.to && "border-destructive ring-1 ring-destructive/30")}
              />
              {!showCc && (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowCc(true)}
                  className="text-xs text-muted-foreground"
                >
                  CC
                </Button>
              )}
            </div>
            {fieldErrors.to && (
              <p className="text-[13px] text-destructive">{fieldErrors.to}</p>
            )}
          </div>

          {/* Naam ontvanger */}
          <div className="space-y-1.5">
            <Label htmlFor="email-to-name">Naam ontvanger</Label>
            <Input
              id="email-to-name"
              placeholder="Naam (voor aanhef)"
              value={toName}
              onChange={(e) => setToName(e.target.value)}
            />
          </div>

          {/* CC */}
          {showCc && (
            <div className="space-y-1.5">
              <Label>CC</Label>
              {ccList.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mb-1.5">
                  {ccList.map((email) => (
                    <span
                      key={email}
                      className="inline-flex items-center gap-1 rounded-full bg-muted px-2.5 py-0.5 text-xs font-medium text-foreground"
                    >
                      {email}
                      <button
                        type="button"
                        onClick={() => removeCc(email)}
                        className="rounded-full p-0.5 hover:bg-destructive/10 hover:text-destructive"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </span>
                  ))}
                </div>
              )}
              <div className="flex gap-2">
                <Input
                  type="email"
                  placeholder="cc@voorbeeld.nl"
                  value={ccInput}
                  onChange={(e) => setCcInput(e.target.value)}
                  onKeyDown={handleCcKeyDown}
                  className="flex-1"
                />
                <Button
                  type="button"
                  variant="outline"
                  size="icon"
                  onClick={addCc}
                  disabled={!ccInput.trim()}
                >
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                Druk op Enter of komma om toe te voegen
              </p>
            </div>
          )}

          {/* Onderwerp */}
          <div className="space-y-1.5">
            <Label htmlFor="email-subject">Onderwerp *</Label>
            <Input
              id="email-subject"
              placeholder="Onderwerp van de e-mail"
              value={subject}
              onChange={(e) => {
                setSubject(e.target.value);
                if (fieldErrors.subject) setFieldErrors((p) => { const n = { ...p }; delete n.subject; return n; });
              }}
              className={cn(fieldErrors.subject && "border-destructive ring-1 ring-destructive/30")}
            />
            {fieldErrors.subject && (
              <p className="text-[13px] text-destructive">{fieldErrors.subject}</p>
            )}
          </div>

          {/* Body */}
          <div className="space-y-1.5">
            <Label htmlFor="email-body">Bericht</Label>
            <Textarea
              id="email-body"
              placeholder="Typ hier uw bericht..."
              value={body}
              onChange={(e) => setBody(e.target.value)}
              rows={6}
              className="resize-y"
            />
          </div>

          {/* Bijlage indicator */}
          {attachmentName && (
            <div className="flex items-center gap-2 rounded-lg border border-border bg-muted/50 px-3 py-2">
              <Paperclip className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">
                Bijlage: <span className="font-medium text-foreground">{attachmentName}</span>
              </span>
            </div>
          )}

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => handleOpenChange(false)}
              disabled={isSending}
            >
              Annuleren
            </Button>
            <Button type="submit" disabled={isSending || !to.trim()}>
              {isSending ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Verzenden...
                </>
              ) : (
                <>
                  <Send className="h-4 w-4" />
                  Versturen
                </>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
