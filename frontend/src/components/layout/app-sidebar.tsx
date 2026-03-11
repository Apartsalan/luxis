"use client";

import { useMemo } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Users,
  Briefcase,
  FileText,
  Settings,
  Scale,
  Clock,
  Receipt,
  Calendar,
  CheckSquare,
  ChevronLeft,
  ChevronRight,
  Mail,
  Gavel,
  Bot,
  Zap,
  Banknote,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useModules, type LuxisModule } from "@/hooks/use-modules";
import { useUnlinkedCount } from "@/hooks/use-email-sync";
import { useIncassoQueueCounts } from "@/hooks/use-incasso";
import { usePendingCount } from "@/hooks/use-ai-agent";
import { useIntakePendingCount } from "@/hooks/use-intake";
import { useFollowupPendingCount } from "@/hooks/use-followup";
import { usePaymentPendingCount } from "@/hooks/use-payment-matching";

interface NavItem {
  name: string;
  href: string;
  icon: typeof LayoutDashboard;
  module?: LuxisModule;
  badge?: "unlinked-count" | "incasso-action" | "ai-pending" | "intake-pending" | "followup-pending" | "payment-pending";
}

const ALL_NAVIGATION: NavItem[] = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Mijn Taken", href: "/taken", icon: CheckSquare },
  { name: "Relaties", href: "/relaties", icon: Users },
  { name: "Dossiers", href: "/zaken", icon: Briefcase, badge: "ai-pending" },
  { name: "AI Intake", href: "/intake", icon: Bot, badge: "intake-pending" },
  { name: "Follow-up", href: "/followup", icon: Zap, badge: "followup-pending" },
  { name: "Betalingen", href: "/betalingen", icon: Banknote, badge: "payment-pending" },
  { name: "Incasso", href: "/incasso", icon: Gavel, module: "incasso", badge: "incasso-action" },
  { name: "Correspondentie", href: "/correspondentie", icon: Mail, badge: "unlinked-count" },
  { name: "Agenda", href: "/agenda", icon: Calendar },
  { name: "Uren", href: "/uren", icon: Clock, module: "tijdschrijven" },
  { name: "Facturen", href: "/facturen", icon: Receipt, module: "facturatie" },
  { name: "Documenten", href: "/documenten", icon: FileText },
  { name: "Instellingen", href: "/instellingen", icon: Settings },
];

interface AppSidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  mobileOpen: boolean;
  onMobileClose: () => void;
}

