<script setup>
import { ref, computed, watch } from "vue";
import { useAuthStore } from "../stores/auth";
import { obtenirCompteurs } from "../services/rapports";

// Compteurs de rapports pour le tableau de bord : chef de mission (les siens) et
// administrateur (tous). Les autres rôles ne voient rien.
const authStore = useAuthStore();
const compteurs = ref(null);

const role = computed(() => authStore.utilisateur?.role);
const visible = computed(() =>
  ["chef_mission", "administrateur"].includes(role.value)
);

const cartes = computed(() => {
  const c = compteurs.value;
  if (!c) return [];
  if (role.value === "administrateur") {
    return [
      {
        libelle: "Rapports à valider",
        valeur: c.soumis,
        statut: "soumis",
        alerte: c.soumis > 0,
      },
      { libelle: "Rapports validés", valeur: c.valide, statut: "valide" },
    ];
  }
  return [
    {
      libelle: "À corriger",
      valeur: c.a_corriger,
      statut: "a_corriger",
      alerte: c.a_corriger > 0,
    },
    { libelle: "Brouillons", valeur: c.brouillon, statut: "brouillon" },
    { libelle: "En attente de validation", valeur: c.soumis, statut: "soumis" },
    { libelle: "Validés", valeur: c.valide, statut: "valide" },
  ];
});

async function charger() {
  try {
    compteurs.value = await obtenirCompteurs();
  } catch {
    compteurs.value = null;
  }
}

// Le profil peut arriver après l'affichage de la page : on attend de connaître le rôle.
watch(
  visible,
  (estVisible) => {
    if (estVisible) charger();
  },
  { immediate: true }
);
</script>

<template>
  <section v-if="visible && cartes.length" class="rapports-compteurs">
    <p class="eyebrow">Rapports de mission</p>
    <div class="grille">
      <RouterLink
        v-for="carte in cartes"
        :key="carte.statut"
        :to="{ name: 'rapports', query: { statut: carte.statut } }"
        class="card card-hover carte"
        :class="{ 'carte-alerte': carte.alerte }"
      >
        <span class="valeur">{{ carte.valeur }}</span>
        <span class="libelle">{{ carte.libelle }}</span>
      </RouterLink>
    </div>
  </section>
</template>

<style scoped>
.rapports-compteurs {
  margin-bottom: 1.5rem;
}

.grille {
  display: grid;
  gap: 1.5rem;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
}

.carte {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 0;
  padding: 1.2rem 1rem;
  color: inherit;
  text-align: center;
}

.carte:hover {
  text-decoration: none;
}

.carte-alerte {
  border-color: #d6336c;
}

.valeur {
  font-size: 2rem;
  font-weight: 700;
  line-height: 1.1;
  color: var(--violet);
}

.carte-alerte .valeur {
  color: #d6336c;
}

.libelle {
  font-size: 0.8rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--muted);
}
</style>
