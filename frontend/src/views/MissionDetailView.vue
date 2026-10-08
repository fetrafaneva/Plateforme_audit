<script setup>
import { ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import {
  obtenirMission,
  listerAxes,
  listerEquipes,
  listerParticipants,
  listerMissionsDistricts,
  listerDistricts,
} from "../services/missions";

const route = useRoute();
const mission = ref(null);
const axesDetails = ref([]);
const chargement = ref(true);
const erreur = ref("");

function classeStatut(statut) {
  if (statut === "en_cours") return "badge-info";
  if (["terminee", "termine", "realisee"].includes(statut)) return "badge-ok";
  if (statut === "annulee") return "badge-off";
  return "badge-neutral";
}

function initiales(nom) {
  return (nom || "?")
    .split(" ")
    .filter(Boolean)
    .map((mot) => mot[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

function formaterDate(d) {
  return d ? new Date(d).toLocaleDateString("fr-FR") : null;
}

async function charger() {
  chargement.value = true;
  erreur.value = "";
  try {
    const missionId = route.params.id;
    mission.value = await obtenirMission(missionId);

    const [axes, districts] = await Promise.all([
      listerAxes(missionId),
      listerDistricts(),
    ]);
    const districtsParId = Object.fromEntries(
      districts.map((d) => [d.id, d.nom])
    );

    axesDetails.value = await Promise.all(
      axes.map(async (axe) => {
        const [equipes, missionsDistricts] = await Promise.all([
          listerEquipes(axe.id),
          listerMissionsDistricts(axe.id),
        ]);

        const equipesAvecParticipants = await Promise.all(
          equipes.map(async (equipe) => ({
            equipe,
            participants: await listerParticipants(equipe.id),
          }))
        );

        return {
          axe,
          equipes: equipesAvecParticipants,
          districts: missionsDistricts.map((md) => ({
            ...md,
            nom:
              districtsParId[md.district_id] || `District #${md.district_id}`,
          })),
        };
      })
    );
  } catch {
    erreur.value = "Impossible de charger le détail de la mission.";
  } finally {
    chargement.value = false;
  }
}

onMounted(charger);
</script>

<template>
  <div>
    <header class="hero hero-compact">
      <div class="container">
        <RouterLink class="back" to="/missions"
          >&larr; Retour aux missions</RouterLink
        >
        <h1>{{ mission ? mission.titre : "Détail de la mission" }}</h1>
        <p v-if="mission" class="hero-meta">
          <span>{{ mission.type_mission || "Type non précisé" }}</span>
          <span v-if="mission.date_debut">
            · du {{ formaterDate(mission.date_debut) }}
            <template v-if="mission.date_fin_prevue">
              au {{ formaterDate(mission.date_fin_prevue) }}
            </template>
          </span>
          <span class="badge badge-light">{{ mission.statut }}</span>
        </p>
      </div>
    </header>

    <main class="container page">
      <p v-if="erreur" class="alert-error">{{ erreur }}</p>
      <p v-if="chargement" class="card">Chargement...</p>

      <template v-else-if="mission">
        <p v-if="axesDetails.length === 0" class="card muted">
          Aucun axe créé pour cette mission.
        </p>

        <article
          v-for="detail in axesDetails"
          :key="detail.axe.id"
          class="card"
        >
          <h2>Axe {{ detail.axe.numero_axe ?? detail.axe.id }}</h2>
          <p v-if="detail.axe.itineraire_principal" class="muted">
            {{ detail.axe.itineraire_principal }}
          </p>

          <div class="grid-2">
            <section>
              <p class="eyebrow">Districts visités</p>
              <ul v-if="detail.districts.length" class="list-clean">
                <li
                  v-for="d in detail.districts"
                  :key="d.id"
                  class="ligne-district"
                >
                  <span>{{ d.nom }}</span>
                  <span class="badge" :class="classeStatut(d.statut)">{{
                    d.statut
                  }}</span>
                </li>
              </ul>
              <p v-else class="muted">Aucun district rattaché à cet axe.</p>
            </section>

            <section>
              <p class="eyebrow">Équipes</p>
              <p v-if="detail.equipes.length === 0" class="muted">
                Aucune équipe pour cet axe.
              </p>
              <div
                v-for="eq in detail.equipes"
                :key="eq.equipe.id"
                class="equipe-bloc"
              >
                <h3>
                  {{ eq.equipe.type_equipe || "Équipe #" + eq.equipe.id }}
                </h3>
                <ul v-if="eq.participants.length" class="list-clean">
                  <li
                    v-for="p in eq.participants"
                    :key="p.id"
                    class="ligne-participant"
                  >
                    <span class="avatar">{{ initiales(p.nom) }}</span>
                    <span>
                      <strong>{{ p.nom }}</strong
                      ><br />
                      <small class="muted">{{
                        p.fonction || "Rôle non précisé"
                      }}</small>
                    </span>
                  </li>
                </ul>
                <p v-else class="muted">Aucun participant.</p>
              </div>
            </section>
          </div>
        </article>
      </template>
    </main>
  </div>
</template>

<style scoped>
.ligne-district {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.55rem 0;
  border-bottom: 1px solid var(--border);
}

.equipe-bloc {
  background: var(--bg-soft);
  border-radius: 18px;
  padding: 1rem 1.2rem;
  margin-bottom: 0.9rem;
}

.ligne-participant {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.4rem 0;
}
</style>
