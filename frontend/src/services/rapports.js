import api from "./api";

const data = (res) => res.data;

export const listerRapports = (params = {}) =>
  api.get("/rapports/", { params }).then(data);
export const listerAxesDisponibles = () =>
  api.get("/rapports/axes-disponibles").then(data);
export const creerRapport = (axeId) =>
  api.post("/rapports/", { axe_id: axeId }).then(data);
export const obtenirRapport = (id) => api.get(`/rapports/${id}`).then(data);
export const modifierRapport = (id, payload) =>
  api.patch(`/rapports/${id}`, payload).then(data);
export const remplacerDifficultes = (id, liste) =>
  api.put(`/rapports/${id}/difficultes`, liste).then(data);

// Pièces jointes. api.js impose « application/json » par défaut : pour un
// fichier il faut le remplacer, sinon axios convertirait le FormData en JSON.
export const deposerPiece = (id, formData) =>
  api
    .post(`/rapports/${id}/pieces`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    })
    .then(data);
export const supprimerPiece = (id, idPiece) =>
  api.delete(`/rapports/${id}/pieces/${idPiece}`);
export const recupererPiece = (id, idPiece) =>
  api
    .get(`/rapports/${id}/pieces/${idPiece}/fichier`, { responseType: "blob" })
    .then(data);

// Soumission et validation
export const soumettreRapport = (id) =>
  api.post(`/rapports/${id}/soumettre`).then(data);
export const validerRapport = (id) =>
  api.post(`/rapports/${id}/valider`).then(data);
export const demanderCorrection = (id, commentaire) =>
  api.post(`/rapports/${id}/demander-correction`, { commentaire }).then(data);

// PDF d'un rapport validé. Le fichier est récupéré avec le jeton d'accès puis
// enregistré par le navigateur. En cas d'erreur, la réponse (un JSON) arrive
// sous forme de blob : on la relit pour que l'appelant puisse afficher le message.
export async function telechargerPdf(id, numeroAxe) {
  try {
    const blob = await api
      .get(`/rapports/${id}/pdf`, { responseType: "blob" })
      .then(data);
    const url = URL.createObjectURL(blob);
    const lien = document.createElement("a");
    lien.href = url;
    lien.download = `rapport_mission_axe${numeroAxe}_${id}.pdf`;
    lien.click();
    URL.revokeObjectURL(url);
  } catch (e) {
    if (e.response?.data instanceof Blob) {
      try {
        e.response.data = JSON.parse(await e.response.data.text());
      } catch {
        /* réponse non JSON : on garde l'erreur telle quelle */
      }
    }
    throw e;
  }
}
