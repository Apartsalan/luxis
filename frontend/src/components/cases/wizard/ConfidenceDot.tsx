import { confidenceBgColor, confidenceLabelText } from "@/lib/confidence";

export function ConfidenceDot({ field, confidence }: { field: string; confidence: Record<string, number> }) {
  const value = confidence[field];
  if (value === undefined || value === null) return null;
  const color = confidenceBgColor(value);
  return (
    <span className="relative group ml-1.5 inline-block">
      <span className={`inline-block h-2 w-2 rounded-full ${color}`} />
      <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 hidden group-hover:block whitespace-nowrap rounded bg-foreground px-2 py-0.5 text-[10px] text-background">
        AI: {confidenceLabelText(value)}
      </span>
    </span>
  );
}
