<script setup>
import { ref, computed, onMounted } from "vue";
import ModalDialog from "../components/ModalDialog.vue";
import { useAuthStore } from "../stores/auth";
import {
  listerPeriodes,
  calculerPeriode,
  obtenirClassement,
  obtenirMonBenchmark,
  listerRapportsAudit,
} from "../services/benchmarking";

const authStore = useAuthStore();

const role = computed(() => authStore.utilisateur?.role);
// L'auditeur et l'administrateur voient le classement nominatif et peuvent
// clôturer une période. Le responsable hiérarchique ne voit que son périmètre.
const estAuditeur = computed(() =>
  ["auditeur", "administrateur"].includes(role.value)
);

const chargement = ref(true);
const erreur = ref("");
const message = ref("");

const periodes = ref([]);
const periodeChoisie = ref("");

const classement = ref(null);
const monBenchmark = ref(null);
const rapports = ref([]);

const onglet = ref("classement");
const rapportOuvert = ref(null);

const modaleCalcul = ref(false);
const periodeACalculer = ref("");
const calculEnCours = ref(false);
const erreurCalcul = ref("");

// --- Périodes proposées au calcul : les 12 derniers mois (mois courant en tête) ---
const periodesCandidates = computed(() => {
  const maintenant = new Date();
  const liste = [];
  for (let k = 0; k < 12; k += 1) {
    const d = new Date(maintenant.getFullYear(), maintenant.getMonth() - k, 1);
    const mois = String(d.getMonth() + 1).padStart(2, "0");
    liste.push(`${d.getFullYear()}-${mois}`);
  }
  return liste;
});

function libellePeriode(periode) {
  if (!periode) return "—";
  const [annee, mois] = periode.split("-");
  const d = new Date(Number(annee), Number(mois) - 1, 1);
  return d.toLocaleDateString("fr-FR", { month: "long", year: "numeric" });
}

function formaterDateHeure(d) {
  return d
    ? new Date(d).toLocaleString("fr-FR", {
        dateStyle: "short",
        timeStyle: "short",
      })
    : "—";
}

function messageErreur(e, defaut) {
  const detail = e.response?.data?.detail;
  return typeof detail === "string" ? detail : defaut;
}

// En dessous de 2 services classés dans un type, la médiane du type se confond
// avec le service lui-même : aucune lecture comparative n'est affichée.
const MIN_SERVICES_COMPARAISON = 2;
// Même facteur que le backend (app/core/benchmarking.py).
const FACTEUR_CONTROLE_APPROFONDI = 1.5;

// Un service se détache nettement de son type soit parce que la majorité des
// services comparables n'a aucune alerte (médiane nulle), soit parce que son
// taux atteint 1,5 fois la médiane du type.
function seDetache(ligne, repere) {
  const median = repere.taux_median;
  const medianeNulle = median === 0 && repere.nb_services_classes >= 3;
  return (
    medianeNulle ||
    (median > 0 &&
      ligne.taux_alertes >= median * FACTEUR_CONTROLE_APPROFONDI)
  );
}

// --- Lecture du risque d'une ligne par rapport aux repères de son type ---
function classeTaux(ligne, repere) {
  if (ligne.rang === null) return "badge-neutral";
  if (ligne.nb_alertes === 0) return "badge-ok";
  if ((repere?.nb_services_classes ?? 0) < MIN_SERVICES_COMPARAISON) {
    return "badge-neutral";
  }
  if (seDetache(ligne, repere)) return "badge-off";
  if (ligne.taux_alertes > repere.taux_median) return "badge-warn";
  return "badge-ok";
}

// Repères du type d'une ligne, dans la vue auditeur
const reperesParType = computed(() => {
  const index = {};
  (classement.value?.reperes ?? []).forEach((r) => {
    index[r.type] = r;
  });
  return index;
});

function repereDe(ligne) {
  return reperesParType.value[ligne.type] ?? null;
}

// Lignes groupées par type de service, pour ne pas mélanger communes et districts
const groupes = computed(() => {
  const parType = {};
  (classement.value?.lignes ?? []).forEach((ligne) => {
    (parType[ligne.type] = parType[ligne.type] ?? []).push(ligne);
  });
  return Object.entries(parType).map(([type, lignes]) => ({
    type,
    lignes,
    repere: reperesParType.value[type] ?? null,
  }));
});

