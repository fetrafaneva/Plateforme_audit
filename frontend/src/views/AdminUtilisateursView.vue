<script setup>
import { ref, reactive, onMounted } from "vue";
import ModalDialog from "../components/ModalDialog.vue";
import { useAuthStore } from "../stores/auth";
import {
  listerComptes,
  listerRoles,
  listerServices,
  creerCompte,
  changerStatutCompte,
} from "../services/utilisateurs";

const authStore = useAuthStore();

const comptes = ref([]);
const roles = ref([]);
const services = ref([]);
const chargement = ref(true);
const erreur = ref("");
const message = ref("");
const envoi = ref(false);

const modaleOuverte = ref(false);
const erreurModale = ref("");
const formulaire = reactive({
  nom: "",
  prenom: "",
  email: "",
  matricule: "",
  motDePasse: "",
  idService: "",
  idRole: "",
});

function messageErreur(e, defaut = "L'opération a échoué.") {
  const detail = e.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length) {
    return detail.map((d) => d.msg).join(" ; ");
  }
  return defaut;
}

function libelle(valeur) {
  return (valeur || "").replaceAll("_", " ");
}

async function charger() {
  chargement.value = true;
  erreur.value = "";
  try {
    const [c, r, s] = await Promise.all([
      listerComptes(),
      listerRoles(),
      listerServices(),
    ]);
    comptes.value = c;
    roles.value = r;
    services.value = s;
  } catch (e) {
    erreur.value = messageErreur(e, "Impossible de charger les comptes.");
  } finally {
    chargement.value = false;
  }
}

function ouvrirModale() {
  Object.assign(formulaire, {
    nom: "",
    prenom: "",
    email: "",
    matricule: "",
    motDePasse: "",
    idService: services.value[0]?.id_service ?? "",
    idRole: "",
  });
  erreurModale.value = "";
  modaleOuverte.value = true;
}

function fermerModale() {
  modaleOuverte.value = false;
  erreurModale.value = "";
}

async function soumettre() {
  erreurModale.value = "";
  envoi.value = true;
  try {
    const cree = await creerCompte({
      nom: formulaire.nom.trim(),
      prenom: formulaire.prenom.trim(),
      email: formulaire.email.trim(),
      matricule: formulaire.matricule.trim(),
      mot_de_passe: formulaire.motDePasse,
      id_service: Number(formulaire.idService),
      id_role: Number(formulaire.idRole),
    });
    fermerModale();
    message.value = `Compte créé pour ${cree.prenom} ${cree.nom}.`;
    await charger();
  } catch (e) {
    erreurModale.value = messageErreur(e, "Impossible de créer le compte.");
  } finally {
    envoi.value = false;
  }
}

async function basculerStatut(compte) {
  const vers = compte.statut === "actif" ? "inactif" : "actif";
  if (
    vers === "inactif" &&
    !window.confirm(`Désactiver le compte de ${compte.prenom} ${compte.nom} ?`)
  ) {
    return;
  }
  erreur.value = "";
  message.value = "";
  try {
    await changerStatutCompte(compte.id_utilisateur, vers);
    await charger();
  } catch (e) {
    erreur.value = messageErreur(e);
  }
}

onMounted(charger);
</script>

