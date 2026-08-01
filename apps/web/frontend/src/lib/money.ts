import { computed, ref } from "vue";

const MONEY_LOCALE = "es-CL";
const MONEY_HIDDEN_KEY = "money_hidden";

const moneyHidden = ref(getMoneyHidden());
export const moneyHiddenValue = computed(() => moneyHidden.value);

function getMoneyHidden(): boolean {
  try {
    return localStorage.getItem(MONEY_HIDDEN_KEY) === "1";
  } catch {
    return false;
  }
}

export function toggleMoneyHidden(): void {
  moneyHidden.value = !moneyHidden.value;
  try {
    localStorage.setItem(MONEY_HIDDEN_KEY, moneyHidden.value ? "1" : "0");
  } catch {
    // ignore
  }
}

export function formatAmountInput(value: number): string {
  return value ? value.toLocaleString(MONEY_LOCALE) : "";
}

export function formatMoney(amount: number): string {
  if (moneyHidden.value) return "•••••";
  return `$${amount.toLocaleString(MONEY_LOCALE)}`;
}
