export const COLORS = {
  // 🔴 Reds
  red:     { bg: "bg-red-100",     text: "text-red-700",     solid: "#ef4444" },
  rose:    { bg: "bg-rose-100",    text: "text-rose-700",    solid: "#f43f5e" },
  // 🌸 Pinks
  pink:    { bg: "bg-pink-100",    text: "text-pink-700",    solid: "#ec4899" },
  fuchsia: { bg: "bg-fuchsia-100", text: "text-fuchsia-700", solid: "#d946ef" },
  // 🟣 Purples
  purple:  { bg: "bg-purple-100",  text: "text-purple-700",  solid: "#a855f7" },
  violet:  { bg: "bg-violet-100",  text: "text-violet-700",  solid: "#8b5cf6" },
  indigo:  { bg: "bg-indigo-100",  text: "text-indigo-700",  solid: "#6366f1" },
  // 🔵 Blues
  blue:    { bg: "bg-blue-100",    text: "text-blue-700",    solid: "#3b82f6" },
  sky:     { bg: "bg-sky-100",     text: "text-sky-700",     solid: "#0ea5e9" },
  cyan:    { bg: "bg-cyan-100",    text: "text-cyan-700",    solid: "#06b6d4" },
  // 🟢 Greens
  teal:    { bg: "bg-teal-100",    text: "text-teal-700",    solid: "#14b8a6" },
  emerald: { bg: "bg-emerald-100", text: "text-emerald-700", solid: "#10b981" },
  green:   { bg: "bg-green-100",   text: "text-green-700",   solid: "#22c55e" },
  lime:    { bg: "bg-lime-100",    text: "text-lime-700",    solid: "#84cc16" },
  // 🟡 Yellows
  yellow:  { bg: "bg-yellow-100",  text: "text-yellow-700",  solid: "#eab308" },
  amber:   { bg: "bg-amber-100",   text: "text-amber-700",   solid: "#f59e0b" },
  // 🟠 Oranges
  orange:  { bg: "bg-orange-100",  text: "text-orange-700",  solid: "#f97316" },
  // ⚪ Neutral
  stone:   { bg: "bg-stone-100",   text: "text-stone-700",   solid: "#78716c" },
  neutral: { bg: "bg-neutral-100", text: "text-neutral-700", solid: "#737373" },
  zinc:    { bg: "bg-zinc-100",    text: "text-zinc-700",    solid: "#71717a" },
  gray:    { bg: "bg-gray-100",    text: "text-gray-700",    solid: "#6b7280" },
  slate:   { bg: "bg-slate-100",   text: "text-slate-700",   solid: "#94a3b8" },
} as const;

const USER_COLORS = [
  "blue", "pink", "emerald", "orange", "purple",
  "red", "cyan", "amber", "indigo", "lime"
] as const;

const TAG_COLORS = [
  "rose", "fuchsia", "violet", "sky",
  "teal", "green", "yellow", "slate"
] as const;

export interface UserColor {
  bg: string;
  text: string;
  solid: string;
}

const USER_PALETTE: UserColor[] = USER_COLORS.map((name) => COLORS[name]);

export function colorsByUser(users: Array<{ id: number }>): Record<number, UserColor> {
  const map: Record<number, UserColor> = {};
  users.forEach((user) => {
    map[user.id] = USER_PALETTE[(user.id - 1) % USER_PALETTE.length];
  });
  return map;
}

export interface TagColor {
  bg: string;
  text: string;
}

const TAG_PALETTE: Record<string, TagColor> = Object.fromEntries(                                                                                  
  TAG_COLORS.map((name) => [name, { bg: COLORS[name].bg, text: COLORS[name].text }])                                                               
); 

export function tagColor(key: string): TagColor {
  return TAG_PALETTE[key.toLowerCase()] ?? { bg: COLORS.neutral.bg, text: COLORS.neutral.text };
}
