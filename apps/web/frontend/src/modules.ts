import type { Component } from "vue";
import { icons } from "./lib/icons";
import FinanceModule from "./modules/finances/FinanceModule.vue";
import FitnessModule from "./modules/fitness/FitnessModule.vue";
import FoodModule from "./modules/food/FoodModule.vue";
import RemindersModule from "./modules/reminders/RemindersModule.vue";
import TasksModule from "./modules/tasks/TasksModule.vue";
import UsersModule from "./modules/users/UsersModule.vue";

export interface ModuleDef {
  id: string;
  label: string;
  icon: string;
  component: Component;
  requiresAdmin?: boolean;
}

export const modules: ModuleDef[] = [
  {
    id: "tasks",
    label: "Tareas",
    icon: icons.checkSquare,
    component: TasksModule,
  },
  {
    id: "finances",
    label: "Finanzas",
    icon: icons.wallet,
    component: FinanceModule,
  },
  { id: "food", label: "Comida", icon: icons.utensils, component: FoodModule },
  {
    id: "fitness",
    label: "Fitness",
    icon: icons.dumbbell,
    component: FitnessModule,
  },
  {
    id: "reminders",
    label: "Recordatorios",
    icon: icons.bell,
    component: RemindersModule,
  },
  {
    id: "users",
    label: "Usuarios",
    icon: icons.users,
    component: UsersModule,
    requiresAdmin: true,
  },
];