// Position du service du responsable par rapport à la médiane de son type
const lecture = computed(() => {
  const ligne = monBenchmark.value?.service;
  const repere = monBenchmark.value?.reperes;
  if (!ligne || !repere) return null;
  const median = repere.taux_median;
  if (ligne.nb_alertes === 0) {
    return {
      ton: "badge-ok",
      texte: "Aucune alerte retenue sur la période.",
    };
  }
  if (repere.nb_services_classes < MIN_SERVICES_COMPARAISON) {
    return {
      ton: "badge-neutral",
      texte: `Seul service de type « ${ligne.type} » classé sur cette période : aucune comparaison possible.`,
    };
  }
  if (median === 0 && repere.nb_services_classes >= 3) {
    return {
      ton: "badge-off",
      texte: `Ton service a des alertes alors que la majorité des services classés de type « ${ligne.type} » n'en a aucune.`,
    };
  }
  if (repere.nb_services_classes === MIN_SERVICES_COMPARAISON) {
    // Sur deux services, la médiane est le milieu des deux valeurs : on compare
    // directement plutôt que d'invoquer une médiane que personne n'atteint.
    const plusExpose = ligne.rang === 1;
    return {
      ton: plusExpose ? "badge-warn" : "badge-ok",
      texte: `${
        plusExpose ? "Le plus exposé" : "Le moins exposé"
      } des ${repere.nb_services_classes} services classés de type « ${
        ligne.type
      } ».`,
    };
  }
  if (seDetache(ligne, repere)) {
    return {
      ton: "badge-off",
      texte: `Taux d'alertes nettement au-dessus de la médiane des services de type « ${ligne.type} » (${median} pour 100 accès).`,
    };
  }
  if (ligne.taux_alertes > median) {
    return {
      ton: "badge-warn",
      texte: `Taux d'alertes au-dessus de la médiane de son type (${median} pour 100 accès).`,
    };
  }
  return {
    ton: "badge-ok",
    texte: `Taux d'alertes au niveau de la médiane de son type (${median} pour 100 accès) ou en dessous.`,
  };
});

async function chargerDonnees() {
  chargement.value = true;
  erreur.value = "";
  message.value = "";
  try {
    const params = periodeChoisie.value
      ? { periode: periodeChoisie.value }
      : {};
    if (estAuditeur.value) {
      classement.value = await obtenirClassement(params);
      periodeChoisie.value = classement.value.periode;
      message.value = classement.value.message ?? "";
      rapports.value = await listerRapportsAudit({
        periode: classement.value.periode,
      });
    } else {
      monBenchmark.value = await obtenirMonBenchmark(params);
      periodeChoisie.value = monBenchmark.value.periode;
      message.value = monBenchmark.value.message ?? "";
    }
  } catch (e) {
    erreur.value = messageErreur(e, "Impossible de charger le benchmarking.");
  } finally {
    chargement.value = false;
  }
}

async function changerPeriode(periode) {
  if (periode === periodeChoisie.value) return;
  periodeChoisie.value = periode;
  await chargerDonnees();
}

function ouvrirCalcul() {
  periodeACalculer.value = periodesCandidates.value[0];
  erreurCalcul.value = "";
  modaleCalcul.value = true;
}

async function lancerCalcul() {
  calculEnCours.value = true;
  erreurCalcul.value = "";
  try {
    const resultat = await calculerPeriode(periodeACalculer.value);
    modaleCalcul.value = false;
    periodes.value = await listerPeriodes();
    periodeChoisie.value = resultat.periode;
    await chargerDonnees();
    message.value =
      `Période ${resultat.periode} clôturée : ${resultat.nb_services} service(s) mesuré(s), ` +
      `${resultat.nb_services_classes} classé(s), ${resultat.nb_rapports_generes} synthèse(s) générée(s).`;
  } catch (e) {
    erreurCalcul.value = messageErreur(e, "Le calcul a échoué.");
  } finally {
    calculEnCours.value = false;
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
  try {
    periodes.value = await listerPeriodes();
  } catch (e) {
    erreur.value = messageErreur(e, "Impossible de charger les périodes.");
  }
  await chargerDonnees();
});
</script>