<template>
  <div>
    <header class="hero hero-compact">
      <div class="container">
        <p class="eyebrow" style="color: #fff; opacity: 0.85">Administration</p>
        <h1>Comptes utilisateurs</h1>
        <p class="hero-meta">
          Création des comptes, attribution des rôles, activation et
          désactivation.
        </p>
      </div>
    </header>

    <main class="container page">
      <div class="barre-actions">
        <button class="btn btn-primary btn-sm" @click="ouvrirModale">
          + Nouveau compte
        </button>
      </div>

      <p v-if="erreur" class="alert-error">{{ erreur }}</p>
      <p v-if="message" class="message-ok">{{ message }}</p>

      <section class="card">
        <p v-if="chargement" class="muted">Chargement...</p>
        <p v-else-if="comptes.length === 0" class="muted">Aucun compte.</p>
        <div v-else class="defilement">
          <table class="tableau">
            <thead>
              <tr>
                <th>Nom</th>
                <th>Email</th>
                <th>Matricule</th>
                <th>Rôle</th>
                <th>Service</th>
                <th>Statut</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="c in comptes" :key="c.id_utilisateur">
                <td>
                  <strong>{{ c.prenom }} {{ c.nom }}</strong>
                </td>
                <td>{{ c.email }}</td>
                <td>{{ c.matricule }}</td>
                <td>
                  <span class="badge badge-neutral">{{ libelle(c.role) }}</span>
                </td>
                <td>{{ c.service }}</td>
                <td>
                  <span
                    class="badge"
                    :class="c.statut === 'actif' ? 'badge-ok' : 'badge-off'"
                    >{{ c.statut }}</span
                  >
                </td>
                <td class="cellule-actions">
                  <button
                    class="btn btn-outline btn-sm"
                    :disabled="
                      c.id_utilisateur === authStore.utilisateur?.id_utilisateur
                    "
                    :title="
                      c.id_utilisateur === authStore.utilisateur?.id_utilisateur
                        ? 'Tu ne peux pas désactiver ton propre compte'
                        : ''
                    "
                    @click="basculerStatut(c)"
                  >
                    {{ c.statut === "actif" ? "Désactiver" : "Réactiver" }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </main>

    <ModalDialog
      v-if="modaleOuverte"
      titre="Nouveau compte"
      @fermer="fermerModale"
    >
      <p v-if="erreurModale" class="alert-error">{{ erreurModale }}</p>
      <form @submit.prevent="soumettre">
        <div class="grid-2">
          <div class="field">
            <label for="c-prenom">Prénom</label>
            <input id="c-prenom" v-model="formulaire.prenom" required />
          </div>
          <div class="field">
            <label for="c-nom">Nom</label>
            <input id="c-nom" v-model="formulaire.nom" required />
          </div>
        </div>
        <div class="field">
          <label for="c-email">Email</label>
          <input
            id="c-email"
            v-model="formulaire.email"
            type="email"
            required
          />
        </div>
        <div class="field">
          <label for="c-matricule">Matricule</label>
          <input id="c-matricule" v-model="formulaire.matricule" required />
        </div>
        <div class="field">
          <label for="c-mdp">Mot de passe (8 caractères minimum)</label>
          <input
            id="c-mdp"
            v-model="formulaire.motDePasse"
            type="password"
            minlength="8"
            autocomplete="new-password"
            required
          />
        </div>
        <div class="grid-2">
          <div class="field">
            <label for="c-service">Service</label>
            <select id="c-service" v-model="formulaire.idService" required>
              <option value="" disabled>Choisir un service</option>
              <option
                v-for="s in services"
                :key="s.id_service"
                :value="s.id_service"
              >
                {{ s.nom_service }}
              </option>
            </select>
          </div>
          <div class="field">
            <label for="c-role">Rôle</label>
            <select id="c-role" v-model="formulaire.idRole" required>
              <option value="" disabled>Choisir un rôle</option>
              <option v-for="r in roles" :key="r.id_role" :value="r.id_role">
                {{ libelle(r.nom_role) }}
              </option>
            </select>
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
            {{ envoi ? "Création..." : "Créer le compte" }}
          </button>
        </div>
      </form>
    </ModalDialog>
  </div>
</template>

<style scoped>
.barre-actions {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 1.5rem;
}

.message-ok {
  margin: 0 0 1rem;
  padding: 0.75rem 1rem;
  background: #d5faf5;
  color: #067a6f;
  border: 1px solid #a8efe6;
  border-radius: 14px;
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

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.6rem;
  margin-top: 1.2rem;
}
</style>
