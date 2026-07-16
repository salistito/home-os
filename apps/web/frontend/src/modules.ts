import type { Component } from "vue";
import TasksModule from "./modules/tasks/TasksModule.vue";
import RemindersModule from "./modules/reminders/RemindersModule.vue";
import { icons } from "./lib/icons";

export interface ModuleDef {
  id: string;
  label: string;
  icon: string;
  component: Component;
}

export const modules: ModuleDef[] = [
  { id: "tasks", label: "Tareas", icon: icons.list, component: TasksModule },
  { id: "reminders", label: "Recordatorios", icon: icons.bell, component: RemindersModule },
];
