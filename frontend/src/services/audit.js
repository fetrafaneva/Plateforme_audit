import api from "./api";

const data = (res) => res.data;

// Synthèse
export const obtenirResume = () => api.get("/audit/resume").then(data);

// Intégrité de la chaîne du journal
export const verifierIntegrite = () => api.get("/journal/verify").then(data);

// Journal d'accès (paginé)
export const listerJournal = (params = {}) =>
  api.get("/audit/journal", { params }).then(data);

// Alertes
export const listerAlertes = (params = {}) =>
  api.get("/audit/alertes", { params }).then(data);
export const modifierAlerte = (id, statut) =>
  api.patch(`/audit/alertes/${id}`, { statut }).then(data);

// Investigations
export const ouvrirInvestigation = (idAlerte) =>
  api.post(`/audit/alertes/${idAlerte}/investigation`).then(data);
export const listerInvestigations = (params = {}) =>
  api.get("/audit/investigations", { params }).then(data);
export const cloturerInvestigation = (id, conclusion) =>
  api.patch(`/audit/investigations/${id}/cloture`, { conclusion }).then(data);

// Profils et ressources
export const listerProfils = () => api.get("/audit/profils").then(data);
export const listerRessources = () => api.get("/audit/ressources").then(data);
