"use client";

import { useState, useRef, useEffect } from "react";
import { LogOut, User, Bell, Search, Menu, Check, CheckCheck, Clock, AlertTriangle, FileText, Mail, ArrowRight, Info } from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import { usePathname } from "next/navigation";
import Link from "next/link";
import {
  useNotifications,
  useUnreadCount,
  useMarkAsRead,
  useMarkAllAsRead,
  formatNotificationTime,
  NOTIFICATION_TYPE_CONFIG,
  type Notification,
  type NotificationType,
} from "@/hooks/use-notifications";
import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { useBreadcrumbContext } from "@/components/layout/breadcrumb-context";

const PAGE_TITLES: Record<string, string> = {
  "/": "Dashboard",
  "/relaties": "Relaties",
  "/relaties/nieuw": "Nieuwe relatie",
  "/zaken": "Dossiers",
  "/zaken/nieuw": "Nieuw dossier",
  "/uren": "Uren",
  "/taken": "Mijn Taken",
  "/facturen": "Facturen",
  "/facturen/nieuw": "Nieuwe factuur",
  "/documenten": "Documenten",
  "/tarieven": "Tarieven",
  "/agenda": "Agenda",
  "/instellingen": "Instellingen",
};

const ICON_MAP: Record<string, typeof Clock> = {
  clock: Clock,
  "alert-triangle": AlertTriangle,
  "user-plus": User,
  "check-circle": Check,
  "arrow-right": ArrowRight,
  "file-text": FileText,
  mail: Mail,
  "mail-x": Mail,
  "alert-circle": AlertTriangle,
  info: Info,
};

const COLOR_MAP: Record<string, string> = {
  amber: "bg-amber-50 text-amber-600",
  red: "bg-red-50 text-red-600",
  blue: "bg-blue-50 text-blue-600",
  emerald: "bg-emerald-50 text-emerald-600",
  indigo: "bg-indigo-50 text-indigo-600",
  gray: "bg-gray-50 text-gray-600",
};

interface AppHeaderProps {
  onMobileMenuToggle?: () => void;
}

