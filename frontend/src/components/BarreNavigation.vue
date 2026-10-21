<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import NotificationBell from "./NotificationBell.vue";

// Nombre de liens affichés dans la barre ; les suivants vont dans le menu « Plus ».
const NB_PRINCIPAUX = 5;

// Ordre = priorité. Sans `roles`, le lien est visible par tous les utilisateurs connectés.
const LIENS = [
  { libelle: "Tableau de bord", to: "/dashboard" },
  { libelle: "Missions", to: "/missions" },
  {
    libelle: "Rapports",
    to: "/rapports",
    roles: [
      "chef_mission",
      "administrateur",
      "responsable_hierarchique",
      "auditeur",
    ],
  },
  { libelle: "Audit", to: "/audit", roles: ["auditeur", "administrateur"] },
  { libelle: "Comptes", to: "/admin/utilisateurs", roles: ["administrateur"] },
  {
    libelle: "Référentiels",
    to: "/admin/referentiels",
    roles: ["administrateur"],
  },
  {
    libelle: "Mon service",
    to: "/service",
    roles: ["responsable_hierarchique", "administrateur"],
  },
];

const authStore = useAuthStore();
const route = useRoute();
const router = useRouter();

const refPlus = ref(null);
const refUtilisateur = ref(null);
const plusOuvert = ref(false);
const utilisateurOuvert = ref(false);

// Petit écran : tous les liens passent dans un seul menu.
const requete = window.matchMedia("(max-width: 860px)");
const etroit = ref(requete.matches);
function surChangementEcran(evenement) {
  etroit.value = evenement.matches;
}

const role = computed(() => authStore.utilisateur?.role);
const visibles = computed(() =>
  LIENS.filter((lien) => !lien.roles || lien.roles.includes(role.value))
);
const principaux = computed(() =>
  etroit.value ? [] : visibles.value.slice(0, NB_PRINCIPAUX)
);
const autres = computed(() =>
  etroit.value ? visibles.value : visibles.value.slice(NB_PRINCIPAUX)
);
// Le bouton « Plus » est mis en évidence quand la page courante est l'un de ses liens.
const plusActif = computed(() =>
  autres.value.some((lien) => route.path.startsWith(lien.to))
);

const initiales = computed(() => {
  const u = authStore.utilisateur;
  return u
    ? `${u.prenom?.[0] ?? ""}${u.nom?.[0] ?? ""}`.toUpperCase() || "?"
    : "?";
});

function libelleRole(valeur) {
  return (valeur || "").replaceAll("_", " ");
}

function fermerTout() {
  plusOuvert.value = false;
  utilisateurOuvert.value = false;
}

function basculerPlus() {
  utilisateurOuvert.value = false;
  plusOuvert.value = !plusOuvert.value;
}

function basculerUtilisateur() {
  plusOuvert.value = false;
  utilisateurOuvert.value = !utilisateurOuvert.value;
}

function seDeconnecter() {
  fermerTout();
  authStore.deconnexion();
  router.push({ name: "login" });
}

function surClic(evenement) {
  if (plusOuvert.value && !refPlus.value?.contains(evenement.target))
    plusOuvert.value = false;
  if (
    utilisateurOuvert.value &&
    !refUtilisateur.value?.contains(evenement.target)
  ) {
    utilisateurOuvert.value = false;
  }
}

function surTouche(evenement) {
  if (evenement.key === "Escape") fermerTout();
}

watch(() => route.fullPath, fermerTout);

onMounted(() => {
  document.addEventListener("click", surClic);
  document.addEventListener("keydown", surTouche);
  requete.addEventListener("change", surChangementEcran);
});

onBeforeUnmount(() => {
  document.removeEventListener("click", surClic);
  document.removeEventListener("keydown", surTouche);
  requete.removeEventListener("change", surChangementEcran);
});
</script>

