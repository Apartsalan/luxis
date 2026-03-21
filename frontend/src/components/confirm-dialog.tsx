"use client";

import { useState, useCallback, useRef } from "react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

// ── ConfirmDialog ────────────────────────────────────────────────────────────

interface ConfirmDialogProps {
  open: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  title: string;
  description?: string;
  confirmText?: string;
  cancelText?: string;
  variant?: "default" | "destructive";
}

export function ConfirmDialog({
  open,
  onConfirm,
  onCancel,
  title,
  description,
  confirmText = "Bevestigen",
  cancelText = "Annuleren",
  variant = "default",
}: ConfirmDialogProps) {
  return (
    <AlertDialog open={open} onOpenChange={(o) => !o && onCancel()}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{title}</AlertDialogTitle>
          {description && (
            <AlertDialogDescription>{description}</AlertDialogDescription>
          )}
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel onClick={onCancel}>{cancelText}</AlertDialogCancel>
          <AlertDialogAction
            onClick={onConfirm}
            className={
              variant === "destructive"
                ? "bg-destructive text-destructive-foreground hover:bg-destructive/90"
                : undefined
            }
          >
            {confirmText}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}

// ── PromptDialog (with textarea input) ───────────────────────────────────────

interface PromptDialogProps {
  open: boolean;
  onConfirm: (value: string) => void;
  onCancel: () => void;
  title: string;
  description?: string;
  confirmText?: string;
  cancelText?: string;
  placeholder?: string;
  defaultValue?: string;
}

export function PromptDialog({
  open,
  onConfirm,
  onCancel,
  title,
  description,
  confirmText = "Bevestigen",
  cancelText = "Annuleren",
  placeholder,
  defaultValue = "",
}: PromptDialogProps) {
  const [value, setValue] = useState(defaultValue);

  return (
    <AlertDialog open={open} onOpenChange={(o) => { if (!o) { onCancel(); setValue(defaultValue); } }}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{title}</AlertDialogTitle>
          {description && (
            <AlertDialogDescription>{description}</AlertDialogDescription>
          )}
        </AlertDialogHeader>
        <textarea
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder={placeholder}
          rows={3}
          className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors resize-none"
          autoFocus
        />
        <AlertDialogFooter>
          <AlertDialogCancel onClick={() => { onCancel(); setValue(defaultValue); }}>
            {cancelText}
          </AlertDialogCancel>
          <AlertDialogAction onClick={() => { onConfirm(value); setValue(defaultValue); }}>
            {confirmText}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}

// ── useConfirm hook — simplifies replacing confirm() calls ───────────────────

type ConfirmConfig = {
  title: string;
  description?: string;
  confirmText?: string;
  cancelText?: string;
  variant?: "default" | "destructive";
};

type ConfirmState = ConfirmConfig & { open: boolean };

export function useConfirm() {
  const [state, setState] = useState<ConfirmState>({
    open: false,
    title: "",
  });
  const resolveRef = useRef<((value: boolean) => void) | null>(null);

  const confirm = useCallback((config: ConfirmConfig): Promise<boolean> => {
    return new Promise((resolve) => {
      resolveRef.current = resolve;
      setState({ ...config, open: true });
    });
  }, []);

  const handleConfirm = useCallback(() => {
    setState((s) => ({ ...s, open: false }));
    resolveRef.current?.(true);
    resolveRef.current = null;
  }, []);

  const handleCancel = useCallback(() => {
    setState((s) => ({ ...s, open: false }));
    resolveRef.current?.(false);
    resolveRef.current = null;
  }, []);

  const ConfirmDialogElement = (
    <ConfirmDialog
      open={state.open}
      onConfirm={handleConfirm}
      onCancel={handleCancel}
      title={state.title}
      description={state.description}
      confirmText={state.confirmText}
      cancelText={state.cancelText}
      variant={state.variant}
    />
  );

  return { confirm, ConfirmDialog: ConfirmDialogElement };
}

// ── usePrompt hook — simplifies replacing prompt() calls ─────────────────────

type PromptConfig = {
  title: string;
  description?: string;
  confirmText?: string;
  cancelText?: string;
  placeholder?: string;
  defaultValue?: string;
};

type PromptState = PromptConfig & { open: boolean };

export function usePrompt() {
  const [state, setState] = useState<PromptState>({
    open: false,
    title: "",
  });
  const resolveRef = useRef<((value: string | null) => void) | null>(null);

  const prompt = useCallback((config: PromptConfig): Promise<string | null> => {
    return new Promise((resolve) => {
      resolveRef.current = resolve;
      setState({ ...config, open: true });
    });
  }, []);

  const handleConfirm = useCallback((value: string) => {
    setState((s) => ({ ...s, open: false }));
    resolveRef.current?.(value);
    resolveRef.current = null;
  }, []);

  const handleCancel = useCallback(() => {
    setState((s) => ({ ...s, open: false }));
    resolveRef.current?.(null);
    resolveRef.current = null;
  }, []);

  const PromptDialogElement = (
    <PromptDialog
      open={state.open}
      onConfirm={handleConfirm}
      onCancel={handleCancel}
      title={state.title}
      description={state.description}
      confirmText={state.confirmText}
      cancelText={state.cancelText}
      placeholder={state.placeholder}
      defaultValue={state.defaultValue}
    />
  );

  return { prompt, PromptDialog: PromptDialogElement };
}
