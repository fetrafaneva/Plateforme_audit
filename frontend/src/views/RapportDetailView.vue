<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { useRoute } from "vue-router";
import ModalDialog from "../components/ModalDialog.vue";
import PiecesJointes from "../components/PiecesJointes.vue";
import { useAuthStore } from "../stores/auth";
import { confirmer } from "../composables/useConfirmation";
import {
  obtenirRapport,
  modifierRapport,
  remplacerDifficultes,
  soumettreRapport,
  validerRapport,
  demanderCorrection,
  telechargerPdf,
} from "../services/rapports";

const route = useRoute();
const authStore = useAuthStore();
const idRapport = route.params.id;

const rapport = ref(null);
const form = reactive({});
const difficultes = ref([]);
const chargement = ref(true);
const erreur = ref("");
const message = ref("");
const envoi = ref(false);

const modaleCorrection = ref(false);
const commentaire = ref("");
const erreurModale = ref("");

const CHAMPS_TEXTE = [
  "contexte",
  "justification",
  "itineraire_reel",
  "inventaire_materiel",
  "configuration_technique",
  "tests_securite",
  "profil_participants",
  "themes_formation",
  "evaluation_formation",
  "points_forts",
  "lecons_apprises",
  "bonnes_pratiques",
  "conclusion",
  "recommandations",
];

// Sections du rapport, dans l'ordre de ton modèle de rapport.
const SECTIONS_REDACTION = [
  {
    titre: "1 et 2. Contexte et justification de la mission",
    champs: [
      { cle: "contexte", label: "Contexte *", lignes: 6 },
      { cle: "justification", label: "Justification de la mission", lignes: 5 },
    ],
  },
  {
    titre: "3.1 Itinéraire suivi",
    champs: [{ cle: "itineraire_reel", label: "Itinéraire réel", lignes: 2 }],
  },
  {
    titre: "3.2 Travaux techniques réalisés",
    champs: [
      {
        cle: "inventaire_materiel",
        label: "Inventaire du matériel reçu et installé",
        lignes: 3,
      },
      {
        cle: "configuration_technique",
        label: "Configuration technique",
        lignes: 4,
      },
      {
        cle: "tests_securite",
        label: "Tests de connectivité et de sécurité",
        lignes: 3,
      },
    ],
  },
  {
    titre: "3.3 Renforcement de capacités",
    champs: [
      { cle: "nb", label: "Nombre de participants formés", type: "nombre" },
      {
        cle: "profil_participants",
        label: "Profil des participants",
        type: "ligne",
      },
      { cle: "themes_formation", label: "Thèmes abordés", lignes: 4 },
      {
        cle: "evaluation_formation",
        label: "Évaluation de la formation",
        lignes: 4,
      },
    ],
  },
];

const SECTIONS_BILAN = [
  {
    titre: "6. Points forts, leçons apprises et bonnes pratiques",
    champs: [
      { cle: "points_forts", label: "Points forts", lignes: 3 },
      { cle: "lecons_apprises", label: "Leçons apprises", lignes: 3 },
      { cle: "bonnes_pratiques", label: "Bonnes pratiques", lignes: 3 },
    ],
  },
  {
    titre: "7. Conclusion et recommandations",
    champs: [
      { cle: "conclusion", label: "Conclusion générale *", lignes: 5 },
      {
        cle: "recommandations",
        label: "Recommandations (une par ligne)",
        lignes: 5,
      },
    ],
  },
];

const LIBELLES_STATUT = {
  brouillon: "Brouillon",
  soumis: "Soumis",
  a_corriger: "À corriger",
  valide: "Validé",
};

const manquants = computed(() =>
  rapport.value
    ? rapport.value.completude.elements.filter((e) => !e.ok).length
    : 0
);

function classeStatut(statut) {
  if (statut === "valide") return "badge-ok";
  if (statut === "soumis") return "badge-info";
  if (statut === "a_corriger") return "badge-warn";
  return "badge-neutral";
}

function formaterDate(d) {
  return d ? new Date(d).toLocaleDateString("fr-FR") : "—";
}

