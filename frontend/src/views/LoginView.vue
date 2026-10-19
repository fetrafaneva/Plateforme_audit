<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import ModalDialog from "../components/ModalDialog.vue";
import { demanderSansConnexion } from "../services/demandesMdp";

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
    // 401 : identifiants incorrects ; 429 : trop de tentatives (le message dit combien attendre)
    erreur.value = e.response?.data?.detail || "Identifiants incorrects.";
  } finally {
    chargement.value = false;
  }
}

// ---------- Demande de nouveau mot de passe (traitée par l'administrateur) ----------

const demandeOuverte = ref(false);
const demandeEmail = ref("");
const demandeMatricule = ref("");
const demandeMotif = ref("");
const demandeEnvoi = ref(false);
const demandeErreur = ref("");
const demandeAccuse = ref("");

function ouvrirDemande() {
  demandeEmail.value = email.value; // reprend l'adresse déjà saisie
  demandeMatricule.value = "";
  demandeMotif.value = "";
  demandeErreur.value = "";
  demandeAccuse.value = "";
  demandeOuverte.value = true;
}

async function envoyerDemande() {
  demandeErreur.value = "";
  demandeEnvoi.value = true;
  try {
    const reponse = await demanderSansConnexion({
      email: demandeEmail.value.trim(),
      matricule: demandeMatricule.value.trim(),
      motif: demandeMotif.value.trim() || null,
    });
    demandeAccuse.value = reponse.message;
  } catch (e) {
    const detail = e.response?.data?.detail;
    demandeErreur.value =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail) && detail.length
        ? detail.map((d) => d.msg).join(" ; ")
        : "L'envoi de la demande a échoué.";
  } finally {
    demandeEnvoi.value = false;
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

      <button type="button" class="lien-secondaire" @click="ouvrirDemande">
        Mot de passe oublié ou à changer ?
      </button>
    </div>

    <ModalDialog
      v-if="demandeOuverte"
      titre="Demander un nouveau mot de passe"
      @fermer="demandeOuverte = false"
    >
      <template v-if="demandeAccuse">
        <p class="accuse">{{ demandeAccuse }}</p>
        <div class="actions-modale">
          <button
            type="button"
            class="btn btn-primary btn-sm"
            @click="demandeOuverte = false"
          >
            Fermer
          </button>
        </div>
      </template>

      <form v-else @submit.prevent="envoyerDemande">
        <p class="muted">
          Le mot de passe est changé par l'administrateur, qui te le communique
          directement. Indique ton adresse et ton matricule pour qu'il puisse
          t'identifier.
        </p>
        <p v-if="demandeErreur" class="alert-error">{{ demandeErreur }}</p>
        <div class="field">
          <label for="d-email">Email</label>
          <input id="d-email" v-model="demandeEmail" type="email" required />
        </div>
        <div class="field">
          <label for="d-matricule">Matricule</label>
          <input
            id="d-matricule"
            v-model="demandeMatricule"
            required
            maxlength="30"
          />
        </div>
        <div class="field">
          <label for="d-motif">Motif (facultatif)</label>
          <input
            id="d-motif"
            v-model="demandeMotif"
            maxlength="300"
            placeholder="ex : mot de passe oublié"
          />
        </div>
        <div class="actions-modale">
          <button
            type="button"
            class="btn btn-outline btn-sm"
            @click="demandeOuverte = false"
          >
            Annuler
          </button>
          <button
            type="submit"
            class="btn btn-primary btn-sm"
            :disabled="demandeEnvoi"
          >
            {{ demandeEnvoi ? "Envoi..." : "Envoyer la demande" }}
          </button>
        </div>
      </form>
    </ModalDialog>
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
  margin-top: 1.5rem;
  padding: 0;
  background: none;
  border: none;
  font: inherit;
  font-size: 0.9rem;
  color: var(--violet);
  cursor: pointer;
}

.lien-secondaire:hover {
  text-decoration: underline;
}

.accuse {
  margin: 0 0 1rem;
  padding: 0.8rem 1rem;
  background: #d5faf5;
  color: #067a6f;
  border: 1px solid #a8efe6;
  border-radius: 14px;
}

.actions-modale {
  display: flex;
  justify-content: flex-end;
  gap: 0.6rem;
  margin-top: 1.2rem;
}
</style>
