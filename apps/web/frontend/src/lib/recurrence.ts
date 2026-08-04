const RECURRENCE_LABELS: Record<string, string> = {
  daily: "diaria",
  weekly: "semanal",
  monthly: "mensual",
  yearly: "anual",
};

const CUSTOM_RECURRENCE_REGEX = /^([1-9]\d*)([hdwmy])$/;

export const CUSTOM_RECURRENCE_UNITS: { value: string; label: string }[] = [
  { value: "h", label: "horas" },
  { value: "d", label: "días" },
  { value: "w", label: "semanas" },
  { value: "m", label: "meses" },
  { value: "y", label: "años" },
];

const RECURRENCE_HOURS: Record<string, number> = {
  daily: 24,
  weekly: 24 * 7,
  monthly: 24 * 30,
  yearly: 24 * 365,
  h: 1,
  d: 24,
  w: 24 * 7,
  m: 24 * 30,
  y: 24 * 365,
};

export function parseCustomRecurrence(value: string): { amount: number; unit: string } | null {
  const match = value.match(CUSTOM_RECURRENCE_REGEX);
  if (!match) return null;
  return { amount: Number(match[1]), unit: match[2] };
}

export function recurrenceLabel(recurrence: string): string {
  if (recurrence === "none") return "Una vez";
  if (recurrence in RECURRENCE_LABELS) return RECURRENCE_LABELS[recurrence];
  const parsed = parseCustomRecurrence(recurrence);
  if (parsed) {
    const unit = CUSTOM_RECURRENCE_UNITS.find((u) => u.value === parsed.unit);
    return `${parsed.amount} ${unit?.label ?? parsed.unit}`;
  }
  return recurrence;
}

export function recurrenceRank(recurrence: string): number {
  if (recurrence === "none") return 0;
  if (recurrence in RECURRENCE_HOURS) return RECURRENCE_HOURS[recurrence];
  const parsed = parseCustomRecurrence(recurrence);
  if (parsed) return parsed.amount * RECURRENCE_HOURS[parsed.unit];
  return Infinity;
}
