export const COLORS = {
  // 🔴 Reds
  red:     { bg: "bg-red-50", text: "text-red-700", solid: "#ef4444", ring: "ring-red-100" },
  rose:    { bg: "bg-rose-50", text: "text-rose-700", solid: "#f43f5e", ring: "ring-rose-100" },
  // 🌸 Pinks
  pink:    { bg: "bg-pink-50", text: "text-pink-700", solid: "#e18ac1", ring: "ring-pink-100" },
  fuchsia: { bg: "bg-fuchsia-50", text: "text-fuchsia-700", solid: "#d946ef", ring: "ring-fuchsia-100" },
  // 🟣 Purples
  purple:  { bg: "bg-purple-50", text: "text-purple-700", solid: "#a855f7", ring: "ring-purple-100" },
  violet:  { bg: "bg-violet-50", text: "text-violet-700", solid: "#8b5cf6", ring: "ring-violet-100" },
  indigo:  { bg: "bg-indigo-50", text: "text-indigo-700", solid: "#6366f1", ring: "ring-indigo-100" },
  // 🔵 Blues
  blue:    { bg: "bg-blue-50", text: "text-blue-700", solid: "#7ba6dd", ring: "ring-blue-100" },
  sky:     { bg: "bg-sky-50", text: "text-sky-700", solid: "#0ea5e9", ring: "ring-sky-100" },
  cyan:    { bg: "bg-cyan-50", text: "text-cyan-700", solid: "#06b6d4", ring: "ring-cyan-100" },
  // 🟢 Greens
  teal:    { bg: "bg-teal-50", text: "text-teal-700", solid: "#14b8a6", ring: "ring-teal-100" },
  emerald: { bg: "bg-emerald-50", text: "text-emerald-700", solid: "#10b981", ring: "ring-emerald-100" },
  green:   { bg: "bg-green-50", text: "text-green-700", solid: "#22c55e", ring: "ring-green-100" },
  lime:    { bg: "bg-lime-50", text: "text-lime-700", solid: "#84cc16", ring: "ring-lime-100" },
  // 🟡 Yellows
  yellow:  { bg: "bg-yellow-50", text: "text-yellow-700", solid: "#eab308", ring: "ring-yellow-100" },
  amber:   { bg: "bg-amber-50", text: "text-amber-700", solid: "#f59e0b", ring: "ring-amber-100" },
  // 🟠 Oranges
  orange:  { bg: "bg-orange-50", text: "text-orange-700", solid: "#f97316", ring: "ring-orange-100" },
  // ⚪ Neutral
  stone:   { bg: "bg-stone-50", text: "text-stone-700", solid: "#78716c", ring: "ring-stone-100" },
  neutral: { bg: "bg-neutral-50", text: "text-neutral-700", solid: "#737373", ring: "ring-neutral-100" },
  zinc:    { bg: "bg-zinc-50", text: "text-zinc-700", solid: "#71717a", ring: "ring-zinc-100" },
  gray:    { bg: "bg-gray-50", text: "text-gray-700", solid: "#6b7280", ring: "ring-gray-100" },
  slate:   { bg: "bg-slate-50", text: "text-slate-700", solid: "#94a3b8", ring: "ring-slate-200" },
} as const;

export type ColorName = keyof typeof COLORS;

const USER_COLORS = [
  "blue", "pink", "purple", "cyan",
  "green", "yellow", "rose"
] as const satisfies readonly ColorName[];

const TAG_COLORS = [
  "fuchsia", "violet", "indigo", "sky",
  "teal", "lime", "orange"
] as const satisfies readonly ColorName[];

export interface Color {
  bg: string;
  text: string;
  solid: string;
  ring: string;
}

function pick(palette: readonly ColorName[], index: number): Color {
  return COLORS[palette[((index % palette.length) + palette.length) % palette.length]];
}

export function colorsByUser(users: Array<{ id: number }>): Record<number, Color> {
  const map: Record<number, Color> = {};
  users.forEach((user) => {
    map[user.id] = pick(USER_COLORS, user.id - 1);
  });
  return new Proxy(map, {
    get: (target, prop) =>
      Object.prototype.hasOwnProperty.call(target, prop)
        ? target[Number(prop)]
        : COLORS.neutral,
  });
}

function hash(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  return Math.abs(hash);
}

export function color(str: string | null | undefined): Color {
  if (!str) return COLORS.neutral;
  const name = str.toLowerCase();
  if (Object.prototype.hasOwnProperty.call(COLORS, name)) {
    return (COLORS as Record<string, Color>)[name];
  }
  return pick(TAG_COLORS, hash(name));
}
