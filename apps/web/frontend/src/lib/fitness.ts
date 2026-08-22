import type { ExerciseIntensity } from "../types";

export const INTENSITY_OPTIONS: { value: ExerciseIntensity; label: string }[] =
  [
    { value: "low", label: "Baja" },
    { value: "medium", label: "Media" },
    { value: "high", label: "Alta" },
  ];

export const INTENSITY_LABELS: Record<string, string> = {
  low: "Baja",
  medium: "Media",
  high: "Alta",
};

export const INTENSITY_STYLES: Record<string, string> = {
  low: "bg-slate-100 text-slate-600",
  medium: "bg-amber-50 text-amber-700",
  high: "bg-red-50 text-red-700",
};

export const EXERCISE_TYPE_SUGGESTIONS = [
  "correr",
  "gym",
  "bicicleta",
  "natación",
  "caminata",
  "fútbol",
  "yoga",
  "crossfit",
];

export function formatDelta(value: number | null): string {
  if (value === null || Number.isNaN(value)) return "—";
  const rounded = Math.round(value * 10) / 10;
  if (rounded === 0) return "0 kg";
  return `${rounded > 0 ? "+" : ""}${rounded} kg`;
}

export function formatWeight(value: number | null): string {
  if (value === null || Number.isNaN(value)) return "—";
  return `${Math.round(value * 10) / 10}`;
}
