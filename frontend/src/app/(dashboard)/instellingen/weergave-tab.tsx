"use client";


export function WeergaveTab() {
  return (
    <div className="rounded-xl border border-border bg-card p-6">
      <h2 className="text-base font-semibold text-foreground mb-2">
        Weergave-instellingen
      </h2>
      <p className="text-sm text-muted-foreground mb-6">
        Pas de weergave van Luxis aan je voorkeuren aan
      </p>
      <div className="space-y-6 max-w-md">
        <div>
          <label className="block text-sm font-medium text-foreground mb-2">
            Thema
          </label>
          <div className="flex gap-3">
            <button
              className="flex-1 rounded-lg border p-3 text-center text-sm font-medium transition-all border-primary bg-primary/5 text-primary ring-1 ring-primary/20"
            >
              Licht
            </button>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-foreground mb-2">
            Sidebar
          </label>
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="sidebar_collapsed"
              className="h-4 w-4 rounded border-input accent-primary"
            />
            <label
              htmlFor="sidebar_collapsed"
              className="text-sm text-foreground"
            >
              Sidebar standaard ingeklapt
            </label>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-foreground mb-2">
            Datumformaat
          </label>
          <select
            defaultValue="nl"
            className="w-full rounded-lg border border-input bg-background px-3 py-2.5 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors"
          >
            <option value="nl">17-02-2026 (DD-MM-JJJJ)</option>
            <option value="iso">2026-02-17 (JJJJ-MM-DD)</option>
          </select>
        </div>
      </div>
    </div>
  );
}
