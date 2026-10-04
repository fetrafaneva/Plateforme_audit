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
    <div class="carte-auth">
      <h1>Créer un compte</h1>
      <p class="sous-titre">Plateforme d'audit — MID</p>

      <form @submit.prevent="creerCompte">
        <label for="nom">Nom</label>
        <input id="nom" v-model="nom" required />

        <label for="prenom">Prénom</label>
        <input id="prenom" v-model="prenom" required />

        <label for="email">Email</label>
        <input id="email" v-model="email" type="email" required />

        <label for="matricule">Matricule</label>
        <input id="matricule" v-model="matricule" required />

        <label for="mdp">Mot de passe</label>
        <input
          id="mdp"
          v-model="motDePasse"
          type="password"
          required
          minlength="8"
        />

        <label for="service">ID service</label>
        <input
          id="service"
          v-model="idService"
          type="number"
          min="1"
          required
        />

        <label for="role">ID rôle</label>
        <input id="role" v-model="idRole" type="number" min="1" required />

        <p v-if="erreur" class="message-erreur">{{ erreur }}</p>
        <p v-if="succes" class="message-succes">Compte créé — redirection...</p>

        <button type="submit" :disabled="chargement">
          {{ chargement ? "Création..." : "Créer le compte" }}
        </button>
      </form>

      <router-link to="/login" class="lien-secondaire"
        >Déjà un compte ? Se connecter</router-link
      >
    </div>
  </div>
</template>
