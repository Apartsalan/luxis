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

export function AppSidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-border bg-white">
      {/* Logo */}
      <div className="flex h-16 items-center border-b border-border px-6">
        <Link href="/" className="flex items-center gap-2">
          <Scale className="h-7 w-7 text-navy-500" />
          <span className="text-xl font-bold text-navy-500">Luxis</span>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navigation.map((item) => {
          const isActive =
            pathname === item.href ||
            (item.href !== "/" && pathname.startsWith(item.href));

          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-colors",
                isActive
                  ? "bg-navy-500 text-white"
                  : "text-navy-600 hover:bg-navy-50 hover:text-navy-800"
              )}
            >
              <item.icon className="h-5 w-5 shrink-0" />
              {item.name}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="border-t border-border px-6 py-4">
        <p className="text-xs text-muted-foreground">
          Luxis v0.1.0
        </p>
      </div>
    </aside>
  );
}
