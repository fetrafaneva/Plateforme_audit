import api from "./api";

export function listerMissions() {
  return api.get("/missions/").then((res) => res.data);
}

export function creerMission(payload) {
  return api.post("/missions/", payload).then((res) => res.data);
}

export function obtenirMission(id) {
  return api.get(`/missions/${id}`).then((res) => res.data);
}

export function listerAxes(missionId) {
  return api
    .get("/axes/", { params: { mission_id: missionId } })
    .then((res) => res.data);
}

export function listerEquipes(axeId) {
  return api
    .get("/equipes/", { params: { axe_id: axeId } })
    .then((res) => res.data);
}

export function listerParticipants(equipeId) {
  return api
    .get("/participants/", { params: { equipe_id: equipeId } })
    .then((res) => res.data);
}

export function listerMissionsDistricts(axeId) {
  return api
    .get("/missions-districts/", { params: { axe_id: axeId } })
    .then((res) => res.data);
}

export function listerDistricts() {
  return api.get("/districts/").then((res) => res.data);
}

export function modifierMission(id, payload) {
  return api.patch(`/missions/${id}`, payload).then((res) => res.data);
}

export function modifierMissionDistrict(id, payload) {
  return api
    .patch(`/missions-districts/${id}`, payload)
    .then((res) => res.data);
}

export function supprimerParticipant(id) {
  return api.delete(`/participants/${id}`);
}

export function supprimerEquipe(id) {
  return api.delete(`/equipes/${id}`);
}

export function supprimerAxe(id) {
  return api.delete(`/axes/${id}`);
}
