<script setup>
import { onMounted } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";

const authStore = useAuthStore();
const router = useRouter();

onMounted(() => {
  if (!authStore.utilisateur) {
    authStore.chargerUtilisateur();
  }
});

function seDeconnecter() {
  authStore.deconnexion();
  router.push({ name: "login" });
}
</script>

<template>
  <div class="page-dashboard">
    <header class="entete">
      <h1>Tableau de bord</h1>
      <button class="bouton-discret" @click="seDeconnecter">Déconnexion</button>
    </header>

    <section v-if="authStore.utilisateur" class="carte-info">
      <p>
        Connectée en tant que
        <strong
          >{{ authStore.utilisateur.prenom }}
          {{ authStore.utilisateur.nom }}</strong
        >
      </p>
      <p class="detail">
        {{ authStore.utilisateur.email }} — matricule
        {{ authStore.utilisateur.matricule }}
      </p>
    </section>
  </div>
</template>
