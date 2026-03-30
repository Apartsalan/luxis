"use client";

import { useState } from "react";
import { Shield, Loader2, Mail, X, UserPlus, UserX, UserCheck } from "lucide-react";
import { toast } from "sonner";
import { useAuth, ROLE_LABELS } from "@/hooks/use-auth";
import { useUsers, useInviteUser, useUpdateUser, useDeactivateUser, useReactivateUser, ROLE_OPTIONS } from "@/hooks/use-users";

export function TeamTab() {
  const { user: currentUser } = useAuth();
  const { data: users, isLoading } = useUsers();
  const inviteUser = useInviteUser();
  const updateUser = useUpdateUser();
  const deactivateUser = useDeactivateUser();
  const reactivateUser = useReactivateUser();

  const [showInvite, setShowInvite] = useState(false);
  const [inviteForm, setInviteForm] = useState({
    email: "",
    full_name: "",
    role: "medewerker" as "admin" | "advocaat" | "medewerker",
  });
  const [editingUser, setEditingUser] = useState<string | null>(null);
  const [editRole, setEditRole] = useState<"admin" | "advocaat" | "medewerker">("medewerker");

  const inputClass =
    "w-full rounded-lg border border-input bg-background px-3 py-2.5 text-sm placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors";

  const isAdmin = currentUser?.role === "admin";

  const handleInvite = () => {
    if (!inviteForm.email || !inviteForm.full_name) {
      toast.error("Vul alle velden in");
      return;
    }
    inviteUser.mutate(inviteForm, {
      onSuccess: () => {
        setShowInvite(false);
        setInviteForm({ email: "", full_name: "", role: "medewerker" });
      },
    });
  };

  const handleRoleChange = (userId: string) => {
    updateUser.mutate({ id: userId, role: editRole }, {
      onSuccess: () => setEditingUser(null),
    });
  };

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
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-semibold text-foreground">Teamleden</h2>
            <p className="text-sm text-muted-foreground">
              {activeUsers.length} actief{inactiveUsers.length > 0 ? ` · ${inactiveUsers.length} inactief` : ""}
            </p>
          </div>
          {isAdmin && (
            <button
              onClick={() => setShowInvite(!showInvite)}
              className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
            >
              <UserPlus className="h-4 w-4" />
              Uitnodigen
            </button>
          )}
        </div>

        {/* Invite form */}
        {showInvite && (
          <div className="mb-6 rounded-lg border border-primary/20 bg-primary/5 p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-foreground">Nieuw teamlid uitnodigen</h3>
              <button
                onClick={() => setShowInvite(false)}
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="grid gap-3 sm:grid-cols-3">
              <div>
                <label htmlFor="settings-invite-name" className="block text-xs font-medium text-foreground mb-1">Naam</label>
                <input
                  id="settings-invite-name"
                  type="text"
                  value={inviteForm.full_name}
                  onChange={(e) => setInviteForm({ ...inviteForm, full_name: e.target.value })}
                  placeholder="Volledige naam"
                  className={inputClass}
                />
              </div>
              <div>
                <label htmlFor="settings-invite-email" className="block text-xs font-medium text-foreground mb-1">E-mail</label>
                <input
                  id="settings-invite-email"
                  type="email"
                  value={inviteForm.email}
                  onChange={(e) => setInviteForm({ ...inviteForm, email: e.target.value })}
                  placeholder="naam@kantoor.nl"
                  className={inputClass}
                />
              </div>
              <div>
                <label htmlFor="settings-invite-role" className="block text-xs font-medium text-foreground mb-1">Rol</label>
                <select
                  id="settings-invite-role"
                  value={inviteForm.role}
                  onChange={(e) => setInviteForm({ ...inviteForm, role: e.target.value as any })}
                  className={inputClass}
                >
                  {ROLE_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>
            </div>
            <button
              onClick={handleInvite}
              disabled={inviteUser.isPending}
              className="mt-3 inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50"
            >
              {inviteUser.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Mail className="h-4 w-4" />
              )}
              Uitnodiging versturen
            </button>
          </div>
        )}

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
              <div className="flex items-center gap-2">
                {editingUser === u.id ? (
                  <div className="flex items-center gap-2">
                    <select
                      value={editRole}
                      onChange={(e) => setEditRole(e.target.value as any)}
                      className="rounded-md border border-input bg-background px-2 py-1 text-xs"
                    >
                      {ROLE_OPTIONS.map((opt) => (
                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                      ))}
                    </select>
                    <button
                      onClick={() => handleRoleChange(u.id)}
                      className="rounded-md bg-primary px-2 py-1 text-xs text-primary-foreground"
                    >
                      Opslaan
                    </button>
                    <button
                      onClick={() => setEditingUser(null)}
                      className="rounded-md border border-border px-2 py-1 text-xs"
                    >
                      Annuleren
                    </button>
                  </div>
                ) : (
                  <>
                    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${
                      u.role === "admin"
                        ? "bg-purple-50 text-purple-700 ring-purple-600/20"
                        : u.role === "advocaat"
                        ? "bg-blue-50 text-blue-700 ring-blue-600/20"
                        : "bg-gray-50 text-gray-700 ring-gray-600/20"
                    }`}>
                      {ROLE_LABELS[u.role] ?? u.role}
                    </span>
                    {isAdmin && u.id !== currentUser?.id && (
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => { setEditingUser(u.id); setEditRole(u.role); }}
                          className="rounded-md p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                          title="Rol wijzigen"
                        >
                          <Shield className="h-3.5 w-3.5" />
                        </button>
                        <button
                          onClick={() => deactivateUser.mutate(u.id)}
                          className="rounded-md p-1.5 text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-colors"
                          title="Deactiveren"
                        >
                          <UserX className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    )}
                  </>
                )}
              </div>
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
                {isAdmin && (
                  <button
                    onClick={() => reactivateUser.mutate(u.id)}
                    className="inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium text-primary hover:bg-primary/10 transition-colors"
                  >
                    <UserCheck className="h-3.5 w-3.5" />
                    Heractiveren
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
