<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";

const email = ref("");
const motDePasse = ref("");
const erreur = ref("");
const chargement = ref(false);

const authStore = useAuthStore();
const router = useRouter();

async function seConnecter() {
  erreur.value = "";
  chargement.value = true;
  try {
    await authStore.login(email.value, motDePasse.value);
    router.push({ name: "dashboard" });
  } catch (e) {
    erreur.value = e.response?.data?.detail || "Identifiants incorrects.";
  } finally {
    chargement.value = false;
  }
}
</script>

<template>
  <div class="page-auth">
    <div class="carte-auth">
      <h1>Plateforme d'audit</h1>
      <p class="sous-titre">
        Ministère de l'Intérieur et de la Décentralisation
      </p>

      <form @submit.prevent="seConnecter">
        <label for="email">Email</label>
        <input
          id="email"
          v-model="email"
          type="email"
          required
          autocomplete="username"
        />

        <label for="mdp">Mot de passe</label>
        <input
          id="mdp"
          v-model="motDePasse"
          type="password"
          required
          autocomplete="current-password"
        />

        <p v-if="erreur" class="message-erreur">{{ erreur }}</p>

        <button type="submit" :disabled="chargement">
          {{ chargement ? "Connexion..." : "Se connecter" }}
        </button>
      </form>

      <router-link to="/register" class="lien-secondaire"
        >Créer un compte</router-link
      >
    </div>
  </div>
</template>
