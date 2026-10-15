import api from "./api";

const data = (res) => res.data;

export const listerNotifications = () => api.get("/notifications/").then(data);
export const marquerLue = (id) =>
  api.post(`/notifications/${id}/lue`).then(data);
export const toutLire = () => api.post("/notifications/tout-lire").then(data);
