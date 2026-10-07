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
    <header class="bandeau">
      <h1>Plateforme d'audit</h1>
      <p class="sous-titre">
        Ministère de l'Intérieur et de la Décentralisation
      </p>
    </header>

    <div class="carte-auth">
      <h2>Connexion</h2>

      <form @submit.prevent="seConnecter">
        <div class="field">
          <label for="email">Email</label>
          <input
            id="email"
            v-model="email"
            type="email"
            required
            autocomplete="username"
          />
        </div>

        <div class="field">
          <label for="mdp">Mot de passe</label>
          <input
            id="mdp"
            v-model="motDePasse"
            type="password"
            required
            autocomplete="current-password"
          />
        </div>

        <p v-if="erreur" class="alert-error">{{ erreur }}</p>

        <button
          type="submit"
          class="btn btn-primary bouton-plein"
          :disabled="chargement"
        >
          {{ chargement ? "Connexion..." : "Se connecter" }}
        </button>
      </form>

      <router-link to="/register" class="lien-secondaire">
        Pas encore de compte ? Créer un compte
      </router-link>
    </div>
  </div>
</template>

<style scoped>
.page-auth {
  flex: 1;
}

.bandeau {
  background: var(--grad);
  color: #fff;
  text-align: center;
  padding: 3.5rem 1rem 6rem;
  border-radius: 0 0 0 80px;
}

.bandeau h1 {
  margin-bottom: 0.4rem;
}

.sous-titre {
  margin: 0;
  opacity: 0.92;
}

.carte-auth {
  width: min(440px, 92%);
  margin: -3.5rem auto 3rem;
  padding: 2rem;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  text-align: center;
}

.carte-auth h2 {
  margin-bottom: 1.5rem;
}

.field {
  text-align: left;
}

.bouton-plein {
  width: 100%;
  margin-top: 0.5rem;
}

.bouton-plein:disabled {
  opacity: 0.6;
  cursor: wait;
  transform: none;
}

.lien-secondaire {
  display: inline-block;
  margin-top: 1.5rem;
  font-size: 0.9rem;
}
</style>
