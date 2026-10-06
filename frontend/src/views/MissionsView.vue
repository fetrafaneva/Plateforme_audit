<script setup>
import { ref, computed, onMounted } from "vue";
import { useAuthStore } from "../stores/auth";
import { listerMissions, creerMission } from "../services/missions";

const authStore = useAuthStore();
const missions = ref([]);
const chargement = ref(false);
const erreur = ref("");

const peutCreer = computed(() =>
  ["chef_mission", "administrateur"].includes(authStore.utilisateur?.role)
);

const nouvelleMission = ref({
  titre: "",
  type_mission: "",
  date_debut: "",
  date_fin_prevue: "",
});

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
  erreur.value = "";
  try {
    await creerMission({ ...nouvelleMission.value });
    nouvelleMission.value = {
      titre: "",
      type_mission: "",
      date_debut: "",
      date_fin_prevue: "",
    };
    await charger();
  } catch (e) {
    erreur.value = e.response?.data?.detail || "Erreur lors de la création.";
  }
}

onMounted(charger);
</script>

<template>
  <div class="missions-view">
    <h1>Missions</h1>

    <form v-if="peutCreer" @submit.prevent="soumettre">
      <h2>Nouvelle mission</h2>
      <input v-model="nouvelleMission.titre" placeholder="Titre" required />
      <input
        v-model="nouvelleMission.type_mission"
        placeholder="Type de mission"
      />
      <input v-model="nouvelleMission.date_debut" type="date" />
      <input v-model="nouvelleMission.date_fin_prevue" type="date" />
      <button type="submit">Créer</button>
    </form>

    <p v-if="erreur" style="color: red">{{ erreur }}</p>
    <p v-if="chargement">Chargement...</p>

    <table v-else>
      <thead>
        <tr>
          <th>Titre</th>
          <th>Type</th>
          <th>Statut</th>
          <th>Début</th>
          <th>Fin prévue</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="mission in missions" :key="mission.id">
          <td>
            <RouterLink :to="`/missions/${mission.id}`">{{
              mission.titre
            }}</RouterLink>
          </td>
          <td>{{ mission.type_mission }}</td>
          <td>{{ mission.statut }}</td>
          <td>{{ mission.date_debut }}</td>
          <td>{{ mission.date_fin_prevue }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