export function AppSidebar({
  collapsed,
  onToggle,
  mobileOpen,
  onMobileClose,
}: AppSidebarProps) {
  const pathname = usePathname();
  const { hasModule } = useModules();
  const { data: unlinkedCountData } = useUnlinkedCount();
  const unlinkedCount = unlinkedCountData?.count ?? 0;
  const { data: queueCounts } = useIncassoQueueCounts();
  const incassoActionCount = queueCounts?.action_required ?? 0;
  const { data: aiPendingData } = usePendingCount();
  const aiPendingCount = aiPendingData?.count ?? 0;
  const { data: intakePendingData } = useIntakePendingCount();
  const intakePendingCount = intakePendingData?.count ?? 0;
  const { data: followupPendingData } = useFollowupPendingCount();
  const followupPendingCount = followupPendingData?.count ?? 0;
  const { data: paymentPendingData } = usePaymentPendingCount();
  const paymentPendingCount = paymentPendingData?.count ?? 0;

  const navigation = useMemo(
    () =>
      ALL_NAVIGATION.filter(
        (item) => !item.module || hasModule(item.module)
      ),
    [hasModule]
  );

  return (
    <>
      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={onMobileClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex flex-col bg-sidebar-bg transition-all duration-200",
          // Desktop: always visible, respect collapsed state
          "hidden lg:flex",
          collapsed ? "lg:w-16" : "lg:w-60",
          // Mobile: slide in/out
          mobileOpen && "!flex w-60"
        )}
      >
        {/* Logo + mobile close */}
        <div
          className={cn(
            "flex h-14 items-center border-b border-sidebar-muted",
            collapsed && !mobileOpen
              ? "justify-center px-2"
              : "justify-between px-5"
          )}
        >
          <Link
            href="/"
            className="flex items-center gap-2.5"
            onClick={onMobileClose}
          >
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-sidebar-accent">
              <Scale className="h-4 w-4 text-white" />
            </div>
            {(!collapsed || mobileOpen) && (
              <span className="text-lg font-bold text-white tracking-tight">
                Luxis
              </span>
            )}
          </Link>
          {mobileOpen && (
            <button
              onClick={onMobileClose}
              className="lg:hidden rounded-md p-1.5 text-sidebar-foreground/50 hover:bg-sidebar-muted hover:text-sidebar-foreground transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          )}
        </div>

        {/* Navigation */}
        <nav
          className={cn(
            "flex-1 space-y-0.5 py-3",
            collapsed && !mobileOpen ? "px-2" : "px-3"
          )}
        >
          {navigation.map((item) => {
            const isActive =
              pathname === item.href ||
              (item.href !== "/" && pathname.startsWith(item.href));

            const badgeCount =
              item.badge === "unlinked-count" ? unlinkedCount :
              item.badge === "incasso-action" ? incassoActionCount :
              item.badge === "ai-pending" ? aiPendingCount :
              item.badge === "intake-pending" ? intakePendingCount :
              item.badge === "followup-pending" ? followupPendingCount :
              item.badge === "payment-pending" ? paymentPendingCount : 0;

            return (
              <Link
                key={item.name}
                href={item.href}
                onClick={onMobileClose}
                title={collapsed && !mobileOpen ? item.name : undefined}
                className={cn(
                  "group flex items-center rounded-md text-sm font-medium transition-all duration-150",
                  collapsed && !mobileOpen
                    ? "justify-center p-2.5"
                    : "gap-3 px-3 py-2",
                  isActive
                    ? "bg-sidebar-accent text-white"
                    : "text-sidebar-foreground/70 hover:bg-sidebar-muted hover:text-sidebar-foreground"
                )}
              >
                <div className="relative shrink-0">
                  <item.icon
                    className={cn(
                      collapsed && !mobileOpen ? "h-5 w-5" : "h-[18px] w-[18px]"
                    )}
                  />
                  {/* Badge dot on collapsed icon */}
                  {collapsed && !mobileOpen && badgeCount > 0 && (
                    <span className="absolute -top-1 -right-1 h-2 w-2 rounded-full bg-red-500" />
                  )}
                </div>
                {(!collapsed || mobileOpen) && (
                  <>
                    <span className="flex-1">{item.name}</span>
                    {badgeCount > 0 && (
                      <span className="flex h-5 min-w-5 items-center justify-center rounded-full bg-red-500/20 px-1.5 text-[10px] font-semibold text-red-400">
                        {badgeCount > 99 ? "99+" : badgeCount}
                      </span>
                    )}
                  </>
                )}
              </Link>
            );
          })}
        </nav>

        {/* Collapse toggle (desktop only) */}
        <div
          className={cn(
            "hidden lg:block border-t border-sidebar-muted py-3",
            collapsed ? "px-2" : "px-3"
          )}
        >
          <button
            onClick={onToggle}
            className={cn(
              "flex w-full items-center rounded-md text-sm text-sidebar-foreground/50 hover:bg-sidebar-muted hover:text-sidebar-foreground transition-colors",
              collapsed ? "justify-center p-2.5" : "gap-3 px-3 py-2"
            )}
            title={collapsed ? "Menu uitklappen" : "Menu inklappen"}
          >
            {collapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <>
                <ChevronLeft className="h-4 w-4" />
                <span>Inklappen</span>
              </>
            )}
          </button>
          {!collapsed && (
            <p className="mt-2 px-3 text-[10px] text-sidebar-foreground/30">
              Luxis v0.1.0
            </p>
          )}
        </div>
      </aside>
    </>
  );
}
