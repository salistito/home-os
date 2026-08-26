import { parseYearMonth } from "./date";

export const MONTHS = [
  "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
];

export const WEEKDAYS = [
  "Domingo", "Lunes", "Martes", "Miércoles",
  "Jueves", "Viernes", "Sábado"
];

export const WEEKDAYS_SHORT = ["Dom", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"];

export function formatDate(iso: string): string {
  const [year, month, day] = iso.split("-");
  return `${day}/${month}/${year}`;
}

export function formatDateShort(iso: string): string {
  const [, month, day] = iso.split("-");
  return `${day}/${month}`;
}

export function formatDateYear(iso: string): string {
  const [year, month, day] = iso.split("-");
  return `${day}/${month}/${year.slice(2)}`;
}

export function formatMonth(monthIndex: number): string {
  return MONTHS[monthIndex];
}

export function formatYearMonth(yearMonth: string): string {
  const { year, month } = parseYearMonth(yearMonth);
  return `${MONTHS[month]} ${year}`;
}

export function formatWeekdayAndDay(iso: string): string {
  const [year, month, day] = iso.split("-").map(Number);
  const weekday = WEEKDAYS[new Date(year, month - 1, day).getDay()];
  return `${weekday} ${day}`;
}

export function formatWeekdayAndDayShort(iso: string): string {
  const [year, month, day] = iso.split("-").map(Number);
  const weekdayShort = WEEKDAYS_SHORT[new Date(year, month - 1, day).getDay()];
  return `${weekdayShort} ${day}`;
}

export function formatWeekdayShort(iso: string): string {
  const [year, month, day] = iso.split("-").map(Number);
  const weekdayShort = WEEKDAYS_SHORT[new Date(year, month - 1, day).getDay()];
  return weekdayShort;
}

export function capitalize(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

export function capitalizeAll(str: string): string {
  return str.split(" ").map(capitalize).join(" ");
}