<template>
  <header class="topbar">
    <div class="container topbar-inner">
      <RouterLink to="/" class="logo">
        <span class="logo-mark">a</span>
        Plateforme MID
      </RouterLink>

      <nav
        v-if="authStore.estConnecte"
        class="navigation"
        aria-label="Navigation principale"
      >
        <RouterLink
          v-for="lien in principaux"
          :key="lien.to"
          :to="lien.to"
          class="lien"
        >
          {{ lien.libelle }}
        </RouterLink>

        <div v-if="autres.length" ref="refPlus" class="menu">
          <button
            type="button"
            class="lien lien-bouton"
            :class="{ 'lien-actif': plusActif }"
            aria-haspopup="true"
            :aria-expanded="plusOuvert"
            @click="basculerPlus"
          >
            {{ etroit ? "Menu" : "Plus" }}
            <svg
              class="chevron"
              :class="{ ouvert: plusOuvert }"
              viewBox="0 0 24 24"
              width="14"
              height="14"
              fill="none"
              stroke="currentColor"
              stroke-width="2.5"
              stroke-linecap="round"
              stroke-linejoin="round"
              aria-hidden="true"
            >
              <path d="m6 9 6 6 6-6" />
            </svg>
          </button>
          <div v-if="plusOuvert" class="panneau">
            <RouterLink
              v-for="lien in autres"
              :key="lien.to"
              :to="lien.to"
              class="element"
            >
              {{ lien.libelle }}
            </RouterLink>
          </div>
        </div>

        <NotificationBell />

        <div ref="refUtilisateur" class="menu">
          <button
            type="button"
            class="bouton-utilisateur"
            aria-haspopup="true"
            :aria-expanded="utilisateurOuvert"
            :aria-label="`Menu de ${
              authStore.utilisateur?.prenom ?? 'ton compte'
            }`"
            @click="basculerUtilisateur"
          >
            <span class="initiales">{{ initiales }}</span>
            <span class="prenom">{{ authStore.utilisateur?.prenom }}</span>
            <svg
              class="chevron"
              :class="{ ouvert: utilisateurOuvert }"
              viewBox="0 0 24 24"
              width="14"
              height="14"
              fill="none"
              stroke="currentColor"
              stroke-width="2.5"
              stroke-linecap="round"
              stroke-linejoin="round"
              aria-hidden="true"
            >
              <path d="m6 9 6 6 6-6" />
            </svg>
          </button>
          <div v-if="utilisateurOuvert" class="panneau panneau-droite">
            <div v-if="authStore.utilisateur" class="identite">
              <strong
                >{{ authStore.utilisateur.prenom }}
                {{ authStore.utilisateur.nom }}</strong
              >
              <small>{{ libelleRole(authStore.utilisateur.role) }}</small>
            </div>
            <RouterLink to="/compte" class="element">Mon compte</RouterLink>
            <button
              type="button"
              class="element element-bouton"
              @click="seDeconnecter"
            >
              Déconnexion
            </button>
          </div>
        </div>
      </nav>
    </div>
  </header>
</template>

<style scoped>
.navigation {
  display: flex;
  align-items: center;
  gap: 1.4rem;
}

/* Liens de la barre */
.lien {
  position: relative;
  padding: 0.4rem 0;
  background: none;
  border: none;
  font: inherit;
  font-size: 0.8rem;
  font-weight: 500;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--ink);
  cursor: pointer;
  text-decoration: none;
}

.lien:hover {
  color: var(--violet);
  text-decoration: none;
}

.lien.router-link-active,
.lien.lien-actif {
  color: var(--violet);
  font-weight: 700;
}

.lien.router-link-active::after,
.lien.lien-actif::after {
  content: "";
  position: absolute;
  left: 0;
  right: 0;
  bottom: -6px;
  height: 3px;
  border-radius: 3px;
  background: var(--teal);
}

.lien-bouton {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
}

.chevron {
  transition: transform 0.15s;
}

.chevron.ouvert {
  transform: rotate(180deg);
}

/* Menus déroulants */
.menu {
  position: relative;
}

.panneau {
  position: absolute;
  top: calc(100% + 14px);
  left: 0;
  z-index: 60;
  display: flex;
  flex-direction: column;
  min-width: 220px;
  max-height: min(60vh, 360px);
  overflow-y: auto;
  padding: 0.4rem;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 16px;
  box-shadow: var(--shadow);
}

.panneau-droite {
  left: auto;
  right: 0;
}

.element {
  display: block;
  width: 100%;
  padding: 0.65rem 0.9rem;
  background: none;
  border: none;
  border-radius: 10px;
  font: inherit;
  font-size: 0.92rem;
  color: var(--ink);
  text-align: left;
  text-decoration: none;
  cursor: pointer;
}

.element:hover {
  background: var(--bg-soft);
  text-decoration: none;
}

.element.router-link-active {
  color: var(--violet);
  font-weight: 600;
}

.element-bouton {
  color: #b0173f;
}

.identite {
  display: flex;
  flex-direction: column;
  padding: 0.6rem 0.9rem 0.7rem;
  margin-bottom: 0.3rem;
  border-bottom: 1px solid var(--border);
}

.identite small {
  color: var(--muted);
  text-transform: capitalize;
}

/* Bouton du compte */
.bouton-utilisateur {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.2rem 0.6rem 0.2rem 0.2rem;
  background: none;
  border: 1px solid var(--border);
  border-radius: 999px;
  font: inherit;
  color: var(--ink);
  cursor: pointer;
}

.bouton-utilisateur:hover {
  border-color: var(--teal);
}

.initiales {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: var(--grad);
  color: #fff;
  font-size: 0.72rem;
  font-weight: 700;
}

.prenom {
  font-size: 0.85rem;
  font-weight: 600;
}

@media (max-width: 860px) {
  .navigation {
    gap: 0.8rem;
  }

  .prenom {
    display: none;
  }

  .bouton-utilisateur {
    padding-right: 0.45rem;
  }

  /* À petite largeur, le menu s'ouvre vers la gauche pour rester dans l'écran */
  .panneau {
    left: auto;
    right: 0;
  }
}
</style>
