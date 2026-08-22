export function valueOrNull<T>(value: T | ""): T | null {
  return value === "" ? null : value;
}
