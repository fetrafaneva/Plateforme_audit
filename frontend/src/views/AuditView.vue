<script setup>
import { ref, onMounted } from "vue";
import ModalDialog from "../components/ModalDialog.vue";
import {
  obtenirResume,
  verifierIntegrite,
  listerJournal,
  listerAlertes,
  modifierAlerte,
  ouvrirInvestigation,
  listerInvestigations,
  cloturerInvestigation,
  listerProfils,
  listerRessources,
} from "../services/audit";

const PAGE = 50;

const resume = ref(null);
const onglet = ref("alertes");
const erreur = ref("");
const message = ref("");
const envoi = ref(false);

// Alertes
const alertes = ref([]);
const filtreStatut = ref("");
const chargementAlertes = ref(false);

// Journal
const journal = ref([]);
const journalComplet = ref(false);
const chargementJournal = ref(false);

// Investigations
const investigations = ref([]);
const chargementInvestigations = ref(false);
const investigationACloturer = ref(null);
const conclusion = ref("");
const erreurModale = ref("");

// Profils
const profils = ref([]);
const ressourcesParId = ref({});
const chargementProfils = ref(false);

// Vérification de la chaîne
const verification = ref(null);
const verificationEnCours = ref(false);

function messageErreur(e, defaut = "L'opération a échoué.") {
  const detail = e.response?.data?.detail;
  return typeof detail === "string" ? detail : defaut;
}

function libelle(valeur) {
  return (valeur || "").replaceAll("_", " ");
}

function formaterDateHeure(d) {
  return d
    ? new Date(d).toLocaleString("fr-FR", { dateStyle: "short", timeStyle: "short" })
    : "—";
}

function formaterZ(z) {
  return `${z >= 0 ? "+" : ""}${z.toFixed(1)}`;
}

function courtHash(h) {
  return h ? `${h.slice(0, 10)}…` : "—";
}

function classeGravite(g) {
  if (g === "critique") return "badge-off";
  if (g === "moyen") return "badge-warn";
  return "badge-neutral";
}

function classeStatut(s) {
  if (s === "traitee" || s === "cloturee") return "badge-ok";
  if (s === "nouvelle" || s === "ouverte") return "badge-info";
  return "badge-neutral";
}

function nomsRessources(ids) {
  const noms = (ids || "")
    .split(",")
    .filter(Boolean)
    .map((id) => ressourcesParId.value[Number(id)] || `#${id}`);
  return noms.length ? noms.join(", ") : "—";
}

// ---------- Chargements ----------

async function chargerResume() {
  try {
    resume.value = await obtenirResume();
  } catch (e) {
    erreur.value = messageErreur(e, "Impossible de charger la synthèse.");
  }
}

async function chargerAlertes() {
  chargementAlertes.value = true;
  try {
    alertes.value = await listerAlertes(
      filtreStatut.value ? { statut: filtreStatut.value } : {}
    );
  } catch (e) {
    erreur.value = messageErreur(e, "Impossible de charger les alertes.");
  } finally {
    chargementAlertes.value = false;
  }
}

async function chargerJournal(reinitialiser = false) {
  if (reinitialiser) {
    journal.value = [];
    journalComplet.value = false;
  }
  chargementJournal.value = true;
  try {
    const page = await listerJournal({ limit: PAGE, offset: journal.value.length });
    journal.value = [...journal.value, ...page];
    journalComplet.value = page.length < PAGE;
  } catch (e) {
    erreur.value = messageErreur(e, "Impossible de charger le journal.");
  } finally {
    chargementJournal.value = false;
  }
}

async function chargerInvestigations() {
  chargementInvestigations.value = true;
  try {
    investigations.value = await listerInvestigations();
  } catch (e) {
    erreur.value = messageErreur(e, "Impossible de charger les investigations.");
  } finally {
    chargementInvestigations.value = false;
  }
}

async function chargerProfils() {
  chargementProfils.value = true;
  try {
    const [liste, ressources] = await Promise.all([listerProfils(), listerRessources()]);
    profils.value = liste;
    ressourcesParId.value = Object.fromEntries(
      ressources.map((r) => [r.id_ressource, r.type_ressource])
    );
  } catch (e) {
    erreur.value = messageErreur(e, "Impossible de charger les profils.");
  } finally {
    chargementProfils.value = false;
  }
}

function choisirOnglet(nom) {
  onglet.value = nom;
  erreur.value = "";
  if (nom === "alertes") chargerAlertes();
  if (nom === "journal" && journal.value.length === 0) chargerJournal(true);
  if (nom === "investigations") chargerInvestigations();
  if (nom === "profils") chargerProfils();
}

