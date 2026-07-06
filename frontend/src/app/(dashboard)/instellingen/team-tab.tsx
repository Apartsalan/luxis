"use client";

import { useAuth, ROLE_LABELS } from "@/hooks/use-auth";
import { useUsers } from "@/hooks/use-users";

// Read-only teamoverzicht. Uitnodigen/rol-wijzigen/deactiveren is bewust weggelaten:
// die knoppen riepen backend-endpoints aan die niet bestaan (POST /api/users/invite,
// PUT /api/users/{id}) — een echte uitnodig-flow (mail + wachtwoord-link) is voor een
// eenpersoonskantoor YAGNI. Nieuwe gebruiker nodig? Aanmaken via /api/auth/register.
export function TeamTab() {
  const { user: currentUser } = useAuth();
  const { data: users, isLoading } = useUsers();

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex items-center justify-between rounded-xl border border-border bg-card p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-full skeleton" />
              <div className="space-y-2">
                <div className="h-4 w-36 rounded skeleton" />
                <div className="h-3 w-48 rounded skeleton" />
              </div>
            </div>
            <div className="h-6 w-16 rounded-full skeleton" />
          </div>
        ))}
      </div>
    );
  }

  const activeUsers = (users ?? []).filter((u) => u.is_active);
  const inactiveUsers = (users ?? []).filter((u) => !u.is_active);

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-border bg-card p-6">
        <div className="mb-4">
          <h2 className="text-base font-semibold text-foreground">Teamleden</h2>
          <p className="text-sm text-muted-foreground">
            {activeUsers.length} actief{inactiveUsers.length > 0 ? ` · ${inactiveUsers.length} inactief` : ""}
          </p>
        </div>

        {/* User list */}
        <div className="divide-y divide-border rounded-lg border border-border overflow-hidden">
          {activeUsers.map((u) => (
            <div key={u.id} className="flex items-center justify-between px-4 py-3 hover:bg-muted/50 transition-colors">
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary/10 text-primary text-sm font-semibold">
                  {u.full_name.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase()}
                </div>
                <div>
                  <p className="text-sm font-medium text-foreground">
                    {u.full_name}
                    {u.id === currentUser?.id && (
                      <span className="ml-1.5 text-xs text-muted-foreground">(jij)</span>
                    )}
                  </p>
                  <p className="text-xs text-muted-foreground">{u.email}</p>
                </div>
              </div>
              <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${
                u.role === "admin"
                  ? "bg-purple-50 text-purple-700 ring-purple-600/20"
                  : u.role === "advocaat"
                  ? "bg-blue-50 text-blue-700 ring-blue-600/20"
                  : "bg-gray-50 text-gray-700 ring-gray-600/20"
              }`}>
                {ROLE_LABELS[u.role] ?? u.role}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Inactive users */}
      {inactiveUsers.length > 0 && (
        <div className="rounded-xl border border-border bg-card p-6">
          <h2 className="text-base font-semibold text-foreground mb-4">
            Gedeactiveerde gebruikers
          </h2>
          <div className="divide-y divide-border rounded-lg border border-border overflow-hidden">
            {inactiveUsers.map((u) => (
              <div key={u.id} className="flex items-center justify-between px-4 py-3 opacity-60">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-full bg-muted text-muted-foreground text-sm font-semibold">
                    {u.full_name.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase()}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-foreground">{u.full_name}</p>
                    <p className="text-xs text-muted-foreground">{u.email}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
