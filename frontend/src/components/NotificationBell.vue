<script setup>
import { ref, onMounted, onBeforeUnmount } from "vue";
import { useRouter } from "vue-router";
import {
  listerNotifications,
  marquerLue,
  toutLire,
} from "../services/notifications";

const INTERVALLE = 60 * 1000; // l'application interroge le serveur chaque minute

const router = useRouter();
const racine = ref(null);
const ouvert = ref(false);
const nonLues = ref(0);
const notifications = ref([]);
let minuteur = null;

async function charger() {
  try {
    const donnees = await listerNotifications();
    nonLues.value = donnees.non_lues;
    notifications.value = donnees.notifications;
  } catch {
    /* échec silencieux : la prochaine interrogation réessaiera */
  }
}

function basculer() {
  ouvert.value = !ouvert.value;
  if (ouvert.value) charger();
}

async function ouvrir(notification) {
  ouvert.value = false;
  if (!notification.lue) {
    try {
      await marquerLue(notification.id);
    } catch {
      /* sans gravité */
    }
    await charger();
  }
  if (notification.lien) router.push(notification.lien);
}

async function toutMarquerLu() {
  try {
    await toutLire();
  } catch {
    /* sans gravité */
  }
  await charger();
}

function formaterDateHeure(d) {
  return new Date(d).toLocaleString("fr-FR", {
    dateStyle: "short",
    timeStyle: "short",
  });
}

function surClicExterieur(evenement) {
  if (
    ouvert.value &&
    racine.value &&
    !racine.value.contains(evenement.target)
  ) {
    ouvert.value = false;
  }
}

function surTouche(evenement) {
  if (evenement.key === "Escape") ouvert.value = false;
}

onMounted(() => {
  charger();
  minuteur = setInterval(charger, INTERVALLE);
  document.addEventListener("click", surClicExterieur);
  document.addEventListener("keydown", surTouche);
});

onBeforeUnmount(() => {
  clearInterval(minuteur);
  document.removeEventListener("click", surClicExterieur);
  document.removeEventListener("keydown", surTouche);
});
</script>

<template>
  <div ref="racine" class="cloche">
    <button
      type="button"
      class="bouton-cloche"
      :aria-label="`Notifications, ${nonLues} non lue(s)`"
      :aria-expanded="ouvert"
      @click="basculer"
    >
      <svg
        viewBox="0 0 24 24"
        width="20"
        height="20"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
        aria-hidden="true"
      >
        <path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9" />
        <path d="M13.7 21a2 2 0 0 1-3.4 0" />
      </svg>
      <span v-if="nonLues > 0" class="pastille">{{
        nonLues > 9 ? "9+" : nonLues
      }}</span>
    </button>

    <div v-if="ouvert" class="panneau" role="dialog" aria-label="Notifications">
      <div class="panneau-entete">
        <strong>Notifications</strong>
        <button
          v-if="nonLues > 0"
          type="button"
          class="lien"
          @click="toutMarquerLu"
        >
          Tout marquer comme lu
        </button>
      </div>
      <p v-if="notifications.length === 0" class="vide">Aucune notification.</p>
      <ul v-else class="liste">
        <li v-for="n in notifications" :key="n.id">
          <button
            type="button"
            class="element"
            :class="{ 'non-lue': !n.lue }"
            @click="ouvrir(n)"
          >
            <span class="message">{{ n.message }}</span>
            <small class="date">{{ formaterDateHeure(n.date_creation) }}</small>
          </button>
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.cloche {
  position: relative;
}

.bouton-cloche {
  position: relative;
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  padding: 0;
  background: none;
  border: 1px solid var(--border);
  border-radius: 50%;
  color: var(--ink);
  cursor: pointer;
}

.bouton-cloche:hover {
  border-color: var(--teal);
}

.pastille {
  position: absolute;
  top: -5px;
  right: -5px;
  min-width: 18px;
  padding: 0 4px;
  border-radius: 999px;
  background: #d6336c;
  color: #fff;
  font-size: 0.7rem;
  font-weight: 700;
  line-height: 18px;
  text-align: center;
}

.panneau {
  position: absolute;
  top: calc(100% + 10px);
  right: 0;
  z-index: 50;
  width: min(360px, 90vw);
  max-height: 440px;
  overflow-y: auto;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 16px;
  box-shadow: var(--shadow);
}

.panneau-entete {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.8rem 1rem;
  border-bottom: 1px solid var(--border);
}

.lien {
  padding: 0;
  background: none;
  border: none;
  font: inherit;
  font-size: 0.8rem;
  color: var(--violet);
  cursor: pointer;
}

.lien:hover {
  text-decoration: underline;
}

.vide {
  margin: 0;
  padding: 1.2rem 1rem;
  color: var(--muted);
}

.liste {
  margin: 0;
  padding: 0;
  list-style: none;
}

.element {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  width: 100%;
  padding: 0.75rem 1rem;
  background: none;
  border: none;
  border-bottom: 1px solid var(--border);
  border-left: 3px solid transparent;
  font: inherit;
  text-align: left;
  cursor: pointer;
}

.element:hover {
  background: var(--bg-soft);
}

.element.non-lue {
  background: var(--bg-soft);
  border-left-color: var(--violet);
}

.message {
  font-size: 0.88rem;
  line-height: 1.4;
}

.element.non-lue .message {
  font-weight: 600;
}

.date {
  color: var(--muted);
  font-size: 0.75rem;
}
</style>
