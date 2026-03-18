"use client";

import { useCallback, useRef, useState } from "react";
import { FileText, Upload, Loader2, CheckCircle, AlertCircle } from "lucide-react";
import { useParseInvoice, type InvoiceParseResult } from "@/hooks/use-invoice-parser";

type UploadState = "idle" | "uploading" | "success" | "error";

interface InvoiceUploadZoneProps {
  onParsed: (data: InvoiceParseResult, file: File) => void;
}

export function InvoiceUploadZone({ onParsed }: InvoiceUploadZoneProps) {
  const [state, setState] = useState<UploadState>("idle");
  const [filename, setFilename] = useState<string>("");
  const [errorMsg, setErrorMsg] = useState<string>("");
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const parseInvoice = useParseInvoice();

  const handleFile = useCallback(
    async (file: File) => {
      if (file.type !== "application/pdf") {
        setState("error");
        setErrorMsg("Alleen PDF-bestanden zijn toegestaan");
        return;
      }
      if (file.size > 10 * 1024 * 1024) {
        setState("error");
        setErrorMsg("Bestand is te groot (max 10 MB)");
        return;
      }

      setFilename(file.name);
      setState("uploading");
      setErrorMsg("");

      try {
        const result = await parseInvoice.mutateAsync(file);
        setState("success");
        onParsed(result, file);
      } catch (err: any) {
        setState("error");
        setErrorMsg(err.message || "Factuur parsing mislukt");
      }
    },
    [parseInvoice, onParsed]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={handleDrop}
      onClick={() => state !== "uploading" && inputRef.current?.click()}
      className={`relative rounded-xl border-2 border-dashed p-4 text-center transition-all cursor-pointer ${
        dragOver
          ? "border-primary bg-primary/5"
          : state === "success"
          ? "border-green-300 bg-green-50/50 dark:border-green-700 dark:bg-green-950/20"
          : state === "error"
          ? "border-red-300 bg-red-50/50 dark:border-red-700 dark:bg-red-950/20"
          : "border-border hover:border-primary/50 hover:bg-muted/50"
      }`}
    >
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf"
        onChange={handleChange}
        className="hidden"
      />

      {state === "idle" && (
        <div className="flex items-center justify-center gap-3 py-2">
          <div className="rounded-lg bg-primary/10 p-2">
            <Upload className="h-5 w-5 text-primary" />
          </div>
          <div className="text-left">
            <p className="text-sm font-medium text-foreground">
              Upload een factuur om automatisch in te vullen
            </p>
            <p className="text-xs text-muted-foreground">
              Sleep een PDF hierheen of klik om te uploaden (optioneel)
            </p>
          </div>
        </div>
      )}

      {state === "uploading" && (
        <div className="flex items-center justify-center gap-3 py-2">
          <Loader2 className="h-5 w-5 animate-spin text-primary" />
          <div className="text-left">
            <p className="text-sm font-medium text-foreground">
              Factuur wordt geanalyseerd...
            </p>
            <p className="text-xs text-muted-foreground">{filename}</p>
          </div>
        </div>
      )}

      {state === "success" && (
        <div className="flex items-center justify-center gap-3 py-2">
          <CheckCircle className="h-5 w-5 text-green-600" />
          <div className="text-left">
            <p className="text-sm font-medium text-green-700 dark:text-green-400">
              Factuur geanalyseerd — velden ingevuld
            </p>
            <p className="text-xs text-muted-foreground">{filename}</p>
          </div>
        </div>
      )}

      {state === "error" && (
        <div className="flex items-center justify-center gap-3 py-2">
          <AlertCircle className="h-5 w-5 text-red-600" />
          <div className="text-left">
            <p className="text-sm font-medium text-red-700 dark:text-red-400">
              {errorMsg}
            </p>
            <p className="text-xs text-muted-foreground">
              Klik om opnieuw te proberen
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
