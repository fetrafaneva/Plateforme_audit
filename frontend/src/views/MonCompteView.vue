<script setup>
import { ref, computed, onMounted } from "vue";
import { useAuthStore } from "../stores/auth";
import { maDerniereDemande, demanderConnecte } from "../services/demandesMdp";

const authStore = useAuthStore();
const demande = ref(null);
const motif = ref("");
const chargement = ref(true);
const envoi = ref(false);
const erreur = ref("");
const message = ref("");

const utilisateur = computed(() => authStore.utilisateur);
const enAttente = computed(() => demande.value?.statut === "en_attente");

function libelle(valeur) {
  return (valeur || "").replaceAll("_", " ");
}

function formaterDateHeure(d) {
  return d
    ? new Date(d).toLocaleString("fr-FR", {
        dateStyle: "short",
        timeStyle: "short",
      })
    : "—";
}

function messageErreur(e, defaut) {
  const detail = e.response?.data?.detail;
  return typeof detail === "string" ? detail : defaut;
}

async function charger() {
  chargement.value = true;
  try {
    demande.value = await maDerniereDemande();
  } catch (e) {
    erreur.value = messageErreur(e, "Impossible de charger ta demande.");
  } finally {
    chargement.value = false;
  }
}

async function envoyer() {
  erreur.value = "";
  message.value = "";
  envoi.value = true;
  try {
    const reponse = await demanderConnecte(motif.value.trim());
    message.value = reponse.message;
    motif.value = "";
    await charger();
  } catch (e) {
    erreur.value = messageErreur(e, "L'envoi de la demande a échoué.");
  } finally {
    envoi.value = false;
  }
}

onMounted(async () => {
  if (!authStore.utilisateur) {
    try {
      await authStore.chargerUtilisateur();
    } catch {
      /* l'intercepteur gère le 401 */
    }
  }
  charger();
});
</script>

<template>
  <div>
    <header class="hero hero-compact">
      <div class="container">
        <p class="eyebrow" style="color: #fff; opacity: 0.85">Mon compte</p>
        <h1 v-if="utilisateur">
          {{ utilisateur.prenom }} {{ utilisateur.nom }}
        </h1>
        <h1 v-else>Mon compte</h1>
        <p class="hero-meta">Tes informations et ton mot de passe.</p>
      </div>
    </header>

    <main class="container page">
      <section v-if="utilisateur" class="card">
        <p class="eyebrow">Profil</p>
        <dl class="infos">
          <div>
            <dt>Email</dt>
            <dd>{{ utilisateur.email }}</dd>
          </div>
          <div>
            <dt>Matricule</dt>
            <dd>{{ utilisateur.matricule }}</dd>
          </div>
          <div>
            <dt>Rôle</dt>
            <dd>
              <span class="badge badge-neutral">{{
                libelle(utilisateur.role)
              }}</span>
            </dd>
          </div>
          <div>
            <dt>Statut</dt>
            <dd>
              <span
                class="badge"
                :class="
                  utilisateur.statut === 'actif' ? 'badge-ok' : 'badge-off'
                "
              >
                {{ utilisateur.statut }}
              </span>
            </dd>
          </div>
        </dl>
      </section>

      <section class="card">
        <p class="eyebrow">Mot de passe</p>
        <p class="muted">
          Le mot de passe n'est pas modifiable directement : tu envoies une
          demande à l'administrateur, qui vérifie ton identité puis te
          communique un mot de passe temporaire.
        </p>

        <p v-if="erreur" class="alert-error">{{ erreur }}</p>
        <p v-if="message" class="message-ok">{{ message }}</p>

        <p v-if="chargement" class="muted">Chargement...</p>

        <template v-else>
          <p v-if="enAttente" class="etat etat-attente">
            Demande envoyée le {{ formaterDateHeure(demande.date_demande) }} :
            elle attend d'être traitée par l'administrateur.
          </p>

          <template v-else>
            <p
              v-if="demande && demande.statut === 'traitee'"
              class="etat etat-ok"
            >
              Ta dernière demande a été traitée le
              {{ formaterDateHeure(demande.date_traitement) }} par
              {{ demande.nom_traitant }}.
            </p>
            <p
              v-else-if="demande && demande.statut === 'rejetee'"
              class="etat etat-refus"
            >
              Ta dernière demande a été rejetée le
              {{ formaterDateHeure(demande.date_traitement) }} par
              {{ demande.nom_traitant }}.
            </p>

            <form @submit.prevent="envoyer">
              <div class="field">
                <label for="motif">Motif (facultatif)</label>
                <input
                  id="motif"
                  v-model="motif"
                  maxlength="300"
                  placeholder="ex : je soupçonne que mon mot de passe est connu"
                />
              </div>
              <button
                type="submit"
                class="btn btn-primary btn-sm"
                :disabled="envoi"
              >
                {{
                  envoi ? "Envoi..." : "Demander un changement de mot de passe"
                }}
              </button>
            </form>
          </template>
        </template>
      </section>
    </main>
  </div>
</template>

<style scoped>
.message-ok {
  margin: 0 0 1rem;
  padding: 0.75rem 1rem;
  background: #d5faf5;
  color: #067a6f;
  border: 1px solid #a8efe6;
  border-radius: 14px;
}

.infos {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
  margin: 0;
}

.infos dt {
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--muted);
}

.infos dd {
  margin: 0.15rem 0 0;
}

.etat {
  margin: 0 0 1rem;
  padding: 0.75rem 1rem;
  border-radius: 14px;
}

.etat-attente {
  background: #dff0fc;
  color: #1767a3;
  border: 1px solid #b7dcf5;
}

.etat-ok {
  background: #d5faf5;
  color: #067a6f;
  border: 1px solid #a8efe6;
}

.etat-refus {
  background: #fff1d6;
  color: #7a4700;
  border: 1px solid #f3d29a;
}
</style>
