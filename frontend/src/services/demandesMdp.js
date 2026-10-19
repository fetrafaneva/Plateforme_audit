import api from "./api";

const data = (res) => res.data;

// Sans être connecté (page de connexion) : l'adresse et le matricule doivent correspondre
// à un compte actif ; la réponse est toujours la même, que le compte existe ou non.
export const demanderSansConnexion = (payload) =>
  api.post("/demandes-mot-de-passe/", payload).then(data);

// Connecté (page « Mon compte »)
export const maDerniereDemande = () =>
  api.get("/demandes-mot-de-passe/moi").then(data);
export const demanderConnecte = (motif) =>
  api.post("/demandes-mot-de-passe/moi", { motif: motif || null }).then(data);

// Administrateur
export const listerDemandes = (statut = "en_attente") =>
  api.get("/demandes-mot-de-passe/", { params: { statut } }).then(data);
export const traiterDemande = (id) =>
  api.post(`/demandes-mot-de-passe/${id}/traiter`).then(data);
export const rejeterDemande = (id) =>
  api.post(`/demandes-mot-de-passe/${id}/rejeter`).then(data);
