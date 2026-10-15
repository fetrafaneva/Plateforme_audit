<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import ModalDialog from "../components/ModalDialog.vue";
import { confirmer } from "../composables/useConfirmation";
import { listerDistricts, listerTypesActivite } from "../services/missions";
import {
  creerDistrict,
  modifierDistrict,
  supprimerDistrict,
  importerDistricts,
  creerTypeActivite,
  modifierTypeActivite,
  supprimerTypeActivite,
} from "../services/referentiels";

const PROVINCES = [
  "Antananarivo",
  "Antsiranana",
  "Fianarantsoa",
  "Mahajanga",
  "Toamasina",
  "Toliara",
];

const onglet = ref("districts");
const districts = ref([]);
const types = ref([]);
const recherche = ref("");
const chargement = ref(true);
const erreur = ref("");
const message = ref("");
const envoi = ref(false);

// Fenêtre ouverte : { type: "district" | "type" | "import", element? }
const modale = ref(null);
const erreurModale = ref("");
const formulaire = reactive({
  nom: "",
  region: "",
  province: "",
  electrifie: "non",
  libelle: "",
});
const fichier = ref(null);
const resultatImport = ref(null);

function normaliser(texte) {
  return (texte || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

function messageErreur(e, defaut = "L'opération a échoué.") {
  const detail = e.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length)
    return detail.map((d) => d.msg).join(" ; ");
  return defaut;
}

const districtsFiltres = computed(() => {
  const terme = normaliser(recherche.value);
  if (!terme) return districts.value;
  return districts.value.filter((d) =>
    [d.nom, d.region, d.province].some((champ) =>
      normaliser(champ).includes(terme)
    )
  );
});

async function charger() {
  chargement.value = true;
  erreur.value = "";
  try {
    const [listeDistricts, listeTypes] = await Promise.all([
      listerDistricts(),
      listerTypesActivite(),
    ]);
    districts.value = [...listeDistricts].sort((a, b) =>
      a.nom.localeCompare(b.nom, "fr")
    );
    types.value = [...listeTypes].sort((a, b) =>
      a.libelle.localeCompare(b.libelle, "fr")
    );
  } catch (e) {
    erreur.value = messageErreur(e, "Impossible de charger les référentiels.");
  } finally {
    chargement.value = false;
  }
}

function ouvrir(type, element = null) {
  erreurModale.value = "";
  resultatImport.value = null;
  fichier.value = null;
  Object.assign(formulaire, {
    nom: element?.nom ?? "",
    region: element?.region ?? "",
    province: element?.province ?? "",
    electrifie: element?.electrifie ? "oui" : "non",
    libelle: element?.libelle ?? "",
  });
  modale.value = { type, element };
}

function fermer() {
  modale.value = null;
  erreurModale.value = "";
}

async function executer(action, texteSucces) {
  erreurModale.value = "";
  envoi.value = true;
  try {
    await action();
    fermer();
    message.value = texteSucces;
    await charger();
  } catch (e) {
    erreurModale.value = messageErreur(e);
  } finally {
    envoi.value = false;
  }
}

function enregistrerDistrict() {
  const nom = formulaire.nom.trim();
  const element = modale.value.element;
  const doublon = districts.value.some(
    (d) => normaliser(d.nom) === normaliser(nom) && d.id !== element?.id
  );
  if (doublon) {
    erreurModale.value = "Un district porte déjà ce nom.";
    return;
  }
  const payload = {
    nom,
    region: formulaire.region.trim() || null,
    province: formulaire.province.trim() || null,
    electrifie: formulaire.electrifie === "oui",
  };
  return element
    ? executer(() => modifierDistrict(element.id, payload), "District modifié.")
    : executer(() => creerDistrict(payload), "District ajouté.");
}

async function retirerDistrict(district) {
  const ok = await confirmer({
    titre: "Supprimer le district",
    message: `« ${district.nom} » sera supprimé du référentiel.`,
    libelleConfirmer: "Supprimer",
    danger: true,
  });
  if (!ok) return;
  erreur.value = "";
  message.value = "";
  try {
    await supprimerDistrict(district.id);
    message.value = "District supprimé.";
    await charger();
  } catch (e) {
    erreur.value = messageErreur(e);
  }
}

function enregistrerType() {
  const libelle = formulaire.libelle.trim();
  const element = modale.value.element;
  const doublon = types.value.some(
    (t) => normaliser(t.libelle) === normaliser(libelle) && t.id !== element?.id
  );
  if (doublon) {
    erreurModale.value = "Un type d'activité porte déjà ce libellé.";
    return;
  }
  return element
    ? executer(
        () => modifierTypeActivite(element.id, { libelle }),
        "Type d'activité modifié."
      )
    : executer(() => creerTypeActivite({ libelle }), "Type d'activité ajouté.");
}

async function retirerType(type) {
  const ok = await confirmer({
    titre: "Supprimer le type d'activité",
    message: `« ${type.libelle} » sera supprimé du référentiel.`,
    libelleConfirmer: "Supprimer",
    danger: true,
  });
  if (!ok) return;
  erreur.value = "";
  message.value = "";
  try {
    await supprimerTypeActivite(type.id);
    message.value = "Type d'activité supprimé.";
    await charger();
  } catch (e) {
    erreur.value = messageErreur(e);
  }
}

function choisirFichier(evenement) {
  fichier.value = evenement.target.files?.[0] ?? null;
  erreurModale.value = "";
}

async function importer() {
  if (!fichier.value) {
    erreurModale.value = "Choisis un fichier CSV.";
    return;
  }
  const donnees = new FormData();
  donnees.append("fichier", fichier.value);
  erreurModale.value = "";
  envoi.value = true;
  try {
    resultatImport.value = await importerDistricts(donnees);
    await charger();
  } catch (e) {
    erreurModale.value = messageErreur(e, "L'import a échoué.");
  } finally {
    envoi.value = false;
  }
}

onMounted(charger);
</script>

<template>
  <div>
    <header class="hero hero-compact">
      <div class="container">
        <p class="eyebrow" style="color: #fff; opacity: 0.85">Administration</p>
        <h1>Référentiels</h1>
        <p class="hero-meta">
          Districts de Madagascar et types d'activité proposés dans les
          missions.
        </p>
      </div>
    </header>

    <main class="container page">
      <p v-if="erreur" class="alert-error">{{ erreur }}</p>
      <p v-if="message" class="message-ok">{{ message }}</p>

      <div class="onglets">
        <button
          type="button"
          class="onglet"
          :class="{ actif: onglet === 'districts' }"
          @click="onglet = 'districts'"
        >
          Districts ({{ districts.length }})
        </button>
        <button
          type="button"
          class="onglet"
          :class="{ actif: onglet === 'types' }"
          @click="onglet = 'types'"
        >
          Types d'activité ({{ types.length }})
        </button>
      </div>

      <!-- Districts -->
      <section v-if="onglet === 'districts'" class="card">
        <div class="barre">
          <input
            v-model="recherche"
            class="recherche"
            type="search"
            placeholder="Rechercher un district, une région, une province..."
            aria-label="Rechercher"
          />
          <div class="actions">
            <button class="btn btn-outline btn-sm" @click="ouvrir('import')">
              Importer un CSV
            </button>
            <button class="btn btn-primary btn-sm" @click="ouvrir('district')">
              + Ajouter un district
            </button>
          </div>
        </div>
        <p v-if="chargement" class="muted">Chargement...</p>
        <p v-else-if="districts.length === 0" class="muted">
          Aucun district. Importe un fichier CSV ou ajoute-les un par un.
        </p>
        <p v-else-if="districtsFiltres.length === 0" class="muted">
          Aucun résultat.
        </p>
        <div v-else class="defilement">
          <table class="tableau">
            <thead>
              <tr>
                <th>Nom</th>
                <th>Région</th>
                <th>Province</th>
                <th>Électrifié</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="d in districtsFiltres" :key="d.id">
                <td>
                  <strong>{{ d.nom }}</strong>
                </td>
                <td>{{ d.region || "—" }}</td>
                <td>{{ d.province || "—" }}</td>
                <td>
                  <span
                    class="badge"
                    :class="d.electrifie ? 'badge-ok' : 'badge-neutral'"
                  >
                    {{ d.electrifie ? "Oui" : "Non / inconnu" }}
                  </span>
                </td>
                <td class="cellule-actions">
                  <button
                    class="btn btn-outline btn-sm"
                    @click="ouvrir('district', d)"
                  >
                    Modifier
                  </button>
                  <button class="btn-suppr" @click="retirerDistrict(d)">
                    Supprimer
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- Types d'activité -->
      <section v-else class="card">
        <div class="barre">
          <p class="muted" style="margin: 0">
            Activités proposées pour les phases d'un district (ex. Installation
            serveur).
          </p>
          <button class="btn btn-primary btn-sm" @click="ouvrir('type')">
            + Ajouter un type
          </button>
        </div>
        <p v-if="chargement" class="muted">Chargement...</p>
        <p v-else-if="types.length === 0" class="muted">
          Aucun type d'activité.
        </p>
        <ul v-else class="list-clean">
          <li v-for="t in types" :key="t.id" class="ligne-type">
            <strong>{{ t.libelle }}</strong>
            <span class="cellule-actions">
              <button class="btn btn-outline btn-sm" @click="ouvrir('type', t)">
                Modifier
              </button>
              <button class="btn-suppr" @click="retirerType(t)">
                Supprimer
              </button>
            </span>
          </li>
        </ul>
      </section>
    </main>

    <!-- District : ajout ou modification -->
    <ModalDialog
      v-if="modale && modale.type === 'district'"
      :titre="modale.element ? 'Modifier le district' : 'Nouveau district'"
      @fermer="fermer"
    >
      <p v-if="erreurModale" class="alert-error">{{ erreurModale }}</p>
      <form @submit.prevent="enregistrerDistrict">
        <div class="field">
          <label for="d-nom">Nom</label>
          <input id="d-nom" v-model="formulaire.nom" required maxlength="200" />
        </div>
        <div class="grid-2">
          <div class="field">
            <label for="d-region">Région</label>
            <input id="d-region" v-model="formulaire.region" maxlength="200" />
          </div>
          <div class="field">
            <label for="d-province">Province</label>
            <input
              id="d-province"
              v-model="formulaire.province"
              list="provinces"
              maxlength="200"
            />
            <datalist id="provinces">
              <option v-for="p in PROVINCES" :key="p" :value="p"></option>
            </datalist>
          </div>
        </div>
        <div class="field">
          <label for="d-elec">Électrifié</label>
          <select id="d-elec" v-model="formulaire.electrifie">
            <option value="non">Non / inconnu</option>
            <option value="oui">Oui</option>
          </select>
        </div>
        <div class="actions-modale">
          <button type="button" class="btn btn-outline btn-sm" @click="fermer">
            Annuler
          </button>
          <button
            type="submit"
            class="btn btn-primary btn-sm"
            :disabled="envoi"
          >
            {{ modale.element ? "Enregistrer" : "Ajouter" }}
          </button>
        </div>
      </form>
    </ModalDialog>

    <!-- Type d'activité : ajout ou modification -->
    <ModalDialog
      v-if="modale && modale.type === 'type'"
      :titre="
        modale.element
          ? 'Modifier le type d\'activité'
          : 'Nouveau type d\'activité'
      "
      @fermer="fermer"
    >
      <p v-if="erreurModale" class="alert-error">{{ erreurModale }}</p>
      <form @submit.prevent="enregistrerType">
        <div class="field">
          <label for="t-libelle">Libellé</label>
          <input
            id="t-libelle"
            v-model="formulaire.libelle"
            required
            maxlength="200"
            placeholder="ex : Installation serveur"
          />
        </div>
        <div class="actions-modale">
          <button type="button" class="btn btn-outline btn-sm" @click="fermer">
            Annuler
          </button>
          <button
            type="submit"
            class="btn btn-primary btn-sm"
            :disabled="envoi"
          >
            {{ modale.element ? "Enregistrer" : "Ajouter" }}
          </button>
        </div>
      </form>
    </ModalDialog>

    <!-- Import CSV -->
    <ModalDialog
      v-if="modale && modale.type === 'import'"
      titre="Importer des districts (CSV)"
      @fermer="fermer"
    >
      <p v-if="erreurModale" class="alert-error">{{ erreurModale }}</p>

      <template v-if="resultatImport">
        <p class="message-ok">
          {{ resultatImport.crees }} district(s) ajouté(s),
          {{ resultatImport.ignores }} déjà présent(s).
        </p>
        <ul v-if="resultatImport.erreurs.length" class="list-clean">
          <li v-for="(e, i) in resultatImport.erreurs" :key="i" class="muted">
            {{ e }}
          </li>
        </ul>
        <div class="actions-modale">
          <button type="button" class="btn btn-primary btn-sm" @click="fermer">
            Fermer
          </button>
        </div>
      </template>

      <form v-else @submit.prevent="importer">
        <p class="muted">
          Première ligne : les noms de colonnes
          <code>nom;region;province;electrifie</code>
          (seule « nom » est obligatoire ; séparateur « ; » ou « , »). Un
          district dont le nom existe déjà est ignoré.
        </p>
        <div class="field">
          <label for="i-fichier">Fichier CSV (1 Mo maximum)</label>
          <input
            id="i-fichier"
            type="file"
            accept=".csv,.txt,text/csv"
            required
            @change="choisirFichier"
          />
        </div>
        <div class="actions-modale">
          <button type="button" class="btn btn-outline btn-sm" @click="fermer">
            Annuler
          </button>
          <button
            type="submit"
            class="btn btn-primary btn-sm"
            :disabled="envoi"
          >
            {{ envoi ? "Import..." : "Importer" }}
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

.onglets {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin: 0 0 1.2rem;
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

.barre {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.8rem;
  margin-bottom: 1rem;
}

.recherche {
  flex: 1 1 260px;
  max-width: 420px;
}

.actions {
  display: flex;
  gap: 0.6rem;
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
  display: inline-flex;
  align-items: center;
  gap: 0.8rem;
  white-space: nowrap;
}

td.cellule-actions {
  display: table-cell;
  text-align: right;
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

.ligne-type {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.7rem 0;
  border-bottom: 1px solid var(--border);
}

.actions-modale {
  display: flex;
  justify-content: flex-end;
  gap: 0.6rem;
  margin-top: 1.2rem;
}
</style>
