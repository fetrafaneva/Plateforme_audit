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
  remplacerChronogramme,
} from "../services/rapports";

const route = useRoute();
const authStore = useAuthStore();
const idRapport = route.params.id;

const rapport = ref(null);
const form = reactive({});
const difficultes = ref([]);
const chrono = ref([]); // une ligne par journée de l'axe
const chargement = ref(true);
const erreur = ref("");
const message = ref("");
const envoi = ref(false);

const modaleCorrection = ref(false);
const commentaire = ref("");
const erreurModale = ref("");

// Fenêtres de saisie : une journée du chronogramme, une difficulté.
const idJourneeOuverte = ref(null);
const indexDifficulteOuverte = ref(null);

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

// Onglets : chaque écran regroupe quelques sections du modèle de rapport.
const ONGLETS = [
  { cle: "contexte", libelle: "Contexte" },
  { cle: "deroulement", libelle: "Déroulement" },
  { cle: "resultats", libelle: "Résultats" },
  { cle: "bilan", libelle: "Bilan" },
  { cle: "annexes", libelle: "Annexes" },
];
const ongletActif = ref("contexte");

// Sections à rédiger, dans l'ordre du modèle de rapport, rangées par onglet.
const SECTIONS = [
  {
    onglet: "contexte",
    titre: "1 et 2. Contexte et justification de la mission",
    champs: [
      { cle: "contexte", label: "Contexte *", lignes: 8 },
      { cle: "justification", label: "Justification de la mission", lignes: 6 },
    ],
  },
  {
    onglet: "deroulement",
    titre: "3.1 Itinéraire suivi et chronogramme",
    chrono: true,
    champs: [{ cle: "itineraire_reel", label: "Itinéraire réel", lignes: 2 }],
  },
  {
    onglet: "deroulement",
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
    onglet: "deroulement",
    titre: "3.3 Renforcement de capacités",
    ligneDouble: ["nb", "profil_participants"],
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
  {
    onglet: "bilan",
    titre: "6. Points forts, leçons apprises et bonnes pratiques",
    champs: [
      { cle: "points_forts", label: "Points forts", lignes: 3 },
      { cle: "lecons_apprises", label: "Leçons apprises", lignes: 3 },
      { cle: "bonnes_pratiques", label: "Bonnes pratiques", lignes: 3 },
    ],
  },
  {
    onglet: "bilan",
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

const LIBELLES_JOURNEE = {
  prevue: "Prévue",
  realisee: "Réalisée",
  annulee: "Annulée",
};

const manquants = computed(() =>
  rapport.value
    ? rapport.value.completude.elements.filter((e) => !e.ok).length
    : 0
);

const positionOnglet = computed(() =>
  ONGLETS.findIndex((o) => o.cle === ongletActif.value)
);

// Journée et difficulté actuellement ouvertes dans leur fenêtre.
const journeeOuverte = computed(
  () =>
    chrono.value.find((j) => j.id_journee === idJourneeOuverte.value) ?? null
);
const difficulteOuverte = computed(() =>
  indexDifficulteOuverte.value === null
    ? null
    : difficultes.value[indexDifficulteOuverte.value] ?? null
);
const titreJourneeOuverte = computed(() => {
  const j = journeeOuverte.value;
  if (!j || !rapport.value) return "";
  const district = rapport.value.districts.find(
    (d) => d.id_mission_district === j.id_mission_district
  );
  return `${district ? district.nom + ", " : ""}${dateSimple(j.date)}`;
});

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
  chrono.value = r.journees.map((j) => ({
    ...j,
    activites_prevues: j.activites_prevues ?? "",
    activites_realisees: j.activites_realisees ?? "",
    ecart: j.ecart ?? "",
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
  if (chrono.value.length) {
    await remplacerChronogramme(
      idRapport,
      chrono.value.map((j) => ({
        id_journee: j.id_journee,
        activites_prevues: j.activites_prevues,
        activites_realisees: j.activites_realisees,
        ecart: j.ecart,
      }))
    );
  }
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

// ---- Difficultés ----

function ajouterDifficulte() {
  difficultes.value.push({ categorie: "", description: "", solution: "" });
  indexDifficulteOuverte.value = difficultes.value.length - 1;
}

function retirerDifficulte(index) {
  difficultes.value.splice(index, 1);
}

function ouvrirDifficulte(index) {
  indexDifficulteOuverte.value = index;
}

// Une difficulté laissée vide à la fermeture est retirée : elle ne serait pas enregistrée.
function fermerDifficulte() {
  const i = indexDifficulteOuverte.value;
  const d = difficultes.value[i];
  indexDifficulteOuverte.value = null;
  if (
    d &&
    !d.categorie.trim() &&
    !d.description.trim() &&
    rapport.value?.modifiable
  ) {
    retirerDifficulte(i);
  }
}

function supprimerDifficulteOuverte() {
  const i = indexDifficulteOuverte.value;
  indexDifficulteOuverte.value = null;
  if (i !== null) retirerDifficulte(i);
}

// ---- Chronogramme ----

function chronoDe(idMissionDistrict) {
  return chrono.value.filter(
    (j) => j.id_mission_district === idMissionDistrict
  );
}

function nbJourneesRenseignees(idMissionDistrict) {
  return chronoDe(idMissionDistrict).filter((j) =>
    (j.activites_realisees || "").trim()
  ).length;
}

function ouvrirJournee(journee) {
  idJourneeOuverte.value = journee.id_journee;
}

// Les dates des journées n'ont pas d'heure : on évite le décalage de fuseau.
function dateSimple(d) {
  if (!d) return "date à définir";
  const [annee, mois, jour] = String(d).slice(0, 10).split("-");
  return `${jour}/${mois}/${annee}`;
}

// ---- Onglets ----

function allerA(cle) {
  ongletActif.value = cle;
  document
    .getElementById("onglets-rapport")
    ?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function ongletPrecedent() {
  if (positionOnglet.value > 0) allerA(ONGLETS[positionOnglet.value - 1].cle);
}

function ongletSuivant() {
  if (positionOnglet.value < ONGLETS.length - 1)
    allerA(ONGLETS[positionOnglet.value + 1].cle);
}

// Pastille « à compléter » sur un onglet.
function aCompleter(cle) {
  if (!rapport.value) return false;
  if (cle === "annexes") return manquants.value > 0;
  if (!rapport.value.modifiable) return false;
  if (cle === "contexte") return !String(form.contexte ?? "").trim();
  if (cle === "bilan") return !String(form.conclusion ?? "").trim();
  return false;
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
          <div class="groupe-actions">
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
        </div>

        <!-- Fiche de la mission (reprise de la mission) -->
        <section class="card fiche">
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
          <div class="equipe">
            <span class="equipe-titre">Équipe de mission</span>
            <p v-if="rapport.membres.length === 0" class="muted">
              Aucun participant enregistré.
            </p>
            <ul v-else class="membres">
              <li v-for="(m, i) in rapport.membres" :key="i" class="membre">
                <strong>{{ m.nom }}</strong>
                <span class="muted">{{
                  m.fonction || "fonction non précisée"
                }}</span>
              </li>
            </ul>
          </div>
          <p class="muted petit">
            Ces informations viennent de la mission. Pour les corriger, modifie
            la mission.
          </p>
        </section>

        <!-- Onglets -->
        <div
          id="onglets-rapport"
          class="onglets"
          role="tablist"
          aria-label="Sections du rapport"
        >
          <button
            v-for="o in ONGLETS"
            :key="o.cle"
            type="button"
            class="onglet"
            role="tab"
            :aria-selected="ongletActif === o.cle"
            :class="{ actif: ongletActif === o.cle }"
            @click="allerA(o.cle)"
          >
            {{ o.libelle }}
            <span v-if="aCompleter(o.cle)" class="pastille" title="À compléter">
              <span class="sr-only">à compléter</span>
            </span>
          </button>
        </div>

        <!-- Sections à rédiger (rangées par onglet) -->
        <section
          v-for="s in SECTIONS"
          v-show="s.onglet === ongletActif"
          :key="s.titre"
          class="card"
        >
          <h2>{{ s.titre }}</h2>
          <div class="champs" :class="{ 'champs-double': s.ligneDouble }">
            <div
              v-for="c in s.champs"
              :key="c.cle"
              class="field"
              :class="{
                'champ-large': s.ligneDouble && !s.ligneDouble.includes(c.cle),
              }"
            >
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
          </div>

          <!-- Chronogramme : un résumé par journée, la saisie se fait dans une fenêtre -->
          <template v-if="s.chrono">
            <h3 class="sous-titre">Chronogramme réalisé</h3>
            <p v-if="chrono.length === 0" class="muted">
              Aucune journée enregistrée pour cet axe. Ajoute-les depuis « Voir
              le suivi » d'un district, sur la page de la mission : elles
              apparaîtront ici.
            </p>
            <template
              v-for="d in rapport.districts"
              :key="d.id_mission_district"
            >
              <div
                v-if="chronoDe(d.id_mission_district).length"
                class="bloc-district"
              >
                <div class="bloc-district-entete">
                  <h4>{{ d.nom }}</h4>
                  <span class="muted">
                    {{ nbJourneesRenseignees(d.id_mission_district) }} /
                    {{ chronoDe(d.id_mission_district).length }} journée(s)
                    renseignée(s)
                  </span>
                </div>
                <ul class="journees">
                  <li
                    v-for="j in chronoDe(d.id_mission_district)"
                    :key="j.id_journee"
                    class="journee"
                  >
                    <span class="journee-date">{{ dateSimple(j.date) }}</span>
                    <span class="journee-lieu">{{
                      j.lieu || "lieu non précisé"
                    }}</span>
                    <span
                      class="journee-resume"
                      :class="{ vide: !j.activites_realisees }"
                    >
                      {{
                        j.activites_realisees ||
                        "Activités réalisées à renseigner"
                      }}
                    </span>
                    <span class="badge badge-neutral">{{
                      LIBELLES_JOURNEE[j.statut] ?? j.statut
                    }}</span>
                    <button
                      type="button"
                      class="btn btn-outline btn-sm"
                      @click="ouvrirJournee(j)"
                    >
                      {{
                        !rapport.modifiable
                          ? "Voir"
                          : j.activites_realisees
                          ? "Modifier"
                          : "Renseigner"
                      }}
                    </button>
                  </li>
                </ul>
              </div>
            </template>
          </template>
        </section>

        <!-- Résultats : calculés depuis les indicateurs de la mission -->
        <section v-show="ongletActif === 'resultats'" class="card">
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

        <!-- Difficultés : liste résumée, saisie dans une fenêtre -->
        <section v-show="ongletActif === 'resultats'" class="card">
          <div class="entete-section">
            <h2>5. Difficultés rencontrées et solutions apportées</h2>
            <button
              v-if="rapport.modifiable"
              type="button"
              class="btn btn-outline btn-sm"
              @click="ajouterDifficulte"
            >
              + Ajouter une difficulté
            </button>
          </div>
          <p v-if="difficultes.length === 0" class="muted">
            Aucune difficulté signalée.
          </p>
          <ul v-else class="difficultes">
            <li v-for="(d, i) in difficultes" :key="i" class="difficulte">
              <div class="difficulte-texte">
                <strong>{{ d.categorie || "Sans catégorie" }}</strong>
                <span class="difficulte-resume">{{
                  d.description || "Description à renseigner"
                }}</span>
                <span v-if="d.solution" class="difficulte-solution">
                  Solution : {{ d.solution }}
                </span>
              </div>
              <button
                type="button"
                class="btn btn-outline btn-sm"
                @click="ouvrirDifficulte(i)"
              >
                {{ rapport.modifiable ? "Modifier" : "Voir" }}
              </button>
            </li>
          </ul>
        </section>

        <!-- Annexes -->
        <section v-show="ongletActif === 'annexes'" class="card">
          <h2>Annexes à joindre</h2>
          <p class="muted">
            Chaque district a besoin d'une fiche de réception signée, d'une
            fiche de présence et d'au moins une photo. Une fiche d'évaluation
            consolidée est requise pour l'axe. Le rapport ne peut être soumis
            que lorsque tout est fourni.
          </p>
          <PiecesJointes :rapport="rapport" @change="charger(false)" />
        </section>

        <!-- Navigation entre les onglets -->
        <div class="navigation-onglets">
          <button
            v-if="positionOnglet > 0"
            type="button"
            class="btn btn-outline btn-sm"
            @click="ongletPrecedent"
          >
            &larr; {{ ONGLETS[positionOnglet - 1].libelle }}
          </button>
          <span v-else></span>
          <button
            v-if="positionOnglet < ONGLETS.length - 1"
            type="button"
            class="btn btn-primary btn-sm"
            @click="ongletSuivant"
          >
            {{ ONGLETS[positionOnglet + 1].libelle }} &rarr;
          </button>
        </div>
      </template>
    </main>

    <!-- Saisie d'une journée du chronogramme -->
    <ModalDialog
      v-if="journeeOuverte"
      :titre="'Chronogramme : ' + titreJourneeOuverte"
      @fermer="idJourneeOuverte = null"
    >
      <p class="jour-entete">
        <span class="muted">{{
          journeeOuverte.lieu || "lieu non précisé"
        }}</span>
        <span class="badge badge-neutral">{{
          LIBELLES_JOURNEE[journeeOuverte.statut] ?? journeeOuverte.statut
        }}</span>
      </p>
      <div class="field">
        <label for="m-prevues">Activités planifiées</label>
        <textarea
          id="m-prevues"
          v-model="journeeOuverte.activites_prevues"
          rows="3"
          :readonly="!rapport.modifiable"
        ></textarea>
      </div>
      <div class="field">
        <label for="m-realisees">Activités réellement réalisées</label>
        <textarea
          id="m-realisees"
          v-model="journeeOuverte.activites_realisees"
          rows="4"
          :readonly="!rapport.modifiable"
        ></textarea>
      </div>
      <div class="field">
        <label for="m-ecart">Écart / justification</label>
        <textarea
          id="m-ecart"
          v-model="journeeOuverte.ecart"
          rows="3"
          :readonly="!rapport.modifiable"
        ></textarea>
      </div>
      <p v-if="rapport.modifiable" class="muted petit">
        Pense à enregistrer le brouillon pour conserver ces informations.
      </p>
      <div class="actions-modale">
        <button
          type="button"
          class="btn btn-primary btn-sm"
          @click="idJourneeOuverte = null"
        >
          Terminé
        </button>
      </div>
    </ModalDialog>

    <!-- Saisie d'une difficulté -->
    <ModalDialog
      v-if="difficulteOuverte"
      titre="Difficulté rencontrée"
      @fermer="fermerDifficulte"
    >
      <div class="grid-2">
        <div class="field">
          <label for="m-cat">Catégorie</label>
          <input
            id="m-cat"
            v-model="difficulteOuverte.categorie"
            maxlength="100"
            placeholder="ex : Électricité"
            :readonly="!rapport.modifiable"
          />
        </div>
        <div class="field">
          <label for="m-sol">Solution apportée</label>
          <input
            id="m-sol"
            v-model="difficulteOuverte.solution"
            :readonly="!rapport.modifiable"
          />
        </div>
      </div>
      <div class="field">
        <label for="m-desc">Description</label>
        <textarea
          id="m-desc"
          v-model="difficulteOuverte.description"
          rows="4"
          :readonly="!rapport.modifiable"
        ></textarea>
      </div>
      <div class="actions-modale actions-modale-ecartees">
        <button
          v-if="rapport.modifiable"
          type="button"
          class="btn btn-outline btn-sm btn-suppr"
          @click="supprimerDifficulteOuverte"
        >
          Retirer
        </button>
        <span v-else></span>
        <button
          type="button"
          class="btn btn-primary btn-sm"
          @click="fermerDifficulte"
        >
          Terminé
        </button>
      </div>
    </ModalDialog>

    <!-- Demande de correction -->
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

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
}

/* ---- Barre d'actions ---- */
.barre-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.8rem;
  margin-bottom: 1.2rem;
}

.groupe-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 0.6rem;
}

/* ---- Fiche de la mission ---- */
.fiche {
  margin-bottom: 1.4rem;
}

.infos {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
  gap: 1rem 1.5rem;
  margin: 0 0 1.1rem;
}

.infos dt {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--muted);
}

.infos dd {
  margin: 0.15rem 0 0;
}

.equipe-titre {
  display: block;
  margin-bottom: 0.5rem;
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--muted);
}

.membres {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.membre {
  display: flex;
  flex-direction: column;
  padding: 0.45rem 0.8rem;
  background: var(--bg-soft);
  border-radius: 12px;
  font-size: 0.88rem;
}

.membre .muted {
  font-size: 0.8rem;
}

.petit {
  margin: 0.8rem 0 0;
  font-size: 0.82rem;
}

/* ---- Onglets ---- */
.onglets {
  display: flex;
  gap: 0.25rem;
  max-width: 100%;
  margin: 0 0 1.2rem;
  padding: 0.3rem;
  overflow-x: auto;
  background: var(--bg-soft);
  border: 1px solid var(--border);
  border-radius: 999px;
  scroll-margin-top: 1rem;
}

.onglet {
  flex: 1 0 auto;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.5rem 1.1rem;
  background: transparent;
  border: none;
  border-radius: 999px;
  font: inherit;
  font-weight: 600;
  white-space: nowrap;
  color: var(--muted);
  cursor: pointer;
  transition: background 0.15s, color 0.15s, box-shadow 0.15s;
}

.onglet:hover:not(.actif) {
  color: var(--violet);
}

.onglet:focus-visible {
  outline: 2px solid var(--violet);
  outline-offset: 2px;
}

.onglet.actif {
  background: #fff;
  color: var(--violet);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.12);
}

.pastille {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #e8960c;
}

/* ---- Champs ---- */
.champs-double {
  display: grid;
  grid-template-columns: 10rem 1fr;
  column-gap: 1rem;
}

.champs-double .champ-large {
  grid-column: 1 / -1;
}

@media (max-width: 640px) {
  .champs-double {
    grid-template-columns: 1fr;
  }
}

textarea[readonly],
input[readonly] {
  background: var(--bg-soft);
}

.sous-titre {
  margin: 1.4rem 0 0.8rem;
  font-size: 1.05rem;
}

/* ---- Chronogramme (résumé) ---- */
.bloc-district {
  margin-bottom: 1.2rem;
}

.bloc-district-entete {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.5rem;
  margin-bottom: 0.4rem;
}

.bloc-district-entete h4 {
  margin: 0;
  font-size: 0.98rem;
}

.bloc-district-entete .muted {
  font-size: 0.82rem;
}

.journees {
  margin: 0;
  padding: 0;
  list-style: none;
  border: 1px solid var(--border);
  border-radius: 14px;
  overflow: hidden;
}

.journee {
  display: grid;
  grid-template-columns: 6rem 9rem minmax(0, 1fr) auto auto;
  align-items: center;
  gap: 0.8rem;
  padding: 0.6rem 0.9rem;
  border-bottom: 1px solid var(--border);
}

.journee:last-child {
  border-bottom: none;
}

.journee:hover {
  background: var(--bg-soft);
}

.journee-date {
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.journee-lieu {
  font-size: 0.88rem;
  color: var(--muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.journee-resume {
  font-size: 0.88rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.journee-resume.vide {
  color: var(--muted);
  font-style: italic;
}

@media (max-width: 760px) {
  .journee {
    grid-template-columns: auto minmax(0, 1fr) auto;
    grid-template-areas:
      "date lieu badge"
      "resume resume resume"
      "bouton bouton bouton";
    row-gap: 0.4rem;
  }

  .journee-date {
    grid-area: date;
  }

  .journee-lieu {
    grid-area: lieu;
  }

  .journee-resume {
    grid-area: resume;
  }

  .journee .badge {
    grid-area: badge;
  }

  .journee .btn {
    grid-area: bouton;
  }
}

/* ---- Difficultés (résumé) ---- */
.entete-section {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.8rem;
  margin-bottom: 0.8rem;
}

.entete-section h2 {
  margin: 0;
}

.difficultes {
  margin: 0;
  padding: 0;
  list-style: none;
}

.difficulte {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.8rem 0;
  border-bottom: 1px solid var(--border);
}

.difficulte:last-child {
  border-bottom: none;
}

.difficulte-texte {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  min-width: 0;
}

.difficulte-resume {
  font-size: 0.9rem;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.difficulte-solution {
  font-size: 0.85rem;
  color: var(--muted);
}

/* ---- Tableau des résultats ---- */
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

/* ---- Navigation entre onglets ---- */
.navigation-onglets {
  display: flex;
  justify-content: space-between;
  gap: 0.8rem;
  margin-top: 0.5rem;
}

/* ---- Fenêtres ---- */
.jour-entete {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.7rem;
  margin: 0 0 1rem;
}

.actions-modale {
  display: flex;
  justify-content: flex-end;
  gap: 0.6rem;
  margin-top: 1.2rem;
}

.actions-modale-ecartees {
  justify-content: space-between;
}

.btn-suppr {
  color: #b0173f;
  border-color: #f0b8c8;
}

.btn-suppr:hover:not(:disabled),
.btn-suppr:focus-visible {
  background: #fdecf1;
  border-color: #b0173f;
  color: #b0173f;
}
</style>
