<script setup>
import { ref, watch, nextTick, onBeforeUnmount } from "vue";
import {
  etatConfirmation as etat,
  repondre,
} from "../composables/useConfirmation";

const boite = ref(null);

// Écouté en phase de capture sur window : si une autre fenêtre est ouverte
// dessous (ex. le suivi d'un district), Échap ne ferme que cette confirmation.
function surTouche(e) {
  if (e.key === "Escape") {
    e.stopPropagation();
    repondre(false);
  }
}

watch(
  () => etat.ouvert,
  async (ouvert) => {
    if (ouvert) {
      window.addEventListener("keydown", surTouche, true);
      await nextTick();
      boite.value?.focus();
    } else {
      window.removeEventListener("keydown", surTouche, true);
    }
  }
);

onBeforeUnmount(() => window.removeEventListener("keydown", surTouche, true));
</script>

<template>
  <Teleport to="body">
    <div v-if="etat.ouvert" class="voile" @mousedown.self="repondre(false)">
      <div
        ref="boite"
        class="boite"
        role="alertdialog"
        aria-modal="true"
        :aria-label="etat.titre"
        tabindex="-1"
      >
        <h2>{{ etat.titre }}</h2>
        <p v-if="etat.message" class="message">{{ etat.message }}</p>
        <div class="actions">
          <button
            type="button"
            class="btn btn-outline btn-sm"
            @click="repondre(false)"
          >
            {{ etat.libelleAnnuler }}
          </button>
          <button
            type="button"
            class="btn btn-sm"
            :class="etat.danger ? 'btn-danger' : 'btn-primary'"
            @click="repondre(true)"
          >
            {{ etat.libelleConfirmer }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.voile {
  position: fixed;
  inset: 0;
  z-index: 1100; /* au-dessus des autres fenêtres (1000) */
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  background: rgba(20, 24, 40, 0.55);
}

.boite {
  width: min(440px, 100%);
  padding: 1.5rem;
  background: #fff;
  border-radius: 20px;
  box-shadow: 0 24px 60px rgba(20, 24, 40, 0.3);
  outline: none;
}

h2 {
  margin: 0 0 0.6rem;
  font-size: 1.15rem;
}

.message {
  margin: 0 0 1.4rem;
  color: var(--muted, #666);
  white-space: pre-line;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.6rem;
}

.btn-danger {
  background: #d6336c;
  border-color: #d6336c;
  color: #fff;
}

.btn-danger:hover {
  background: #b82a5b;
}
</style>
