export interface UserColor {
  bg: string;
  text: string;
  solid: string;
}

const PALETTE: UserColor[] = [
  { bg: "bg-[#f6dcec]", text: "text-[#a83a80]", solid: "#e18ac1" },
  { bg: "bg-[#dbe6f5]", text: "text-[#35608f]", solid: "#7ba6dd" },
];

export function colorsByUser(ids: string[]): Record<string, UserColor> {
  const map: Record<string, UserColor> = {};
  [...new Set(ids)].sort().forEach((id, i) => {
    map[id] = PALETTE[i % PALETTE.length];
  });
  return map;
}
