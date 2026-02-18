"use client";

import { LogOut, User, Bell, Search } from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import { usePathname } from "next/navigation";

const PAGE_TITLES: Record<string, string> = {
  "/": "Dashboard",
  "/relaties": "Relaties",
  "/relaties/nieuw": "Nieuwe relatie",
  "/zaken": "Zaken",
  "/zaken/nieuw": "Nieuwe zaak",
  "/documenten": "Documenten",
  "/tarieven": "Tarieven",
  "/instellingen": "Instellingen",
};

export function AppHeader() {
  const { user, logout } = useAuth();
  const pathname = usePathname();

  const pageTitle =
    PAGE_TITLES[pathname] ||
    (pathname.startsWith("/relaties/") ? "Relatiedetail" : null) ||
    (pathname.startsWith("/zaken/") ? "Zaakdetail" : null) ||
    "Luxis";

  return (
    <header className="sticky top-0 z-40 flex h-14 items-center justify-between border-b border-border bg-white/80 backdrop-blur-sm px-6">
      {/* Left: page title */}
      <div>
        <h2 className="text-sm font-semibold text-foreground">{pageTitle}</h2>
      </div>

      {/* Right: search + notifications + user menu */}
      <div className="flex items-center gap-2">
        <button
          className="hidden sm:flex items-center gap-2 rounded-md border border-border bg-muted/50 px-3 py-1.5 text-xs text-muted-foreground hover:bg-muted transition-colors"
          onClick={() => {}}
        >
          <Search className="h-3.5 w-3.5" />
          <span>Zoeken...</span>
          <kbd className="ml-2 rounded border border-border bg-white px-1.5 py-0.5 text-[10px] font-mono">
            Ctrl+K
          </kbd>
        </button>

        <button
          className="relative rounded-md p-2 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
          title="Meldingen"
        >
          <Bell className="h-4 w-4" />
        </button>

        {user && (
          <div className="flex items-center gap-2 ml-1">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-primary">
              <User className="h-4 w-4" />
            </div>
            <div className="hidden sm:block">
              <p className="text-sm font-medium text-foreground leading-tight">
                {user.full_name}
              </p>
              <p className="text-[11px] text-muted-foreground leading-tight">
                {user.email}
              </p>
            </div>
            <button
              onClick={logout}
              className="ml-1 rounded-md p-2 text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-colors"
              title="Uitloggen"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
