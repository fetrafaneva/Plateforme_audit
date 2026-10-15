import api from "./api";

const data = (res) => res.data;

// La liste des districts et des types d'activité vient de services/missions.js
// (listerDistricts, listerTypesActivite) ; ici : création, modification, suppression.

export const creerDistrict = (payload) =>
  api.post("/districts/", payload).then(data);
export const modifierDistrict = (id, payload) =>
  api.patch(`/districts/${id}`, payload).then(data);
export const supprimerDistrict = (id) => api.delete(`/districts/${id}`);

// Import d'un fichier CSV. api.js impose « application/json » par défaut : pour un
// fichier il faut le remplacer, sinon axios convertirait le FormData en JSON.
export const importerDistricts = (formData) =>
  api
    .post("/districts/import", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    })
    .then(data);

export const creerTypeActivite = (payload) =>
  api.post("/types-activite/", payload).then(data);
export const modifierTypeActivite = (id, payload) =>
  api.patch(`/types-activite/${id}`, payload).then(data);
export const supprimerTypeActivite = (id) =>
  api.delete(`/types-activite/${id}`);
