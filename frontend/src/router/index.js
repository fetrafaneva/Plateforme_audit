import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "../stores/auth";
import LoginView from "../views/LoginView.vue";
import RegisterView from "../views/RegisterView.vue";
import DashboardView from "../views/DashboardView.vue";
import MissionsView from "../views/MissionsView.vue";
import MissionDetailView from "../views/MissionDetailView.vue";

const routes = [
  { path: "/", redirect: "/dashboard" },
  { path: "/login", name: "login", component: LoginView },
  {
    path: "/register",
    name: "register",
    component: RegisterView,
    meta: { requiresAuth: true },
  },
  {
    path: "/dashboard",
    name: "dashboard",
    component: DashboardView,
    meta: { requiresAuth: true },
  },
  {
    path: "/missions",
    name: "missions",
    component: MissionsView,
    meta: { requiresAuth: true },
  },
  {
    path: "/missions/:id",
    name: "mission-detail",
    component: MissionDetailView,
    meta: { requiresAuth: true },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to) => {
  const authStore = useAuthStore();
  if (to.meta.requiresAuth && !authStore.estConnecte) {
    return { name: "login" };
  }
});

export default router;
