"use client";

import { AlertTriangle, RefreshCw, WifiOff } from "lucide-react";

interface QueryErrorProps {
  message?: string;
  onRetry?: () => void;
}

export function QueryError({ message, onRetry }: QueryErrorProps) {
  const isNetworkError =
    message?.includes("fetch") ||
    message?.includes("network") ||
    message?.includes("Failed to fetch");

  return (
    <div className="flex items-center justify-center py-12">
      <div className="text-center max-w-sm">
        <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-full bg-destructive/10">
          {isNetworkError ? (
            <WifiOff className="h-5 w-5 text-destructive" />
          ) : (
            <AlertTriangle className="h-5 w-5 text-destructive" />
          )}
        </div>
        <p className="mt-3 text-sm font-medium text-foreground">
          {isNetworkError
            ? "Geen verbinding met de server"
            : "Fout bij laden van gegevens"}
        </p>
        <p className="mt-1 text-xs text-muted-foreground">
          {isNetworkError
            ? "Controleer of de backend draait en probeer opnieuw."
            : message || "Probeer het later opnieuw."}
        </p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="mt-4 inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-2 text-xs font-medium hover:bg-muted transition-colors"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Opnieuw proberen
          </button>
        )}
      </div>
    </div>
  );
}
