"use client";

import { cn } from "@/lib/utils";

interface FormFieldErrorProps {
  error?: string;
  touched?: boolean;
  className?: string;
}

export function FormFieldError({ error, touched = true, className }: FormFieldErrorProps) {
  if (!error || !touched) return null;
  return (
    <p className={cn("text-[13px] text-destructive mt-1", className)}>
      {error}
    </p>
  );
}

/** CSS classes for input with error state */
export function fieldErrorClasses(error?: string, touched?: boolean): string {
  if (!error || !touched) return "";
  return "border-destructive ring-1 ring-destructive/30 focus-visible:ring-destructive/50";
}
