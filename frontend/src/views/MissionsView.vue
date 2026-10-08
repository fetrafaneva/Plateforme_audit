<script setup>
import { ref, computed, onMounted } from "vue";
import { useAuthStore } from "../stores/auth";
import { listerMissions, creerMission } from "../services/missions";

const authStore = useAuthStore();

const missions = ref([]);
const chargement = ref(true);
const erreur = ref("");

const formulaireOuvert = ref(false);
const envoi = ref(false);
const erreurForm = ref("");
const titre = ref("");
const typeMission = ref("");
const dateDebut = ref("");
const dateFinPrevue = ref("");

const peutCreer = computed(() =>
  ["chef_mission", "administrateur"].includes(authStore.utilisateur?.nom_role)
);

const missionsRecentes = computed(() => [...missions.value].reverse());

function classeStatut(statut) {
  if (statut === "en_cours") return "badge-info";
  if (statut === "terminee") return "badge-ok";
  if (statut === "annulee") return "badge-off";
  return "badge-neutral";
}

function formaterDate(d) {
  return d ? new Date(d).toLocaleDateString("fr-FR") : null;
}

async function charger() {
  chargement.value = true;
  erreur.value = "";
  try {
    missions.value = await listerMissions();
  } catch {
    erreur.value = "Impossible de charger les missions.";
  } finally {
    chargement.value = false;
  }
}

async function soumettre() {
  erreurForm.value = "";
  envoi.value = true;
  try {
    await creerMission({
      titre: titre.value.trim(),
      type_mission: typeMission.value.trim() || null,
      date_debut: dateDebut.value ? `${dateDebut.value}T00:00:00` : null,
      date_fin_prevue: dateFinPrevue.value
        ? `${dateFinPrevue.value}T00:00:00`
        : null,
    });
    titre.value = "";
    typeMission.value = "";
    dateDebut.value = "";
    dateFinPrevue.value = "";
    formulaireOuvert.value = false;
    await charger();
  } catch (e) {
    const detail = e.response?.data?.detail;
    erreurForm.value =
      typeof detail === "string" ? detail : "Impossible de créer la mission.";
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
        <p class="eyebrow" style="color: #fff; opacity: 0.85">Missions</p>
        <h1>Missions de terrain</h1>
        <p class="hero-meta">
          Déploiements, formations et interventions menés par le MID.
        </p>
      </div>
    </header>

    <main class="container page">
      <div v-if="peutCreer" class="barre-actions">
        <button
          class="btn btn-primary"
          @click="formulaireOuvert = !formulaireOuvert"
        >
          {{ formulaireOuvert ? "Fermer" : "+ Nouvelle mission" }}
        </button>
      </div>

      <section v-if="formulaireOuvert" class="card">
        <h2>Nouvelle mission</h2>
        <form @submit.prevent="soumettre">
          <div class="field">
            <label for="titre">Titre</label>
            <input id="titre" v-model="titre" required />
          </div>
          <div class="field">
            <label for="type">Type de mission</label>
            <input
              id="type"
              v-model="typeMission"
              placeholder="ex : deploiement_serveur"
            />
          </div>
          <div class="grid-2">
            <div class="field">
              <label for="debut">Date de début</label>
              <input id="debut" v-model="dateDebut" type="date" />
            </div>
            <div class="field">
              <label for="fin">Date de fin prévue</label>
              <input id="fin" v-model="dateFinPrevue" type="date" />
            </div>
          </div>
          <p v-if="erreurForm" class="alert-error">{{ erreurForm }}</p>
          <button type="submit" class="btn btn-primary" :disabled="envoi">
            {{ envoi ? "Création..." : "Créer la mission" }}
          </button>
        </form>
      </section>

      <p v-if="erreur" class="alert-error">{{ erreur }}</p>
      <p v-if="chargement" class="card">Chargement...</p>
      <p v-else-if="!erreur && missions.length === 0" class="card muted">
        Aucune mission pour le moment.
      </p>

      <div v-else class="grid">
        <RouterLink
          v-for="m in missionsRecentes"
          :key="m.id"
          :to="{ name: 'mission-detail', params: { id: m.id } }"
          class="card card-hover carte-mission"
        >
          <div class="carte-entete">
            <span class="badge" :class="classeStatut(m.statut)">{{
              m.statut
            }}</span>
            <span class="muted">#{{ m.id }}</span>
          </div>
          <h2>{{ m.titre }}</h2>
          <p class="muted">{{ m.type_mission || "Type non précisé" }}</p>
          <p v-if="m.date_debut" class="dates">
            {{ formaterDate(m.date_debut) }}
            <template v-if="m.date_fin_prevue">
              &rarr; {{ formaterDate(m.date_fin_prevue) }}
            </template>
          </p>
          <span class="lien-voir">Voir le détail &rarr;</span>
        </RouterLink>
      </div>
    </main>
  </div>
</template>

<style scoped>
.barre-actions {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 1.5rem;
}

.carte-mission {
  display: flex;
  flex-direction: column;
  color: inherit;
  margin-bottom: 0;
}

.carte-mission:hover {
  text-decoration: none;
}

.carte-entete {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.8rem;
  font-size: 0.8rem;
}

.dates {
  margin: 0 0 1rem;
  font-size: 0.85rem;
  font-weight: 600;
}

.lien-voir {
  margin-top: auto;
  color: var(--violet);
  font-size: 0.85rem;
  font-weight: 600;
}
</style>
