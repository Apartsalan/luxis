"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Briefcase, CheckSquare, LayoutDashboard, Mail, Menu } from "lucide-react";
import { cn } from "@/lib/utils";
import { useUnlinkedCount } from "@/hooks/use-email-sync";
import { useMyTasks } from "@/hooks/use-workflow";

// Onderste navigatiebalk — alleen op telefoon (<md). Vijf vaste ingangen; het
// vijfde ("Menu") opent de bestaande zijbalk-lade zodat alle overige pagina's
// bereikbaar blijven. De content-container krijgt in layout.tsx onderruimte zodat
// deze balk niets afdekt.

interface MobileNavProps {
  onMenuOpen: () => void;
}

const ITEMS = [
  { name: "Home", href: "/", icon: LayoutDashboard },
  { name: "Dossiers", href: "/zaken", icon: Briefcase },
  { name: "Mail", href: "/correspondentie", icon: Mail, badge: "unlinked" as const },
  { name: "Taken", href: "/taken", icon: CheckSquare, badge: "taken" as const },
];

export function MobileNav({ onMenuOpen }: MobileNavProps) {
  const pathname = usePathname();
  const { data: unlinkedData } = useUnlinkedCount();
  const unlinkedCount = unlinkedData?.count ?? 0;
  const { data: myTasks } = useMyTasks();
  const takenOpenCount =
    myTasks?.filter((t) => t.status !== "completed" && t.status !== "skipped").length ?? 0;

  const badgeFor = (badge?: "unlinked" | "taken") =>
    badge === "unlinked" ? unlinkedCount : badge === "taken" ? takenOpenCount : 0;

  const isActive = (href: string) =>
    href === "/" ? pathname === "/" : pathname.startsWith(href);

  return (
    <nav
      aria-label="Hoofdnavigatie"
      className="fixed inset-x-0 bottom-0 z-40 flex md:hidden border-t border-border bg-white/95 backdrop-blur-sm pb-[env(safe-area-inset-bottom)]"
    >
      {ITEMS.map((item) => {
        const active = isActive(item.href);
        const count = badgeFor(item.badge);
        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "relative flex flex-1 flex-col items-center justify-center gap-0.5 py-2 text-[11px] font-medium transition-colors",
              active ? "text-primary" : "text-muted-foreground"
            )}
          >
            <span className="relative">
              <item.icon className="h-5 w-5" />
              {count > 0 && (
                <span className="absolute -right-2 -top-1.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[9px] font-bold text-white">
                  {count > 9 ? "9+" : count}
                </span>
              )}
            </span>
            {item.name}
          </Link>
        );
      })}
      <button
        type="button"
        onClick={onMenuOpen}
        className="flex flex-1 flex-col items-center justify-center gap-0.5 py-2 text-[11px] font-medium text-muted-foreground transition-colors"
      >
        <Menu className="h-5 w-5" />
        Menu
      </button>
    </nav>
  );
}