function formaterDateHeure(d) {
  return d
    ? new Date(d).toLocaleString("fr-FR", {
        dateStyle: "short",
        timeStyle: "short",
      })
    : "—";
}

function messageErreur(e, defaut = "L'opération a échoué.") {
  const detail = e.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length)
    return detail.map((d) => d.msg).join(" ; ");
  return defaut;
}

function remplir(r) {
  for (const cle of CHAMPS_TEXTE) form[cle] = r[cle] ?? "";
  form.nb = r.nb_participants_formes ?? "";
  difficultes.value = r.difficultes.map((d) => ({
    categorie: d.categorie,
    description: d.description,
    solution: d.solution ?? "",
  }));
}

// remplirFormulaire = false : on met à jour l'état du rapport (pièces, statut)
// sans écraser ce que l'utilisateur est en train de saisir.
async function charger(remplirFormulaire = true) {
  erreur.value = "";
  try {
    rapport.value = await obtenirRapport(idRapport);
    if (remplirFormulaire) remplir(rapport.value);
  } catch (e) {
    erreur.value = messageErreur(e, "Impossible de charger le rapport.");
  } finally {
    chargement.value = false;
  }
}

async function enregistrer() {
  const payload = Object.fromEntries(
    CHAMPS_TEXTE.map((cle) => [cle, form[cle]])
  );
  payload.nb_participants_formes = form.nb === "" ? null : Number(form.nb);
  await modifierRapport(idRapport, payload);
  await remplacerDifficultes(
    idRapport,
    difficultes.value
      .filter((d) => d.categorie.trim() && d.description.trim())
      .map((d) => ({
        categorie: d.categorie.trim(),
        description: d.description.trim(),
        solution: d.solution.trim() || null,
      }))
  );
}

async function executer(action, texteSucces) {
  erreur.value = "";
  message.value = "";
  envoi.value = true;
  try {
    await action();
    message.value = texteSucces;
    await charger(true);
  } catch (e) {
    erreur.value = messageErreur(e);
    window.scrollTo({ top: 0, behavior: "smooth" });
  } finally {
    envoi.value = false;
  }
}

function enregistrerBrouillon() {
  return executer(enregistrer, "Brouillon enregistré.");
}

async function soumettre() {
  const ok = await confirmer({
    titre: "Soumettre le rapport",
    message:
      "Une fois soumis, le rapport ne pourra plus être modifié tant que l'administrateur ne l'a pas validé ou renvoyé pour correction.",
    libelleConfirmer: "Soumettre",
  });
  if (!ok) return;
  return executer(async () => {
    await enregistrer();
    await soumettreRapport(idRapport);
  }, "Rapport soumis à l'administrateur.");
}

async function valider() {
  const ok = await confirmer({
    titre: "Valider le rapport",
    message:
      "Le rapport sera marqué comme validé et ne pourra plus être modifié.",
    libelleConfirmer: "Valider",
  });
  if (!ok) return;
  return executer(() => validerRapport(idRapport), "Rapport validé.");
}

function ouvrirCorrection() {
  commentaire.value = "";
  erreurModale.value = "";
  modaleCorrection.value = true;
}

async function envoyerCorrection() {
  erreurModale.value = "";
  envoi.value = true;
  try {
    await demanderCorrection(idRapport, commentaire.value.trim());
    modaleCorrection.value = false;
    message.value = "Rapport renvoyé au chef de mission pour correction.";
    await charger(true);
  } catch (e) {
    erreurModale.value = messageErreur(e);
  } finally {
    envoi.value = false;
  }
}

function ajouterDifficulte() {
  difficultes.value.push({ categorie: "", description: "", solution: "" });
}

function retirerDifficulte(index) {
  difficultes.value.splice(index, 1);
}

async function telechargerLePdf() {
  erreur.value = "";
  try {
    await telechargerPdf(
      rapport.value.id,
      rapport.value.numero_axe ?? rapport.value.id_axe
    );
  } catch (e) {
    erreur.value = messageErreur(e, "Impossible de générer le PDF.");
  }
}

