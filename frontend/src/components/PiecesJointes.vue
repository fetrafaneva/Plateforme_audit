<script setup>
import { ref, reactive, watch, onBeforeUnmount } from "vue";
import ModalDialog from "./ModalDialog.vue";
import { confirmer } from "../composables/useConfirmation";
import {
  deposerPiece,
  supprimerPiece,
  recupererPiece,
} from "../services/rapports";

const props = defineProps({
  rapport: { type: Object, required: true },
});
const emit = defineEmits(["change"]);

const TAILLE_MAX = 10 * 1024 * 1024;
const DOCUMENTS = ".pdf,.jpg,.jpeg,.png,.docx,.xlsx";

const TYPES_DISTRICT = [
  {
    code: "fiche_reception",
    libelle: "Fiche de réception technique signée",
    accept: DOCUMENTS,
  },
  {
    code: "fiche_presence",
    libelle: "Fiche de présence des participants",
    accept: DOCUMENTS,
  },
  {
    code: "photo",
    libelle: "Photos de la mission",
    accept: ".jpg,.jpeg,.png,.webp",
  },
];
const TYPE_EVALUATION = {
  code: "fiche_evaluation",
  libelle: "Fiche d'évaluation de la formation (consolidée)",
  accept: DOCUMENTS,
};
const TYPE_AUTRE = { code: "autre", libelle: "Autre pièce", accept: DOCUMENTS };

const erreur = ref("");
const miniatures = reactive({}); // id de la pièce -> adresse locale de l'image

// ---------- Aides d'affichage ----------

function piecesDe(code, idMd = null) {
  return props.rapport.pieces.filter(
    (p) =>
      p.type_piece === code && (idMd === null || p.id_mission_district === idMd)
  );
}

function element(code, nomDistrict = null) {
  return props.rapport.completude.elements.find(
    (e) => e.code === code && e.district === nomDistrict
  );
}

function formaterTaille(octets) {
  if (octets < 1024 * 1024)
    return `${Math.max(1, Math.round(octets / 1024))} Ko`;
  return `${(octets / (1024 * 1024)).toFixed(1)} Mo`;
}

function messageErreur(e, defaut) {
  const detail = e.response?.data?.detail;
  return typeof detail === "string" ? detail : defaut;
}

// ---------- Vignettes des photos ----------
// Les images exigent le jeton d'accès : on les télécharge en mémoire plutôt
// que de laisser le navigateur les demander seul avec une balise <img src>.

async function chargerMiniatures() {
  for (const p of props.rapport.pieces) {
    if (p.type_piece === "photo" && !(p.id in miniatures)) {
      miniatures[p.id] = "";
      try {
        miniatures[p.id] = URL.createObjectURL(
          await recupererPiece(props.rapport.id, p.id)
        );
      } catch {
        /* vignette absente : le nom du fichier reste affiché */
      }
    }
  }
}

watch(() => props.rapport.pieces, chargerMiniatures, { immediate: true });

onBeforeUnmount(() => {
  Object.values(miniatures).forEach((url) => url && URL.revokeObjectURL(url));
});

// ---------- Téléchargement et suppression ----------

async function telecharger(piece) {
  erreur.value = "";
  try {
    const blob = await recupererPiece(props.rapport.id, piece.id);
    const url = URL.createObjectURL(blob);
    const lien = document.createElement("a");
    lien.href = url;
    lien.download = piece.nom_original;
    lien.click();
    URL.revokeObjectURL(url);
  } catch (e) {
    erreur.value = messageErreur(e, "Impossible de télécharger ce fichier.");
  }
}

async function supprimer(piece) {
  const ok = await confirmer({
    titre: "Supprimer la pièce",
    message: `« ${piece.nom_original} » sera retirée du rapport.`,
    libelleConfirmer: "Supprimer",
    danger: true,
  });
  if (!ok) return;
  erreur.value = "";
  try {
    await supprimerPiece(props.rapport.id, piece.id);
    emit("change");
  } catch (e) {
    erreur.value = messageErreur(e, "Suppression impossible.");
  }
}

// ---------- Dépôt ----------

const depot = ref(null); // { code, libelle, accept, idMd, nomDistrict }
const fichier = ref(null);
const legende = ref("");
const erreurDepot = ref("");
const envoi = ref(false);

function ouvrirDepot(type, district = null) {
  depot.value = {
    ...type,
    idMd: district ? district.id_mission_district : null,
    nomDistrict: district ? district.nom : null,
  };
  fichier.value = null;
  legende.value = "";
  erreurDepot.value = "";
}