<template>
  <div>
    <header class="hero hero-compact">
      <div class="container">
        <p class="eyebrow" style="color: #fff; opacity: 0.85">Audit</p>
        <h1>Benchmarking des services</h1>
        <p class="hero-meta">
          Comparaison du risque d'accès entre services de même type, période par
          période.
        </p>
      </div>
    </header>

    <main class="container page">
      <div class="barre">
        <div class="filtre">
          <span id="periode-libelle" class="filtre-libelle">Période</span>
          <div
            v-if="periodes.length"
            class="segments"
            role="radiogroup"
            aria-labelledby="periode-libelle"
          >
            <button
              v-for="p in periodes"
              :key="p.periode"
              type="button"
              class="segment"
              role="radio"
              :aria-checked="periodeChoisie === p.periode"
              :class="{ actif: periodeChoisie === p.periode }"
              @click="changerPeriode(p.periode)"
            >
              {{ p.periode }}
            </button>
          </div>
          <span v-else class="muted">aucune période calculée</span>
        </div>
        <button
          v-if="estAuditeur"
          class="btn btn-primary btn-sm"
          @click="ouvrirCalcul"
        >
          Clôturer une période
        </button>
      </div>

      <p v-if="erreur" class="alert-error">{{ erreur }}</p>
      <p v-if="message" class="info">{{ message }}</p>

      <p v-if="chargement" class="muted">Chargement...</p>

      <!-- ================= Vue auditeur / administrateur ================= -->
      <template v-else-if="estAuditeur && classement">
        <div class="onglets">
          <button
            v-for="o in [
              ['classement', 'Classement'],
              ['rapports', 'Synthèses d\'audit'],
            ]"
            :key="o[0]"
            type="button"
            class="onglet"
            :class="{ actif: onglet === o[0] }"
            @click="onglet = o[0]"
          >
            {{ o[1] }}
          </button>
        </div>

        <section v-if="onglet === 'classement'">
          <p class="muted explication">
            Rang 1 = service le plus exposé de son type. Un service est classé à
            partir de
            {{ classement.min_acces_classement }} accès journalisés sur la
            période : en dessous, les indicateurs sont trop instables pour être
            comparés.
          </p>

          <section v-for="g in groupes" :key="g.type" class="card">
            <div class="entete-groupe">
              <div>
                <p class="eyebrow">Type de service</p>
                <h2>{{ g.type }}</h2>
              </div>
              <p v-if="g.repere" class="muted reperes">
                {{ g.repere.nb_services_classes }} service(s) classé(s) ·
                taux médian {{ g.repere.taux_median }} · taux moyen
                {{ g.repere.taux_moyen }} · |z| médian
                {{ g.repere.score_median }}
                <template
                  v-if="g.repere.nb_services_classes < MIN_SERVICES_COMPARAISON"
                >
                  <br />
                  Un seul service classé : la médiane se confond avec lui, aucune
                  comparaison n'est faite.
                </template>
              </p>
            </div>

            <div class="defilement">
              <table class="tableau">
                <thead>
                  <tr>
                    <th>Rang</th>
                    <th>Service</th>
                    <th>Agents</th>
                    <th>Accès</th>
                    <th>Alertes</th>
                    <th>Dont critiques</th>
                    <th>Taux / 100 accès</th>
                    <th>Moyenne |z|</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="l in g.lignes" :key="l.id_benchmark">
                    <td>
                      <strong v-if="l.rang !== null">{{ l.rang }}</strong>
                      <span v-else class="muted">non classé</span>
                    </td>
                    <td>
                      <strong>{{ l.nom_service }}</strong>
                    </td>
                    <td>{{ l.nb_agents }}</td>
                    <td>{{ l.nb_acces }}</td>
                    <td>{{ l.nb_alertes }}</td>
                    <td>{{ l.nb_alertes_critiques }}</td>
                    <td>
                      <span class="badge" :class="classeTaux(l, repereDe(l))">
                        {{ l.taux_alertes }}
                      </span>
                    </td>
                    <td>
                      {{ l.score_risque_moyen }}
                      <small class="muted">({{ l.nb_scores }} accès)</small>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          <p v-if="!groupes.length" class="card muted">
            Aucun service mesuré sur cette période.
          </p>
        </section>

        <section v-else class="card">
          <p v-if="!rapports.length" class="muted">
            Aucune synthèse pour cette période.
          </p>
          <ul v-else class="list-clean">
            <li v-for="r in rapports" :key="r.id_rapport" class="ligne-rapport">
              <div>
                <strong>{{ r.nom_service }}</strong>
                <p class="muted">
                  Générée le {{ formaterDateHeure(r.date_generation) }}
                </p>
              </div>
              <button
                class="btn btn-outline btn-sm"
                @click="rapportOuvert = r"
              >
                Lire
              </button>
            </li>
          </ul>
        </section>
      </template>

      <!-- ================= Vue responsable hiérarchique ================= -->
      <template v-else-if="monBenchmark">
        <section class="card">
          <p class="eyebrow">Mon service · {{ libellePeriode(periodeChoisie) }}</p>
          <template v-if="monBenchmark.service">
            <h2>{{ monBenchmark.service.nom_service }}</h2>
            <div class="chiffres">
              <div class="chiffre">
                <span class="valeur">{{
                  monBenchmark.service.rang ?? "—"
                }}</span>
                <span class="libelle">
                  Rang
                  <template v-if="monBenchmark.reperes">
                    sur {{ monBenchmark.reperes.nb_services_classes }} services
                    de type « {{ monBenchmark.service.type }} »
                  </template>
                </span>
              </div>
              <div class="chiffre">
                <span class="valeur">{{
                  monBenchmark.service.taux_alertes
                }}</span>
                <span class="libelle">Alertes pour 100 accès</span>
              </div>
              <div class="chiffre">
                <span class="valeur">{{
                  monBenchmark.service.score_risque_moyen
                }}</span>
                <span class="libelle">
                  Moyenne des |z| ({{ monBenchmark.service.nb_scores }} accès
                  analysés)
                </span>
              </div>
              <div class="chiffre">
                <span class="valeur">{{ monBenchmark.service.nb_acces }}</span>
                <span class="libelle">
                  Accès journalisés ·
                  {{ monBenchmark.service.nb_agents }} agent(s)
                </span>
              </div>
            </div>
            <p v-if="lecture" class="lecture">
              <span class="badge" :class="lecture.ton">Lecture</span>
              {{ lecture.texte }}
            </p>
            <p class="muted explication">
              Les autres services ne sont pas nommés : tu te situes par rapport à
              la médiane et à la moyenne des services de même type.
            </p>
          </template>
          <p v-else class="muted">
            Ton service n'apparaît pas dans le benchmark de cette période.
          </p>
        </section>

        <section v-if="monBenchmark.sous_services.length" class="card">
          <h2>Mes sous-services</h2>
          <div class="defilement">
            <table class="tableau">
              <thead>
                <tr>
                  <th>Rang</th>
                  <th>Service</th>
                  <th>Type</th>
                  <th>Accès</th>
                  <th>Alertes</th>
                  <th>Taux / 100 accès</th>
                  <th>Moyenne |z|</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="l in monBenchmark.sous_services"
                  :key="l.id_benchmark"
                >
                  <td>
                    <strong v-if="l.rang !== null">{{ l.rang }}</strong>
                    <span v-else class="muted">non classé</span>
                  </td>
                  <td>
                    <strong>{{ l.nom_service }}</strong>
                  </td>
                  <td>{{ l.type }}</td>
                  <td>{{ l.nb_acces }}</td>
                  <td>{{ l.nb_alertes }}</td>
                  <td>{{ l.taux_alertes }}</td>
                  <td>{{ l.score_risque_moyen }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <section v-if="monBenchmark.historique.length > 1" class="card">
          <h2>Évolution de mon service</h2>
          <div class="defilement">
            <table class="tableau">
              <thead>
                <tr>
                  <th>Période</th>
                  <th>Accès</th>
                  <th>Alertes</th>
                  <th>Taux / 100 accès</th>
                  <th>Moyenne |z|</th>
                  <th>Rang</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="h in monBenchmark.historique" :key="h.id_benchmark">
                  <td>{{ h.periode }}</td>
                  <td>{{ h.nb_acces }}</td>
                  <td>{{ h.nb_alertes }}</td>
                  <td>{{ h.taux_alertes }}</td>
                  <td>{{ h.score_risque_moyen }}</td>
                  <td>{{ h.rang ?? "—" }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <section v-if="monBenchmark.rapport" class="card">
          <h2>Synthèse d'audit de la période</h2>
          <pre class="synthese">{{ monBenchmark.rapport.contenu }}</pre>
          <p class="muted">
            Générée le
            {{ formaterDateHeure(monBenchmark.rapport.date_generation) }}
          </p>
        </section>
      </template>
    </main>

    <!-- Lecture d'une synthèse (vue auditeur) -->
    <ModalDialog
      v-if="rapportOuvert"
      :titre="`Synthèse — ${rapportOuvert.nom_service}`"
      @fermer="rapportOuvert = null"
    >
      <pre class="synthese">{{ rapportOuvert.contenu }}</pre>
    </ModalDialog>

    <!-- Clôture d'une période -->
    <ModalDialog
      v-if="modaleCalcul"
      titre="Clôturer une période"
      @fermer="modaleCalcul = false"
    >
      <p v-if="erreurCalcul" class="alert-error">{{ erreurCalcul }}</p>
      <form @submit.prevent="lancerCalcul">
        <div class="field">
          <label for="periode">Mois à mesurer</label>
          <select id="periode" v-model="periodeACalculer" required>
            <option v-for="p in periodesCandidates" :key="p" :value="p">
              {{ p }} — {{ libellePeriode(p) }}
            </option>
          </select>
          <small class="muted">
            Le calcul agrège les accès et les alertes du mois (heure de
            Madagascar), classe les services par type et régénère une synthèse
            d'audit par service. Relancer un mois déjà mesuré remplace ses
            résultats.
          </small>
        </div>
        <div class="actions-modale">
          <button
            type="button"
            class="btn btn-outline btn-sm"
            @click="modaleCalcul = false"
          >
            Annuler
          </button>
          <button
            type="submit"
            class="btn btn-primary btn-sm"
            :disabled="calculEnCours"
          >
            {{ calculEnCours ? "Calcul..." : "Lancer le calcul" }}
          </button>
        </div>
      </form>
    </ModalDialog>
  </div>
</template>

<style scoped>
.barre {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.filtre {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.7rem;
  min-width: 0;
}

.filtre-libelle {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--muted);
}

.segments {
  display: inline-flex;
  gap: 0.25rem;
  max-width: 100%;
  padding: 0.3rem;
  overflow-x: auto;
  background: var(--bg-soft);
  border: 1px solid var(--border);
  border-radius: 999px;
}

.segment {
  flex: none;
  padding: 0.4rem 1rem;
  background: transparent;
  border: none;
  border-radius: 999px;
  font: inherit;
  font-size: 0.88rem;
  font-weight: 600;
  white-space: nowrap;
  color: var(--muted);
  cursor: pointer;
  transition: background 0.15s, color 0.15s, box-shadow 0.15s;
}

.segment:hover:not(.actif) {
  color: var(--violet);
}

.segment.actif {
  background: #fff;
  color: var(--violet);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.12);
}

.onglets {
  display: inline-flex;
  gap: 0.25rem;
  margin-bottom: 1.2rem;
  padding: 0.3rem;
  background: var(--bg-soft);
  border: 1px solid var(--border);
  border-radius: 999px;
}

.onglet {
  padding: 0.45rem 1.2rem;
  background: transparent;
  border: none;
  border-radius: 999px;
  font: inherit;
  font-weight: 600;
  font-size: 0.88rem;
  color: var(--muted);
  cursor: pointer;
}

.onglet.actif {
  background: #fff;
  color: var(--violet);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.12);
}

