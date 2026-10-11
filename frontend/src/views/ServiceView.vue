<script setup>
import { ref, onMounted } from "vue";
import { obtenirMonService } from "../services/monService";

const donnees = ref(null);
const jours = ref(30);
const chargement = ref(true);
const erreur = ref("");

function messageErreur(e, defaut) {
  const detail = e.response?.data?.detail;
  return typeof detail === "string" ? detail : defaut;
}

async function charger() {
  chargement.value = true;
  erreur.value = "";
  try {
    donnees.value = await obtenirMonService(jours.value);
  } catch (e) {
    erreur.value = messageErreur(
      e,
      "Impossible de charger les données du service."
    );
  } finally {
    chargement.value = false;
  }
}

function libelle(valeur) {
  return (valeur || "").replaceAll("_", " ");
}

function formaterDateHeure(d) {
  return d
    ? new Date(d).toLocaleString("fr-FR", {
        dateStyle: "short",
        timeStyle: "short",
      })
    : "—";
}

function formaterDate(d) {
  return d ? new Date(d).toLocaleDateString("fr-FR") : "—";
}

function formaterZ(z) {
  return `${z >= 0 ? "+" : ""}${z.toFixed(1)}`;
}

function classeNiveau(niveau) {
  if (niveau === "eleve") return "badge-off";
  if (niveau === "modere") return "badge-warn";
  return "badge-ok";
}

function libelleNiveau(niveau) {
  return { eleve: "Élevé", modere: "Modéré", aucun: "Aucun" }[niveau] ?? niveau;
}

function classeGravite(g) {
  if (g === "critique") return "badge-off";
  if (g === "moyen") return "badge-warn";
  return "badge-neutral";
}

onMounted(charger);
</script>

<template>
  <div>
    <header class="hero hero-compact">
      <div class="container">
        <p class="eyebrow" style="color: #fff; opacity: 0.85">Mon service</p>
        <h1>{{ donnees ? donnees.nom_service : "Mon service" }}</h1>
        <p class="hero-meta">
          Niveau de risque des agents de ton périmètre, à partir des alertes du
          journal d'accès.
        </p>
      </div>
    </header>

    <main class="container page">
      <div class="barre-filtre">
        <label for="periode">Période</label>
        <select id="periode" v-model.number="jours" @change="charger">
          <option :value="7">7 derniers jours</option>
          <option :value="30">30 derniers jours</option>
          <option :value="90">90 derniers jours</option>
        </select>
      </div>

      <p v-if="erreur" class="alert-error">{{ erreur }}</p>
      <p v-if="chargement && !donnees" class="card">Chargement...</p>

      <template v-if="donnees">
        <section class="stats">
          <div class="card card-hover stat">
            <span class="stat-valeur">{{ donnees.nb_agents }}</span>
            <span class="stat-label">Agents suivis</span>
          </div>
          <div class="card card-hover stat">
            <span class="stat-valeur">{{ donnees.nb_alertes }}</span>
            <span class="stat-label">Alertes ({{ donnees.jours }} j)</span>
          </div>
          <div class="card card-hover stat">
            <span class="stat-valeur">{{ donnees.score_risque_moyen }}</span>
            <span class="stat-label">Score de risque moyen</span>
          </div>
        </section>

        <!-- Classement des agents -->
        <section class="card">
          <p class="eyebrow">Classement des agents</p>
          <p v-if="donnees.agents.length === 0" class="muted">
            Aucun agent dans ce périmètre.
          </p>
          <div v-else class="defilement">
            <table class="tableau">
              <thead>
                <tr>
                  <th>Rang</th>
                  <th>Agent</th>
                  <th>Rôle</th>
                  <th>Service</th>
                  <th>Accès</th>
                  <th>Alertes</th>
                  <th>Critiques</th>
                  <th>Missions</th>
                  <th>Risque</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="a in donnees.agents" :key="a.id_utilisateur">
                  <td>
                    <strong>{{ a.rang }}</strong>
                  </td>
                  <td>{{ a.nom_utilisateur }}</td>
                  <td>{{ libelle(a.role) }}</td>
                  <td>{{ a.service }}</td>
                  <td>{{ a.nb_acces }}</td>
                  <td>{{ a.nb_alertes }}</td>
                  <td>{{ a.nb_alertes_critiques }}</td>
                  <td>{{ a.nb_missions }}</td>
                  <td>
                    <span class="badge" :class="classeNiveau(a.niveau_risque)"
                      >{{ libelleNiveau(a.niveau_risque) }} ·
                      {{ a.points_risque }} pts</span
                    >
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <p class="muted petit">
            Points : alerte critique = 5, moyenne = 3, faible = 1 (les fausses
            alertes ne sont pas comptées). Niveau modéré dès 1 point, élevé dès
            5.
          </p>
        </section>

        <!-- Comparaison des services -->
        <section v-if="donnees.services.length > 1" class="card">
          <p class="eyebrow">Comparaison des services</p>
          <div class="defilement">
            <table class="tableau">
              <thead>
                <tr>
                  <th>Rang</th>
                  <th>Service</th>
                  <th>Type</th>
                  <th>Agents</th>
                  <th>Alertes</th>
                  <th>Score moyen</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="s in donnees.services" :key="s.id_service">
                  <td>
                    <strong>{{ s.rang }}</strong>
                  </td>
                  <td>{{ s.nom_service }}</td>
                  <td>{{ s.type }}</td>
                  <td>{{ s.nb_agents }}</td>
                  <td>{{ s.nb_alertes }}</td>
                  <td>
                    <strong>{{ s.score_risque_moyen }}</strong>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <p class="muted petit">
            Rang 1 = service au score de risque moyen le plus élevé.
          </p>
        </section>

        <!-- Alertes récentes -->
        <section class="card">
          <p class="eyebrow">Alertes récentes</p>
          <p v-if="donnees.alertes_recentes.length === 0" class="muted">
            Aucune alerte sur la période.
          </p>
          <ul v-else class="list-clean">
            <li
              v-for="a in donnees.alertes_recentes"
              :key="a.id_alerte"
              class="ligne-alerte"
            >
              <span class="badge" :class="classeGravite(a.niveau_gravite)">{{
                a.niveau_gravite
              }}</span>
              <strong>{{ a.nom_utilisateur }}</strong>
              <span class="muted">{{ formaterDateHeure(a.horodatage) }}</span>
              <span>z = {{ formaterZ(a.z_score) }}</span>
              <span class="badge badge-neutral">{{ libelle(a.statut) }}</span>
            </li>
          </ul>
        </section>
      </template>
    </main>
  </div>
</template>

<style scoped>
.barre-filtre {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  margin-bottom: 1.5rem;
}

.barre-filtre label {
  margin: 0;
}

.barre-filtre select {
  width: auto;
  min-width: 11rem;
}

.stats {
  display: grid;
  gap: 1.5rem;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
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

.petit {
  margin: 0.8rem 0 0;
  font-size: 0.82rem;
}

.ligne-alerte {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.7rem;
  padding: 0.55rem 0;
  border-bottom: 1px solid var(--border);
}
</style>
