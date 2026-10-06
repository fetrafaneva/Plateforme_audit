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
  <div class="mission-detail">
    <RouterLink to="/missions">&larr; Retour aux missions</RouterLink>

    <p v-if="erreur" style="color: red">{{ erreur }}</p>
    <p v-if="chargement">Chargement...</p>

    <div v-else-if="mission">
      <h1>{{ mission.titre }}</h1>
      <p>
        <strong>Type :</strong> {{ mission.type_mission || "—" }} ·
        <strong>Statut :</strong> {{ mission.statut }}
      </p>

      <p v-if="axesDetails.length === 0">Aucun axe créé pour cette mission.</p>

      <section
        v-for="detail in axesDetails"
        :key="detail.axe.id"
        class="axe-bloc"
      >
        <h2>Axe {{ detail.axe.numero_axe ?? detail.axe.id }}</h2>
        <p v-if="detail.axe.itineraire_principal">
          {{ detail.axe.itineraire_principal }}
        </p>

        <h3>Districts visités</h3>
        <ul v-if="detail.districts.length">
          <li v-for="d in detail.districts" :key="d.id">
            {{ d.nom }} — statut : {{ d.statut }}
          </li>
        </ul>
        <p v-else>Aucun district rattaché à cet axe.</p>

        <h3>Équipes</h3>
        <div v-if="detail.equipes.length === 0">
          Aucune équipe pour cet axe.
        </div>
        <div
          v-for="eq in detail.equipes"
          :key="eq.equipe.id"
          class="equipe-bloc"
        >
          <h4>{{ eq.equipe.type_equipe || "Équipe #" + eq.equipe.id }}</h4>
          <ul v-if="eq.participants.length">
            <li v-for="p in eq.participants" :key="p.id">
              {{ p.nom }} — {{ p.fonction || "rôle non précisé" }}
            </li>
          </ul>
          <p v-else>Aucun participant.</p>
        </div>
      </section>
    </div>
  </div>
</template>
