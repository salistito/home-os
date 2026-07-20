import type { Component } from "vue";
import { icons } from "./lib/icons";
import TasksModule from "./modules/tasks/TasksModule.vue";
import FinanceModule from "./modules/finances/FinanceModule.vue";
import RemindersModule from "./modules/reminders/RemindersModule.vue";

export interface ModuleDef {
  id: string;
  label: string;
  icon: string;
  component: Component;
}

export const modules: ModuleDef[] = [
  { id: "tasks", label: "Tareas", icon: icons.list, component: TasksModule },
  { id: "finances", label: "Finanzas", icon: icons.wallet, component: FinanceModule },
  { id: "reminders", label: "Recordatorios", icon: icons.bell, component: RemindersModule },
];
