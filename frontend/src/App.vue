<script setup>
import { useRouter } from "vue-router";
import { useAuthStore } from "./stores/auth";

const authStore = useAuthStore();
const router = useRouter();

function seDeconnecter() {
  authStore.deconnexion();
  router.push({ name: "login" });
}
</script>

<template>
  <header class="topbar">
    <div class="container topbar-inner">
      <RouterLink to="/" class="logo">
        <span class="logo-mark">a</span>
        Plateforme MID
      </RouterLink>
      <nav v-if="authStore.estConnecte" class="nav">
        <RouterLink to="/dashboard">Tableau de bord</RouterLink>
        <RouterLink to="/missions">Missions</RouterLink>
        <button class="btn btn-outline btn-sm" @click="seDeconnecter">
          Déconnexion
        </button>
      </nav>
    </div>
  </header>

  <RouterView />

  <footer class="footer">
    <div class="container">
      <span>© 2026 Plateforme MID</span>
      <span>Gestion des missions et audit comportemental</span>
    </div>
  </footer>
</template>