.info {
  background: #eef6ff;
  color: #1767a3;
  border: 1px solid #cfe4f7;
  padding: 0.75rem 1rem;
  border-radius: 14px;
  margin-bottom: 1rem;
}

.explication {
  font-size: 0.85rem;
  margin-bottom: 1.2rem;
}

.entete-groupe {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: space-between;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.entete-groupe h2 {
  margin: 0;
  text-transform: capitalize;
}

.reperes {
  font-size: 0.82rem;
  margin: 0;
}

.chiffres {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  margin: 1.2rem 0;
}

.chiffre {
  padding: 1rem;
  background: var(--bg-soft);
  border: 1px solid var(--border);
  border-radius: 18px;
}

.chiffre .valeur {
  display: block;
  font-size: 1.8rem;
  font-weight: 700;
  line-height: 1.1;
  color: var(--violet-dark);
}

.chiffre .libelle {
  display: block;
  margin-top: 0.3rem;
  font-size: 0.8rem;
  color: var(--muted);
}

.lecture {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
  margin: 0 0 0.5rem;
}

.ligne-rapport {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.8rem 0;
  border-bottom: 1px solid var(--border);
}

.ligne-rapport:last-child {
  border-bottom: none;
}

.ligne-rapport p {
  margin: 0;
  font-size: 0.82rem;
}

.synthese {
  margin: 0 0 0.8rem;
  padding: 1rem;
  background: var(--bg-soft);
  border: 1px solid var(--border);
  border-radius: 14px;
  font-family: inherit;
  font-size: 0.88rem;
  white-space: pre-wrap;
  word-break: break-word;
}

.badge-warn {
  background: #fff1d6;
  color: #9a5b00;
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

@media (max-width: 640px) {
  .filtre {
    flex: 1 1 100%;
    flex-direction: column;
    align-items: flex-start;
    gap: 0.4rem;
  }

  .segments {
    width: 100%;
  }
}
</style>
