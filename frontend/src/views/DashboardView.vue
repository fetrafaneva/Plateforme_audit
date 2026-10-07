<script setup>
import { ref, computed, onMounted } from "vue";
import { useAuthStore } from "../stores/auth";
import { listerMissions } from "../services/missions";

const authStore = useAuthStore();
const missions = ref([]);
const chargementMissions = ref(true);

onMounted(async () => {
  if (!authStore.utilisateur) {
    authStore.chargerUtilisateur();
  }
  try {
    missions.value = await listerMissions();
  } catch {
    missions.value = [];
  } finally {
    chargementMissions.value = false;
  }
});

const total = computed(() => missions.value.length);
const planifiees = computed(
  () => missions.value.filter((m) => m.statut === "planifiee").length
);
const enCours = computed(
  () => missions.value.filter((m) => m.statut === "en_cours").length
);
const terminees = computed(
  () => missions.value.filter((m) => m.statut === "terminee").length
);
const dernieres = computed(() => [...missions.value].reverse().slice(0, 3));

function initiales(u) {
  return `${u.prenom?.[0] ?? ""}${u.nom?.[0] ?? ""}`.toUpperCase() || "?";
}

function classeStatut(statut) {
  if (statut === "en_cours") return "badge-info";
  if (statut === "terminee") return "badge-ok";
  if (statut === "annulee") return "badge-off";
  return "badge-neutral";
}
</script>

<template>
  <div>
    <header class="hero hero-compact">
      <div class="container">
        <p class="eyebrow" style="color: #fff; opacity: 0.85">
          Tableau de bord
        </p>
        <h1 v-if="authStore.utilisateur">
          Bonjour, {{ authStore.utilisateur.prenom }}
        </h1>
        <h1 v-else>Bonjour</h1>
        <p class="hero-meta">
          Suivi des missions de déploiement et des équipes sur le terrain.
        </p>
      </div>
    </header>

    <main class="container page">
      <section class="stats">
        <div class="card card-hover stat">
          <span class="stat-valeur">{{
            chargementMissions ? "…" : total
          }}</span>
          <span class="stat-label">Missions</span>
        </div>
        <div class="card card-hover stat">
          <span class="stat-valeur">{{
            chargementMissions ? "…" : planifiees
          }}</span>
          <span class="stat-label">Planifiées</span>
        </div>
        <div class="card card-hover stat">
          <span class="stat-valeur">{{
            chargementMissions ? "…" : enCours
          }}</span>
          <span class="stat-label">En cours</span>
        </div>
        <div class="card card-hover stat">
          <span class="stat-valeur">{{
            chargementMissions ? "…" : terminees
          }}</span>
          <span class="stat-label">Terminées</span>
        </div>
      </section>

      <div class="grid-2">
        <section class="card">
          <p class="eyebrow">Mon profil</p>
          <div v-if="authStore.utilisateur" class="profil">
            <span class="avatar avatar-lg">{{
              initiales(authStore.utilisateur)
            }}</span>
            <div>
              <h2 style="margin-bottom: 0.2rem">
                {{ authStore.utilisateur.prenom }}
                {{ authStore.utilisateur.nom }}
              </h2>
              <p class="muted" style="margin: 0">
                {{ authStore.utilisateur.email }}
              </p>
              <p class="muted" style="margin: 0">
                Matricule {{ authStore.utilisateur.matricule }}
              </p>
              <span
                v-if="authStore.utilisateur.statut"
                class="badge"
                :class="
                  authStore.utilisateur.statut === 'actif'
                    ? 'badge-ok'
                    : 'badge-off'
                "
                style="margin-top: 0.6rem"
              >
                {{ authStore.utilisateur.statut }}
              </span>
            </div>
          </div>
          <p v-else class="muted">Chargement du profil...</p>
        </section>

        <section class="card">
          <p class="eyebrow">Dernières missions</p>
          <p v-if="chargementMissions" class="muted">Chargement...</p>
          <p v-else-if="dernieres.length === 0" class="muted">
            Aucune mission pour le moment.
          </p>
          <ul v-else class="list-clean">
            <li v-for="m in dernieres" :key="m.id" class="ligne-mission">
              <RouterLink
                :to="{ name: 'mission-detail', params: { id: m.id } }"
              >
                {{ m.titre }}
              </RouterLink>
              <span class="badge" :class="classeStatut(m.statut)">{{
                m.statut
              }}</span>
            </li>
          </ul>
          <RouterLink
            to="/missions"
            class="btn btn-outline btn-sm"
            style="margin-top: 1rem"
          >
            Voir toutes les missions
          </RouterLink>
        </section>
      </div>
    </main>
  </div>
</template>

<style scoped>
.stats {
  display: grid;
  gap: 1.5rem;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 1.4rem 1rem;
  margin-bottom: 1.5rem;
}

.stat-valeur {
  font-size: 2.2rem;
  font-weight: 700;
  line-height: 1.1;
  background: var(--grad);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.stat-label {
  font-size: 0.8rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--muted);
}

.profil {
  display: flex;
  align-items: center;
  gap: 1.2rem;
}

.avatar-lg {
  width: 64px;
  height: 64px;
  font-size: 1.3rem;
}

.ligne-mission {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  padding: 0.6rem 0;
  border-bottom: 1px solid var(--border);
}
</style>
