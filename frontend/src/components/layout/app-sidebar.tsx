"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Users,
  Briefcase,
  FileText,
  Settings,
  Scale,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navigation = [
  {
    name: "Dashboard",
    href: "/",
    icon: LayoutDashboard,
  },
  {
    name: "Relaties",
    href: "/relaties",
    icon: Users,
  },
  {
    name: "Zaken",
    href: "/zaken",
    icon: Briefcase,
  },
  {
    name: "Documenten",
    href: "/documenten",
    icon: FileText,
  },
  {
    name: "Tarieven",
    href: "/tarieven",
    icon: Scale,
  },
  {
    name: "Instellingen",
    href: "/instellingen",
    icon: Settings,
  },
];

interface AppSidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export function AppSidebar({ collapsed, onToggle }: AppSidebarProps) {
  const pathname = usePathname();

  return (
    <aside
      className={cn(
        "fixed inset-y-0 left-0 z-50 flex flex-col bg-sidebar-bg transition-all duration-200",
        collapsed ? "w-16" : "w-60"
      )}
    >
      {/* Logo */}
      <div
        className={cn(
          "flex h-14 items-center border-b border-sidebar-muted",
          collapsed ? "justify-center px-2" : "px-5"
        )}
      >
        <Link href="/" className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-sidebar-accent">
            <Scale className="h-4 w-4 text-white" />
          </div>
          {!collapsed && (
            <span className="text-lg font-bold text-white tracking-tight">
              Luxis
            </span>
          )}
        </Link>
      </div>

      {/* Navigation */}
      <nav
        className={cn(
          "flex-1 space-y-0.5 py-3",
          collapsed ? "px-2" : "px-3"
        )}
      >
        {navigation.map((item) => {
          const isActive =
            pathname === item.href ||
            (item.href !== "/" && pathname.startsWith(item.href));

          return (
            <Link
              key={item.name}
              href={item.href}
              title={collapsed ? item.name : undefined}
              className={cn(
                "group flex items-center rounded-md text-sm font-medium transition-all duration-150",
                collapsed ? "justify-center p-2.5" : "gap-3 px-3 py-2",
                isActive
                  ? "bg-sidebar-accent text-white"
                  : "text-sidebar-foreground/70 hover:bg-sidebar-muted hover:text-sidebar-foreground"
              )}
            >
              <item.icon
                className={cn("shrink-0", collapsed ? "h-5 w-5" : "h-[18px] w-[18px]")}
              />
              {!collapsed && item.name}
            </Link>
          );
        })}
      </nav>

      {/* Collapse toggle */}
      <div
        className={cn(
          "border-t border-sidebar-muted py-3",
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
  );
}