// ---------- Actions ----------

async function verifier() {
  verificationEnCours.value = true;
  verification.value = null;
  erreur.value = "";
  try {
    verification.value = await verifierIntegrite();
  } catch (e) {
    erreur.value = messageErreur(e, "La vérification a échoué.");
  } finally {
    verificationEnCours.value = false;
  }
}

async function ouvrirEnquete(alerte) {
  message.value = "";
  erreur.value = "";
  envoi.value = true;
  try {
    await ouvrirInvestigation(alerte.id_alerte);
    await chargerResume();
    choisirOnglet("investigations");
    message.value = "Investigation ouverte.";
  } catch (e) {
    erreur.value = messageErreur(e);
  } finally {
    envoi.value = false;
  }
}

async function marquerFausseAlerte(alerte) {
  message.value = "";
  erreur.value = "";
  envoi.value = true;
  try {
    await modifierAlerte(alerte.id_alerte, "fausse_alerte");
    await Promise.all([chargerAlertes(), chargerResume()]);
  } catch (e) {
    erreur.value = messageErreur(e);
  } finally {
    envoi.value = false;
  }
}

function ouvrirCloture(investigation) {
  investigationACloturer.value = investigation;
  conclusion.value = "";
  erreurModale.value = "";
}

function fermerCloture() {
  investigationACloturer.value = null;
  erreurModale.value = "";
}

async function confirmerCloture() {
  erreurModale.value = "";
  envoi.value = true;
  try {
    await cloturerInvestigation(
      investigationACloturer.value.id_investigation,
      conclusion.value.trim()
    );
    fermerCloture();
    await Promise.all([chargerInvestigations(), chargerResume()]);
    message.value = "Investigation clôturée.";
  } catch (e) {
    erreurModale.value = messageErreur(e);
  } finally {
    envoi.value = false;
  }
}

onMounted(() => {
  chargerResume();
  chargerAlertes();
});
</script>

