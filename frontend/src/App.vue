<script setup>
import { onMounted } from "vue";
import { useAuthStore } from "./stores/auth";
import BarreNavigation from "./components/BarreNavigation.vue";
import ConfirmDialog from "./components/ConfirmDialog.vue";

const authStore = useAuthStore();

// Après un rafraîchissement de page, le store est vide : on recharge le profil pour que
// la barre de navigation affiche les liens du bon rôle.
onMounted(async () => {
  if (authStore.estConnecte && !authStore.utilisateur) {
    try {
      await authStore.chargerUtilisateur();
    } catch {
      /* l'intercepteur de api.js gère le 401 */
    }
  }
});
</script>

<template>
  <BarreNavigation />

  <RouterView />
  <ConfirmDialog />

  <footer class="footer">
    <div class="container">
      <span>© 2026 Plateforme MID</span>
      <span>Gestion des missions et audit comportemental</span>
    </div>
  </footer>
</template>
