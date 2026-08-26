export function formatWeight(value: number | null): string {
  if (value === null || Number.isNaN(value)) return "—";
  return `${Math.round(value * 10) / 10}`;
}

export function formatDelta(value: number | null): string {
  if (value === null || Number.isNaN(value)) return "—";
  const rounded = Math.round(value * 10) / 10;
  if (rounded === 0) return "0 kg";
  return `${rounded > 0 ? "+" : ""}${rounded} kg`;
}