onMounted(async () => {
  if (!authStore.utilisateur) {
    try {
      await authStore.chargerUtilisateur();
    } catch {
      /* l'intercepteur gère le 401 */
    }
  }
  charger(true);
});
</script>

<template>
  <div>
    <header class="hero hero-compact">
      <div class="container">
        <RouterLink class="back" to="/rapports"
          >&larr; Retour aux rapports</RouterLink
        >
        <h1>
          Rapport de mission
          <template v-if="rapport"
            >, axe {{ rapport.numero_axe ?? rapport.id_axe }}</template
          >
        </h1>
        <p v-if="rapport" class="hero-meta">
          <span>{{ rapport.titre_mission }}</span>
          <span>· rédigé par {{ rapport.auteur }}</span>
          <span class="badge badge-light">{{
            LIBELLES_STATUT[rapport.statut]
          }}</span>
        </p>
      </div>
    </header>

    <main class="container page">
      <p v-if="erreur" class="alert-error">{{ erreur }}</p>
      <p v-if="message" class="message-ok">{{ message }}</p>
      <p v-if="chargement" class="card">Chargement...</p>

      <template v-else-if="rapport">
        <!-- Bandeaux de situation -->
        <p v-if="rapport.statut === 'a_corriger'" class="bandeau bandeau-warn">
          <strong
            >Correction demandée par {{ rapport.nom_validateur }} :</strong
          >
          {{ rapport.commentaire_validation }}
        </p>
        <p v-else-if="rapport.statut === 'soumis'" class="bandeau bandeau-info">
          Soumis le {{ formaterDateHeure(rapport.date_soumission) }}, en attente
          de validation.
        </p>
        <p v-else-if="rapport.statut === 'valide'" class="bandeau bandeau-ok">
          Validé par {{ rapport.nom_validateur }} le
          {{ formaterDateHeure(rapport.date_validation) }}.
        </p>

        <!-- Barre d'actions -->
        <div class="barre-actions">
          <span
            class="badge"
            :class="rapport.completude.complet ? 'badge-ok' : 'badge-warn'"
          >
            {{
              rapport.completude.complet
                ? "Dossier complet"
                : `${manquants} pièce(s) et ${rapport.completude.sections_manquantes.length} section(s) manquantes`
            }}
          </span>
          <button
            v-if="rapport.peut_telecharger_pdf"
            class="btn btn-primary btn-sm"
            @click="telechargerLePdf"
          >
            Télécharger le PDF
          </button>
          <template v-if="rapport.modifiable">
            <button
              class="btn btn-outline btn-sm"
              :disabled="envoi"
              @click="enregistrerBrouillon"
            >
              Enregistrer le brouillon
            </button>
            <button
              class="btn btn-primary btn-sm"
              :disabled="envoi"
              @click="soumettre"
            >
              Soumettre
            </button>
          </template>
          <template v-if="rapport.peut_valider">
            <button
              class="btn btn-outline btn-sm"
              :disabled="envoi"
              @click="ouvrirCorrection"
            >
              Demander une correction
            </button>
            <button
              class="btn btn-primary btn-sm"
              :disabled="envoi"
              @click="valider"
            >
              Valider
            </button>
          </template>
        </div>

        <!-- Informations générales (reprises de la mission) -->
        <section class="card">
          <h2>Informations générales</h2>
          <dl class="infos">
            <div>
              <dt>Mission</dt>
              <dd>{{ rapport.titre_mission }}</dd>
            </div>
            <div>
              <dt>Axe d'intervention</dt>
              <dd>Axe {{ rapport.numero_axe ?? rapport.id_axe }}</dd>
            </div>
            <div>
              <dt>Districts couverts</dt>
              <dd>
                <template v-if="rapport.districts.length">
                  {{ rapport.districts.map((d) => d.nom).join(", ") }}
                </template>
                <template v-else>Aucun district rattaché</template>
              </dd>
            </div>
            <div>
              <dt>Période</dt>
              <dd>
                <template v-if="rapport.periode_debut">
                  du {{ formaterDate(rapport.periode_debut) }} au
                  {{ formaterDate(rapport.periode_fin) }}
                </template>
                <template v-else>Non renseignée</template>
              </dd>
            </div>
          </dl>
          <p class="eyebrow">Membres de l'équipe de mission</p>
          <p v-if="rapport.membres.length === 0" class="muted">
            Aucun participant enregistré.
          </p>
          <ul v-else class="list-clean">
            <li v-for="(m, i) in rapport.membres" :key="i" class="membre">
              <strong>{{ m.nom }}</strong>
              <span class="muted">{{
                m.fonction || "fonction non précisée"
              }}</span>
            </li>
          </ul>
          <p class="muted petit">
            Ces informations viennent de la mission. Pour les corriger, modifie
            la mission.
          </p>
        </section>

        <!-- Sections à rédiger -->
        <section v-for="s in SECTIONS_REDACTION" :key="s.titre" class="card">
          <h2>{{ s.titre }}</h2>
          <div v-for="c in s.champs" :key="c.cle" class="field">
            <label :for="'f-' + c.cle">{{ c.label }}</label>
            <input
              v-if="c.type === 'nombre'"
              :id="'f-' + c.cle"
              v-model="form[c.cle]"
              type="number"
              min="0"
              :readonly="!rapport.modifiable"
            />
            <input
              v-else-if="c.type === 'ligne'"
              :id="'f-' + c.cle"
              v-model="form[c.cle]"
              maxlength="255"
              :readonly="!rapport.modifiable"
            />
            <textarea
              v-else
              :id="'f-' + c.cle"
              v-model="form[c.cle]"
              :rows="c.lignes"
              :readonly="!rapport.modifiable"
            ></textarea>
          </div>
        </section>

        <!-- Résultats : calculés depuis les indicateurs de la mission -->
        <section class="card">
          <h2>4. Résultats obtenus et performance</h2>
          <p v-if="rapport.resultats.length === 0" class="muted">
            Aucun indicateur défini pour cette mission.
          </p>
          <div v-else class="defilement">
            <table class="tableau">
              <thead>
                <tr>
                  <th>Résultat attendu</th>
                  <th>Indicateur</th>
                  <th>Cible</th>
                  <th>Réalisé</th>
                  <th>Taux</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(r, i) in rapport.resultats" :key="i">
                  <td>{{ r.resultat_attendu || "—" }}</td>
                  <td>{{ r.indicateur_mesure || "—" }}</td>
                  <td>{{ r.cible || "—" }}</td>
                  <td>{{ r.realise || "—" }}</td>
                  <td>
                    <strong>{{ r.taux !== null ? r.taux + " %" : "—" }}</strong>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <p class="muted petit">
            Ce tableau vient des indicateurs de la mission : mets à jour les
            valeurs réalisées depuis la page de la mission.
          </p>
        </section>

        <!-- Difficultés -->
        <section class="card">
          <h2>5. Difficultés rencontrées et solutions apportées</h2>
          <p v-if="difficultes.length === 0" class="muted">
            Aucune difficulté signalée.
          </p>
          <div v-for="(d, i) in difficultes" :key="i" class="difficulte">
            <div class="grid-2">
              <div class="field">
                <label :for="'d-cat-' + i">Catégorie</label>
                <input
                  :id="'d-cat-' + i"
                  v-model="d.categorie"
                  maxlength="100"
                  placeholder="ex : Électricité"
                  :readonly="!rapport.modifiable"
                />
              </div>
              <div class="field">
                <label :for="'d-sol-' + i">Solution apportée</label>
                <input
                  :id="'d-sol-' + i"
                  v-model="d.solution"
                  :readonly="!rapport.modifiable"
                />
              </div>
            </div>
            <div class="field">
              <label :for="'d-desc-' + i">Description</label>
              <textarea
                :id="'d-desc-' + i"
                v-model="d.description"
                rows="2"
                :readonly="!rapport.modifiable"
              ></textarea>
            </div>
            <button
              v-if="rapport.modifiable"
              type="button"
              class="btn btn-outline btn-sm"
              @click="retirerDifficulte(i)"
            >
              Retirer
            </button>
          </div>
          <button
            v-if="rapport.modifiable"
            type="button"
            class="btn btn-outline btn-sm"
            @click="ajouterDifficulte"
          >
            + Ajouter une difficulté
          </button>
        </section>

        <section v-for="s in SECTIONS_BILAN" :key="s.titre" class="card">
          <h2>{{ s.titre }}</h2>
          <div v-for="c in s.champs" :key="c.cle" class="field">
            <label :for="'f-' + c.cle">{{ c.label }}</label>
            <textarea
              :id="'f-' + c.cle"
              v-model="form[c.cle]"
              :rows="c.lignes"
              :readonly="!rapport.modifiable"
            ></textarea>
          </div>
        </section>

        <!-- Annexes -->
        <section class="card">
          <h2>Annexes à joindre</h2>
          <p class="muted">
            Chaque district a besoin d'une fiche de réception signée, d'une
            fiche de présence et d'au moins une photo. Une fiche d'évaluation
            consolidée est requise pour l'axe. Le rapport ne peut être soumis
            que lorsque tout est fourni.
          </p>
          <PiecesJointes :rapport="rapport" @change="charger(false)" />
        </section>
      </template>
    </main>

    <ModalDialog
      v-if="modaleCorrection"
      titre="Demander une correction"
      @fermer="modaleCorrection = false"
    >
      <p v-if="erreurModale" class="alert-error">{{ erreurModale }}</p>
      <form @submit.prevent="envoyerCorrection">
        <div class="field">
          <label for="commentaire">Ce qui doit être corrigé</label>
          <textarea
            id="commentaire"
            v-model="commentaire"
            rows="4"
            maxlength="1000"
            required
            placeholder="Explique au chef de mission ce qu'il doit compléter ou rectifier."
          ></textarea>
        </div>
        <div class="actions-modale">
          <button
            type="button"
            class="btn btn-outline btn-sm"
            @click="modaleCorrection = false"
          >
            Annuler
          </button>
          <button
            type="submit"
            class="btn btn-primary btn-sm"
            :disabled="envoi || !commentaire.trim()"
          >
            Renvoyer le rapport
          </button>
        </div>
      </form>
    </ModalDialog>
  </div>
