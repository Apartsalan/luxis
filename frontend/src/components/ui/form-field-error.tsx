"use client";

import { cn } from "@/lib/utils";

interface FormFieldErrorProps {
  error?: string;
  touched?: boolean;
  className?: string;
  /** Koppel met aria-describedby op het invoerveld */
  id?: string;
}

export function FormFieldError({ error, touched = true, className, id }: FormFieldErrorProps) {
  if (!error || !touched) return null;
  return (
    // role="alert" zodat screenreaders de fout direct voorlezen;
    // text-red-700 i.p.v. text-destructive: 13px-tekst vereist 4.5:1 contrast
    <p id={id} role="alert" className={cn("text-[13px] text-red-700 mt-1", className)}>
      {error}
    </p>
  );
}

/** CSS classes for input with error state */
export function fieldErrorClasses(error?: string, touched?: boolean): string {
  if (!error || !touched) return "";
  return "border-destructive ring-1 ring-destructive/30 focus-visible:ring-destructive/50";
}
