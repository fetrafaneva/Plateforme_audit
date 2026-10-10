import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "../stores/auth";
import LoginView from "../views/LoginView.vue";
import RegisterView from "../views/RegisterView.vue";
import DashboardView from "../views/DashboardView.vue";
import MissionsView from "../views/MissionsView.vue";
import MissionDetailView from "../views/MissionDetailView.vue";
import AuditView from "../views/AuditView.vue";

const routes = [
  { path: "/", redirect: "/dashboard" },
  { path: "/login", name: "login", component: LoginView },
  { path: "/register", name: "register", component: RegisterView },
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
  {
    path: "/audit",
    name: "audit",
    component: AuditView,
    meta: { requiresAuth: true, roles: ["auditeur", "administrateur"] },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach(async (to) => {
  const authStore = useAuthStore();

  if (to.meta.requiresAuth && !authStore.estConnecte) {
    return { name: "login" };
  }

  // Pages réservées à certains rôles : on charge l'utilisateur si besoin
  // (cas d'un rafraîchissement de page, où le store est vide).
  if (to.meta.roles) {
    if (!authStore.utilisateur) {
      try {
        await authStore.chargerUtilisateur();
      } catch {
        return { name: "login" };
      }
    }
    if (!to.meta.roles.includes(authStore.utilisateur?.role)) {
      return { name: "dashboard" };
    }
  }
});

export default router;
