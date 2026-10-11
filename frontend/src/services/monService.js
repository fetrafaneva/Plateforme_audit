import api from "./api";

export const obtenirMonService = (jours = 30) =>
  api
    .get("/service/mon-service", { params: { jours } })
    .then((res) => res.data);
