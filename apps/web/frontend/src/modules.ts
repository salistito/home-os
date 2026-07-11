import type { Component } from "vue";
import TasksModule from "./modules/tasks/TasksModule.vue";
import { icons } from "./lib/icons";

export interface ModuleDef {
  id: string;
  label: string;
  icon: string;
  component: Component;
}

export const modules: ModuleDef[] = [
  { id: "tasks", label: "Tareas", icon: icons.list, component: TasksModule },
];
