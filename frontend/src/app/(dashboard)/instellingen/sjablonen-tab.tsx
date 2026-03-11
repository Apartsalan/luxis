"use client";

import { useState } from "react";
import { Save, Loader2, FileText, Download, Upload, Trash2, Pencil, Lock, X } from "lucide-react";
import { toast } from "sonner";
import {
  useManagedTemplates,
  useUploadTemplate,
  useUpdateTemplate,
  useDeleteTemplate,
  useReplaceTemplateFile,
  downloadTemplate,
  formatFileSize,
  getTemplateKeyLabel,
  TEMPLATE_KEY_LABELS,
  type ManagedTemplate,
} from "@/hooks/use-managed-templates";

export function SjablonenTab() {
  const { data: templates, isLoading } = useManagedTemplates();
  const uploadTemplate = useUploadTemplate();
  const updateTemplate = useUpdateTemplate();
  const deleteTemplate = useDeleteTemplate();
  const replaceFile = useReplaceTemplateFile();

  const [showUpload, setShowUpload] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [editKey, setEditKey] = useState("");

  // Upload form state
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadName, setUploadName] = useState("");
  const [uploadKey, setUploadKey] = useState("herinnering");
  const [uploadDesc, setUploadDesc] = useState("");

  const handleUpload = () => {
    if (!uploadFile || !uploadName || !uploadKey) return;
    uploadTemplate.mutate(
      {
        file: uploadFile,
        name: uploadName,
        template_key: uploadKey,
        description: uploadDesc || undefined,
      },
      {
        onSuccess: () => {
          setShowUpload(false);
          setUploadFile(null);
          setUploadName("");
          setUploadKey("herinnering");
          setUploadDesc("");
        },
      }
    );
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file && file.name.endsWith(".docx")) {
      setUploadFile(file);
      if (!uploadName) setUploadName(file.name.replace(".docx", ""));
      setShowUpload(true);
    } else {
      toast.error("Alleen .docx bestanden zijn toegestaan");
    }
  };

  const startEdit = (tpl: ManagedTemplate) => {
    setEditingId(tpl.id);
    setEditName(tpl.name);
    setEditDescription(tpl.description || "");
    setEditKey(tpl.template_key);
  };

  const saveEdit = () => {
    if (!editingId || !editName) return;
    updateTemplate.mutate(
      {
        id: editingId,
        name: editName,
        description: editDescription || undefined,
        template_key: editKey,
      },
      { onSuccess: () => setEditingId(null) }
    );
  };

  const templateKeyOptions = Object.entries(TEMPLATE_KEY_LABELS);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-border bg-card p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-semibold text-foreground">
              Briefsjablonen
            </h2>
            <p className="text-sm text-muted-foreground mt-0.5">
              Beheer DOCX-sjablonen voor documenten en brieven.
              Bewerk in Word en upload hier.
            </p>
          </div>
          <button
            onClick={() => setShowUpload(true)}
            className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            <Upload className="h-4 w-4" />
            Nieuw sjabloon
          </button>
        </div>

        {/* Drag & drop zone */}
        <div
          onDrop={handleDrop}
          onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
          onDragLeave={() => setIsDragOver(false)}
          className={`mb-4 rounded-lg border-2 border-dashed p-4 text-center transition-colors cursor-pointer ${
            isDragOver
              ? "border-primary bg-primary/5"
              : "border-border hover:border-muted-foreground/30"
          }`}
          onClick={() => {
            const input = document.createElement("input");
            input.type = "file";
            input.accept = ".docx";
            input.onchange = (e) => {
              const file = (e.target as HTMLInputElement).files?.[0];
              if (file) {
                setUploadFile(file);
                if (!uploadName) setUploadName(file.name.replace(".docx", ""));
                setShowUpload(true);
              }
            };
            input.click();
          }}
        >
          <Upload className={`mx-auto h-6 w-6 ${isDragOver ? "text-primary" : "text-muted-foreground/40"}`} />
          <p className="mt-1 text-sm text-muted-foreground">
            {isDragOver ? "Laat los om te uploaden" : "Sleep een .docx bestand hierheen of klik om te kiezen"}
          </p>
        </div>

        {/* Template table */}
        {templates && templates.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left">
                  <th className="pb-2 font-medium text-muted-foreground">Naam</th>
                  <th className="pb-2 font-medium text-muted-foreground">Type</th>
                  <th className="pb-2 font-medium text-muted-foreground">Bestand</th>
                  <th className="pb-2 font-medium text-muted-foreground">Grootte</th>
                  <th className="pb-2 font-medium text-muted-foreground">Status</th>
                  <th className="pb-2 font-medium text-muted-foreground text-right">Acties</th>
                </tr>
              </thead>
              <tbody>
                {templates.map((tpl) => (
                  <tr key={tpl.id} className="border-b border-border/50 last:border-0">
                    <td className="py-2.5 pr-4">
                      {editingId === tpl.id ? (
                        <input
                          value={editName}
                          onChange={(e) => setEditName(e.target.value)}
                          className="w-full rounded border border-input bg-background px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                        />
                      ) : (
                        <div>
                          <span className="font-medium text-foreground">{tpl.name}</span>
                          {tpl.description && (
                            <p className="text-xs text-muted-foreground mt-0.5 line-clamp-1">{tpl.description}</p>
                          )}
                        </div>
                      )}
                    </td>
                    <td className="py-2.5 pr-4">
                      {editingId === tpl.id ? (
                        <select
                          value={editKey}
                          onChange={(e) => setEditKey(e.target.value)}
                          className="rounded border border-input bg-background px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                        >
                          {templateKeyOptions.map(([value, label]) => (
                            <option key={value} value={value}>{label}</option>
                          ))}
                        </select>
                      ) : (
                        <span className="text-muted-foreground">{getTemplateKeyLabel(tpl.template_key)}</span>
                      )}
                    </td>
                    <td className="py-2.5 pr-4">
                      <span className="text-xs text-muted-foreground font-mono">{tpl.original_filename}</span>
                    </td>
                    <td className="py-2.5 pr-4">
                      <span className="text-xs text-muted-foreground">{formatFileSize(tpl.file_size)}</span>
                    </td>
                    <td className="py-2.5 pr-4">
                      {tpl.is_builtin ? (
                        <span className="inline-flex items-center gap-1 rounded-full bg-blue-50 dark:bg-blue-900/20 px-2 py-0.5 text-xs font-medium text-blue-700 dark:text-blue-400">
                          <Lock className="h-3 w-3" />
                          Standaard
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 dark:bg-emerald-900/20 px-2 py-0.5 text-xs font-medium text-emerald-700 dark:text-emerald-400">
                          Aangepast
                        </span>
                      )}
                    </td>
                    <td className="py-2.5 text-right">
                      <div className="flex items-center justify-end gap-1">
                        {editingId === tpl.id ? (
                          <>
                            <button
                              onClick={saveEdit}
                              disabled={updateTemplate.isPending}
                              className="rounded p-1.5 text-primary hover:bg-primary/10 transition-colors"
                              title="Opslaan"
                            >
                              <Save className="h-3.5 w-3.5" />
                            </button>
                            <button
                              onClick={() => setEditingId(null)}
                              className="rounded p-1.5 text-muted-foreground hover:bg-muted transition-colors"
                              title="Annuleren"
                            >
                              <X className="h-3.5 w-3.5" />
                            </button>
                          </>
                        ) : (
                          <>
                            <button
                              onClick={() => downloadTemplate(tpl.id, tpl.original_filename)}
                              className="rounded p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                              title="Download"
                            >
                              <Download className="h-3.5 w-3.5" />
                            </button>
                            <button
                              onClick={() => startEdit(tpl)}
                              className="rounded p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                              title="Bewerken"
                            >
                              <Pencil className="h-3.5 w-3.5" />
                            </button>
                            {!tpl.is_builtin && (
                              <>
                                <button
                                  onClick={() => {
                                    const input = document.createElement("input");
                                    input.type = "file";
                                    input.accept = ".docx";
                                    input.onchange = (e) => {
                                      const file = (e.target as HTMLInputElement).files?.[0];
                                      if (file) replaceFile.mutate({ id: tpl.id, file });
                                    };
                                    input.click();
                                  }}
                                  className="rounded p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                                  title="Bestand vervangen"
                                >
                                  <Upload className="h-3.5 w-3.5" />
                                </button>
                                <button
                                  onClick={() => {
                                    if (confirm("Sjabloon verwijderen?")) {
                                      deleteTemplate.mutate(tpl.id);
                                    }
                                  }}
                                  className="rounded p-1.5 text-muted-foreground hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-900/20 dark:hover:text-red-400 transition-colors"
                                  title="Verwijderen"
                                >
                                  <Trash2 className="h-3.5 w-3.5" />
                                </button>
                              </>
                            )}
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-8 text-center text-sm text-muted-foreground">
            Geen sjablonen gevonden. Upload een .docx bestand om te beginnen.
          </div>
        )}
      </div>

      {/* Upload modal */}
      {showUpload && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50">
          <div className="w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-foreground">
                Sjabloon uploaden
              </h2>
              <button
                onClick={() => { setShowUpload(false); setUploadFile(null); }}
                className="rounded-md p-1.5 text-muted-foreground hover:bg-muted transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-4">
              {/* File selection */}
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Bestand
                </label>
                {uploadFile ? (
                  <div className="flex items-center gap-2 rounded-lg border border-border bg-muted/30 px-3 py-2 text-sm">
                    <FileText className="h-4 w-4 text-muted-foreground" />
                    <span className="flex-1 truncate">{uploadFile.name}</span>
                    <button
                      onClick={() => setUploadFile(null)}
                      className="text-muted-foreground hover:text-foreground"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => {
                      const input = document.createElement("input");
                      input.type = "file";
                      input.accept = ".docx";
                      input.onchange = (e) => {
                        const file = (e.target as HTMLInputElement).files?.[0];
                        if (file) {
                          setUploadFile(file);
                          if (!uploadName) setUploadName(file.name.replace(".docx", ""));
                        }
                      };
                      input.click();
                    }}
                    className="w-full rounded-lg border-2 border-dashed border-border px-3 py-4 text-sm text-muted-foreground hover:border-muted-foreground/30 transition-colors"
                  >
                    Klik om een .docx bestand te kiezen
                  </button>
                )}
              </div>

              {/* Name */}
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Naam
                </label>
                <input
                  value={uploadName}
                  onChange={(e) => setUploadName(e.target.value)}
                  placeholder="Bijv. Aangepaste sommatie"
                  className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                />
              </div>

              {/* Template key */}
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Sjabloontype
                </label>
                <select
                  value={uploadKey}
                  onChange={(e) => setUploadKey(e.target.value)}
                  className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                >
                  {templateKeyOptions.map(([value, label]) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </select>
                <p className="mt-1 text-xs text-muted-foreground">
                  Aangepaste sjablonen met hetzelfde type overschrijven het standaard-sjabloon.
                </p>
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Beschrijving (optioneel)
                </label>
                <textarea
                  value={uploadDesc}
                  onChange={(e) => setUploadDesc(e.target.value)}
                  rows={2}
                  className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary resize-none"
                />
              </div>
            </div>

            <div className="mt-6 flex items-center justify-end gap-2">
              <button
                onClick={() => { setShowUpload(false); setUploadFile(null); }}
                className="rounded-lg border border-border px-4 py-2 text-sm font-medium hover:bg-muted transition-colors"
              >
                Annuleren
              </button>
              <button
                onClick={handleUpload}
                disabled={!uploadFile || !uploadName || !uploadKey || uploadTemplate.isPending}
                className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50"
              >
                {uploadTemplate.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                Uploaden
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
