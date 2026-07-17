"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/use-auth";
import { AppSidebar } from "@/components/layout/app-sidebar";
import { AppHeader } from "@/components/layout/app-header";
import { MobileNav } from "@/components/layout/mobile-nav";
import { BreadcrumbProvider } from "@/components/layout/breadcrumb-context";
import { ErrorBoundary } from "@/components/error-boundary";
import { cn } from "@/lib/utils";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem("luxis_sidebar_collapsed");
    if (stored === "true") setSidebarCollapsed(true);
  }, []);

  // Terug-navigatie: leg bij binnenkomst in de app (de eerste pagina in deze tab)
  // de historie-lengte vast als ijkpunt. De BackButton onderscheidt hiermee "echt
  // terug" (er is ná binnenkomst genavigeerd → history.length is gegroeid) van een
  // direct bezochte/ge-bookmarkte URL (nog op het ijkpunt → val terug op de ouder).
  useEffect(() => {
    if (sessionStorage.getItem("luxis_entry_history_len") === null) {
      sessionStorage.setItem("luxis_entry_history_len", String(window.history.length));
    }
  }, []);

  // Route guard — redirect to login if not authenticated
  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
  }, [loading, user, router]);

  const toggleSidebar = () => {
    setSidebarCollapsed((prev) => {
      const next = !prev;
      localStorage.setItem("luxis_sidebar_collapsed", String(next));
      return next;
    });
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background" role="status" aria-label="Laden">
        <div className="text-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary/20 border-t-primary mx-auto" aria-hidden="true" />
          <p className="mt-4 text-sm text-muted-foreground">Laden...</p>
        </div>
      </div>
    );
  }

  // Don't render dashboard if not authenticated
  if (!user) return null;

  return (
    <BreadcrumbProvider>
      <div className="min-h-screen bg-background">
        <a href="#main-content" className="skip-to-content">
          Naar hoofdinhoud
        </a>
        <AppSidebar
          collapsed={sidebarCollapsed}
          onToggle={toggleSidebar}
          mobileOpen={mobileMenuOpen}
          onMobileClose={() => setMobileMenuOpen(false)}
        />
        <div
          className={cn(
            "transition-all duration-200",
            "lg:pl-60",
            sidebarCollapsed && "lg:pl-16",
            "pl-0"
          )}
        >
          <AppHeader onMobileMenuToggle={() => setMobileMenuOpen(true)} />
          {/* Onderruimte op telefoon zodat de onderbalk niets afdekt (balk ~56px
              + veilige rand); md+ heeft geen onderbalk. */}
          <main
            id="main-content"
            className="p-4 sm:p-6 pb-[calc(4rem+env(safe-area-inset-bottom))] sm:pb-[calc(4rem+env(safe-area-inset-bottom))] md:pb-6"
          >
            <ErrorBoundary>{children}</ErrorBoundary>
          </main>
        </div>
        <MobileNav onMenuOpen={() => setMobileMenuOpen(true)} />
      </div>
    </BreadcrumbProvider>
  );
}
