import type { Component } from "vue";
import { icons } from "./lib/icons";
import FinanceModule from "./modules/finances/FinanceModule.vue";
import FitnessModule from "./modules/fitness/FitnessModule.vue";
import FoodModule from "./modules/food/FoodModule.vue";
import RemindersModule from "./modules/reminders/RemindersModule.vue";
import TasksModule from "./modules/tasks/TasksModule.vue";
import UsersModule from "./modules/users/UsersModule.vue";

export type ModuleId = "tasks" | "finances" | "food" | "fitness" | "reminders" | "users";

export interface ModuleDef {
  id: ModuleId;
  label: string;
  icon: string;
  component: Component;
  canBeInBreak?: boolean;
  requiresAdmin?: boolean;
}

export const modules: ModuleDef[] = [
  { id: "tasks", label: "Tareas", icon: icons.checkSquare, component: TasksModule, canBeInBreak: true, requiresAdmin: false },
  { id: "finances", label: "Finanzas", icon: icons.wallet, component: FinanceModule, canBeInBreak: false, requiresAdmin: false },
  { id: "food", label: "Comida", icon: icons.utensils, component: FoodModule, canBeInBreak: true, requiresAdmin: false },
  { id: "fitness", label: "Fitness", icon: icons.bicepsFlexed, component: FitnessModule, canBeInBreak: true, requiresAdmin: false },
  { id: "reminders", label: "Recordatorios", icon: icons.bell, component: RemindersModule, canBeInBreak: false, requiresAdmin: false },
  { id: "users", label: "Usuarios", icon: icons.users, component: UsersModule, canBeInBreak: false, requiresAdmin: true },
];

export const breakModules: ModuleDef[] = modules.filter((m) => m.canBeInBreak === true);

export function moduleLabel(id: string): string {
  return modules.find((m) => m.id === id)?.label ?? id;
}

export function moduleIcon(id: string): string {
  return modules.find((m) => m.id === id)?.icon ?? "";
}