export function AppHeader({ onMobileMenuToggle }: AppHeaderProps) {
  const { overrides: breadcrumbOverrides } = useBreadcrumbContext();
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const [showNotifications, setShowNotifications] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const { data: notifications = [] } = useNotifications(15);
  const { data: unreadCount = 0 } = useUnreadCount();
  const markAsRead = useMarkAsRead();
  const markAllAsRead = useMarkAllAsRead();

  // Close dropdown on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setShowNotifications(false);
      }
    }
    if (showNotifications) {
      document.addEventListener("mousedown", handleClick);
      return () => document.removeEventListener("mousedown", handleClick);
    }
  }, [showNotifications]);

  const pageTitle = PAGE_TITLES[pathname] || null;
  const isNestedPage = !pageTitle && pathname !== "/";

  function handleNotificationClick(n: Notification) {
    if (!n.is_read) {
      markAsRead.mutate(n.id);
    }
    setShowNotifications(false);
    // Navigation happens via the Link wrapper
  }

  function getNotificationIcon(type: NotificationType) {
    const config = NOTIFICATION_TYPE_CONFIG[type] || NOTIFICATION_TYPE_CONFIG.system;
    const Icon = ICON_MAP[config.icon] || Info;
    const colorClass = COLOR_MAP[config.color] || COLOR_MAP.gray;
    return (
      <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${colorClass}`}>
        <Icon className="h-4 w-4" />
      </div>
    );
  }

  return (
    <header className="sticky top-0 z-40 flex h-14 items-center justify-between border-b border-border bg-white/80 backdrop-blur-sm px-4 sm:px-6">
      {/* Left: hamburger (mobile) + page title */}
      <div className="flex items-center gap-3">
        {onMobileMenuToggle && (
          <button
            onClick={onMobileMenuToggle}
            className="lg:hidden rounded-md p-2.5 -ml-1 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
            aria-label="Menu openen"
          >
            <Menu className="h-5 w-5" />
          </button>
        )}
        {isNestedPage ? (
          <Breadcrumbs overrides={breadcrumbOverrides} />
        ) : (
          <h2 className="text-sm font-semibold text-foreground">{pageTitle ?? "Luxis"}</h2>
        )}
      </div>

      {/* Right: search + notifications + user menu */}
      <div className="flex items-center gap-2">
        <button
          className="hidden sm:flex items-center gap-2 rounded-md border border-border bg-muted/50 px-3 py-1.5 text-xs text-muted-foreground hover:bg-muted transition-colors"
          onClick={() => {
            // Trigger Ctrl+K to open command palette
            window.dispatchEvent(new KeyboardEvent("keydown", { key: "k", ctrlKey: true }));
          }}
        >
          <Search className="h-3.5 w-3.5" />
          <span>Zoeken...</span>
          <kbd className="ml-2 rounded border border-border bg-white px-1.5 py-0.5 text-[10px] font-mono">
            Ctrl+K
          </kbd>
        </button>

        {/* Notification bell */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="relative rounded-md p-2 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
            title="Meldingen"
          >
            <Bell className="h-4 w-4" />
            {unreadCount > 0 && (
              <span className="absolute -top-0.5 -right-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white">
                {unreadCount > 9 ? "9+" : unreadCount}
              </span>
            )}
          </button>

          {/* Notification dropdown */}
          {showNotifications && (
            <div className="absolute right-0 top-full mt-2 w-[calc(100vw-2rem)] sm:w-96 max-w-96 rounded-lg border border-border bg-white shadow-lg overflow-hidden z-50">
              {/* Header */}
              <div className="flex items-center justify-between px-4 py-3 border-b border-border">
                <h3 className="text-sm font-semibold text-foreground">Meldingen</h3>
                {unreadCount > 0 && (
                  <button
                    onClick={() => markAllAsRead.mutate()}
                    className="flex items-center gap-1 text-xs text-primary hover:text-primary/80 transition-colors"
                  >
                    <CheckCheck className="h-3.5 w-3.5" />
                    Alles gelezen
                  </button>
                )}
              </div>

              {/* List */}
              <div className="max-h-96 overflow-y-auto">
                {notifications.length === 0 ? (
                  <div className="py-8 text-center">
                    <Bell className="h-8 w-8 text-muted-foreground/30 mx-auto mb-2" />
                    <p className="text-sm text-muted-foreground">Geen meldingen</p>
                  </div>
                ) : (
                  notifications.map((n) => {
                    const content = (
                      <div
                        className={`flex gap-3 px-4 py-3 hover:bg-muted/50 cursor-pointer transition-colors ${
                          !n.is_read ? "bg-primary/5" : ""
                        }`}
                        onClick={() => handleNotificationClick(n)}
                      >
                        {getNotificationIcon(n.type)}
                        <div className="flex-1 min-w-0">
                          <p className={`text-sm leading-tight ${!n.is_read ? "font-semibold text-foreground" : "text-foreground/80"}`}>
                            {n.title}
                          </p>
                          <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">
                            {n.message}
                          </p>
                          <div className="flex items-center gap-2 mt-1">
                            <span className="text-[11px] text-muted-foreground/60">
                              {formatNotificationTime(n.created_at)}
                            </span>
                            {n.case_number && (
                              <span className="text-[11px] text-primary/60 font-medium">
                                {n.case_number}
                              </span>
                            )}
                          </div>
                        </div>
                        {!n.is_read && (
                          <div className="flex items-start pt-1">
                            <div className="h-2 w-2 rounded-full bg-primary shrink-0" />
                          </div>
                        )}
                      </div>
                    );

                    // Wrap in Link if there's a case_id
                    if (n.case_id) {
                      return (
                        <Link key={n.id} href={`/zaken/${n.case_id}`}>
                          {content}
                        </Link>
                      );
                    }
                    return <div key={n.id}>{content}</div>;
                  })
                )}
              </div>
            </div>
          )}
        </div>

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
