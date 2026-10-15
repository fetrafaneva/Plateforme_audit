<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import ModalDialog from "../components/ModalDialog.vue";
import { confirmer } from "../composables/useConfirmation";
import {
  obtenirMission,
  modifierMission,
  supprimerMission,
  listerAxes,
  creerAxe,
  supprimerAxe,
  listerEquipes,
  creerEquipe,
  supprimerEquipe,
  listerParticipants,
  creerParticipant,
  modifierParticipant,
  supprimerParticipant,
  listerMissionsDistricts,
  creerMissionDistrict,
  modifierMissionDistrict,
  supprimerMissionDistrict,
  listerDistricts,
  listerTypesActivite,
  listerPhases,
  creerPhase,
  modifierPhase,
  listerJournees,
  creerJournee,
  modifierJournee,
  listerLivrables,
  creerLivrable,
  modifierLivrable,
  listerIndicateurs,
  creerIndicateur,
  modifierIndicateur,
  listerUtilisateurs,
} from "../services/missions";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

const mission = ref(null);
const axesDetails = ref([]);
const districts = ref([]);
const indicateurs = ref([]);
const typesParId = ref({});
const typesActivite = ref([]);
const utilisateurs = ref([]);
const chargement = ref(true);
const erreur = ref("");
const erreurAction = ref("");
const envoi = ref(false);

// Fenêtre ouverte : { type: "mission" | "axe" | "equipe" | "participant" | "compte" | "district" | "indicateur" | "suivi", ...contexte }
const modale = ref(null);
const erreurModale = ref("");
const ongletSuivi = ref("phases");

// Formulaire ouvert à l'intérieur de la fenêtre de suivi : { type: "phase" | "journee" | "livrable", phaseId? }
const sousFormulaire = ref(null);

// Suivi par district, rechargé à chaque ouverture de la fenêtre
const details = reactive({});

// Édition d'un indicateur (directement dans le tableau)
const indicateurEnEdition = ref(null);
const valeurEdition = ref("");

function champsVides() {
  return {
    missionTitre: "",
    missionType: "",
    missionDebut: "",
    missionFin: "",
    numeroAxe: "",
    itineraire: "",
    districtId: "",
    ordreVisite: "",
    typeEquipe: "",
    nomParticipant: "",
    fonction: "",
    utilisateurId: "",
    phaseTypeId: "",
    phaseOrdre: "",
    phaseDuree: "",
    phaseLivrable: "",
    journeeNumero: "",
    journeeDate: "",
    journeeLieu: "",
    livrableType: "",
    livrableDate: "",
    resultat: "",
    mesure: "",
    cible: "",
    realise: "",
  };
}
const champs = reactive(champsVides());

const role = computed(() => authStore.utilisateur?.role);
// Planifier : chef de mission et administrateur
const peutPlanifier = computed(() =>
  ["chef_mission", "administrateur"].includes(role.value)
);
// Saisir l'avancement sur le terrain : le technicien aussi
const peutSaisir = computed(() =>
  ["technicien", "chef_mission", "administrateur"].includes(role.value)
);
const estAdmin = computed(() => role.value === "administrateur");

// Transitions proposées dans l'interface. Le backend accepte toute valeur
// valide du schéma : modifier ces tables ne touche pas à l'API.
const TRANSITIONS_MISSION = {
  planifiee: [
    { vers: "en_cours", libelle: "Démarrer" },
    { vers: "annulee", libelle: "Annuler" },
  ],
  en_cours: [
    { vers: "terminee", libelle: "Terminer" },
    { vers: "annulee", libelle: "Annuler" },
  ],
  terminee: [],
  annulee: [{ vers: "planifiee", libelle: "Replanifier" }],
};

const TRANSITIONS_DISTRICT = {
  a_planifier: [{ vers: "planifie", libelle: "Planifier" }],
  planifie: [{ vers: "en_cours", libelle: "Démarrer" }],
  en_cours: [{ vers: "termine", libelle: "Terminer" }],
  termine: [],
};

const TRANSITIONS_PHASE = {
  a_faire: [{ vers: "en_cours", libelle: "Démarrer" }],
  en_cours: [{ vers: "terminee", libelle: "Terminer" }],
  terminee: [],
};

const TRANSITIONS_JOURNEE = {
  prevue: [
    { vers: "realisee", libelle: "Marquer réalisée" },
    { vers: "annulee", libelle: "Annuler" },
  ],
  realisee: [],
  annulee: [{ vers: "prevue", libelle: "Reprogrammer" }],
};

const LIBELLES_STATUT = {
  planifiee: "planifiée",
  en_cours: "en cours",
  terminee: "terminée",
  annulee: "annulée",
  a_planifier: "à planifier",
  planifie: "planifié",
  termine: "terminé",
  a_faire: "à faire",
  prevue: "prévue",
  realisee: "réalisée",
};

const transitionsMission = computed(
  () => TRANSITIONS_MISSION[mission.value?.statut] ?? []
);

function transitionsDistrict(statut) {
  return TRANSITIONS_DISTRICT[statut] ?? [];
}
function transitionsPhase(statut) {
  return TRANSITIONS_PHASE[statut] ?? [];
}
function transitionsJournee(statut) {
  return TRANSITIONS_JOURNEE[statut] ?? [];
}

function classeStatut(statut) {
  if (statut === "en_cours") return "badge-info";
  if (["terminee", "termine", "realisee"].includes(statut)) return "badge-ok";
  if (statut === "annulee") return "badge-off";
  return "badge-neutral";
}

