<script setup>
import { computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "./stores/auth";
import ConfirmDialog from "./components/ConfirmDialog.vue";
import NotificationBell from "./components/NotificationBell.vue";

const authStore = useAuthStore();
const router = useRouter();

const peutAuditer = computed(() =>
  ["auditeur", "administrateur"].includes(authStore.utilisateur?.role)
);

const peutVoirRapports = computed(() =>
  [
    "chef_mission",
    "administrateur",
    "responsable_hierarchique",
    "auditeur",
  ].includes(authStore.utilisateur?.role)
);

const peutVoirService = computed(() =>
  ["responsable_hierarchique", "administrateur"].includes(
    authStore.utilisateur?.role
  )
);

const estAdmin = computed(
  () => authStore.utilisateur?.role === "administrateur"
);

function seDeconnecter() {
  authStore.deconnexion();
  router.push({ name: "login" });
}

// Après un rafraîchissement de page, le store est vide : on recharge le profil
// pour que le lien « Audit » apparaisse selon le rôle.
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
  <header class="topbar">
    <div class="container topbar-inner">
      <RouterLink to="/" class="logo">
        <span class="logo-mark">a</span>
        Plateforme MID
      </RouterLink>
      <nav v-if="authStore.estConnecte" class="nav">
        <RouterLink to="/dashboard">Tableau de bord</RouterLink>
        <RouterLink to="/missions">Missions</RouterLink>
        <RouterLink v-if="peutVoirRapports" to="/rapports">Rapports</RouterLink>
        <RouterLink v-if="peutVoirService" to="/service"
          >Mon service</RouterLink
        >
        <RouterLink v-if="peutAuditer" to="/audit">Audit</RouterLink>
        <RouterLink v-if="estAdmin" to="/admin/utilisateurs"
          >Comptes</RouterLink
        >
        <RouterLink v-if="estAdmin" to="/admin/referentiels"
          >Référentiels</RouterLink
        >
        <RouterLink to="/compte">Mon compte</RouterLink>
        <NotificationBell />
        <button class="btn btn-outline btn-sm" @click="seDeconnecter">
          Déconnexion
        </button>
      </nav>
    </div>
  </header>

  <RouterView />
  <ConfirmDialog />

  <footer class="footer">
    <div class="container">
      <span>© 2026 Plateforme MID</span>
      <span>Gestion des missions et audit comportemental</span>
    </div>
  </footer>
</template>