function fermerDepot() {
  depot.value = null;
}

function choisirFichier(evenement) {
  fichier.value = evenement.target.files?.[0] ?? null;
  erreurDepot.value = "";
}

async function envoyer() {
  if (!fichier.value) {
    erreurDepot.value = "Choisis un fichier.";
    return;
  }
  if (fichier.value.size > TAILLE_MAX) {
    erreurDepot.value = "Fichier trop volumineux (10 Mo maximum).";
    return;
  }
  const formulaire = new FormData();
  formulaire.append("fichier", fichier.value);
  formulaire.append("type_piece", depot.value.code);
  if (depot.value.idMd !== null) {
    formulaire.append("id_mission_district", depot.value.idMd);
  }
  if (legende.value.trim()) formulaire.append("legende", legende.value.trim());

  envoi.value = true;
  erreurDepot.value = "";
  try {
    await deposerPiece(props.rapport.id, formulaire);
    fermerDepot();
    emit("change");
  } catch (e) {
    erreurDepot.value = messageErreur(e, "Le dépôt a échoué.");
  } finally {
    envoi.value = false;
  }
}
</script>

<template>
  <div>
    <p v-if="erreur" class="alert-error">{{ erreur }}</p>

    <!-- Pièces requises pour chaque district -->
    <div
      v-for="d in rapport.districts"
      :key="d.id_mission_district"
      class="bloc-district"
    >
      <h3>{{ d.nom }}</h3>

      <div v-for="t in TYPES_DISTRICT" :key="t.code" class="ligne-type">
        <div class="entete-type">
          <span
            class="badge"
            :class="element(t.code, d.nom)?.ok ? 'badge-ok' : 'badge-off'"
          >
            {{ element(t.code, d.nom)?.fourni ?? 0 }}/{{
              element(t.code, d.nom)?.requis ?? 1
            }}
          </span>
          <strong>{{ t.libelle }}</strong>
          <button
            v-if="rapport.modifiable"
            type="button"
            class="btn btn-outline btn-sm"
            @click="ouvrirDepot(t, d)"
          >
            + Ajouter
          </button>
        </div>

        <div v-if="t.code === 'photo'" class="vignettes">
          <figure
            v-for="p in piecesDe(t.code, d.id_mission_district)"
            :key="p.id"
            class="vignette"
          >
            <img
              v-if="miniatures[p.id]"
              :src="miniatures[p.id]"
              :alt="p.legende || p.nom_original"
            />
            <div v-else class="vignette-vide">{{ p.nom_original }}</div>
            <figcaption>
              <span>{{ p.legende || p.nom_original }}</span>
              <button
                v-if="rapport.modifiable"
                type="button"
                class="lien-suppr"
                @click="supprimer(p)"
              >
                Supprimer
              </button>
            </figcaption>
          </figure>
        </div>

        <ul v-else class="list-clean fichiers">
          <li v-for="p in piecesDe(t.code, d.id_mission_district)" :key="p.id">
            <button type="button" class="lien-nom" @click="telecharger(p)">
              {{ p.nom_original }}
            </button>
            <small class="muted">
              {{ formaterTaille(p.taille) }} · {{ p.nom_televerseur }}
            </small>
            <button
              v-if="rapport.modifiable"
              type="button"
              class="lien-suppr"
              @click="supprimer(p)"
            >
              Supprimer
            </button>
          </li>
        </ul>
      </div>
    </div>

    <p v-if="rapport.districts.length === 0" class="muted">
      Aucun district n'est rattaché à cet axe : ajoute-les depuis la page de la
      mission.
    </p>

    <!-- Pièce commune à tout l'axe -->
    <div class="bloc-district">
      <h3>Pièces communes à l'axe</h3>
      <div class="ligne-type">
        <div class="entete-type">
          <span
            class="badge"
            :class="
              element(TYPE_EVALUATION.code)?.ok ? 'badge-ok' : 'badge-off'
            "
          >
            {{ element(TYPE_EVALUATION.code)?.fourni ?? 0 }}/{{
              element(TYPE_EVALUATION.code)?.requis ?? 1
            }}
          </span>
          <strong>{{ TYPE_EVALUATION.libelle }}</strong>
          <button
            v-if="rapport.modifiable"
            type="button"
            class="btn btn-outline btn-sm"
            @click="ouvrirDepot(TYPE_EVALUATION)"
          >
            + Ajouter
          </button>
        </div>
        <ul class="list-clean fichiers">
          <li v-for="p in piecesDe(TYPE_EVALUATION.code)" :key="p.id">
            <button type="button" class="lien-nom" @click="telecharger(p)">
              {{ p.nom_original }}
            </button>
            <small class="muted"
              >{{ formaterTaille(p.taille) }} · {{ p.nom_televerseur }}</small
            >
            <button
              v-if="rapport.modifiable"
              type="button"
              class="lien-suppr"
              @click="supprimer(p)"
            >
              Supprimer
            </button>
          </li>
        </ul>
      </div>

      <div class="ligne-type">
        <div class="entete-type">
          <span class="badge badge-neutral">{{
            piecesDe("autre").length
          }}</span>
          <strong>Autres pièces (facultatif)</strong>
          <button
            v-if="rapport.modifiable"
            type="button"
            class="btn btn-outline btn-sm"
            @click="ouvrirDepot(TYPE_AUTRE)"
          >
            + Ajouter
          </button>
        </div>
        <ul class="list-clean fichiers">
          <li v-for="p in piecesDe('autre')" :key="p.id">
            <button type="button" class="lien-nom" @click="telecharger(p)">
              {{ p.nom_original }}
            </button>
            <small class="muted"
              >{{ formaterTaille(p.taille) }} · {{ p.nom_televerseur }}</small
            >
            <button
              v-if="rapport.modifiable"
              type="button"
              class="lien-suppr"
              @click="supprimer(p)"
            >
              Supprimer
            </button>
          </li>
        </ul>
      </div>
    </div>

    <!-- Fenêtre de dépôt -->
    <ModalDialog
      v-if="depot"
      :titre="`${depot.libelle}${
        depot.nomDistrict ? ' : ' + depot.nomDistrict : ''
      }`"
      @fermer="fermerDepot"
    >
      <p v-if="erreurDepot" class="alert-error">{{ erreurDepot }}</p>
      <form @submit.prevent="envoyer">
        <div class="field">
          <label for="piece-fichier">Fichier (10 Mo maximum)</label>
          <input
            id="piece-fichier"
            type="file"
            :accept="depot.accept"
            required
            @change="choisirFichier"
          />
          <small class="muted"
            >Formats acceptés : {{ depot.accept.replaceAll(",", " ") }}</small
          >
        </div>
        <div class="field">
          <label for="piece-legende">Légende (facultatif)</label>
          <input
            id="piece-legende"
            v-model="legende"
            maxlength="255"
            placeholder="ex : Session de formation des agents"
          />
        </div>
        <div class="actions-modale">
          <button
            type="button"
            class="btn btn-outline btn-sm"
            @click="fermerDepot"
          >
            Annuler
          </button>
          <button
            type="submit"
            class="btn btn-primary btn-sm"
            :disabled="envoi"
          >
            {{ envoi ? "Envoi..." : "Déposer" }}
          </button>
        </div>
      </form>
    </ModalDialog>
  </div>
</template>

<style scoped>
.bloc-district {
  padding: 1rem 0;
  border-bottom: 1px solid var(--border);
}

.bloc-district:last-child {
  border-bottom: none;
}

.bloc-district h3 {
  margin: 0 0 0.6rem;
  font-size: 1.05rem;
}

.ligne-type {
  margin-bottom: 1rem;
}

.entete-type {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.6rem;
}

.fichiers {
  margin: 0.4rem 0 0 0.2rem;
}

.fichiers li {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.6rem;
  padding: 0.25rem 0;
}

.lien-nom,
.lien-suppr {
  padding: 0;
  background: none;
  border: none;
  font: inherit;
  cursor: pointer;
}

.lien-nom {
  font-weight: 600;
  color: var(--violet);
  text-align: left;
}

.lien-nom:hover {
  text-decoration: underline;
}

.lien-suppr {
  margin-left: auto;
  font-size: 0.82rem;
  color: #b0173f;
}

.vignettes {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 0.8rem;
  margin-top: 0.6rem;
}

.vignette {
  margin: 0;
  overflow: hidden;
  border: 1px solid var(--border);
  border-radius: 14px;
  background: #fff;
}

.vignette img,
.vignette-vide {
  display: block;
  width: 100%;
  height: 110px;
  object-fit: cover;
}

.vignette-vide {
  display: grid;
  place-items: center;
  padding: 0.5rem;
  background: var(--bg-soft);
  font-size: 0.78rem;
  text-align: center;
  word-break: break-all;
}

.vignette figcaption {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  padding: 0.4rem 0.6rem;
  font-size: 0.78rem;
}

.actions-modale {
  display: flex;
  justify-content: flex-end;
  gap: 0.6rem;
  margin-top: 1.2rem;
}
</style>
