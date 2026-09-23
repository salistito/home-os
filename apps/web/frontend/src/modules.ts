import type { Component } from "vue";
import { icons } from "./lib/icons";
import FinanceModule from "./modules/finances/FinanceModule.vue";
import FitnessModule from "./modules/fitness/FitnessModule.vue";
import FoodModule from "./modules/food/FoodModule.vue";
import RemindersModule from "./modules/reminders/RemindersModule.vue";
import TasksModule from "./modules/tasks/TasksModule.vue";
import UsersModule from "./modules/users/UsersModule.vue";

export const MODULE_IDS = ["tasks", "finances", "food", "fitness", "reminders", "users"] as const;

export type ModuleId = (typeof MODULE_IDS)[number];

export interface ModuleDef {
  id: ModuleId;
  label: string;
  icon: string;
  component: Component;
  requiresAdmin?: boolean;
  canBeInBreak?: boolean;
}

export const modules: ModuleDef[] = [
  { id: "tasks", label: "Tareas", icon: icons.checkSquare, component: TasksModule, canBeInBreak: true },
  { id: "finances", label: "Finanzas", icon: icons.wallet, component: FinanceModule, canBeInBreak: true },
  { id: "food", label: "Comida", icon: icons.utensils, component: FoodModule, canBeInBreak: true },
  { id: "fitness", label: "Fitness", icon: icons.bicepsFlexed, component: FitnessModule, canBeInBreak: true },
  { id: "reminders", label: "Recordatorios", icon: icons.bell, component: RemindersModule, canBeInBreak: true },
  { id: "users", label: "Usuarios", icon: icons.users, component: UsersModule, requiresAdmin: true },
];

export interface ModuleOption {
  value: ModuleId;
  label: string;
  icon: string;
}