</template>

<style scoped>
.message-ok {
  margin: 0 0 1rem;
  padding: 0.75rem 1rem;
  background: #d5faf5;
  color: #067a6f;
  border: 1px solid #a8efe6;
  border-radius: 14px;
}

.bandeau {
  margin: 0 0 1rem;
  padding: 0.8rem 1rem;
  border-radius: 14px;
}

.bandeau-warn {
  background: #fff1d6;
  color: #7a4700;
  border: 1px solid #f3d29a;
}

.bandeau-info {
  background: #dff0fc;
  color: #1767a3;
  border: 1px solid #b7dcf5;
}

.bandeau-ok {
  background: #d5faf5;
  color: #067a6f;
  border: 1px solid #a8efe6;
}

.badge-warn {
  background: #fff1d6;
  color: #9a5b00;
}

.barre-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 0.6rem;
  margin-bottom: 1.5rem;
}

.barre-actions .badge {
  margin-right: auto;
}

.infos {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
  margin: 0 0 1.2rem;
}

.infos dt {
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--muted);
}

.infos dd {
  margin: 0.15rem 0 0;
}

.membre {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
  padding: 0.3rem 0;
}

.petit {
  margin: 0.8rem 0 0;
  font-size: 0.82rem;
}

.difficulte {
  margin-bottom: 1rem;
  padding: 1rem;
  background: var(--bg-soft);
  border-radius: 16px;
}

textarea[readonly],
input[readonly] {
  background: var(--bg-soft);
}

.defilement {
  overflow-x: auto;
}

.tableau {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

.tableau th,
.tableau td {
  text-align: left;
  padding: 0.6rem 0.7rem;
  border-bottom: 1px solid var(--border);
  vertical-align: middle;
}

.tableau th {
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  color: var(--muted);
}

.actions-modale {
  display: flex;
  justify-content: flex-end;
  gap: 0.6rem;
  margin-top: 1.2rem;
}
</style>
