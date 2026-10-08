<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import api from "../services/api";

const nom = ref("");
const prenom = ref("");
const email = ref("");
const matricule = ref("");
const motDePasse = ref("");
const idService = ref(1);
const idRole = ref(1);
const erreur = ref("");
const succes = ref(false);
const chargement = ref(false);

const router = useRouter();

async function creerCompte() {
  erreur.value = "";
  chargement.value = true;
  try {
    await api.post("/auth/register", {
      nom: nom.value,
      prenom: prenom.value,
      email: email.value,
      matricule: matricule.value,
      mot_de_passe: motDePasse.value,
      id_service: Number(idService.value),
      id_role: Number(idRole.value),
    });
    succes.value = true;
    setTimeout(() => router.push({ name: "login" }), 1200);
  } catch (e) {
    erreur.value = e.response?.data?.detail || "Impossible de créer le compte.";
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
      <h2>Créer un compte</h2>

      <form @submit.prevent="creerCompte">
        <div class="ligne">
          <div class="field">
            <label for="nom">Nom</label>
            <input id="nom" v-model="nom" required />
          </div>
          <div class="field">
            <label for="prenom">Prénom</label>
            <input id="prenom" v-model="prenom" required />
          </div>
        </div>

        <div class="field">
          <label for="email">Email</label>
          <input id="email" v-model="email" type="email" required />
        </div>

        <div class="field">
          <label for="matricule">Matricule</label>
          <input id="matricule" v-model="matricule" required />
        </div>

        <div class="field">
          <label for="mdp">Mot de passe</label>
          <input
            id="mdp"
            v-model="motDePasse"
            type="password"
            required
            minlength="8"
            autocomplete="new-password"
          />
        </div>

        <div class="ligne">
          <div class="field">
            <label for="service">ID service</label>
            <input
              id="service"
              v-model="idService"
              type="number"
              min="1"
              required
            />
          </div>
          <div class="field">
            <label for="role">ID rôle</label>
            <input id="role" v-model="idRole" type="number" min="1" required />
          </div>
        </div>

        <p v-if="erreur" class="alert-error">{{ erreur }}</p>
        <p v-if="succes" class="alert-succes">Compte créé, redirection...</p>

        <button
          type="submit"
          class="btn btn-primary bouton-plein"
          :disabled="chargement"
        >
          {{ chargement ? "Création..." : "Créer le compte" }}
        </button>
      </form>

      <router-link to="/login" class="lien-secondaire">
        Déjà un compte ? Se connecter
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
  width: min(520px, 92%);
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

.ligne {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

@media (max-width: 520px) {
  .ligne {
    grid-template-columns: 1fr;
    gap: 0;
  }
}

.alert-succes {
  background: #d5faf5;
  color: #067a6f;
  border: 1px solid #a8efe6;
  padding: 0.75rem 1rem;
  border-radius: 14px;
  margin-bottom: 1rem;
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
