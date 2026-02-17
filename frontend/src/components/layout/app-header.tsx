"use client";

import { LogOut, User } from "lucide-react";
import { useAuth } from "@/hooks/use-auth";

export function AppHeader() {
  const { user, logout } = useAuth();

  return (
    <header className="sticky top-0 z-40 flex h-16 items-center justify-between border-b border-border bg-white px-6">
      {/* Left: page context / breadcrumb area */}
      <div />

      {/* Right: user menu */}
      <div className="flex items-center gap-4">
        {user && (
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-navy-100 text-navy-600">
              <User className="h-4 w-4" />
            </div>
            <div className="hidden sm:block">
              <p className="text-sm font-medium text-navy-800">
                {user.full_name}
              </p>
              <p className="text-xs text-muted-foreground">{user.email}</p>
            </div>
            <button
              onClick={logout}
              className="ml-2 rounded-md p-2 text-muted-foreground hover:bg-muted hover:text-navy-800 transition-colors"
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
