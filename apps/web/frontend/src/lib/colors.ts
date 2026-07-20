export interface UserColor {
  bg: string;
  text: string;
  solid: string;
}

const PALETTE: UserColor[] = [
  { bg: "bg-[#f6dcec]", text: "text-[#a83a80]", solid: "#e18ac1" },
  { bg: "bg-[#dbe6f5]", text: "text-[#35608f]", solid: "#7ba6dd" },
];

export function colorsByUser(ids: Array<string | number>): Record<string, UserColor> {
  const map: Record<string, UserColor> = {};
  [...new Set(ids.map(String))].sort().forEach((id, i) => {
    map[id] = PALETTE[i % PALETTE.length];
  });
  return map;
}

export interface TagColor {
  bg: string;
  text: string;
}

const TAG_PALETTE: Record<string, TagColor> = {
  rose: { bg: "bg-rose-100", text: "text-rose-700" },
  orange: { bg: "bg-orange-100", text: "text-orange-700" },
  amber: { bg: "bg-amber-100", text: "text-amber-700" },
  emerald: { bg: "bg-emerald-100", text: "text-emerald-700" },
  teal: { bg: "bg-teal-100", text: "text-teal-700" },
  sky: { bg: "bg-sky-100", text: "text-sky-700" },
  violet: { bg: "bg-violet-100", text: "text-violet-700" },
  pink: { bg: "bg-pink-100", text: "text-pink-700" },
};

const NEUTRAL_TAG: TagColor = { bg: "bg-slate-100", text: "text-slate-500" };

export function tagColor(key: string): TagColor {
  return TAG_PALETTE[key] ?? NEUTRAL_TAG;
}
