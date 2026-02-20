"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronRight, Home } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * Static labels for known path segments (Dutch UI).
 * Dynamic segments like [id] are resolved via props or context.
 */
const SEGMENT_LABELS: Record<string, string> = {
  relaties: "Relaties",
  zaken: "Dossiers",
  taken: "Mijn Taken",
  uren: "Uren",
  facturen: "Facturen",
  documenten: "Documenten",
  instellingen: "Instellingen",
  agenda: "Agenda",
  nieuw: "Nieuw",
};

export interface BreadcrumbOverride {
  /** The path segment to override (e.g., a UUID) */
  segment: string;
  /** The label to display */
  label: string;
}

interface BreadcrumbsProps {
  /** Override labels for dynamic segments (e.g., case numbers, contact names) */
  overrides?: BreadcrumbOverride[];
  className?: string;
}

export function Breadcrumbs({ overrides = [], className }: BreadcrumbsProps) {
  const pathname = usePathname();
  const segments = pathname.split("/").filter(Boolean);

  // Don't render breadcrumbs on dashboard root
  if (segments.length === 0) return null;

  // Build crumbs
  const crumbs: { label: string; href: string; isLast: boolean }[] = [];
  let currentPath = "";

  for (let i = 0; i < segments.length; i++) {
    const seg = segments[i];
    currentPath += `/${seg}`;
    const isLast = i === segments.length - 1;

    // Find label: check overrides first, then static map, then format the segment
    const override = overrides.find((o) => o.segment === seg);
    const label =
      override?.label ??
      SEGMENT_LABELS[seg] ??
      (isUUID(seg) ? "Detail" : capitalize(seg));

    crumbs.push({ label, href: currentPath, isLast });
  }

  return (
    <nav aria-label="Breadcrumb" className={cn("flex items-center gap-1 text-sm", className)}>
      <Link
        href="/"
        className="flex items-center text-muted-foreground hover:text-foreground transition-colors"
        title="Dashboard"
      >
        <Home className="h-3.5 w-3.5" />
      </Link>
      {crumbs.map((crumb) => (
        <span key={crumb.href} className="flex items-center gap-1">
          <ChevronRight className="h-3.5 w-3.5 text-muted-foreground/50" />
          {crumb.isLast ? (
            <span className="font-medium text-foreground truncate max-w-[200px]">
              {crumb.label}
            </span>
          ) : (
            <Link
              href={crumb.href}
              className="text-muted-foreground hover:text-foreground transition-colors truncate max-w-[200px]"
            >
              {crumb.label}
            </Link>
          )}
        </span>
      ))}
    </nav>
  );
}

function isUUID(s: string): boolean {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(s);
}

function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}
