export default function DashboardLoading() {
  return (
    <div className="space-y-6 animate-pulse">
      {/* Header skeleton */}
      <div className="flex items-center justify-between">
        <div>
          <div className="h-7 w-48 rounded-md bg-muted" />
          <div className="mt-2 h-4 w-32 rounded-md bg-muted" />
        </div>
        <div className="h-10 w-32 rounded-lg bg-muted" />
      </div>

      {/* KPI cards skeleton */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="rounded-xl border border-border bg-card p-5">
            <div className="h-10 w-10 rounded-lg bg-muted" />
            <div className="mt-3 h-7 w-20 rounded-md bg-muted" />
            <div className="mt-2 h-4 w-28 rounded-md bg-muted" />
          </div>
        ))}
      </div>

      {/* Content skeleton */}
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-border bg-card p-5 h-64" />
        <div className="rounded-xl border border-border bg-card p-5 h-64" />
      </div>
    </div>
  );
}
