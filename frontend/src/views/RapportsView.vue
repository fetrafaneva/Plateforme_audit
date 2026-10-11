<script setup>
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import ModalDialog from "../components/ModalDialog.vue";
import { useAuthStore } from "../stores/auth";
import {
  listerRapports,
  listerAxesDisponibles,
  creerRapport,
  telechargerPdf,
} from "../services/rapports";

const router = useRouter();
const authStore = useAuthStore();

const rapports = ref([]);
const filtreStatut = ref("");
const chargement = ref(true);
const erreur = ref("");

// Seul le chef de mission rédige (pour son propre axe) ; l'administrateur valide.
const peutRediger = computed(
  () => authStore.utilisateur?.role === "chef_mission"
);
const peutPdf = computed(() =>
  ["chef_mission", "administrateur"].includes(authStore.utilisateur?.role)
);

const modaleOuverte = ref(false);
const axes = ref([]);
const axeChoisi = ref("");
const erreurModale = ref("");
const envoi = ref(false);

const LIBELLES = {
  brouillon: "Brouillon",
  soumis: "Soumis",
  a_corriger: "À corriger",
  valide: "Validé",
};

function classeStatut(statut) {
  if (statut === "valide") return "badge-ok";
  if (statut === "soumis") return "badge-info";
  if (statut === "a_corriger") return "badge-warn";
  return "badge-neutral";
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
  erreur.value = "";
  try {
    rapports.value = await listerRapports(
      filtreStatut.value ? { statut: filtreStatut.value } : {}
    );
  } catch (e) {
    erreur.value = messageErreur(e, "Impossible de charger les rapports.");
  } finally {
    chargement.value = false;
  }
}

async function ouvrirModale() {
  modaleOuverte.value = true;
  axeChoisi.value = "";
  erreurModale.value = "";
  try {
    axes.value = await listerAxesDisponibles();
  } catch (e) {
    erreurModale.value = messageErreur(e, "Impossible de charger les axes.");
  }
}

async function pdf(rapport) {
  erreur.value = "";
  try {
    await telechargerPdf(rapport.id, rapport.numero_axe ?? rapport.id_axe);
  } catch (e) {
    erreur.value = messageErreur(e, "Impossible de générer le PDF.");
  }
}

async function creer() {
  envoi.value = true;
  erreurModale.value = "";
  try {
    const rapport = await creerRapport(Number(axeChoisi.value));
    router.push({ name: "rapport-detail", params: { id: rapport.id } });
  } catch (e) {
    erreurModale.value = messageErreur(e, "Création impossible.");
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
        <p class="eyebrow" style="color: #fff; opacity: 0.85">Rapports</p>
        <h1>Rapports de mission</h1>
        <p class="hero-meta">
          Rédaction, pièces jointes obligatoires, soumission et validation.
        </p>
      </div>
    </header>

    <main class="container page">
      <div class="barre">
        <div class="filtre">
          <label for="filtre">Statut</label>
          <select id="filtre" v-model="filtreStatut" @change="charger">
            <option value="">Tous</option>
            <option
              v-for="(libelle, code) in LIBELLES"
              :key="code"
              :value="code"
            >
              {{ libelle }}
            </option>
          </select>
        </div>
        <button
          v-if="peutRediger"
          class="btn btn-primary btn-sm"
          @click="ouvrirModale"
        >
          + Nouveau rapport
        </button>
      </div>

      <p v-if="erreur" class="alert-error">{{ erreur }}</p>

      <section class="card">
        <p v-if="chargement" class="muted">Chargement...</p>
        <p v-else-if="rapports.length === 0" class="muted">Aucun rapport.</p>
        <div v-else class="defilement">
          <table class="tableau">
            <thead>
              <tr>
                <th>Mission</th>
                <th>Axe</th>
                <th>Auteur</th>
                <th>Statut</th>
                <th>Pièces</th>
                <th>Dernière modification</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in rapports" :key="r.id">
                <td>
                  <strong>{{ r.titre_mission }}</strong>
                </td>
                <td>{{ r.numero_axe ?? r.id_axe }}</td>
                <td>{{ r.auteur }}</td>
                <td>
                  <span class="badge" :class="classeStatut(r.statut)">{{
                    LIBELLES[r.statut] ?? r.statut
                  }}</span>
                </td>
                <td>{{ r.nb_pieces }}</td>
                <td>{{ formaterDateHeure(r.date_modification) }}</td>
                <td class="cellule-actions">
                  <button
                    v-if="r.statut === 'valide' && peutPdf"
                    class="btn btn-primary btn-sm"
                    @click="pdf(r)"
                  >
                    PDF
                  </button>
                  <RouterLink
                    :to="{ name: 'rapport-detail', params: { id: r.id } }"
                    class="btn btn-outline btn-sm"
                  >
                    Ouvrir
                  </RouterLink>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </main>

    <ModalDialog
      v-if="modaleOuverte"
      titre="Nouveau rapport"
      @fermer="modaleOuverte = false"
    >
      <p v-if="erreurModale" class="alert-error">{{ erreurModale }}</p>
      <form @submit.prevent="creer">
        <p v-if="axes.length === 0" class="muted">
          Aucun axe disponible. Tu ne peux rédiger que le rapport d'un axe dont
          tu fais partie de l'équipe : demande que ton compte soit lié à un
          participant de cet axe, depuis la page de la mission.
        </p>
        <div v-else class="field">
          <label for="axe">Axe à rapporter</label>
          <select id="axe" v-model="axeChoisi" required>
            <option value="" disabled>Choisir un axe</option>
            <option v-for="a in axes" :key="a.id_axe" :value="a.id_axe">
              {{ a.titre_mission }}, axe {{ a.numero_axe ?? a.id_axe }}
            </option>
          </select>
          <small class="muted">
            Seuls les axes dont tu fais partie de l'équipe sont proposés. Les
            districts, les dates et les indicateurs sont repris de la mission.
          </small>
        </div>
        <div class="actions-modale">
          <button
            type="button"
            class="btn btn-outline btn-sm"
            @click="modaleOuverte = false"
          >
            Annuler
          </button>
          <button
            v-if="axes.length"
            type="submit"
            class="btn btn-primary btn-sm"
            :disabled="envoi"
          >
            {{ envoi ? "Création..." : "Créer le brouillon" }}
          </button>
        </div>
      </form>
    </ModalDialog>
  </div>
</template>

<style scoped>
.barre {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.filtre {
  display: flex;
  align-items: center;
  gap: 0.7rem;
}

.filtre label {
  margin: 0;
}

.filtre select {
  width: auto;
  min-width: 10rem;
}

.badge-warn {
  background: #fff1d6;
  color: #9a5b00;
}

.defilement {
  overflow-x: auto;
}

.tableau {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

.tableau th,
.tableau td {
  text-align: left;
  padding: 0.6rem 0.7rem;
  border-bottom: 1px solid var(--border);
  vertical-align: middle;
}

.tableau th {
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  color: var(--muted);
}

.cellule-actions {
  text-align: right;
  white-space: nowrap;
}

.actions-modale {
  display: flex;
  justify-content: flex-end;
  gap: 0.6rem;
  margin-top: 1.2rem;
}
</style>
