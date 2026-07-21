const MONTHS = [
  "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
];

const MONTHS_SHORT = [
  "Ene", "Feb", "Mar", "Abr", "May", "Jun",
  "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"
];

const WEEKDAYS = [
  "Domingo", "Lunes", "Martes", "Miércoles",
  "Jueves", "Viernes", "Sábado"
];

const WEEKDAYS_SHORT = ["Dom", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"];

export function formatDate(iso: string): string {
  const [, month, day] = iso.split("-").map(Number);
  return `${day} ${MONTHS[month - 1]}`;
}

export function formatDateShort(iso: string): string {
  const [, month, day] = iso.split("-").map(Number);
  const monthShort = MONTHS_SHORT[month - 1]
  return `${day} ${monthShort}`;
}

export function formatMonth(monthIndex: number): string {
  return MONTHS[monthIndex];
}

export function formatWeekday(iso: string): string {
  const [year, month, day] = iso.split("-").map(Number);
  const weekday = WEEKDAYS[new Date(year, month - 1, day).getDay()];
  return `${weekday} ${day}`;
}

export function formatWeekdayDayShort(iso: string): string {
  const [year, month, day] = iso.split("-").map(Number);
  const weekdayShort = WEEKDAYS_SHORT[new Date(year, month - 1, day).getDay()];
  return `${weekdayShort} ${day}`;
}

export function formatMoney(amount: number): string {
  return `$${amount.toLocaleString("es-CL")}`;
}
