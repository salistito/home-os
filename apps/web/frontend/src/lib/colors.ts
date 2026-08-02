export const COLORS = {
  // 🔴 Reds
  red:     { bg: "bg-red-50",     text: "text-red-700",     solid: "#ef4444" },
  rose:    { bg: "bg-rose-50",    text: "text-rose-700",    solid: "#f43f5e" },
  // 🌸 Pinks
  pink:    { bg: "bg-pink-50",    text: "text-pink-700",    solid: "#e18ac1" },
  fuchsia: { bg: "bg-fuchsia-50", text: "text-fuchsia-700", solid: "#d946ef" },
  // 🟣 Purples
  purple:  { bg: "bg-purple-50",  text: "text-purple-700",  solid: "#a855f7" },
  violet:  { bg: "bg-violet-50",  text: "text-violet-700",  solid: "#8b5cf6" },
  indigo:  { bg: "bg-indigo-50",  text: "text-indigo-700",  solid: "#6366f1" },
  // 🔵 Blues
  blue:    { bg: "bg-blue-50",    text: "text-blue-700",    solid: "#7ba6dd" },
  sky:     { bg: "bg-sky-50",     text: "text-sky-700",     solid: "#0ea5e9" },
  cyan:    { bg: "bg-cyan-50",    text: "text-cyan-700",    solid: "#06b6d4" },
  // 🟢 Greens
  teal:    { bg: "bg-teal-50",    text: "text-teal-700",    solid: "#14b8a6" },
  emerald: { bg: "bg-emerald-50", text: "text-emerald-700", solid: "#10b981" },
  green:   { bg: "bg-green-50",   text: "text-green-700",   solid: "#22c55e" },
  lime:    { bg: "bg-lime-50",    text: "text-lime-700",    solid: "#84cc16" },
  // 🟡 Yellows
  yellow:  { bg: "bg-yellow-50",  text: "text-yellow-700",  solid: "#eab308" },
  amber:   { bg: "bg-amber-50",   text: "text-amber-700",   solid: "#f59e0b" },
  // 🟠 Oranges
  orange:  { bg: "bg-orange-50",  text: "text-orange-700",  solid: "#f97316" },
  // ⚪ Neutral
  stone:   { bg: "bg-stone-50",   text: "text-stone-700",   solid: "#78716c" },
  neutral: { bg: "bg-neutral-50", text: "text-neutral-700", solid: "#737373" },
  zinc:    { bg: "bg-zinc-50",    text: "text-zinc-700",    solid: "#71717a" },
  gray:    { bg: "bg-gray-50",    text: "text-gray-700",    solid: "#6b7280" },
  slate:   { bg: "bg-slate-50",   text: "text-slate-700",   solid: "#94a3b8" },
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
  return new Proxy(map, {
    get: (target, prop) =>
      Object.prototype.hasOwnProperty.call(target, prop)
        ? target[Number(prop)]
        : {
            bg: COLORS.neutral.bg,
            text: COLORS.neutral.text,
            solid: COLORS.neutral.solid,
        }
  });
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

export function tagColorByString(str: string | null): TagColor {
  if (!str) return { bg: COLORS.neutral.bg, text: COLORS.neutral.text };
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  const name = TAG_COLORS[Math.abs(hash) % TAG_COLORS.length];
  return { bg: COLORS[name].bg, text: COLORS[name].text };
}