<template>
  <div>
    <header class="hero hero-compact">
      <div class="container">
        <p class="eyebrow" style="color: #fff; opacity: 0.85">Audit</p>
        <h1>Audit comportemental</h1>
        <p class="hero-meta">
          Journal d'accès inviolable, détection d'anomalies et investigations.
        </p>
      </div>
    </header>

    <main class="container page">
      <!-- Synthèse -->
      <section class="stats">
        <div class="card card-hover stat">
          <span class="stat-valeur">{{ resume ? resume.nb_entrees_journal : "…" }}</span>
          <span class="stat-label">Accès journalisés</span>
        </div>
        <div class="card card-hover stat">
          <span class="stat-valeur">{{ resume ? resume.nb_alertes_nouvelles : "…" }}</span>
          <span class="stat-label">Alertes nouvelles</span>
        </div>
        <div class="card card-hover stat">
          <span class="stat-valeur">{{
            resume ? resume.nb_alertes_critiques_ouvertes : "…"
          }}</span>
          <span class="stat-label">Critiques ouvertes</span>
        </div>
        <div class="card card-hover stat">
          <span class="stat-valeur">{{
            resume ? resume.nb_investigations_ouvertes : "…"
          }}</span>
          <span class="stat-label">Investigations ouvertes</span>
        </div>
      </section>

      <!-- Intégrité de la chaîne -->
      <section class="card">
        <div class="ligne-integrite">
          <div>
            <p class="eyebrow">Intégrité du journal</p>
            <p class="muted" style="margin: 0">
              Rejoue toute la chaîne de hash et signale la première entrée modifiée.
            </p>
          </div>
          <button
            class="btn btn-primary btn-sm"
            :disabled="verificationEnCours"
            @click="verifier"
          >
            {{ verificationEnCours ? "Vérification..." : "Vérifier l'intégrité" }}
          </button>
        </div>
        <p v-if="verification && verification.intact" class="verif verif-ok">
          Chaîne intacte : {{ verification.nb_entrees_verifiees }} entrées vérifiées.
        </p>
        <p v-else-if="verification" class="verif verif-ko">
          Chaîne corrompue à partir de l'entrée n°{{
            verification.premiere_entree_corrompue
          }}
          ({{ verification.nb_entrees_verifiees }} entrées examinées).
        </p>
      </section>

      <p v-if="erreur" class="alert-error">{{ erreur }}</p>
      <p v-if="message" class="verif verif-ok">{{ message }}</p>

      <!-- Onglets -->
      <div class="onglets">
        <button
          v-for="o in [
            ['alertes', 'Alertes'],
            ['investigations', 'Investigations'],
            ['journal', 'Journal d\'accès'],
            ['profils', 'Profils'],
          ]"
          :key="o[0]"
          type="button"
          class="onglet"
          :class="{ actif: onglet === o[0] }"
          @click="choisirOnglet(o[0])"
        >
          {{ o[1] }}
        </button>
      </div>

      <!-- Alertes -->
      <section v-if="onglet === 'alertes'" class="card">
        <div class="barre-filtre">
          <label for="filtre-statut">Statut</label>
          <select id="filtre-statut" v-model="filtreStatut" @change="chargerAlertes">
            <option value="">Toutes</option>
            <option value="nouvelle">Nouvelles</option>
            <option value="en_investigation">En investigation</option>
            <option value="traitee">Traitées</option>
            <option value="fausse_alerte">Fausses alertes</option>
          </select>
        </div>
        <p v-if="chargementAlertes" class="muted">Chargement...</p>
        <p v-else-if="alertes.length === 0" class="muted">Aucune alerte.</p>
        <div v-else class="defilement">
          <table class="tableau">
            <thead>
              <tr>
                <th>Gravité</th>
                <th>Utilisateur</th>
                <th>Accès du</th>
                <th>Z-score</th>
                <th>Statut</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="a in alertes" :key="a.id_alerte">
                <td>
                  <span class="badge" :class="classeGravite(a.niveau_gravite)">{{
                    a.niveau_gravite
                  }}</span>
                </td>
                <td>{{ a.nom_utilisateur }}</td>
                <td>{{ formaterDateHeure(a.horodatage) }}</td>
                <td>
                  <strong>{{ formaterZ(a.z_score) }}</strong>
                </td>
                <td>
                  <span class="badge" :class="classeStatut(a.statut)">{{
                    libelle(a.statut)
                  }}</span>
                </td>
                <td class="cellule-actions">
                  <template v-if="a.statut === 'nouvelle'">
                    <button
                      class="btn btn-primary btn-sm"
                      :disabled="envoi"
                      @click="ouvrirEnquete(a)"
                    >
                      Enquêter
                    </button>
                    <button
                      class="btn btn-outline btn-sm"
                      :disabled="envoi"
                      @click="marquerFausseAlerte(a)"
                    >
                      Fausse alerte
                    </button>
                  </template>
                  <button
                    v-else-if="a.statut === 'en_investigation'"
                    class="btn btn-outline btn-sm"
                    @click="choisirOnglet('investigations')"
                  >
                    Voir l'enquête
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- Investigations -->
      <section v-else-if="onglet === 'investigations'" class="card">
        <p v-if="chargementInvestigations" class="muted">Chargement...</p>
        <p v-else-if="investigations.length === 0" class="muted">
          Aucune investigation.
        </p>
        <ul v-else class="list-clean">
          <li v-for="i in investigations" :key="i.id_investigation" class="investigation">
            <div class="ligne-simple">
              <span>
                <strong>Enquête n°{{ i.id_investigation }}</strong>
                sur {{ i.nom_utilisateur }}
                <span class="badge" :class="classeGravite(i.niveau_gravite)">{{
                  i.niveau_gravite
                }}</span>
              </span>
              <span class="actions-ligne">
                <span class="badge" :class="classeStatut(i.statut)">{{ i.statut }}</span>
                <button
                  v-if="i.statut === 'ouverte'"
                  class="btn btn-outline btn-sm"
                  @click="ouvrirCloture(i)"
                >
                  Clôturer
                </button>
              </span>
            </div>
            <p class="muted petit">
              Enquêteur : {{ i.nom_enqueteur }} · ouverte le
              {{ formaterDateHeure(i.date_ouverture) }}
              <template v-if="i.date_cloture">
                · clôturée le {{ formaterDateHeure(i.date_cloture) }}
              </template>
            </p>
            <p v-if="i.conclusion" class="conclusion">{{ i.conclusion }}</p>
          </li>
        </ul>
      </section>

      <!-- Journal -->
      <section v-else-if="onglet === 'journal'" class="card">
        <p v-if="journal.length === 0 && chargementJournal" class="muted">Chargement...</p>
        <p v-else-if="journal.length === 0" class="muted">Le journal est vide.</p>
        <template v-else>
          <div class="defilement">
            <table class="tableau">
              <thead>
                <tr>
                  <th>N°</th>
                  <th>Date</th>
                  <th>Utilisateur</th>
                  <th>Action</th>
                  <th>Ressource</th>
                  <th>IP</th>
                  <th>Hash</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="e in journal" :key="e.id_entree">
                  <td>{{ e.id_entree }}</td>
                  <td>{{ formaterDateHeure(e.horodatage) }}</td>
                  <td>{{ e.nom_utilisateur }}</td>
                  <td>{{ e.type_action }}</td>
                  <td>{{ e.type_ressource }}</td>
                  <td>{{ e.adresse_ip }}</td>
                  <td>
                    <code :title="e.hash_entree">{{ courtHash(e.hash_entree) }}</code>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="barre-suivi">
            <button
              v-if="!journalComplet"
              class="btn btn-outline btn-sm"
              :disabled="chargementJournal"
              @click="chargerJournal()"
            >
              {{ chargementJournal ? "Chargement..." : "Charger plus" }}
            </button>
            <span v-else class="muted petit">Fin du journal ({{ journal.length }} entrées).</span>
          </div>
        </template>
      </section>

      <!-- Profils -->
      <section v-else class="card">
        <p v-if="chargementProfils" class="muted">Chargement...</p>
        <p v-else-if="profils.length === 0" class="muted">Aucun profil calculé.</p>
        <div v-else class="defilement">
          <table class="tableau">
            <thead>
              <tr>
                <th>Utilisateur</th>
                <th>Période</th>
                <th>Accès / jour</th>
                <th>Horaires habituels</th>
                <th>Ressources habituelles</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="p in profils" :key="p.id_profil">
                <td>{{ p.nom_utilisateur }}</td>
                <td>{{ p.periode_reference }}</td>
                <td>
                  <strong>{{ p.volume_moyen.toFixed(1) }}</strong>
                </td>
                <td>{{ p.horaires_habituels }}</td>
                <td>{{ nomsRessources(p.perimetre_habituel) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </main>

    <!-- Clôture d'une investigation -->
    <ModalDialog
      v-if="investigationACloturer"
      :titre="`Clôturer l'enquête n°${investigationACloturer.id_investigation}`"
      @fermer="fermerCloture"
    >
      <p v-if="erreurModale" class="alert-error">{{ erreurModale }}</p>
      <form @submit.prevent="confirmerCloture">
        <div class="field">
          <label for="conclusion">Conclusion</label>
          <textarea
            id="conclusion"
            v-model="conclusion"
            rows="4"
            maxlength="500"
            required
            placeholder="Résultat de l'enquête, décision prise..."
          ></textarea>
          <small class="muted">{{ conclusion.length }}/500</small>
        </div>
        <div class="modal-actions">
          <button type="button" class="btn btn-outline btn-sm" @click="fermerCloture">
            Annuler
          </button>
          <button
            type="submit"
            class="btn btn-primary btn-sm"
            :disabled="envoi || !conclusion.trim()"
          >
            Clôturer
          </button>
        </div>
      </form>
    </ModalDialog>
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

.ligne-integrite {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.verif {
  margin: 1rem 0 0;
  padding: 0.75rem 1rem;
  border-radius: 14px;
}

.verif-ok {
  background: #d5faf5;
  color: #067a6f;
  border: 1px solid #a8efe6;
}

.verif-ko {
  background: #fff0f4;
  color: #b0173f;
  border: 1px solid #ffc9d6;
}

.badge-warn {
  background: #fff1d6;
  color: #9a5b00;
}

.onglets {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin: 0.5rem 0 1.2rem;
  border-bottom: 1px solid var(--border);
}

.onglet {
  margin-bottom: -1px;
  padding: 0.6rem 1rem;
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

.barre-filtre {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  margin-bottom: 1rem;
}

.barre-filtre label {
  margin: 0;
}

.barre-filtre select {
  width: auto;
  min-width: 11rem;
}

.barre-suivi {
  display: flex;
  justify-content: center;
  margin-top: 1rem;
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

.cellule-actions {
  white-space: nowrap;
  text-align: right;
}

.cellule-actions .btn + .btn {
  margin-left: 0.4rem;
}

.investigation {
  padding: 0.9rem 0;
  border-bottom: 1px solid var(--border);
}

.investigation:last-child {
  border-bottom: none;
}

.ligne-simple {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 0.6rem;
}

.actions-ligne {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.petit {
  margin: 0.3rem 0 0;
  font-size: 0.85rem;
}

.conclusion {
  margin: 0.5rem 0 0;
  padding: 0.7rem 1rem;
  background: var(--bg-soft);
  border-radius: 14px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.6rem;
  margin-top: 1.2rem;
}

code {
  font-size: 0.8rem;
}
</style>