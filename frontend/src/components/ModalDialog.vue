<script setup>
import { ref, onMounted, onBeforeUnmount } from "vue";

defineProps({
  titre: { type: String, required: true },
  large: { type: Boolean, default: false },
});

const emit = defineEmits(["fermer"]);
const boite = ref(null);

function surTouche(e) {
  if (e.key === "Escape") emit("fermer");
}

onMounted(() => {
  document.addEventListener("keydown", surTouche);
  document.body.style.overflow = "hidden";
  boite.value?.focus();
});

onBeforeUnmount(() => {
  document.removeEventListener("keydown", surTouche);
  document.body.style.overflow = "";
});
</script>

<template>
  <Teleport to="body">
    <div class="voile" @mousedown.self="emit('fermer')">
      <div
        ref="boite"
        class="boite"
        :class="{ large }"
        role="dialog"
        aria-modal="true"
        :aria-label="titre"
        tabindex="-1"
      >
        <header class="boite-entete">
          <h2>{{ titre }}</h2>
          <button
            type="button"
            class="fermer"
            aria-label="Fermer"
            @click="emit('fermer')"
          >
            &times;
          </button>
        </header>
        <div class="boite-corps">
          <slot />
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.voile {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  background: rgba(20, 24, 40, 0.55);
}

.boite {
  display: flex;
  flex-direction: column;
  width: min(520px, 100%);
  max-height: min(88vh, 900px);
  background: #fff;
  border-radius: 20px;
  box-shadow: 0 24px 60px rgba(20, 24, 40, 0.3);
  outline: none;
}

.boite.large {
  width: min(820px, 100%);
}

.boite-entete {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1.1rem 1.4rem;
  border-bottom: 1px solid var(--border, #e5e7eb);
}

.boite-entete h2 {
  margin: 0;
  font-size: 1.2rem;
}

.fermer {
  padding: 0 0.3rem;
  background: none;
  border: none;
  font-size: 1.8rem;
  line-height: 1;
  color: var(--muted, #666);
  cursor: pointer;
}

.boite-corps {
  padding: 1.2rem 1.4rem 1.4rem;
  overflow-y: auto;
}
</style>