function initiales(nom) {
  return (nom || "?")
    .split(" ")
    .filter(Boolean)
    .map((mot) => mot[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

function formaterDate(d) {
  return d ? new Date(d).toLocaleDateString("fr-FR") : null;
}

// Pour les champs "date" sans heure (ex : 2026-09-10) : pas de décalage de fuseau
function formaterDateSimple(d) {
  if (!d) return null;
  const [annee, mois, jour] = String(d).slice(0, 10).split("-");
  return `${jour}/${mois}/${annee}`;
}

function messageErreur(e, defaut = "L'opération a échoué.") {
  const detail = e.response?.data?.detail;
  return typeof detail === "string" ? detail : defaut;
}

function libelleAxe(detail) {
  return `Axe ${detail.axe.numero_axe ?? detail.axe.id}`;
}

function districtsDisponibles(detail) {
  const dejaLies = new Set(detail.districts.map((d) => d.district_id));
  return districts.value.filter((d) => !dejaLies.has(d.id));
}

// ---------- Éléments liés à la fenêtre ouverte ----------

const detailModale = computed(() => {
  const axeId = modale.value?.axeId;
  if (axeId == null) return null;
  return axesDetails.value.find((a) => a.axe.id === axeId) ?? null;
});

const equipeModale = computed(() => {
  const equipeId = modale.value?.equipeId;
  if (equipeId == null) return null;
  for (const detail of axesDetails.value) {
    const trouvee = detail.equipes.find((eq) => eq.equipe.id === equipeId);
    if (trouvee) return trouvee.equipe;
  }
  return null;
});

const mdCourant = computed(() => {
  const mdId = modale.value?.mdId;
  if (mdId == null) return null;
  for (const detail of axesDetails.value) {
    const trouve = detail.districts.find((d) => d.id === mdId);
    if (trouve) return trouve;
  }
  return null;
});

const titreModale = computed(() => {
  const m = modale.value;
  if (!m) return "";
  if (m.type === "mission") return "Modifier la mission";
  if (m.type === "axe") return "Nouvel axe";
  if (m.type === "equipe") {
    return detailModale.value
      ? `Nouvelle équipe, ${libelleAxe(detailModale.value)}`
      : "Nouvelle équipe";
  }
  if (m.type === "participant") {
    return equipeModale.value
      ? `Nouveau participant, ${
          equipeModale.value.type_equipe || "équipe #" + equipeModale.value.id
        }`
      : "Nouveau participant";
  }
  if (m.type === "compte") return `Lier un compte à ${m.participantNom}`;
  if (m.type === "district") {
    return detailModale.value
      ? `Lier un district, ${libelleAxe(detailModale.value)}`
      : "Lier un district";
  }
  if (m.type === "indicateur") return "Nouvel indicateur";
  if (m.type === "suivi") {
    return mdCourant.value
      ? `Suivi du district : ${mdCourant.value.nom}`
      : "Suivi du district";
  }
  return "";
});

async function chargerUtilisateurs() {
  if (utilisateurs.value.length) return;
  try {
    utilisateurs.value = await listerUtilisateurs();
  } catch {
    utilisateurs.value = [];
  }
}

function ouvrirModale(type, contexte = {}) {
  Object.assign(champs, champsVides());
  sousFormulaire.value = null;
  erreurModale.value = "";
  ongletSuivi.value = "phases";
  if (type === "axe") {
    champs.numeroAxe = axesDetails.value.length + 1;
  }
  if (type === "mission") {
    champs.missionTitre = mission.value.titre ?? "";
    champs.missionType = mission.value.type_mission ?? "";
    champs.missionDebut = (mission.value.date_debut ?? "").slice(0, 10);
    champs.missionFin = (mission.value.date_fin_prevue ?? "").slice(0, 10);
  }
  modale.value = { type, ...contexte };
  if (type === "participant" || type === "compte") chargerUtilisateurs();
  if (type === "suivi") chargerSuivi(contexte.mdId);
}

function fermerModale() {
  modale.value = null;
  sousFormulaire.value = null;
  erreurModale.value = "";
}

// ---------- Chargement ----------

async function charger(silencieux = false) {
  if (!silencieux) chargement.value = true;
  erreur.value = "";
  try {
    const missionId = route.params.id;
    mission.value = await obtenirMission(missionId);

    const [axes, listeDistricts, types, listeIndicateurs] = await Promise.all([
      listerAxes(missionId),
      listerDistricts(),
      listerTypesActivite(),
      listerIndicateurs(missionId),
    ]);
    districts.value = listeDistricts;
    indicateurs.value = listeIndicateurs;
    typesActivite.value = types;
    typesParId.value = Object.fromEntries(types.map((t) => [t.id, t.libelle]));
    const districtsParId = Object.fromEntries(
      listeDistricts.map((d) => [d.id, d.nom])
    );

    axesDetails.value = await Promise.all(
      axes.map(async (axe) => {
        const [equipes, missionsDistricts] = await Promise.all([
          listerEquipes(axe.id),
          listerMissionsDistricts(axe.id),
        ]);

        const equipesAvecParticipants = await Promise.all(
          equipes.map(async (equipe) => ({
            equipe,
            participants: await listerParticipants(equipe.id),
          }))
        );

        return {
          axe,
          equipes: equipesAvecParticipants,
          districts: missionsDistricts.map((md) => ({
            ...md,
            nom:
              districtsParId[md.district_id] || `District #${md.district_id}`,
          })),
        };
      })
    );
  } catch {
    erreur.value = "Impossible de charger le détail de la mission.";
  } finally {
    chargement.value = false;
  }
}

// ---------- Suivi d'un district : phases, livrables, journées ----------

async function chargerSuivi(mdId, silencieux = false) {
  if (!silencieux) {
    details[mdId] = { chargement: true, erreur: "", phases: [], journees: [] };
  }
  try {
    const [phases, journees] = await Promise.all([
      listerPhases(mdId),
      listerJournees(mdId),
    ]);

    const phasesCompletes = await Promise.all(
      phases.map(async (phase) => ({
        ...phase,
        libelle:
          typesParId.value[phase.type_activite_id] ||
          `Activité #${phase.type_activite_id}`,
        livrables: await listerLivrables(phase.id),
      }))
    );
    phasesCompletes.sort(
      (a, b) => (a.numero_ordre ?? 0) - (b.numero_ordre ?? 0)
    );
    journees.sort((a, b) => (a.numero_jour ?? 0) - (b.numero_jour ?? 0));

    details[mdId] = {
      chargement: false,
      erreur: "",
      phases: phasesCompletes,
      journees,
    };
  } catch {
    details[mdId] = {
      chargement: false,
      erreur: "Impossible de charger le suivi de ce district.",
      phases: [],
      journees: [],
    };
  }
}

async function executerSuivi(mdId, action) {
  erreurModale.value = "";
  envoi.value = true;
  try {
    await action();
    await chargerSuivi(mdId, true);
  } catch (e) {
    erreurModale.value = messageErreur(e);
  } finally {
    envoi.value = false;
  }
}

function confirmerStatut(objet, nom, vers) {
  return confirmer({
    titre: "Changer le statut",
    message: `${objet} « ${nom} » passera au statut « ${
      LIBELLES_STATUT[vers] ?? vers
    } ».`,
    libelleConfirmer: "Confirmer",
    danger: vers === "annulee",
  });
}

async function changerStatutPhase(mdId, phase, vers) {
  if (!(await confirmerStatut("La phase", phase.libelle, vers))) return;
  return executerSuivi(mdId, () => modifierPhase(phase.id, { statut: vers }));
}

async function changerStatutJournee(mdId, journee, vers) {
  if (
    !(await confirmerStatut(
      "La journée",
      `jour ${journee.numero_jour ?? "–"}`,
      vers
    ))
  )
    return;
  return executerSuivi(mdId, () =>
    modifierJournee(journee.id, { statut: vers })
  );
}

async function signerLivrable(mdId, livrable) {
  const ok = await confirmer({
    titre: "Marquer le livrable signé",
    message: `« ${
      livrable.type_livrable || "Livrable"
    } » sera marqué comme signé. Cette action ne peut pas être annulée depuis l'interface.`,
    libelleConfirmer: "Marquer signé",
  });
  if (!ok) return;
  return executerSuivi(mdId, () =>
    modifierLivrable(livrable.id, { signe: true })
  );
}

async function changerStatutDistrict(md, vers) {
  if (!(await confirmerStatut("Le district", md.nom, vers))) return;
  erreurModale.value = "";
  envoi.value = true;
  try {
    await modifierMissionDistrict(md.id, { statut: vers });
    await charger(true);
  } catch (e) {
    erreurModale.value = messageErreur(e);
  } finally {
    envoi.value = false;
  }
}

// ---------- Indicateurs ----------

function commencerEdition(indicateur) {
  indicateurEnEdition.value = indicateur.id;
  valeurEdition.value = indicateur.valeur_realisee ?? "";
}

function annulerEdition() {
  indicateurEnEdition.value = null;
}

async function enregistrerIndicateur(indicateur) {
  erreurAction.value = "";
  envoi.value = true;
  try {
    await modifierIndicateur(indicateur.id, {
      valeur_realisee: valeurEdition.value.trim(),
    });
    indicateurEnEdition.value = null;
    indicateurs.value = await listerIndicateurs(mission.value.id);
  } catch (e) {
    erreurAction.value = messageErreur(e);
    window.scrollTo({ top: 0, behavior: "smooth" });
  } finally {
    envoi.value = false;
  }
}

// ---------- Formulaires (dans les fenêtres) ----------

async function executerFormulaire(action) {
  erreurModale.value = "";
  envoi.value = true;
  try {
    await action();
    fermerModale();
    await charger(true);
  } catch (e) {
    erreurModale.value = messageErreur(e);
  } finally {
    envoi.value = false;
  }
}

function modifierLaMission() {
  const payload = {
    titre: champs.missionTitre.trim(),
    type_mission: champs.missionType.trim(),
  };
  if (champs.missionDebut)
    payload.date_debut = `${champs.missionDebut}T00:00:00`;
  if (champs.missionFin)
    payload.date_fin_prevue = `${champs.missionFin}T00:00:00`;
  return executerFormulaire(() => modifierMission(mission.value.id, payload));
}

function ajouterAxe() {
  return executerFormulaire(() =>
    creerAxe({
      mission_id: mission.value.id,
      numero_axe: champs.numeroAxe ? Number(champs.numeroAxe) : null,
      itineraire_principal: champs.itineraire.trim() || null,
    })
  );
}

function ajouterEquipe() {
  return executerFormulaire(() =>
    creerEquipe({
      axe_id: modale.value.axeId,
      type_equipe: champs.typeEquipe.trim() || null,
    })
  );
}

function ajouterParticipant() {
  return executerFormulaire(() =>
    creerParticipant({
      equipe_id: modale.value.equipeId,
      nom: champs.nomParticipant.trim(),
      fonction: champs.fonction.trim() || null,
      id_utilisateur: champs.utilisateurId
        ? Number(champs.utilisateurId)
        : null,
    })
  );
}

function lierCompte() {
  return executerFormulaire(() =>
    modifierParticipant(modale.value.participantId, {
      id_utilisateur: Number(champs.utilisateurId),
    })
  );
}

function lierDistrict() {
  const detail = detailModale.value;
  return executerFormulaire(() =>
    creerMissionDistrict({
      axe_id: detail.axe.id,
      district_id: Number(champs.districtId),
      ordre_visite: champs.ordreVisite
        ? Number(champs.ordreVisite)
        : detail.districts.length + 1,
    })
  );
}

function ajouterIndicateur() {
  return executerFormulaire(() =>
    creerIndicateur({
      mission_id: mission.value.id,
      resultat_attendu: champs.resultat.trim() || null,
      indicateur_mesure: champs.mesure.trim() || null,
      cible: champs.cible.trim() || null,
      valeur_realisee: champs.realise.trim() || null,
    })
  );
}

// ---------- Formulaires dans la fenêtre de suivi ----------

function ouvrirSousFormulaire(type, contexte = {}) {
  Object.assign(champs, champsVides());
  erreurModale.value = "";
  const suivi = details[modale.value.mdId];
  if (type === "phase") champs.phaseOrdre = (suivi?.phases.length ?? 0) + 1;
  if (type === "journee")
    champs.journeeNumero = (suivi?.journees.length ?? 0) + 1;
  sousFormulaire.value = { type, ...contexte };
}

function fermerSousFormulaire() {
  sousFormulaire.value = null;
  erreurModale.value = "";
}

async function executerSousFormulaire(action) {
  erreurModale.value = "";
  envoi.value = true;
  try {
    await action();
    sousFormulaire.value = null;
    await chargerSuivi(modale.value.mdId, true);
  } catch (e) {
    erreurModale.value = messageErreur(e);
  } finally {
    envoi.value = false;
  }
}

function ajouterPhase() {
  return executerSousFormulaire(() =>
    creerPhase({
      mission_district_id: modale.value.mdId,
      type_activite_id: Number(champs.phaseTypeId),
      numero_ordre: champs.phaseOrdre ? Number(champs.phaseOrdre) : null,
      duree_prevue: champs.phaseDuree.trim() || null,
      livrable_attendu: champs.phaseLivrable.trim() || null,
    })
  );
}

function ajouterJournee() {
  return executerSousFormulaire(() =>
    creerJournee({
      mission_district_id: modale.value.mdId,
      numero_jour: champs.journeeNumero ? Number(champs.journeeNumero) : null,
      date: champs.journeeDate || null,
      lieu: champs.journeeLieu.trim() || null,
    })
  );
}

function ajouterLivrable() {
  return executerSousFormulaire(() =>
    creerLivrable({
      phase_id: sousFormulaire.value.phaseId,
      type_livrable: champs.livrableType.trim() || null,
      date_production: champs.livrableDate
        ? `${champs.livrableDate}T00:00:00`
        : null,
    })
  );
}

// ---------- Actions sur la mission ----------

async function changerStatutMission(vers) {
  if (!(await confirmerStatut("La mission", mission.value.titre, vers))) return;
  erreurAction.value = "";
  envoi.value = true;
  try {
    await modifierMission(mission.value.id, { statut: vers });
    await charger(true);
  } catch (e) {
    erreurAction.value = messageErreur(e);
    window.scrollTo({ top: 0, behavior: "smooth" });
  } finally {
    envoi.value = false;
  }
}

// ---------- Suppressions ----------
// Le serveur refuse de supprimer un élément qui contient encore d'autres éléments
// (une équipe avec des participants, par exemple) et explique pourquoi : ce message
// est affiché tel quel en haut de la page.

async function supprimerElement({ titre, message, action, apres }) {
  const ok = await confirmer({
    titre,
    message,
    libelleConfirmer: "Supprimer",
    danger: true,
  });
  if (!ok) return;
  erreurAction.value = "";
  try {
    await action();
    if (apres) apres();
    else await charger(true);
  } catch (e) {
    erreurAction.value = messageErreur(e);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
}

function retirerParticipant(participant) {
  return supprimerElement({
    titre: "Retirer le participant",
    message: `« ${participant.nom} » sera retiré de l'équipe.`,
    action: () => supprimerParticipant(participant.id),
  });
}

function retirerEquipe(eq) {
  return supprimerElement({
    titre: "Supprimer l'équipe",
    message: `L'équipe « ${
      eq.equipe.type_equipe || "#" + eq.equipe.id
    } » sera supprimée. Elle doit d'abord ne plus avoir de participant.`,
    action: () => supprimerEquipe(eq.equipe.id),
  });
}

function retirerDistrictLie(md) {
  return supprimerElement({
    titre: "Retirer le district",
    message: `« ${md.nom} » ne sera plus rattaché à cet axe. Impossible tant qu'il a des phases ou des journées.`,
    action: () => supprimerMissionDistrict(md.id),
  });
}

function retirerAxe(detail) {
  return supprimerElement({
    titre: "Supprimer l'axe",
    message: `${libelleAxe(
      detail
    )} sera supprimé. Il doit d'abord ne plus avoir ni équipe ni district.`,
    action: () => supprimerAxe(detail.axe.id),
  });
}

function retirerMission() {
  return supprimerElement({
    titre: "Supprimer la mission",
    message: `La mission « ${mission.value.titre} » sera supprimée définitivement. Elle doit d'abord ne plus avoir d'axe ni d'indicateur.`,
    action: () => supprimerMission(mission.value.id),
    apres: () => router.push({ name: "missions" }),
  });
}

onMounted(async () => {
  if (!authStore.utilisateur) {
    try {
      await authStore.chargerUtilisateur();
    } catch {
      /* l'intercepteur gère le 401 */
    }
  }
  charger();
});
</script>

<template>
  <div>
    <header class="hero hero-compact">
      <div class="container">
        <RouterLink class="back" to="/missions"
          >&larr; Retour aux missions</RouterLink
        >
        <h1>{{ mission ? mission.titre : "Détail de la mission" }}</h1>
        <p v-if="mission" class="hero-meta">
          <span>{{ mission.type_mission || "Type non précisé" }}</span>
          <span v-if="mission.date_debut">
            · du {{ formaterDate(mission.date_debut) }}
            <template v-if="mission.date_fin_prevue">
              au {{ formaterDate(mission.date_fin_prevue) }}
            </template>
          </span>
          <span class="badge badge-light">{{ mission.statut }}</span>
        </p>
      </div>
    </header>

    <main class="container page">
      <p v-if="erreur" class="alert-error">{{ erreur }}</p>
      <p v-if="chargement" class="card">Chargement...</p>

      <template v-else-if="mission">
        <div v-if="peutPlanifier" class="barre-actions">
          <button
            v-for="t in transitionsMission"
            :key="t.vers"
            class="btn btn-outline btn-sm"
            :disabled="envoi"
            @click="changerStatutMission(t.vers)"
          >
            {{ t.libelle }}
          </button>
          <button
            class="btn btn-outline btn-sm"
            @click="ouvrirModale('mission')"
          >
            Modifier la mission
          </button>
          <button class="btn btn-primary btn-sm" @click="ouvrirModale('axe')">
            + Ajouter un axe
          </button>
          <button v-if="estAdmin" class="btn-suppr" @click="retirerMission">
            Supprimer la mission
          </button>
        </div>

        <p v-if="erreurAction" class="alert-error">{{ erreurAction }}</p>

        <!-- Indicateurs de performance -->
        <section class="card">
          <p class="eyebrow">Indicateurs de performance</p>
          <button
            v-if="peutPlanifier"
            class="btn btn-outline btn-sm"
            style="margin-bottom: 0.8rem"
            @click="ouvrirModale('indicateur')"
          >
            + Ajouter un indicateur
          </button>
          <p v-if="indicateurs.length === 0" class="muted">
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
                  <th v-if="peutPlanifier"></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="ind in indicateurs" :key="ind.id">
                  <td>{{ ind.resultat_attendu || "—" }}</td>
                  <td>{{ ind.indicateur_mesure || "—" }}</td>
                  <td>{{ ind.cible || "—" }}</td>
                  <td>
                    <input
                      v-if="indicateurEnEdition === ind.id"
                      v-model="valeurEdition"
                      class="saisie-courte"
                      @keyup.enter="enregistrerIndicateur(ind)"
                    />
                    <strong v-else>{{ ind.valeur_realisee || "—" }}</strong>
                  </td>
                  <td v-if="peutPlanifier" class="cellule-actions">
                    <template v-if="indicateurEnEdition === ind.id">
                      <button
                        class="btn btn-primary btn-sm"
                        :disabled="envoi"
                        @click="enregistrerIndicateur(ind)"
                      >
                        Enregistrer
                      </button>
                      <button
                        class="btn btn-outline btn-sm"
                        @click="annulerEdition"
                      >
                        Annuler
                      </button>
                    </template>
                    <button
                      v-else
                      class="btn btn-outline btn-sm"
                      @click="commencerEdition(ind)"
                    >
                      Modifier
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <p v-if="axesDetails.length === 0" class="card muted">
          Aucun axe créé pour cette mission.
        </p>

        <article
          v-for="detail in axesDetails"
          :key="detail.axe.id"
          class="card"
        >
          <div class="entete-axe">
            <h2>{{ libelleAxe(detail) }}</h2>
            <button
              v-if="peutPlanifier"
              class="btn-suppr"
              @click="retirerAxe(detail)"
            >
              Supprimer l'axe
            </button>
          </div>
          <p v-if="detail.axe.itineraire_principal" class="muted">
            {{ detail.axe.itineraire_principal }}
          </p>

          <div class="grid-2">
            <!-- Districts -->
            <section>
              <p class="eyebrow">Districts visités</p>
              <ul v-if="detail.districts.length" class="list-clean">
                <li
                  v-for="d in detail.districts"
                  :key="d.id"
                  class="ligne-district"
                >
                  <span>{{ d.nom }}</span>
                  <span class="actions-ligne">
                    <span class="badge" :class="classeStatut(d.statut)">{{
                      d.statut
                    }}</span>
                    <button
                      class="btn btn-outline btn-sm"
                      @click="
                        ouvrirModale('suivi', {
                          axeId: detail.axe.id,
                          mdId: d.id,
                        })
                      "
                    >
                      Voir le suivi
                    </button>
                    <button
                      v-if="peutPlanifier"
                      class="btn-suppr"
                      @click="retirerDistrictLie(d)"
                    >
                      Retirer
                    </button>
                  </span>
                </li>
              </ul>
              <p v-else class="muted">Aucun district rattaché à cet axe.</p>

              <button
                v-if="peutPlanifier"
                class="btn btn-outline btn-sm lien-ajout"
                @click="ouvrirModale('district', { axeId: detail.axe.id })"
              >
                + Lier un district
              </button>
            </section>

            <!-- Équipes -->
            <section>
              <p class="eyebrow">Équipes</p>
              <p v-if="detail.equipes.length === 0" class="muted">
                Aucune équipe pour cet axe.
              </p>

              <div
                v-for="eq in detail.equipes"
                :key="eq.equipe.id"
                class="equipe-bloc"
              >
                <div class="entete-equipe">
                  <h3>
                    {{ eq.equipe.type_equipe || "Équipe #" + eq.equipe.id }}
                  </h3>
                  <button
                    v-if="peutPlanifier"
                    class="btn-suppr"
                    @click="retirerEquipe(eq)"
                  >
                    Supprimer
                  </button>
                </div>
                <ul v-if="eq.participants.length" class="list-clean">
                  <li
                    v-for="p in eq.participants"
                    :key="p.id"
                    class="ligne-participant"
                  >
                    <span class="avatar">{{ initiales(p.nom) }}</span>
                    <span>
                      <strong>{{ p.nom }}</strong
                      ><br />
                      <small class="muted">{{
                        p.fonction || "Rôle non précisé"
                      }}</small>
                    </span>
                    <span class="actions-participant">
                      <span v-if="p.id_utilisateur" class="badge badge-ok"
                        >Compte lié</span
                      >
                      <button
                        v-else-if="peutPlanifier"
                        class="btn btn-outline btn-sm"
                        @click="
                          ouvrirModale('compte', {
                            participantId: p.id,
                            participantNom: p.nom,
                          })
                        "
                      >
                        Lier un compte
                      </button>
                      <button
                        v-if="peutPlanifier"
                        class="btn-suppr"
                        @click="retirerParticipant(p)"
                      >
                        Retirer
                      </button>
                    </span>
                  </li>
                </ul>
                <p v-else class="muted">Aucun participant.</p>

                <button
                  v-if="peutPlanifier"
                  class="btn btn-outline btn-sm lien-ajout"
                  @click="
                    ouvrirModale('participant', { equipeId: eq.equipe.id })
                  "
                >
                  + Participant
                </button>
              </div>

              <button
                v-if="peutPlanifier"
                class="btn btn-outline btn-sm lien-ajout"
                @click="ouvrirModale('equipe', { axeId: detail.axe.id })"
              >
                + Ajouter une équipe
              </button>
            </section>
          </div>
        </article>
      </template>
    </main>

    <!-- Fenêtres modales -->
    <ModalDialog
      v-if="modale"
      :titre="titreModale"
      :large="modale.type === 'suivi'"
      @fermer="fermerModale"
    >
      <p v-if="erreurModale" class="alert-error">{{ erreurModale }}</p>

      <!-- Modifier la mission -->
      <form
        v-if="modale.type === 'mission'"
        @submit.prevent="modifierLaMission"
      >
        <div class="field">
          <label for="m-titre">Titre</label>
          <input id="m-titre" v-model="champs.missionTitre" required />
        </div>
        <div class="field">
          <label for="m-type">Type de mission</label>
          <input
            id="m-type"
            v-model="champs.missionType"
            placeholder="ex : deploiement_serveur"
          />
        </div>
        <div class="grid-2">
          <div class="field">
            <label for="m-debut">Date de début</label>
            <input id="m-debut" v-model="champs.missionDebut" type="date" />
          </div>
          <div class="field">
            <label for="m-fin">Date de fin prévue</label>
            <input id="m-fin" v-model="champs.missionFin" type="date" />
          </div>
        </div>
        <p class="muted petit">
          Le statut se change avec les boutons « Démarrer », « Terminer » ou «
          Annuler ».
        </p>
        <div class="modal-actions">
          <button
            type="button"
            class="btn btn-outline btn-sm"
            @click="fermerModale"
          >
            Annuler
          </button>
          <button
            type="submit"
            class="btn btn-primary btn-sm"
            :disabled="envoi"
          >
            {{ envoi ? "Enregistrement..." : "Enregistrer" }}
          </button>
        </div>
      </form>

      <!-- Nouvel axe -->
      <form v-else-if="modale.type === 'axe'" @submit.prevent="ajouterAxe">
        <div class="field">
          <label for="num-axe">Numéro de l'axe</label>
          <input
            id="num-axe"
            v-model="champs.numeroAxe"
            type="number"
            min="1"
          />
        </div>
        <div class="field">
          <label for="itineraire">Itinéraire principal</label>
          <input
            id="itineraire"
            v-model="champs.itineraire"
            placeholder="ex : Tanà → Ambovombe → Tanà"
          />
        </div>
        <div class="modal-actions">
          <button
            type="button"
            class="btn btn-outline btn-sm"
            @click="fermerModale"
          >
            Annuler
          </button>
          <button
            type="submit"
            class="btn btn-primary btn-sm"
            :disabled="envoi"
          >
            {{ envoi ? "Création..." : "Créer l'axe" }}
          </button>
        </div>
      </form>

      <!-- Nouvelle équipe -->
      <form
        v-else-if="modale.type === 'equipe'"
        @submit.prevent="ajouterEquipe"
      >
        <div class="field">
          <label for="type-equipe">Type d'équipe</label>
          <input
            id="type-equipe"
            v-model="champs.typeEquipe"
            placeholder="ex : DSID, SI CSB"
          />
        </div>
        <div class="modal-actions">
          <button
            type="button"
            class="btn btn-outline btn-sm"
            @click="fermerModale"
          >
            Annuler
          </button>
          <button
            type="submit"
            class="btn btn-primary btn-sm"
            :disabled="envoi"
          >
            Créer l'équipe
          </button>
        </div>
      </form>

      <!-- Nouveau participant -->
      <form
        v-else-if="modale.type === 'participant'"
        @submit.prevent="ajouterParticipant"
      >
        <div class="field">
          <label for="nom-participant">Nom</label>
          <input
            id="nom-participant"
            v-model="champs.nomParticipant"
            required
          />
        </div>
        <div class="field">
          <label for="fonction">Fonction</label>
          <input
            id="fonction"
            v-model="champs.fonction"
            placeholder="ex : Technicien serveur"
          />
        </div>
        <div class="field">
          <label for="compte-participant"
            >Compte utilisateur (facultatif)</label
          >
          <select id="compte-participant" v-model="champs.utilisateurId">
            <option value="">Aucun compte</option>
            <option
              v-for="u in utilisateurs"
              :key="u.id_utilisateur"
              :value="u.id_utilisateur"
            >
              {{ u.prenom }} {{ u.nom }} ({{ u.matricule }}), {{ u.role }}
            </option>
          </select>
        </div>
        <div class="modal-actions">
          <button
            type="button"
            class="btn btn-outline btn-sm"
            @click="fermerModale"
          >
            Annuler
          </button>
          <button
            type="submit"
            class="btn btn-primary btn-sm"
            :disabled="envoi"
          >
            Ajouter
          </button>
        </div>
      </form>

      <!-- Lier un compte à un participant existant -->
      <form v-else-if="modale.type === 'compte'" @submit.prevent="lierCompte">
        <p v-if="utilisateurs.length === 0" class="muted">
          Aucun compte disponible.
        </p>
        <div v-else class="field">
          <label for="compte">Compte utilisateur</label>
          <select id="compte" v-model="champs.utilisateurId" required>
            <option value="" disabled>Choisir un compte</option>
            <option
              v-for="u in utilisateurs"
              :key="u.id_utilisateur"
              :value="u.id_utilisateur"
            >
              {{ u.prenom }} {{ u.nom }} ({{ u.matricule }}), {{ u.role }}
            </option>
          </select>
        </div>
        <div class="modal-actions">
          <button
            type="button"
            class="btn btn-outline btn-sm"
            @click="fermerModale"
          >
            Annuler
          </button>
          <button
            v-if="utilisateurs.length"
            type="submit"
            class="btn btn-primary btn-sm"
            :disabled="envoi"
          >
            Lier le compte
          </button>
        </div>
      </form>

      <!-- Lier un district -->
      <form
        v-else-if="modale.type === 'district' && detailModale"
        @submit.prevent="lierDistrict"
      >
        <p v-if="districtsDisponibles(detailModale).length === 0" class="muted">
          Aucun district disponible : l'administrateur doit d'abord en ajouter
          dans « Référentiels ».
        </p>
        <template v-else>
          <div class="field">
            <label for="district">District</label>
            <select id="district" v-model="champs.districtId" required>
              <option value="" disabled>Choisir un district</option>
              <option
                v-for="d in districtsDisponibles(detailModale)"
                :key="d.id"
                :value="d.id"
              >
                {{ d.nom }}
              </option>
            </select>
          </div>
          <div class="field">
            <label for="ordre">Ordre de visite (facultatif)</label>
            <input
              id="ordre"
              v-model="champs.ordreVisite"
              type="number"
              min="1"
            />
          </div>
        </template>
        <div class="modal-actions">
          <button
            type="button"
            class="btn btn-outline btn-sm"
            @click="fermerModale"
          >
            Annuler
          </button>
          <button
            v-if="districtsDisponibles(detailModale).length"
            type="submit"
            class="btn btn-primary btn-sm"
            :disabled="envoi"
          >
            Lier le district
          </button>
        </div>
      </form>

      <!-- Nouvel indicateur -->
      <form
        v-else-if="modale.type === 'indicateur'"
        @submit.prevent="ajouterIndicateur"
      >
        <div class="field">
          <label for="ind-resultat">Résultat attendu</label>
          <input
            id="ind-resultat"
            v-model="champs.resultat"
            placeholder="ex : 16 serveurs opérationnels"
            required
          />
        </div>
        <div class="field">
          <label for="ind-mesure">Indicateur de mesure</label>
          <input
            id="ind-mesure"
            v-model="champs.mesure"
            placeholder="ex : Nombre de serveurs"
          />
        </div>
        <div class="grid-2">
          <div class="field">
            <label for="ind-cible">Cible</label>
            <input
              id="ind-cible"
              v-model="champs.cible"
              placeholder="ex : 16"
            />
          </div>
          <div class="field">
            <label for="ind-realise">Réalisé (facultatif)</label>
            <input id="ind-realise" v-model="champs.realise" />
          </div>
        </div>
        <div class="modal-actions">
          <button
            type="button"
            class="btn btn-outline btn-sm"
            @click="fermerModale"
          >
            Annuler
          </button>
          <button
            type="submit"
            class="btn btn-primary btn-sm"
            :disabled="envoi"
          >
            Créer l'indicateur
          </button>
        </div>
      </form>

      <!-- Suivi d'un district -->
      <template v-else-if="modale.type === 'suivi' && mdCourant">
        <div class="entete-suivi">
          <span class="badge" :class="classeStatut(mdCourant.statut)">{{
            mdCourant.statut
          }}</span>
          <template v-if="peutPlanifier">
            <button
              v-for="t in transitionsDistrict(mdCourant.statut)"
              :key="t.vers"
              class="btn btn-outline btn-sm"
              :disabled="envoi"
              @click="changerStatutDistrict(mdCourant, t.vers)"
            >
              {{ t.libelle }} le district
            </button>
          </template>
        </div>

        <div v-if="!sousFormulaire" class="onglets">
          <button
            type="button"
            class="onglet"
            :class="{ actif: ongletSuivi === 'phases' }"
            @click="ongletSuivi = 'phases'"
          >
            Phases et livrables
          </button>
          <button
            type="button"
            class="onglet"
            :class="{ actif: ongletSuivi === 'journees' }"
            @click="ongletSuivi = 'journees'"
          >
            Journées
          </button>
        </div>

        <p
          v-if="!details[mdCourant.id] || details[mdCourant.id].chargement"
          class="muted"
        >
          Chargement du suivi...
        </p>
        <p v-else-if="details[mdCourant.id].erreur" class="alert-error">
          {{ details[mdCourant.id].erreur }}
        </p>

        <!-- Formulaires de création (phase, journée, livrable) -->
        <template v-else-if="sousFormulaire">
          <form
            v-if="sousFormulaire.type === 'phase'"
            @submit.prevent="ajouterPhase"
          >
            <p v-if="typesActivite.length === 0" class="muted">
              Aucun type d'activité : l'administrateur doit d'abord en ajouter
              dans « Référentiels ».
            </p>
            <template v-else>
              <div class="field">
                <label for="phase-type">Type d'activité</label>
                <select id="phase-type" v-model="champs.phaseTypeId" required>
                  <option value="" disabled>Choisir une activité</option>
                  <option v-for="t in typesActivite" :key="t.id" :value="t.id">
                    {{ t.libelle }}
                  </option>
                </select>
              </div>
              <div class="field">
                <label for="phase-ordre">Ordre</label>
                <input
                  id="phase-ordre"
                  v-model="champs.phaseOrdre"
                  type="number"
                  min="1"
                />
              </div>
              <div class="field">
                <label for="phase-duree">Durée prévue</label>
                <input
                  id="phase-duree"
                  v-model="champs.phaseDuree"
                  placeholder="ex : J1-J2"
                />
              </div>
              <div class="field">
                <label for="phase-livrable">Livrable attendu</label>
                <input
                  id="phase-livrable"
                  v-model="champs.phaseLivrable"
                  placeholder="ex : PV d'installation"
                />
              </div>
            </template>
            <div class="modal-actions">
              <button
                type="button"
                class="btn btn-outline btn-sm"
                @click="fermerSousFormulaire"
              >
                Retour
              </button>
              <button
                v-if="typesActivite.length"
                type="submit"
                class="btn btn-primary btn-sm"
                :disabled="envoi"
              >
                Créer la phase
              </button>
            </div>
          </form>

          <form
            v-else-if="sousFormulaire.type === 'journee'"
            @submit.prevent="ajouterJournee"
          >
            <div class="field">
              <label for="jour-num">Numéro du jour</label>
              <input
                id="jour-num"
                v-model="champs.journeeNumero"
                type="number"
                min="1"
              />
            </div>
            <div class="field">
              <label for="jour-date">Date</label>
              <input id="jour-date" v-model="champs.journeeDate" type="date" />
            </div>
            <div class="field">
              <label for="jour-lieu">Lieu</label>
              <input
                id="jour-lieu"
                v-model="champs.journeeLieu"
                placeholder="ex : Ambovombe"
              />
            </div>
            <div class="modal-actions">
              <button
                type="button"
                class="btn btn-outline btn-sm"
                @click="fermerSousFormulaire"
              >
                Retour
              </button>
              <button
                type="submit"
                class="btn btn-primary btn-sm"
                :disabled="envoi"
              >
                Créer la journée
              </button>
            </div>
          </form>

          <form
            v-else-if="sousFormulaire.type === 'livrable'"
            @submit.prevent="ajouterLivrable"
          >
            <div class="field">
              <label for="liv-type">Type de livrable</label>
              <input
                id="liv-type"
                v-model="champs.livrableType"
                placeholder="ex : PV de formation"
                required
              />
            </div>
            <div class="field">
              <label for="liv-date">Date de production</label>
              <input id="liv-date" v-model="champs.livrableDate" type="date" />
            </div>
            <div class="modal-actions">
              <button
                type="button"
                class="btn btn-outline btn-sm"
                @click="fermerSousFormulaire"
              >
                Retour
              </button>
              <button
                type="submit"
                class="btn btn-primary btn-sm"
                :disabled="envoi"
              >
                Créer le livrable
              </button>
            </div>
          </form>
        </template>

        <template v-else-if="ongletSuivi === 'phases'">
          <div v-if="peutPlanifier" class="barre-suivi">
            <button
              class="btn btn-primary btn-sm"
              @click="ouvrirSousFormulaire('phase')"
            >
              + Ajouter une phase
            </button>
          </div>
          <p v-if="details[mdCourant.id].phases.length === 0" class="muted">
            Aucune phase définie pour ce district.
          </p>
          <div
            v-for="p in details[mdCourant.id].phases"
            :key="p.id"
            class="phase"
          >
            <div class="ligne-simple">
              <span>
                <strong>{{ p.numero_ordre ?? "–" }}. {{ p.libelle }}</strong>
                <small v-if="p.duree_prevue" class="muted">
                  ({{ p.duree_prevue }})</small
                >
              </span>
              <span class="actions-ligne">
                <span class="badge" :class="classeStatut(p.statut)">{{
                  p.statut
                }}</span>
                <template v-if="peutPlanifier">
                  <button
                    v-for="t in transitionsPhase(p.statut)"
                    :key="t.vers"
                    class="btn btn-outline btn-sm"
                    :disabled="envoi"
                    @click="changerStatutPhase(mdCourant.id, p, t.vers)"
                  >
                    {{ t.libelle }}
                  </button>
                </template>
              </span>
            </div>
            <p v-if="p.livrable_attendu" class="muted petit">
              Livrable attendu : {{ p.livrable_attendu }}
            </p>
            <ul v-if="p.livrables.length" class="list-clean">
              <li v-for="l in p.livrables" :key="l.id" class="ligne-simple">
                <span>
                  {{ l.type_livrable || "Livrable" }}
                  <small v-if="l.date_production" class="muted">
                    — {{ formaterDate(l.date_production) }}
                  </small>
                </span>
                <span class="actions-ligne">
                  <span
                    class="badge"
                    :class="l.signe ? 'badge-ok' : 'badge-neutral'"
                  >
                    {{ l.signe ? "Signé" : "Non signé" }}
                  </span>
                  <button
                    v-if="peutPlanifier && !l.signe"
                    class="btn btn-outline btn-sm"
                    :disabled="envoi"
                    @click="signerLivrable(mdCourant.id, l)"
                  >
                    Marquer signé
                  </button>
                </span>
              </li>
            </ul>
            <p v-else class="muted petit">Aucun livrable enregistré.</p>
            <button
              v-if="peutSaisir"
              class="btn btn-outline btn-sm"
              @click="ouvrirSousFormulaire('livrable', { phaseId: p.id })"
            >
              + Livrable
            </button>
          </div>
        </template>

        <template v-else>
          <div v-if="peutSaisir" class="barre-suivi">
            <button
              class="btn btn-primary btn-sm"
              @click="ouvrirSousFormulaire('journee')"
            >
              + Ajouter une journée
            </button>
          </div>
          <p v-if="details[mdCourant.id].journees.length === 0" class="muted">
            Aucune journée enregistrée pour ce district.
          </p>
          <ul v-else class="list-clean">
            <li
              v-for="j in details[mdCourant.id].journees"
              :key="j.id"
              class="ligne-simple"
            >
              <span>
                Jour {{ j.numero_jour ?? "–" }}
                <small class="muted">
                  — {{ formaterDateSimple(j.date) || "date à définir"
                  }}<template v-if="j.lieu">, {{ j.lieu }}</template>
                </small>
              </span>
              <span class="actions-ligne">
                <span class="badge" :class="classeStatut(j.statut)">{{
                  j.statut
                }}</span>
                <template v-if="peutSaisir">
                  <button
                    v-for="t in transitionsJournee(j.statut)"
                    :key="t.vers"
                    class="btn btn-outline btn-sm"
                    :disabled="envoi"
                    @click="changerStatutJournee(mdCourant.id, j, t.vers)"
                  >
                    {{ t.libelle }}
                  </button>
                </template>
              </span>
            </li>
          </ul>
        </template>
      </template>
    </ModalDialog>
  </div>
</template>

<style scoped>
.barre-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 0.6rem;
  margin-bottom: 1.5rem;
}

.btn-suppr {
  padding: 0;
  background: none;
  border: none;
  font: inherit;
  font-size: 0.85rem;
  color: #b0173f;
  cursor: pointer;
}

.btn-suppr:hover {
  text-decoration: underline;
}

.entete-axe,
.entete-equipe {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.entete-equipe h3 {
  margin: 0;
}

.ligne-district {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.6rem;
  padding: 0.55rem 0;
  border-bottom: 1px solid var(--border);
}

.actions-ligne {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 0.4rem;
}

.equipe-bloc {
  background: var(--bg-soft);
  border-radius: 18px;
  padding: 1rem 1.2rem;
  margin-bottom: 0.9rem;
}

.ligne-participant {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.4rem 0;
}

.actions-participant {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin-left: auto;
}

.lien-ajout {
  margin-top: 0.8rem;
}

/* Contenu des fenêtres */
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.6rem;
  margin-top: 1.2rem;
}

.entete-suivi {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
}

.onglets {
  display: flex;
  gap: 0.4rem;
  margin: 1rem 0;
  border-bottom: 1px solid var(--border);
}

.onglet {
  margin-bottom: -1px;
  padding: 0.5rem 0.9rem;
  background: none;
  border: none;
  border-bottom: 3px solid transparent;
  font: inherit;
  font-weight: 600;
  color: var(--muted);
  cursor: pointer;
}

.onglet.actif {
  color: var(--violet);
  border-bottom-color: var(--violet);
}

.barre-suivi {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 0.8rem;
}

.phase {
  padding: 0.7rem 0;
  border-bottom: 1px solid var(--border);
}

.phase:last-child {
  border-bottom: none;
}

.ligne-simple {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.6rem;
  padding: 0.3rem 0;
}

.petit {
  margin: 0.2rem 0 0.4rem;
  font-size: 0.85rem;
}

/* Tableau des indicateurs */
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

.cellule-actions {
  white-space: nowrap;
  text-align: right;
}

.cellule-actions .btn + .btn {
  margin-left: 0.4rem;
}

.saisie-courte {
  width: 100%;
  min-width: 8rem;
  padding: 0.4rem 0.6rem;
  border: 1px solid var(--border);
  border-radius: 10px;
  font: inherit;
}

select {
  width: 100%;
  padding: 0.65rem 0.8rem;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: #fff;
  font: inherit;
}
</style>
