import api from "./api";

const data = (res) => res.data;

export const listerComptes = () => api.get("/utilisateurs/gestion").then(data);
export const listerRoles = () => api.get("/utilisateurs/roles").then(data);
export const listerServices = () =>
  api.get("/utilisateurs/services").then(data);
export const creerCompte = (payload) =>
  api.post("/auth/register", payload).then(data);
export const changerStatutCompte = (id, statut) =>
  api.patch(`/utilisateurs/${id}/statut`, { statut }).then(data);
