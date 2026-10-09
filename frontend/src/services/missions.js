import api from "./api";

const data = (res) => res.data;

// Missions
export const listerMissions = () => api.get("/missions/").then(data);
export const creerMission = (payload) =>
  api.post("/missions/", payload).then(data);
export const obtenirMission = (id) => api.get(`/missions/${id}`).then(data);
export const modifierMission = (id, payload) =>
  api.patch(`/missions/${id}`, payload).then(data);

// Axes
export const listerAxes = (missionId) =>
  api.get("/axes/", { params: { mission_id: missionId } }).then(data);
export const creerAxe = (payload) => api.post("/axes/", payload).then(data);

// Équipes
export const listerEquipes = (axeId) =>
  api.get("/equipes/", { params: { axe_id: axeId } }).then(data);
export const creerEquipe = (payload) =>
  api.post("/equipes/", payload).then(data);

// Participants
export const listerParticipants = (equipeId) =>
  api.get("/participants/", { params: { equipe_id: equipeId } }).then(data);
export const creerParticipant = (payload) =>
  api.post("/participants/", payload).then(data);

// Districts et liaison axe ↔ district
export const listerDistricts = () => api.get("/districts/").then(data);
export const listerMissionsDistricts = (axeId) =>
  api.get("/missions-districts/", { params: { axe_id: axeId } }).then(data);
export const creerMissionDistrict = (payload) =>
  api.post("/missions-districts/", payload).then(data);
export const modifierMissionDistrict = (id, payload) =>
  api.patch(`/missions-districts/${id}`, payload).then(data);

// Types d'activité (référentiel)
export const listerTypesActivite = () => api.get("/types-activite/").then(data);

// Phases
export const listerPhases = (missionDistrictId) =>
  api
    .get("/phases/", { params: { mission_district_id: missionDistrictId } })
    .then(data);
export const modifierPhase = (id, payload) =>
  api.patch(`/phases/${id}`, payload).then(data);

// Journées
export const listerJournees = (missionDistrictId) =>
  api
    .get("/journees/", { params: { mission_district_id: missionDistrictId } })
    .then(data);
export const modifierJournee = (id, payload) =>
  api.patch(`/journees/${id}`, payload).then(data);

// Livrables
export const listerLivrables = (phaseId) =>
  api.get("/livrables/", { params: { phase_id: phaseId } }).then(data);
export const modifierLivrable = (id, payload) =>
  api.patch(`/livrables/${id}`, payload).then(data);

// Indicateurs de performance
export const listerIndicateurs = (missionId) =>
  api
    .get("/indicateurs-performance/", { params: { mission_id: missionId } })
    .then(data);
export const modifierIndicateur = (id, payload) =>
  api.patch(`/indicateurs-performance/${id}`, payload).then(data);

// Suppressions (pas encore utilisées dans l'interface)
export const supprimerParticipant = (id) => api.delete(`/participants/${id}`);
export const supprimerEquipe = (id) => api.delete(`/equipes/${id}`);
export const supprimerAxe = (id) => api.delete(`/axes/${id}`);

// Créations (phases, journées, livrables, indicateurs)
export const creerPhase = (payload) => api.post("/phases/", payload).then(data);
export const creerJournee = (payload) =>
  api.post("/journees/", payload).then(data);
export const creerLivrable = (payload) =>
  api.post("/livrables/", payload).then(data);
export const creerIndicateur = (payload) =>
  api.post("/indicateurs-performance/", payload).then(data);
